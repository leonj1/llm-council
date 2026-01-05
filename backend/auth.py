"""Google OAuth authentication for the API."""

import os
from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from google.oauth2 import id_token
from google.auth.transport import requests

# Get from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

security = HTTPBearer(auto_error=False)


@dataclass
class User:
    """Authenticated user from Google OAuth."""
    id: str  # Google's 'sub' claim - stable user identifier
    email: str
    name: str
    picture: Optional[str] = None


def verify_google_token(token: str) -> dict:
    """
    Verify Google ID token and return claims.

    Args:
        token: Google ID token from frontend

    Returns:
        Token claims dict containing sub, email, name, picture, etc.

    Raises:
        HTTPException: If token is invalid
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GOOGLE_CLIENT_ID not configured"
        )

    try:
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            GOOGLE_CLIENT_ID
        )
        return idinfo
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    FastAPI dependency to get current authenticated user.

    Extracts and validates the Google ID token from the Authorization header.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        User object with id, email, name, picture

    Raises:
        HTTPException: If not authenticated or token invalid
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    claims = verify_google_token(credentials.credentials)

    return User(
        id=claims['sub'],  # Stable user ID from Google
        email=claims['email'],
        name=claims.get('name', ''),
        picture=claims.get('picture')
    )


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[User]:
    """
    FastAPI dependency for endpoints that optionally accept auth.

    Args:
        credentials: HTTP Bearer credentials from request

    Returns:
        User object if authenticated, None otherwise
    """
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
