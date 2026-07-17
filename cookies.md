class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that reads tokens from cookies.

    Falls back to reading JWT tokens from HTTP-only cookies if the token
    is not provided in the Authorization header. This approach is more
    secure against XSS attacks.
    """

    def authenticate(self, request):
        auth_header = self.get_header(request)

        if auth_header is None:
            raw_token = request.COOKIES.get('access_token')

            if raw_token is None:
                return None
        else:
            raw_token = self.get_raw_token(auth_header)
            if raw_token is None:
                return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except Exception:
            raise AuthenticationFailed("Invalid token in cookies")

        return self.get_user(validated_token), validated_token

class CookieTokenObtainPairView(TokenObtainPairView):
    """Handle user login and issue JWT tokens via HTTP-only cookies.

    Authenticates user credentials and returns JWT tokens stored in
    secure HTTP-only cookies to prevent XSS attacks.
    """
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate user and set tokens in cookies.

        Validates username and password, generates JWT tokens, and stores
        them in secure HTTP-only cookies.

        Args:
            request: HTTP request containing username and password
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments

        Returns:
            Response: Login success message with user data and tokens in
                secure HTTP-only cookies
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh = serializer.validated_data['refresh']
        access = serializer.validated_data['access']
        user = serializer.validated_data.get('user')

        response = Response({
            'detail': 'Login successfully!',
            'user': user
        }, status=status.HTTP_200_OK)

        return set_auth_cookies(response, access, refresh)


class LogoutView(APIView):
    """Handle user logout and invalidate authentication tokens.

    Blacklists the refresh token and clears authentication cookies to
    securely log out users and prevent further token usage.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """Log out user by invalidating tokens and clearing cookies.

        Retrieves refresh token from cookies, adds it to blacklist, and
        removes authentication cookies from the response.

        Args:
            request: HTTP request from authenticated user
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments

        Returns:
            Response: Success message with status 200
        """
        refresh_token = request.COOKIES.get('refresh_token')
        blacklist_refresh_token(refresh_token)

        response = Response(
            {"detail": "Successfully logged out. Tokens have been deleted."},
            status=status.HTTP_200_OK
        )
        return clear_auth_cookies(response)


class CookieRefreshView(TokenRefreshView):
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
            *args: Variable positional arguments
            **kwargs: Variable keyword arguments

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

utils.py
"""Utility functions for authentication API operations."""

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken


def blacklist_refresh_token(refresh_token):
    """Blacklist a refresh token to invalidate it.

    Prevents further use of a refresh token by adding it to the blacklist.
    Safely handles cases where token is invalid or already blacklisted.

    Args:
        refresh_token: Token string to blacklist

    Returns:
        bool: True if blacklisting was successful, False if token invalid
    """
    if not refresh_token:
        return False

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
        return True
    except TokenError:
        return False


def set_auth_cookies(response, access_token, refresh_token):
    """Set authentication tokens as HTTP-only cookies.

    Configures secure, HTTP-only cookies for storing JWT access and refresh
    tokens. These cookies are protected against XSS attacks.

    Args:
        response: Django response object to set cookies on
        access_token: JWT access token string
        refresh_token: JWT refresh token string

    Returns:
        Response: Modified response object with cookies set
    """
    response.set_cookie(
        key='access_token',
        value=str(access_token),
        httponly=True,
        secure=True,
        samesite='Lax'
    )
    response.set_cookie(
        key='refresh_token',
        value=str(refresh_token),
        httponly=True,
        secure=True,
        samesite='Lax'
    )
    return response


def set_access_cookie(response, access_token):
    """Set only the access token as HTTP-only cookie.

    Configures secure HTTP-only cookie for storing JWT access token.
    Used when refreshing tokens without updating the refresh token.

    Args:
        response: Django response object to set cookie on
        access_token: JWT access token string

    Returns:
        Response: Modified response object with access cookie set
    """
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        secure=True,
        samesite='Lax'
    )
    return response


def clear_auth_cookies(response):
    """Clear authentication cookies from response.

    Removes access and refresh token cookies by setting them to empty values.

    Args:
        response: Django response object to clear cookies from

    Returns:
        Response: Modified response object with cookies cleared
    """
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response
