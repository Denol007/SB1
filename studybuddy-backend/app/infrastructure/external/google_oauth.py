"""Google OAuth 2.0 client for user authentication.

This module provides a client for Google OAuth 2.0 authentication flow:
1. Generate authorization URL for user consent
2. Exchange authorization code for access/refresh tokens
3. Retrieve user information from Google

Example:
    >>> from app.core.config import Settings
    >>> settings = Settings()
    >>> client = GoogleOAuthClient(settings)
    >>> auth_url = client.get_authorization_url(state="csrf-token")
    >>> # User authorizes, receives code
    >>> tokens = await client.exchange_code_for_token(code)
    >>> user_info = await client.get_user_info(tokens["access_token"])
"""

from typing import Any
from urllib.parse import urlencode

import httpx

from app.core.config import Settings


class GoogleOAuthClient:
    """Client for Google OAuth 2.0 authentication.

    Handles the complete OAuth flow including authorization URL generation,
    token exchange, and user information retrieval.

    Attributes:
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret
        redirect_uri: Callback URL for OAuth flow
        auth_url: Google authorization endpoint
        token_url: Google token exchange endpoint
        userinfo_url: Google user info endpoint
    """

    def __init__(self, settings: Settings) -> None:
        """Initialize Google OAuth client with settings.

        Args:
            settings: Application settings containing OAuth credentials
        """
        self.client_id = settings.GOOGLE_CLIENT_ID
        self.client_secret = settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = settings.GOOGLE_REDIRECT_URI

        # Google OAuth 2.0 endpoints
        self.auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"

        # OAuth scopes required
        self.scopes = [
            "openid",
            "email",
            "profile",
        ]

    def get_authorization_url(self, state: str) -> str:
        """Generate Google OAuth authorization URL.

        Creates a URL that redirects the user to Google's consent screen.
        The state parameter is used for CSRF protection.

        Args:
            state: Random string for CSRF protection (verify on callback)

        Returns:
            Complete authorization URL with all required parameters

        Example:
            >>> client = GoogleOAuthClient(settings)
            >>> url = client.get_authorization_url(state="random-token")
            >>> # Redirect user to this URL
        """
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "consent",  # Force consent screen for refresh token
        }

        return f"{self.auth_url}?{urlencode(params)}"

    async def exchange_code_for_token(self, code: str) -> dict[str, Any]:
        """Exchange authorization code for access and refresh tokens.

        After user authorizes, Google redirects to callback URL with a code.
        This method exchanges that code for tokens.

        Args:
            code: Authorization code from Google callback

        Returns:
            Dictionary containing:
                - access_token: Token for API requests (expires in 1 hour)
                - refresh_token: Token to get new access tokens
                - expires_in: Seconds until access token expires
                - token_type: Should be "Bearer"
                - scope: Granted scopes

        Raises:
            Exception: If token exchange fails (invalid code, network error, etc.)

        Example:
            >>> tokens = await client.exchange_code_for_token("auth-code")
            >>> access_token = tokens["access_token"]
        """
        data = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as http_client:
            response = await http_client.post(self.token_url, data=data)

            if response.status_code != 200:
                error_detail = response.json() if response.text else response.text
                raise Exception(
                    f"Failed to exchange code for token: {response.status_code} - {error_detail}"
                )

            return response.json()

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Retrieve user information from Google using access token.

        Calls Google's userinfo endpoint to get the authenticated user's
        profile information.

        Args:
            access_token: Valid Google OAuth access token

        Returns:
            Dictionary containing:
                - sub: Google user ID (unique identifier)
                - email: User's email address
                - email_verified: Whether email is verified
                - name: Full name
                - given_name: First name
                - family_name: Last name
                - picture: Profile picture URL

        Raises:
            Exception: If user info request fails (invalid token, network error, etc.)

        Example:
            >>> user_info = await client.get_user_info(access_token)
            >>> email = user_info["email"]
            >>> google_id = user_info["sub"]
        """
        headers = {"Authorization": f"Bearer {access_token}"}

        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(self.userinfo_url, headers=headers)

            if response.status_code != 200:
                error_detail = response.json() if response.text else response.text
                raise Exception(f"Failed to get user info: {response.status_code} - {error_detail}")

            return response.json()
