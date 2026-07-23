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
        value=str(access_token),
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
