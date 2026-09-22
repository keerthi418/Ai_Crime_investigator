"""
Authentication Dependencies
---------------------------

FastAPI authentication dependencies for the
AI Crime Investigator.

Authentication architecture:

    FastAPI
       |
       v
    HTTP Bearer Token
       |
       v
    In-Memory Session Store
       |
       v
    SQLite User Database

This project does NOT use:

    - JWT
    - SQLAlchemy
    - OAuth
    - External authentication frameworks
"""

from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from backend.auth.auth import (
    get_session_user,
)

from backend.database.models import (
    get_user_by_username,
)


# ============================================================
# BEARER AUTHENTICATION
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# AUTHENTICATION EXCEPTION
# ============================================================

def authentication_exception() -> HTTPException:
    """
    Create the standard authentication error.

    HTTP 401 means the request does not contain
    valid authentication credentials.
    """

    return HTTPException(
        status_code=401,
        detail="Invalid or expired authentication token",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )


# ============================================================
# EXTRACT BEARER TOKEN
# ============================================================

def _extract_token(
    credentials: HTTPAuthorizationCredentials
):
    """
    Safely extract the Bearer token.

    Returns:

        token -> valid-looking token
        None  -> missing/invalid credentials
    """

    if credentials is None:
        return None

    token = credentials.credentials

    if token is None:
        return None

    token = str(token).strip()

    if not token:
        return None

    return token


# ============================================================
# GET CURRENT USERNAME
# ============================================================

def get_current_username(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    )
) -> str:
    """
    Validate the Bearer session token and return
    the authenticated username.

    Expected HTTP header:

        Authorization: Bearer <session_token>

    Returns:

        username

    Raises:

        HTTP 401 if the token is missing,
        invalid, or expired.
    """

    token = _extract_token(
        credentials
    )

    if not token:
        raise authentication_exception()

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
    Get the complete authenticated user record
    from the SQLite database.

    Returns:

        sqlite3.Row

    Typical fields include:

        id
        username
        email
        password_hash
        two_factor_enabled
        two_factor_secret
        created_at

    Raises:

        HTTP 401 if the session is valid but the
        corresponding database user no longer exists.
    """

    if not username:
        raise authentication_exception()

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

    Unlike get_current_user(), this function does NOT
    raise an exception when the user is not authenticated.

    Returns:

        user -> authenticated database user
        None -> no valid authentication
    """

    token = _extract_token(
        credentials
    )

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
) -> str:
    """
    Return the currently authenticated session token.

    Useful for routes such as:

        - Logout
        - Session invalidation
        - Security operations

    Raises:

        HTTP 401 if the token is missing,
        invalid, or expired.
    """

    token = _extract_token(
        credentials
    )

    if not token:
        raise authentication_exception()

    # Validate that the token actually belongs
    # to an active session.
    username = get_session_user(
        token
    )

    if not username:
        raise authentication_exception()

    return token


# ============================================================
# GET CURRENT USERNAME FROM TOKEN
# ============================================================

def get_username_from_token(
    token: str
):
    """
    Utility function for internal application code.

    Returns:

        username -> valid session
        None     -> invalid/expired session

    This function does not raise HTTP exceptions,
    making it useful outside FastAPI dependency injection.
    """

    if not token:
        return None

    token = str(token).strip()

    if not token:
        return None

    return get_session_user(
        token
    )