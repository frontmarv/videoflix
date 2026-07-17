from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import RegisterSerializer, LoginSerializer
from .utils import set_auth_cookies, clear_auth_cookies, set_access_cookie, blacklist_refresh_token
from ..tokens import account_activation_token
from core.task_service import TaskService

User = get_user_model()


class LoginView(APIView):
    """Handle user login and issue JWT tokens via HTTP-only cookies.

    Authenticates user credentials and returns JWT tokens stored in
    secure HTTP-only cookies to prevent XSS attacks.
    """

    def post(self, request):
        """Authenticate user and set tokens in cookies.

        Validates email and password, generates JWT tokens, and stores
        them in secure HTTP-only cookies.

        Args:
            request: HTTP request containing email and password

        Returns:
            Response: Login success message with user data and tokens in
                secure HTTP-only cookies
        """
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        token_data = serializer.save()
        user = token_data['user']

        if not user.is_activated:
            return Response(
                {'detail': 'Account has not been activated yet. Please check your email for the activation link.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        access_token = token_data['access']
        refresh_token = token_data['refresh']

        response = Response(
            {
                'detail': 'Login successfully!',
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                }
            },
            status=status.HTTP_200_OK,
        )

        return set_auth_cookies(response, access_token, refresh_token)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        activation_path = reverse(
            'activate', kwargs={'uidb64': uidb64, 'token': token})
        activation_link = request.build_absolute_uri(activation_path)

        TaskService.send_activation_email(user.pk, activation_link)

        return Response(
            {
                'user': {
                    'id': user.id,
                    'email': user.email,
                },
                'token': token,
            },
            status=status.HTTP_201_CREATED,
        )


class ActivateAccountView(APIView):
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid activation link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_activation_token.check_token(user, token):
            return Response(
                {'detail': 'Activation link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_activated:
            return Response(
                {'detail': 'Account is already activated.'},
                status=status.HTTP_200_OK,
            )

        user.is_activated = True
        user.save()

        return Response(
            {"message": "Account successfully activated."},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """Handle user logout and invalidate authentication tokens.

    Blacklists the refresh token, clears authentication cookies, and
    deactivates the user account to securely log out users and prevent
    further token usage.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Log out user by invalidating tokens and clearing cookies.

        Retrieves refresh token from cookies, adds it to blacklist,
        deactivates the user account, and removes authentication cookies
        from the response.

        Args:
            request: HTTP request from authenticated user

        Returns:
            Response: Success message with status 200
        """
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'detail': 'No refresh token found.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not blacklist_refresh_token(refresh_token):
            return Response(
                {'detail': 'Invalid or already expired refresh token.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        response = Response(
            {"detail": "Logout successful! All tokens have been invalidated."},
            status=status.HTTP_200_OK
        )
        return clear_auth_cookies(response)


class CookieTokenRefreshView(TokenRefreshView):
    """Handle token refresh using refresh token from cookies.

    Validates refresh token, generates new access token, and updates the
    access token cookie without requiring re-authentication.
    """

    def post(self, request, *args, **kwargs):
        """Refresh the access token using refresh token from cookies.

        Retrieves refresh token from cookies, validates it, generates
        a new access token, and updates the access token cookie.

        Args:
            request: HTTP request containing refresh token in cookies

        Returns:
            Response: New access token with 200 status or error with
                401 status if refresh token not found or invalid
        """
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token not found in cookies'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = self.get_serializer(data={'refresh': refresh_token})
        serializer.is_valid(raise_exception=True)

        access_token = serializer.validated_data.get('access')
        response = Response(
            {'detail': 'Token refreshed'},
            status=status.HTTP_200_OK
        )
        return set_access_cookie(response, access_token)
