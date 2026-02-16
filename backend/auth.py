"""Google OAuth authentication for LLM Council."""

import os
import secrets
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
import httpx

from .database import (
    upsert_user,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
    update_session_role,
    cleanup_expired_sessions,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:5173/api/auth/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# OAuth state store (short-lived, in-memory is fine for CSRF protection)
oauth_states: dict[str, bool] = {}


@router.get("/google")
async def google_login():
    """Redirect to Google OAuth consent screen."""
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Google OAuth not configured")

    state = secrets.token_urlsafe(32)
    oauth_states[state] = True

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    google_auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str = None, state: str = None, error: str = None):
    """Handle Google OAuth callback."""
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}?error={error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="Missing code or state")

    # Verify state
    if state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid state")
    del oauth_states[state]

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": GOOGLE_REDIRECT_URI,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for tokens")

        tokens = token_response.json()
        access_token = tokens.get("access_token")

        # Get user info
        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get user info")

        user_info = userinfo_response.json()

    # Persist user to database
    google_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    db_user = upsert_user(
        google_id=google_id,
        email=email,
        name=name,
        picture_url=picture,
    )

    # Fail login if database persistence failed - user_id is required for all operations
    if db_user is None:
        return RedirectResponse(url=f"{FRONTEND_URL}?error=database_unavailable")

    print(f"User persisted to database: {email} (id={db_user['id']})")

    # Create persistent session in database
    session_id = secrets.token_urlsafe(32)
    session = create_session(
        session_id=session_id,
        user_id=db_user["id"],
        email=email,
        name=name,
        picture_url=picture,
        role=db_user.get("role", "user"),
        expires_days=7,
    )

    if session is None:
        return RedirectResponse(url=f"{FRONTEND_URL}?error=session_creation_failed")

    # Redirect to frontend with session cookie
    response = RedirectResponse(url=f"{FRONTEND_URL}/chat")
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,  # 7 days
    )
    return response


@router.get("/me")
async def get_current_user(request: Request):
    """Get current user from session.
    
    Always refreshes the role from the database to ensure role changes
    are immediately reflected without requiring re-login.
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get session from database (returns None if not found or expired)
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Refresh role from database to pick up any role changes
    if "user_id" in session:
        db_user = get_user_by_id(session["user_id"])
        if db_user:
            new_role = db_user.get("role", "user")
            if new_role != session.get("role"):
                # Update session in database with new role
                update_session_role(session_id, new_role)
                session["role"] = new_role
    
    return session


@router.post("/logout")
async def logout(request: Request):
    """Logout and clear session."""
    session_id = request.cookies.get("session_id")
    if session_id:
        delete_session(session_id)

    response = RedirectResponse(url=FRONTEND_URL)
    response.delete_cookie("session_id")
    return response


async def require_auth(request: Request) -> dict:
    """
    FastAPI dependency to require authentication.

    Extracts session_id from cookie and returns the user dict from database.
    Raises 401 HTTPException if session is missing, invalid, or expired.

    Returns:
        dict: User session data containing email, name, picture, and user_id

    Raises:
        HTTPException: 401 if not authenticated
    """
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return session
