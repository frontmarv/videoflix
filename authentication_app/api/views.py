from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenRefreshView

from .serializers import RegisterSerializer, LoginSerializer, PasswordResetRequestSerializer, PasswordResetConfirmSerializer
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


class PasswordResetRequestView(APIView):
    """Handle password reset request.

    Sends a password reset link to the user's email if the account exists.
    """

    def post(self, request):
        """Initiate password reset by sending reset link to email.

        Validates that user with provided email exists, generates a
        password reset token, constructs the reset link, and sends it
        via email asynchronously.

        Args:
            request: HTTP request containing email

        Returns:
            Response: Success message if email is valid, or error if invalid
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_404_NOT_FOUND
            )

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)

        reset_path = reverse(
            'password_confirm', kwargs={'uidb64': uidb64, 'token': token})
        reset_link = request.build_absolute_uri(reset_path)

        TaskService.send_password_reset_email(user.pk, reset_link)

        return Response(
            {'detail': 'An email has been sent to reset your password.',
             'reset_path': reset_path},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    """Handle password reset confirmation.

    Validates reset token and updates user's password.
    """

    def get(self, request, uidb64, token):
        """Validate password reset link.

        Validates that the reset token and uidb64 are valid.
        Used when user clicks the reset link in email.

        Args:
            request: HTTP request
            uidb64: Base64-encoded user ID
            token: Password reset token

        Returns:
            Response: Success message if token is valid, or error if
                token invalid or expired
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid password reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_activation_token.check_token(user, token):
            return Response(
                {'detail': 'Password reset link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {'detail': 'Password reset link is valid. You can now set a new password.'},
            status=status.HTTP_200_OK,
        )

    def post(self, request, uidb64, token):
        """Confirm password reset with token and new password.

        Decodes the uidb64, validates the reset token, validates the
        request body payload, and updates the user's password if all
        validations pass.

        Args:
            request: HTTP request containing new_password and confirm_password
            uidb64: Base64-encoded user ID
            token: Password reset token


        Returns:
            Response: Success message if password reset, or error if
                token invalid, expired, or passwords don't match
        """
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {'detail': 'Invalid password reset link.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not account_activation_token.check_token(user, token):
            return Response(
                {'detail': 'Password reset link is invalid or has expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()

        return Response(
            {'detail': 'Your Password has been successfully reset.'},
            status=status.HTTP_200_OK,
        )
