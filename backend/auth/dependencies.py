"""
Authentication Dependencies
---------------------------

FastAPI authentication dependencies for the
AI Crime Investigator.

This project uses:

    SQLite
       +
    In-memory session tokens

It does NOT use SQLAlchemy or JWT.
"""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.auth.auth import get_session_user
from backend.database.models import get_user_by_username


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# AUTHENTICATION EXCEPTION
# ============================================================

def authentication_exception():
    """
    Return the standard authentication error.
    """

    return HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )


# ============================================================
# GET CURRENT USERNAME
# ============================================================

def get_current_username(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    """
    Extract and validate the session token.

    Expected HTTP header:

        Authorization: Bearer <session_token>

    Returns:

        username

    Raises:

        401 if the token is missing or invalid.
    """

    # --------------------------------------------------------
    # Check Authorization header.
    # --------------------------------------------------------

    if credentials is None:
        raise authentication_exception()

    # --------------------------------------------------------
    # HTTPBearer already validates the scheme.
    # --------------------------------------------------------

    token = credentials.credentials

    if not token:
        raise authentication_exception()

    # --------------------------------------------------------
    # Find username associated with session token.
    # --------------------------------------------------------

    username = get_session_user(
        token
    )

    if not username:
        raise authentication_exception()

    return username


# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    username: str = Depends(
        get_current_username
    )
):
    """
    Get the complete user record from the database.

    Returns:

        sqlite3.Row

    containing fields such as:

        id
        username
        email
        password_hash
        two_factor_enabled
        two_factor_secret
        created_at
    """

    user = get_user_by_username(
        username
    )

    if user is None:
        raise authentication_exception()

    return user


# ============================================================
# OPTIONAL CURRENT USER
# ============================================================

def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    """
    Optional authentication dependency.

    Unlike get_current_user(), this does not raise an
    error when the user is not logged in.

    Returns:

        user       -> authenticated user
        None       -> no valid authentication
    """

    if credentials is None:
        return None

    token = credentials.credentials

    if not token:
        return None

    username = get_session_user(
        token
    )

    if not username:
        return None

    user = get_user_by_username(
        username
    )

    return user


# ============================================================
# GET CURRENT SESSION TOKEN
# ============================================================

def get_current_token(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
):
    """
    Return the authenticated session token.

    Useful for routes that need to explicitly remove
    or invalidate the current session.
    """

    if credentials is None:
        raise authentication_exception()

    token = credentials.credentials

    if not token:
        raise authentication_exception()

    username = get_session_user(
        token
    )

    if not username:
        raise authentication_exception()

    return token