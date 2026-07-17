from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT authentication that reads tokens from cookies.

    Falls back to reading JWT tokens from HTTP-only cookies if the token
    is not provided in the Authorization header. This approach is more
    secure against XSS attacks.
    """

    def authenticate(self, request):
        """Authenticate user using JWT token from header or cookies.

        First attempts to get token from Authorization header. If not found,
        falls back to reading the 'access_token' cookie.

        Args:
            request: HTTP request object

        Returns:
            tuple: (user, validated_token) if authentication successful
            None: If no token found in header or cookies

        Raises:
            AuthenticationFailed: If token is invalid or expired
        """
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
