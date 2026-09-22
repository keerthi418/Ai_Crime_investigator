"""
API Routes
==========

AI Crime Investigator

This module provides:

    Authentication
    2FA / TOTP
    Password change
    Password reset
    Text investigation
    Excel investigation
    Knowledge graph generation
    BFS / DFS / A* search
    Bayesian confidence
    CSP contradiction detection
    PDF report generation
    Activity logs

Architecture:

    Frontend
        |
        v
    FastAPI Routes
        |
        +---- Authentication
        |
        +---- NER
        |
        +---- Relation Extraction
        |
        +---- Knowledge Graph
        |
        +---- BFS / DFS / A*
        |
        +---- Bayesian Confidence
        |
        +---- CSP
        |
        +---- PDF Report
        |
        v
    JSON Response
"""

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    UploadFile,
    File,
)

from fastapi.security import (
    HTTPBearer,
    HTTPAuthorizationCredentials,
)

from pydantic import BaseModel, EmailStr

import pandas as pd
import networkx as nx
import io
import os
import secrets
import hashlib

from datetime import (
    datetime,
    timedelta,
    timezone,
)


# ============================================================
# DATABASE
# ============================================================

from backend.database.database import (
    init_database,
    log_activity,
    get_connection,
)

from backend.database.models import (
    create_user,
    get_user_by_username,
    get_user_by_email,
    update_password,
    get_2fa_status,
    set_2fa,
    create_reset_token,
    consume_reset_token,
)


# ============================================================
# AUTHENTICATION
# ============================================================

from backend.auth.auth import (
    hash_password,
    verify_password,
    create_session,
    get_session_user,
    remove_session,
    create_2fa_challenge,
    get_2fa_challenge,
    consume_2fa_challenge,
    generate_totp_secret,
    verify_totp,
    totp_provisioning_uri,
)


# ============================================================
# NLP
# ============================================================

from backend.nlp.ner_extractor import (
    extract_entities,
)

from backend.nlp.relation_extractor import (
    extract_relations,
)


# ============================================================
# GRAPH
# ============================================================

from backend.graph.case_graph_builder import (
    build_case_graph,
    graph_to_json,
    graph_has_path,
    get_graph_summary,
)

from backend.graph.graph_store import (
    bfs,
    dfs,
    astar,
    run_search_details,
    normalize_node,
)


# ============================================================
# REASONING
# ============================================================

from backend.reasoning.bayesian import (
    calculate_confidence,
    explain_confidence,
    get_confidence_details,
)

from backend.reasoning.csp import (
    detect_contradictions,
)


# ============================================================
# REPORT
# ============================================================

from backend.report.report_generator import (
    generate_report,
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter()


# ============================================================
# AUTHENTICATION SECURITY
# ============================================================

security = HTTPBearer(
    auto_error=False
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

init_database()


# ============================================================
# REQUEST MODELS
# ============================================================


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Verify2FARequest(BaseModel):
    challenge_token: str
    code: str


class Enable2FARequest(BaseModel):
    code: str


class Disable2FARequest(BaseModel):
    code: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class InvestigationRequest(BaseModel):
    text: str
    start_node: str = ""
    target_node: str = ""
    case_name: str = ""


class AnalyzeCaseRequest(BaseModel):
    start_node: str = ""
    target_node: str = ""


# ============================================================
# HELPER - AUTHENTICATED USER
# ============================================================


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None,
):
    """
    Validate the Bearer session token and return:

        user, token
    """

    # --------------------------------------------------------
    # Check credentials
    # --------------------------------------------------------

    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    # --------------------------------------------------------
    # Extract token
    # --------------------------------------------------------

    token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication token is missing.",
        )

    # --------------------------------------------------------
    # Find username from active session
    # --------------------------------------------------------

    username = get_session_user(token)

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session.",
        )

    # --------------------------------------------------------
    # Get user from SQLite
    # --------------------------------------------------------

    user = get_user_by_username(username)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user, token


# ============================================================
# API STATUS
# ============================================================


@router.get("/")
def api_status():
    """
    API health/status endpoint.
    """

    return {
        "message": "AI Crime Investigator API is running",
        "status": "success",
    }


# ============================================================
# REGISTER
# ============================================================


@router.post("/auth/register")
def register(
    request: RegisterRequest,
):
    """
    Register a new investigator account.
    """

    username = request.username.strip()
    email = str(request.email).strip().lower()
    password = request.password

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Username is required.",
        )

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required.",
        )

    if len(password) < 6:
        raise HTTPException(
            status_code=400,
            detail="Password must contain at least 6 characters.",
        )

    # --------------------------------------------------------
    # Username check
    # --------------------------------------------------------

    if get_user_by_username(username):
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )

    # --------------------------------------------------------
    # Email check
    # --------------------------------------------------------

    if get_user_by_email(email):
        raise HTTPException(
            status_code=409,
            detail="Email already registered.",
        )

    # --------------------------------------------------------
    # Hash password
    # --------------------------------------------------------

    password_hash = hash_password(
        password
    )

    # --------------------------------------------------------
    # Create user
    # --------------------------------------------------------

    user_id = create_user(
        username,
        email,
        password_hash,
    )

    if not user_id:
        raise HTTPException(
            status_code=500,
            detail="Account creation failed.",
        )

    # --------------------------------------------------------
    # Activity log
    # --------------------------------------------------------

    log_activity(
        username,
        "ACCOUNT_CREATED",
        "New investigator account created.",
    )

    return {
        "status": "success",
        "message": "Account created successfully.",
        "user": {
            "id": user_id,
            "username": username,
            "email": email,
        },
    }


# ============================================================
# LOGIN
# ============================================================


@router.post("/auth/login")
def login(
    request: LoginRequest,
):
    """
    Login using email and password.

    If 2FA is enabled:
        return challenge_token

    Otherwise:
        return session token
    """

    email = str(
        request.email
    ).strip().lower()

    # --------------------------------------------------------
    # Find user
    # --------------------------------------------------------

    user = get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # --------------------------------------------------------
    # Verify password
    # --------------------------------------------------------

    password_valid = verify_password(
        request.password,
        user["password_hash"],
    )

    if not password_valid:

        log_activity(
            user["username"],
            "LOGIN_FAILED",
            "Invalid password.",
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    # --------------------------------------------------------
    # Check 2FA
    # --------------------------------------------------------

    two_factor_enabled = bool(
        user["two_factor_enabled"]
    )

    if two_factor_enabled:

        challenge_token = create_2fa_challenge(
            user["username"]
        )

        log_activity(
            user["username"],
            "LOGIN_2FA_REQUIRED",
            "Password verified. Waiting for 2FA verification.",
        )

        return {
            "status": "success",
            "requires_2fa": True,
            "message": "Two-factor authentication required.",
            "challenge_token": challenge_token,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
            },
        }

    # --------------------------------------------------------
    # Normal session
    # --------------------------------------------------------

    token = create_session(
        user["username"]
    )

    log_activity(
        user["username"],
        "LOGIN",
        "Investigator logged into the system.",
    )

    return {
        "status": "success",
        "requires_2fa": False,
        "message": "Login successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        },
    }


# ============================================================
# LOGIN - VERIFY 2FA
# ============================================================


@router.post("/auth/2fa/verify")
def verify_login_2fa(
    request: Verify2FARequest,
):
    """
    Verify the TOTP code after password login.
    """

    # --------------------------------------------------------
    # Validate challenge
    # --------------------------------------------------------

    username = get_2fa_challenge(
        request.challenge_token
    )

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired 2FA challenge.",
        )

    # --------------------------------------------------------
    # Get user
    # --------------------------------------------------------

    user = get_user_by_username(
        username
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    # --------------------------------------------------------
    # Check 2FA status
    # --------------------------------------------------------

    if not user["two_factor_enabled"]:
        raise HTTPException(
            status_code=400,
            detail="Two-factor authentication is not enabled.",
        )

    secret = user["two_factor_secret"]

    if not secret:
        raise HTTPException(
            status_code=500,
            detail="2FA secret is missing.",
        )

    # --------------------------------------------------------
    # Verify TOTP
    # --------------------------------------------------------

    if not verify_totp(
        secret,
        request.code,
    ):

        log_activity(
            username,
            "LOGIN_2FA_FAILED",
            "Invalid two-factor authentication code.",
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid verification code.",
        )

    # --------------------------------------------------------
    # Consume challenge
    # --------------------------------------------------------

    consume_2fa_challenge(
        request.challenge_token
    )

    # --------------------------------------------------------
    # Create final session
    # --------------------------------------------------------

    token = create_session(
        username
    )

    log_activity(
        username,
        "LOGIN",
        "Investigator logged in successfully using 2FA.",
    )

    return {
        "status": "success",
        "message": "2FA verification successful.",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
        },
    }


# ============================================================
# LOGOUT
# ============================================================


@router.post("/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Logout and remove the current session.
    """

    if not credentials:
        return {
            "status": "success",
            "message": "Already logged out.",
        }

    token = credentials.credentials

    username = get_session_user(
        token
    )

    if username:

        log_activity(
            username,
            "LOGOUT",
            "Investigator logged out.",
        )

        remove_session(
            token
        )

    return {
        "status": "success",
        "message": "Logout successful.",
    }


# ============================================================
# CURRENT USER
# ============================================================


@router.get("/auth/me")
def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Return currently authenticated user.
    """

    user, token = get_authenticated_user(
        credentials
    )

    return {
        "status": "success",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "two_factor_enabled": bool(
                user["two_factor_enabled"]
            ),
        },
    }


# ============================================================
# 2FA - STATUS
# ============================================================


@router.get("/auth/2fa/status")
def two_factor_status(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Return current 2FA status.
    """

    user, token = get_authenticated_user(
        credentials
    )

    status = get_2fa_status(
        user["id"]
    )

    if not status:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    return {
        "status": "success",
        "enabled": bool(
            status["two_factor_enabled"]
        ),
    }


# ============================================================
# 2FA - SETUP
# ============================================================


@router.post("/auth/2fa/setup")
def setup_2fa(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Generate a new TOTP secret.

    The secret is stored while 2FA remains disabled.
    The user must verify the OTP through /enable.
    """

    user, token = get_authenticated_user(
        credentials
    )

    # --------------------------------------------------------
    # Already enabled
    # --------------------------------------------------------

    if user["two_factor_enabled"]:

        return {
            "status": "success",
            "enabled": True,
            "message": (
                "Two-factor authentication is already enabled."
            ),
        }

    # --------------------------------------------------------
    # Generate secret
    # --------------------------------------------------------

    secret = generate_totp_secret()

    # --------------------------------------------------------
    # Store secret
    # --------------------------------------------------------

    success = set_2fa(
        user["id"],
        False,
        secret,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Unable to initialize 2FA setup.",
        )

    # --------------------------------------------------------
    # Generate authenticator URI
    # --------------------------------------------------------

    provisioning_uri = totp_provisioning_uri(
        secret,
        user["email"],
        "AI Crime Investigator",
    )

    log_activity(
        user["username"],
        "2FA_SETUP_STARTED",
        "Two-factor authentication setup initiated.",
    )

    return {
        "status": "success",
        "enabled": False,
        "secret": secret,
        "otpauth_url": provisioning_uri,
        "message": (
            "Use the secret or otpauth URL in "
            "Google Authenticator or another TOTP app."
        ),
    }


# ============================================================
# 2FA - ENABLE
# ============================================================


@router.post("/auth/2fa/enable")
def enable_2fa(
    request: Enable2FARequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Verify TOTP and enable 2FA.
    """

    user, token = get_authenticated_user(
        credentials
    )

    two_factor = get_2fa_status(
        user["id"]
    )

    if not two_factor:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    secret = two_factor["two_factor_secret"]

    if not secret:
        raise HTTPException(
            status_code=400,
            detail="Please start 2FA setup first.",
        )

    # --------------------------------------------------------
    # Verify OTP
    # --------------------------------------------------------

    if not verify_totp(
        secret,
        request.code,
    ):
        log_activity(
            user["username"],
            "2FA_ENABLE_FAILED",
            "Invalid verification code.",
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid verification code.",
        )

    # --------------------------------------------------------
    # Enable
    # --------------------------------------------------------

    success = set_2fa(
        user["id"],
        True,
        secret,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Unable to enable two-factor authentication.",
        )

    log_activity(
        user["username"],
        "2FA_ENABLED",
        "Two-factor authentication enabled.",
    )

    return {
        "status": "success",
        "enabled": True,
        "message": (
            "Two-factor authentication enabled successfully."
        ),
    }


# ============================================================
# 2FA - DISABLE
# ============================================================


@router.post("/auth/2fa/disable")
def disable_2fa(
    request: Disable2FARequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Verify current OTP and disable 2FA.
    """

    user, token = get_authenticated_user(
        credentials
    )

    two_factor = get_2fa_status(
        user["id"]
    )

    if not two_factor:
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    if not two_factor["two_factor_enabled"]:

        return {
            "status": "success",
            "enabled": False,
            "message": (
                "Two-factor authentication is already disabled."
            ),
        }

    secret = two_factor["two_factor_secret"]

    # --------------------------------------------------------
    # Verify OTP
    # --------------------------------------------------------

    if not secret or not verify_totp(
        secret,
        request.code,
    ):

        log_activity(
            user["username"],
            "2FA_DISABLE_FAILED",
            "Invalid verification code.",
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid verification code.",
        )

    # --------------------------------------------------------
    # Disable and clear secret
    # --------------------------------------------------------

    success = set_2fa(
        user["id"],
        False,
        None,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Unable to disable two-factor authentication.",
        )

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET two_factor_secret = NULL
            WHERE id = ?
            """,
            (user["id"],),
        )

        connection.commit()

    finally:

        connection.close()

    log_activity(
        user["username"],
        "2FA_DISABLED",
        "Two-factor authentication disabled.",
    )

    return {
        "status": "success",
        "enabled": False,
        "message": (
            "Two-factor authentication disabled successfully."
        ),
    }


# ============================================================
# CHANGE PASSWORD
# ============================================================


@router.post("/auth/change-password")
def change_password(
    request: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Change password for authenticated user.
    """

    user, token = get_authenticated_user(
        credentials
    )

    # --------------------------------------------------------
    # Validate new password
    # --------------------------------------------------------

    if len(request.new_password) < 6:

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must contain at least 6 characters."
            ),
        )

    # --------------------------------------------------------
    # Verify current password
    # --------------------------------------------------------

    if not verify_password(
        request.current_password,
        user["password_hash"],
    ):

        log_activity(
            user["username"],
            "PASSWORD_CHANGE_FAILED",
            "Incorrect current password.",
        )

        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect.",
        )

    # --------------------------------------------------------
    # Prevent same password
    # --------------------------------------------------------

    if verify_password(
        request.new_password,
        user["password_hash"],
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must be different "
                "from the current password."
            ),
        )

    # --------------------------------------------------------
    # Hash new password
    # --------------------------------------------------------

    new_password_hash = hash_password(
        request.new_password
    )

    # --------------------------------------------------------
    # Update password
    # --------------------------------------------------------

    success = update_password(
        user["id"],
        new_password_hash,
    )

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Unable to update password.",
        )

    log_activity(
        user["username"],
        "PASSWORD_CHANGED",
        "Account password changed successfully.",
    )

    return {
        "status": "success",
        "message": "Password changed successfully.",
    }


# ============================================================
# FORGOT PASSWORD
# ============================================================


@router.post("/auth/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
):
    """
    Generate a password reset token.

    Development version returns the token directly.

    In production, the token should be sent by email.
    """

    email = str(
        request.email
    ).strip().lower()

    user = get_user_by_email(
        email
    )

    # --------------------------------------------------------
    # Avoid account enumeration
    # --------------------------------------------------------

    if not user:

        return {
            "status": "success",
            "message": (
                "If an account exists for this email, "
                "a password reset request has been created."
            ),
        }

    # --------------------------------------------------------
    # Generate secure token
    # --------------------------------------------------------

    raw_token = secrets.token_urlsafe(
        32
    )

    token_hash = hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()

    # --------------------------------------------------------
    # Expiry
    # --------------------------------------------------------

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(minutes=15)
    )

    # --------------------------------------------------------
    # Store hashed token
    # --------------------------------------------------------

    success = create_reset_token(
        user["id"],
        token_hash,
        expires_at.isoformat(),
    )

    if not success:

        raise HTTPException(
            status_code=500,
            detail=(
                "Unable to create password reset request."
            ),
        )

    log_activity(
        user["username"],
        "PASSWORD_RESET_REQUESTED",
        "Password reset request created.",
    )

    # --------------------------------------------------------
    # Development response
    # --------------------------------------------------------

    return {
        "status": "success",
        "message": (
            "Password reset request created. "
            "The reset token is valid for 15 minutes."
        ),
        "reset_token": raw_token,
        "expires_in_minutes": 15,
    }


# ============================================================
# RESET PASSWORD
# ============================================================


@router.post("/auth/reset-password")
def reset_password(
    request: ResetPasswordRequest,
):
    """
    Reset password using a valid reset token.
    """

    # --------------------------------------------------------
    # Validate password
    # --------------------------------------------------------

    if len(request.new_password) < 6:

        raise HTTPException(
            status_code=400,
            detail=(
                "New password must contain at least 6 characters."
            ),
        )

    token = request.token.strip()

    if not token:

        raise HTTPException(
            status_code=400,
            detail="Reset token is required.",
        )

    # --------------------------------------------------------
    # Hash token
    # --------------------------------------------------------

    token_hash = hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()

    # --------------------------------------------------------
    # Find token
    # --------------------------------------------------------

    reset_record = consume_reset_token(
        token_hash
    )

    if not reset_record:

        raise HTTPException(
            status_code=400,
            detail="Invalid or already-used reset token.",
        )

    # --------------------------------------------------------
    # Check expiry
    # --------------------------------------------------------

    try:

        expires_at = datetime.fromisoformat(
            reset_record["expires_at"]
        )

        if expires_at.tzinfo is None:

            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

    except Exception:

        raise HTTPException(
            status_code=400,
            detail="Invalid reset token.",
        )

    if datetime.now(timezone.utc) > expires_at:

        raise HTTPException(
            status_code=400,
            detail="Reset token has expired.",
        )

    # --------------------------------------------------------
    # Update password
    # --------------------------------------------------------

    new_password_hash = hash_password(
        request.new_password
    )

    success = update_password(
        reset_record["user_id"],
        new_password_hash,
    )

    if not success:

        raise HTTPException(
            status_code=500,
            detail="Unable to reset password.",
        )

    # --------------------------------------------------------
    # Get user for logging
    # --------------------------------------------------------

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT username
            FROM users
            WHERE id = ?
            """,
            (reset_record["user_id"],),
        )

        reset_user = cursor.fetchone()

    finally:

        connection.close()

    if reset_user:

        log_activity(
            reset_user["username"],
            "PASSWORD_RESET",
            "Password reset completed successfully.",
        )

    return {
        "status": "success",
        "message": "Password reset successfully.",
    }


# ============================================================
# HELPER - RUN INVESTIGATION PIPELINE
# ============================================================


# ============================================================
# PIPELINE DEBUG TRACE
# ============================================================
#
# Set AI_DEBUG=0 to disable.  Enabled by default so every
# /investigate request prints the full extraction -> graph ->
# search audit trail (entities, relations, graph nodes, graph
# edges, connected components, and the exact start/target pair)
# to the uvicorn console.

PIPELINE_DEBUG = os.environ.get("AI_DEBUG", "1") not in {"0", "false", "False"}


def _trace(*args):
    if PIPELINE_DEBUG:
        print("[PIPELINE]", *args)


def run_investigation_pipeline(
    case_text: str,
    start: str = "",
    target: str = "",
):
    """
    Common investigation pipeline used by:

        /investigate
        /investigate/excel

    Pipeline:

        Text
          ↓
        NER
          ↓
        Relation Extraction
          ↓
        Knowledge Graph
          ↓
        BFS / DFS / A*
          ↓
        CSP
          ↓
        Bayesian Confidence
          ↓
        Explanation
          ↓
        PDF
    """

    # ========================================================
    # ENTITY EXTRACTION
    # ========================================================

    try:

        entities = extract_entities(
            case_text
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Entity extraction failed: {str(e)}"
            ),
        )

    # ========================================================
    # RELATION EXTRACTION
    # ========================================================

    try:

        relations = extract_relations(
            case_text,
            entities,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Relation extraction failed: {str(e)}"
            ),
        )

    # ========================================================
    # GRAPH CONSTRUCTION
    # ========================================================

    try:

        graph = build_case_graph(
            entities,
            relations,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Graph construction failed: {str(e)}"
            ),
        )

    # ========================================================
    # SEARCH PARAMETERS
    # ========================================================

    start = str(start).strip() if start else ""
    target = str(target).strip() if target else ""

    # Use the user-provided nodes EXACTLY.  A node that is not
    # present in the extracted knowledge graph is an explicit
    # error, never a silent empty result.
    if start and normalize_node(graph, start) is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Start node '{start}' is not present in the "
                "extracted knowledge graph."
            ),
        )

    if target and normalize_node(graph, target) is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Target node '{target}' is not present in the "
                "extracted knowledge graph."
            ),
        )

    # The algorithms are a core part of the application, so they
    # must not silently remain "Not run yet" just because the user
    # did not manually select two nodes.  If the investigator did
    # not provide a pair, automatically choose two distinct graph
    # entities.  The selected pair is returned to the UI so it can
    # be displayed and changed later.
    graph_nodes = list(graph.nodes)

    # Prefer meaningful investigative entities (especially people)
    # over dates/times when selecting an automatic algorithm pair.
    preferred_nodes = []
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        value = str(entity.get("text") or entity.get("label") or entity.get("name") or "").strip()
        kind = str(entity.get("type") or "").upper()
        if value and kind not in {"DATE", "TIME", "MONEY"} and value in graph.nodes:
            preferred_nodes.append(value)

    # Deterministic automatic fallback is used ONLY when neither
    # the start nor the target was provided by the investigator.
    if not start and not target and graph.number_of_edges() > 0:
        preferred_set = {value.casefold() for value in preferred_nodes}
        chosen_edge = None

        for edge_source, edge_target in graph.edges():
            if (
                str(edge_source).casefold() in preferred_set
                and str(edge_target).casefold() in preferred_set
            ):
                chosen_edge = (edge_source, edge_target)
                break

        if chosen_edge is None:
            chosen_edge = next(iter(graph.edges()))

        edge_source, edge_target = chosen_edge
        start = str(edge_source)
        target = str(edge_target)

    # If only ONE side was provided, keep it exactly as given and
    # fill only the missing side with a deterministic candidate.
    elif not start:
        candidates = preferred_nodes or [str(node) for node in graph_nodes]
        for node in candidates:
            if str(node).casefold() != target.casefold():
                start = str(node)
                break

    elif not target:
        candidates = preferred_nodes or [str(node) for node in graph_nodes]
        for node in candidates:
            if str(node).casefold() != start.casefold():
                target = str(node)
                break

    if not start:
        start = preferred_nodes[0] if preferred_nodes else (str(graph_nodes[0]) if graph_nodes else "")

    if not target:
        candidates = preferred_nodes or [str(node) for node in graph_nodes]
        for node in candidates:
            if str(node).casefold() != start.casefold():
                target = str(node)
                break

    # Whether a path exists at all is decided ONCE here, before
    # running the algorithms, so the API can tell the UI honestly
    # that the selected entities are disconnected rather than
    # pretending the search "failed".
    path_exists = False

    if start and target:
        try:
            path_exists = graph_has_path(
                graph,
                start,
                target,
            )
        except Exception:
            path_exists = False

    if PIPELINE_DEBUG:

        _trace("=" * 18 + " SEARCH DEBUG " + "=" * 18)
        _trace("  start=%r  canonical=%r" % (start, normalize_node(graph, start)))
        _trace("  target=%r  canonical=%r" % (target, normalize_node(graph, target)))
        _trace("  start exists: %s" % (normalize_node(graph, start) is not None))
        _trace("  target exists: %s" % (normalize_node(graph, target) is not None))
        _trace("  graph edges: %d" % graph.number_of_edges())
        _trace("  graph components: %d" % nx.number_connected_components(graph))
        _trace("  path exists before search: %s" % path_exists)

    # ========================================================
    # SEARCH
    # ========================================================

    # run_search_details() returns structured metrics for each
    # algorithm:
    #
    #     {
    #         "algorithm": "BFS",
    #         "found": True,
    #         "path": [...],
    #         "path_length": 4,
    #         "visited_nodes": 5,
    #         "execution_time_ms": 0.123,
    #     }
    #
    # A* also includes "cost" and "heuristic_used".

    search_details = {}

    if start and target:

        try:

            search_details = run_search_details(
                graph,
                start,
                target,
            )

        except Exception as e:

            # Do not swallow the failure silently: the caller
            # must be able to distinguish a completed search from
            # a search that could not be executed at all.
            print("SEARCH ERROR:", e)
            search_details = {
                "error": f"Search execution failed: {str(e)}"
            }

    search_error = search_details.get("error")

    bfs_path = (
        (search_details.get("BFS") or {}).get("path")
        or []
    )

    dfs_path = (
        (search_details.get("DFS") or {}).get("path")
        or []
    )

    astar_path = (
        (search_details.get("A*") or {}).get("path")
        or []
    )

    # ========================================================
    # SEARCH RESULTS
    # ========================================================

    # The frontend reads search_results.algorithm_pair to
    # display the automatically selected source/target pair.
    search_results = {
        "BFS": search_details.get("BFS"),
        "DFS": search_details.get("DFS"),
        "A*": search_details.get("A*"),
        "algorithm_pair": (
            search_details.get("algorithm_pair")
            or {
                "start": start,
                "target": target,
            }
        ),
        "start": search_details.get("start") or start,
        "target": search_details.get("target") or target,
        "error": search_error,
        "disconnected": (
            bool(start and target)
            and path_exists is False
        ),
    }

    if PIPELINE_DEBUG:

        _trace("=" * 18 + " SEARCH DEBUG " + "=" * 18)

        for algorithm in ("BFS", "DFS", "A*"):

            detail = search_results.get(algorithm) or {}

            _trace("Algorithm: %s" % algorithm)
            _trace("  Start: %s" % search_results.get("start"))
            _trace("  Target: %s" % search_results.get("target"))
            _trace("  Reached target: %s" % detail.get("found"))
            _trace("  Path length: %s" % detail.get("length"))
            _trace("  Returned path: %r" % (detail.get("path") or []))
            _trace("  Returned edges: %r" % (detail.get("edges") or []))

    no_path_hint = (
        f"Selected entities are disconnected. No path exists "
        f"between '{start}' and '{target}' in the knowledge graph."
        if path_exists is False
        else (
            f"No path exists between '{start}' and '{target}' "
            "in the knowledge graph. The extracted graph may be "
            "disconnected or one of the nodes is missing."
        )
    )

    algorithm_status = {}

    for algorithm in ("BFS", "DFS", "A*"):

        detail = (
            search_details.get(algorithm)
            or {}
        )

        if search_error:
            algorithm_status[algorithm] = "error"
        else:
            algorithm_status[algorithm] = (
                "completed"
                if detail.get("found")
                else "no_path"
            )

    search_hint = (
        f"Search could not be completed: {search_error}"
        if search_error
        else (
            "All three algorithms completed."
            if (
                algorithm_status["BFS"] == "completed"
                and algorithm_status["DFS"] == "completed"
                and algorithm_status["A*"] == "completed"
            )
            else no_path_hint
        )
    )

    # ========================================================
    # CSP
    # ========================================================

    try:

        contradictions = detect_contradictions(
            case_text,
            relations,
        )

    except Exception as e:

        contradictions = [
            f"Contradiction analysis failed: {str(e)}"
        ]

    # ========================================================
    # GRAPH SUMMARY (connectivity for confidence)
    # ========================================================

    try:

        graph_summary = get_graph_summary(
            graph
        )

    except Exception:

        graph_summary = {
            "nodes": len(entities),
            "relationships": len(relations),
            "connected": False,
            "components": 1,
            "maximum_node_degree": 0,
        }

    # ========================================================
    # BAYESIAN CONFIDENCE
    # ========================================================

    try:

        confidence = calculate_confidence(
            entities=entities,
            relations=relations,
            contradictions=contradictions,
            connected=graph_summary.get("connected"),
            components=graph_summary.get("components"),
            path_exists=path_exists,
        )

    except Exception:

        confidence = 0

    # ========================================================
    # CONFIDENCE EXPLANATION
    # ========================================================

    try:

        explanation = explain_confidence(
            entities=entities,
            relations=relations,
            contradictions=contradictions,
            connected=graph_summary.get("connected"),
            components=graph_summary.get("components"),
            path_exists=path_exists,
            start=start,
            target=target,
        )

    except Exception as e:

        explanation = (
            "Confidence explanation unavailable: "
            f"{str(e)}"
        )

    try:

        confidence_details = get_confidence_details(
            entities=entities,
            relations=relations,
            contradictions=contradictions,
            connected=graph_summary.get("connected"),
            components=graph_summary.get("components"),
            path_exists=path_exists,
        )

    except Exception:

        confidence_details = {
            "confidence": confidence,
            "confidence_percentage": round(
                float(confidence or 0) * 100,
                1
            ),
        }

    # ========================================================
    # GRAPH JSON
    # ========================================================

    try:

        graph_data = graph_to_json(
            graph
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Graph construction failed: {str(e)}"
            ),
        )

    if PIPELINE_DEBUG:

        _trace("=" * 18 + " ENTITY DEBUG " + "=" * 18)

        for entity in entities:
            _trace(
                "  type=%s text=%r id=%r"
                % (
                    str(entity.get("type", "")).upper(),
                    str(entity.get("text", "")),
                    str(entity.get("id", "")),
                )
            )

        _trace("  TOTAL ENTITIES: %d" % len(entities))

        _trace("=" * 18 + " RELATION DEBUG " + "=" * 18)

        for rel in relations:
            _trace(
                "  %r --%s--> %r (conf=%s)"
                % (
                    str(rel.get("source", "")),
                    str(rel.get("relation", "")),
                    str(rel.get("target", "")),
                    str(rel.get("confidence", "")),
                )
            )

        _trace("  TOTAL RELATIONS: %d" % len(relations))

        _trace("=" * 18 + " GRAPH NODES " + "=" * 18)

        for node, node_data in graph.nodes(data=True):
            _trace(
                "  node=%r type=%s"
                % (
                    str(node),
                    str(node_data.get("type", "")),
                )
            )

        _trace("  TOTAL NODES: %d" % graph.number_of_nodes())

        _trace("=" * 18 + " GRAPH EDGES " + "=" * 18)

        for edge_source, edge_target, edge_data in graph.edges(data=True):
            _trace(
                "  %r --%s--> %r"
                % (
                    str(edge_source),
                    str(edge_data.get("relation", "")),
                    str(edge_target),
                )
            )

        _trace("  TOTAL EDGES: %d" % graph.number_of_edges())

        _trace("=" * 18 + " CONNECTED COMPONENTS " + "=" * 18)

        for index, component in enumerate(
            nx.connected_components(graph)
        ):
            _trace(
                "  Component %d: %r" % (index, sorted(component))
            )

    return {
        "entities": entities,
        "relations": relations,
        "graph": graph,
        "graph_data": graph_data,
        "search_results": search_results,
        "bfs_path": bfs_path,
        "dfs_path": dfs_path,
        "astar_path": astar_path,
        "algorithm_status": algorithm_status,
        "search_hint": search_hint,
        "algorithm_pair": {
            "start": start,
            "target": target,
        },
        "confidence": confidence,
        "confidence_details": confidence_details,
        "graph_summary": graph_summary,
        "contradictions": contradictions,
        "explanation": explanation,
        "start": start,
        "target": target,
    }


# ============================================================
# TEXT INVESTIGATION
# ============================================================


@router.post("/investigate")
def investigate(
    request: InvestigationRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Analyze a crime case description.
    """

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    user, token = get_authenticated_user(
        credentials
    )

    username = user["username"]

    # --------------------------------------------------------
    # Validate case
    # --------------------------------------------------------

    case_text = request.text.strip()

    if not case_text:

        raise HTTPException(
            status_code=400,
            detail="Case description cannot be empty.",
        )

    # ========================================================
    # RUN PIPELINE
    # ========================================================

    result = run_investigation_pipeline(
        case_text,
        request.start_node,
        request.target_node,
    )

    # ========================================================
    # PDF REPORT
    # ========================================================

    report_file = None

    explanation = result["explanation"]

    try:

        report_file = generate_report(
            case_text,
            result["entities"],
            result["relations"],
            result["search_results"],
            result["confidence"],
            result["contradictions"],
            graph_data=result["graph_data"],
            start=result["start"],
            target=result["target"],
            bfs_path=result["bfs_path"],
            dfs_path=result["dfs_path"],
            astar_path=result["astar_path"],
            explanation=result["explanation"],
            username=username,
        )

    except Exception as e:

        explanation = (
            f"{result['explanation']}\n"
            f"PDF report generation failed: {str(e)}"
        )

    # ========================================================
    # SAVE CASE AS ONGOING
    # ========================================================

    case_name = request.case_name.strip() or f"Investigation {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("""INSERT INTO investigation_cases
            (case_name,case_text,username,status,entities_count,relations_count,confidence,contradictions_count,report_file)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (case_name,case_text,username,"ONGOING",len(result["entities"]),len(result["relations"]),
             float(result["confidence"] or 0),len(result["contradictions"]),report_file))
        case_id=cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    # ========================================================
    # ACTIVITY LOG
    # ========================================================

    log_activity(
        username,
        "INVESTIGATION",
        f"Crime investigation executed. Case {case_id} created as ONGOING.",
    )

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {
        "status": "success",

        "case_id": case_id,

        "case_name": case_name,

        "entities": result["entities"],

        "relations": result["relations"],

        "graph": result["graph_data"],

        "search_results": result["search_results"],

        "algorithm_pair": result["algorithm_pair"],

        "algorithm_status": result["algorithm_status"],

        "search_hint": result["search_hint"],

        "start": result["start"],

        "target": result["target"],

        "bfs_path": result["bfs_path"],

        "dfs_path": result["dfs_path"],

        "astar_path": result["astar_path"],

        "bayesian_confidence": result["confidence"],

        "contradictions": result["contradictions"],

        "explanation": explanation,

        "report": {
            "file": report_file,
            "message": (
                "Investigation report generated successfully."
                if report_file
                else "PDF report could not be generated."
            ),
        },
    }


# ============================================================
# EXCEL CASE REPORT INVESTIGATION
# ============================================================


@router.post("/investigate/excel")
async def investigate_excel(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Upload and analyze an Excel crime case report.
    """

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    user, token = get_authenticated_user(
        credentials
    )

    username = user["username"]

    # --------------------------------------------------------
    # File validation
    # --------------------------------------------------------

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Please upload an Excel case report.",
        )

    filename = file.filename.lower()

    if not filename.endswith(
        (".xlsx", ".xls")
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Only Excel files (.xlsx or .xls) "
                "are supported."
            ),
        )

    # --------------------------------------------------------
    # Read file
    # --------------------------------------------------------

    try:

        file_content = await file.read()

        if not file_content:

            raise HTTPException(
                status_code=400,
                detail="Uploaded Excel file is empty.",
            )

        excel_file = io.BytesIO(
            file_content
        )

        if filename.endswith(".xlsx"):

            dataframe = pd.read_excel(
                excel_file,
                engine="openpyxl",
            )

        else:

            dataframe = pd.read_excel(
                excel_file,
                engine="xlrd",
            )

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unable to read Excel file: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # Empty data
    # --------------------------------------------------------

    if dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail="The Excel case report is empty.",
        )

    # --------------------------------------------------------
    # Remove empty rows
    # --------------------------------------------------------

    dataframe = dataframe.dropna(
        how="all"
    )

    # --------------------------------------------------------
    # Remove empty columns
    # --------------------------------------------------------

    dataframe = dataframe.dropna(
        axis=1,
        how="all",
    )

    if dataframe.empty:

        raise HTTPException(
            status_code=400,
            detail=(
                "The Excel case report contains "
                "no usable data."
            ),
        )

    # --------------------------------------------------------
    # Limit file size
    # --------------------------------------------------------

    MAX_ROWS = 5000

    original_rows = len(
        dataframe
    )

    rows_limited = False

    if original_rows > MAX_ROWS:

        dataframe = dataframe.head(
            MAX_ROWS
        )

        rows_limited = True

    # ========================================================
    # CONVERT EXCEL TO TEXT
    # ========================================================

    case_parts = []

    for _, row in dataframe.iterrows():

        row_values = []

        for column, value in row.items():

            if pd.notna(value):

                row_values.append(
                    f"{column}: {value}"
                )

        if row_values:

            case_parts.append(
                " | ".join(row_values)
            )

    case_text = "\n".join(
        case_parts
    )

    if not case_text.strip():

        raise HTTPException(
            status_code=400,
            detail=(
                "No readable case information "
                "was found in the Excel file."
            ),
        )

    # ========================================================
    # FIND DEFAULT SEARCH NODES
    # ========================================================

    # We first extract the entities so we can choose
    # meaningful graph nodes.

    try:

        preliminary_entities = extract_entities(
            case_text
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Entity extraction failed: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # Create relation list
    # --------------------------------------------------------

    try:

        preliminary_relations = extract_relations(
            case_text,
            preliminary_entities,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Relation extraction failed: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # Build graph
    # --------------------------------------------------------

    try:

        preliminary_graph = build_case_graph(
            preliminary_entities,
            preliminary_relations,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Graph construction failed: {str(e)}"
            ),
        )

    # --------------------------------------------------------
    # Select search nodes
    # --------------------------------------------------------

    nodes = list(
        preliminary_graph.nodes
    )

    if len(nodes) >= 2:

        start = str(
            nodes[0]
        )

        target = str(
            nodes[-1]
        )

    else:

        start = ""
        target = ""

    # ========================================================
    # RUN FULL INVESTIGATION PIPELINE
    # ========================================================

    result = run_investigation_pipeline(
        case_text,
        start,
        target,
    )

    # ========================================================
    # PDF REPORT
    # ========================================================

    report_file = None

    explanation = result["explanation"]

    try:

        report_file = generate_report(
            case_text,
            result["entities"],
            result["relations"],
            result["search_results"],
            result["confidence"],
            result["contradictions"],
            graph_data=result["graph_data"],
            start=result["start"],
            target=result["target"],
            bfs_path=result["bfs_path"],
            dfs_path=result["dfs_path"],
            astar_path=result["astar_path"],
            explanation=result["explanation"],
            username=username,
        )

    except Exception as e:

        explanation = (
            f"{result['explanation']}\n"
            f"PDF report generation failed: {str(e)}"
        )

    # ========================================================
    # ACTIVITY LOG
    # ========================================================

    try:

        log_activity(
            username,
            "EXCEL_INVESTIGATION",
            (
                "Excel case report analyzed: "
                f"{file.filename}"
            ),
        )

    except Exception:

        pass

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "status": "success",

        "message": (
            "Excel case report analyzed successfully."
        ),

        "filename": file.filename,

        "original_rows": original_rows,

        "rows_processed": len(
            dataframe
        ),

        "rows_limited": rows_limited,

        "columns_detected": [
            str(column)
            for column in dataframe.columns
        ],

        "entities": result["entities"],

        "relations": result["relations"],

        "graph": result["graph_data"],

        "search_results": result["search_results"],

        "algorithm_pair": result["algorithm_pair"],

        "algorithm_status": result["algorithm_status"],

        "search_hint": result["search_hint"],

        "start": result["start"],

        "target": result["target"],

        "bfs_path": result["bfs_path"],

        "dfs_path": result["dfs_path"],

        "astar_path": result["astar_path"],

        "bayesian_confidence": result["confidence"],

        "contradictions": result["contradictions"],

        "explanation": explanation,

        "report": {

            "file": report_file,

            "message": (
                "Investigation PDF report generated successfully."
                if report_file
                else "PDF report could not be generated."
            ),
        },
    }



# ============================================================
# CASE MANAGEMENT
# ============================================================

@router.get("/dashboard/stats")
def dashboard_stats(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    """Return dashboard statistics for the authenticated investigator."""

    user, _ = get_authenticated_user(credentials)
    username = user["username"]

    conn = get_connection()

    try:
        cur = conn.cursor()

        cur.execute(
            """
            SELECT
                COUNT(*) AS total,
                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(COALESCE(status, ''))) = 'ONGOING'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS ongoing,
                COALESCE(
                    SUM(
                        CASE
                            WHEN UPPER(TRIM(COALESCE(status, ''))) = 'CLOSED'
                            THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS closed,
                COALESCE(SUM(entities_count), 0) AS entities,
                COALESCE(SUM(relations_count), 0) AS relations,
                COALESCE(AVG(confidence), 0) AS confidence,
                COALESCE(SUM(contradictions_count), 0) AS contradictions
            FROM investigation_cases
            WHERE username = ?
            """,
            (username,),
        )

        row = cur.fetchone()
        data = dict(row) if row else {}

        total = int(data.get("total") or 0)
        ongoing = int(data.get("ongoing") or 0)
        closed = int(data.get("closed") or 0)

        cur.execute(
            """
            SELECT
                substr(created_at, 1, 10) AS day,
                COUNT(*) AS count
            FROM investigation_cases
            WHERE
                username = ?
                AND created_at >= datetime('now', '-6 days')
            GROUP BY substr(created_at, 1, 10)
            ORDER BY day
            """,
            (username,),
        )

        daily = [dict(item) for item in cur.fetchall()]

        return {
            "status": "success",
            "total": total,
            "ongoing": ongoing,
            "closed": closed,
            "not_finished": ongoing,
            "entities": int(data.get("entities") or 0),
            "relations": int(data.get("relations") or 0),
            "confidence": round(
                float(data.get("confidence") or 0),
                2,
            ),
            "contradictions": int(
                data.get("contradictions") or 0
            ),
            "daily": daily,
        }

    finally:
        conn.close()

@router.get("/cases")
def list_cases(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    user, _ = get_authenticated_user(credentials)
    conn=get_connection()
    try:
        cur=conn.cursor()
        cur.execute("""SELECT id, case_name title, status, entities_count, relations_count,
                              confidence, contradictions_count, report_file, created_at, updated_at, closed_at
                       FROM investigation_cases WHERE username=? ORDER BY id DESC""", (user["username"],))
        return {"status":"success", "cases":[dict(x) for x in cur.fetchall()]}
    finally:
        conn.close()


@router.get("/cases/{case_id}")
def get_case(case_id:int, credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    user,_=get_authenticated_user(credentials); conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT * FROM investigation_cases WHERE id=? AND username=?",(case_id,user["username"]))
        row=cur.fetchone()
        if not row: raise HTTPException(404,"Case not found.")
        return {"status":"success","case":dict(row)}
    finally: conn.close()


# ============================================================
# ANALYZE EXISTING CASE (NO NEW CASE IS CREATED)
# ============================================================
#
# Re-running the AI pipeline on an existing case MUST NOT
# insert a second row into investigation_cases.  Only the
# explicit "new investigation" endpoint (POST /investigate is
# allowed to create a case.  This endpoint therefore runs the
# exact same NLP -> graph -> search pipeline against the stored
# case text and returns the results bound to the SAME case_id.


@router.post("/cases/{case_id}/analyze")
def analyze_case(
    case_id: int,
    request: AnalyzeCaseRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Re-analyze an existing case without creating a new case.
    """

    user, _ = get_authenticated_user(
        credentials
    )

    # --------------------------------------------------------
    # Load the stored case text (authoritative).
    # --------------------------------------------------------

    conn = get_connection()

    try:

        cur = conn.cursor()

        cur.execute(
            """
            SELECT *
            FROM investigation_cases
            WHERE id = ? AND username = ?
            """,
            (case_id, user["username"]),
        )

        row = cur.fetchone()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Case not found.",
            )

        case = dict(row)

    finally:

        conn.close()

    case_text = str(
        case.get("case_text") or ""
    ).strip()

    if not case_text:
        raise HTTPException(
            status_code=400,
            detail="The stored case description is empty.",
        )

    # --------------------------------------------------------
    # Run the full pipeline with the ORIGINAL case_id attached.
    # --------------------------------------------------------

    result = run_investigation_pipeline(
        case_text,
        request.start_node,
        request.target_node,
    )

    # --------------------------------------------------------
    # REGENERATE THE PDF from the SAME search_results the UI
    # displays.  Re-analysis must never leave the stored report
    # pointing at a stale file from the original investigation.
    # --------------------------------------------------------

    report_file = case.get("report_file")

    try:

        report_file = generate_report(
            case_text,
            result["entities"],
            result["relations"],
            result["search_results"],
            result["confidence"],
            result["contradictions"],
            graph_data=result["graph_data"],
            start=result["start"],
            target=result["target"],
            bfs_path=result["bfs_path"],
            dfs_path=result["dfs_path"],
            astar_path=result["astar_path"],
            explanation=result["explanation"],
            username=user["username"],
        )

        conn = get_connection()

        try:

            cur = conn.cursor()

            cur.execute(
                """
                UPDATE investigation_cases
                SET report_file = ?,
                    entities_count = ?,
                    relations_count = ?,
                    confidence = ?,
                    contradictions_count = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND username = ?
                """,
                (
                    report_file,
                    len(result["entities"]),
                    len(result["relations"]),
                    float(result["confidence"] or 0),
                    len(result["contradictions"]),
                    case_id,
                    user["username"],
                ),
            )

            conn.commit()

        finally:

            conn.close()

    except Exception as e:

        report_file = case.get("report_file")

        log_activity(
            user["username"],
            "CASE_ANALYZED",
            (
                f"Case {case_id} re-analyzed; PDF regeneration "
                f"failed: {str(e)}"
            ),
        )

    log_activity(
        user["username"],
        "CASE_ANALYZED",
        f"Case {case_id} re-analyzed (no new case created).",
    )

    return {
        "status": "success",

        "case_id": case_id,

        "case_name": case.get("case_name"),

        "reanalyzed": True,

        "entities": result["entities"],

        "relations": result["relations"],

        "graph": result["graph_data"],

        "search_results": result["search_results"],

        "algorithm_pair": result["algorithm_pair"],

        "algorithm_status": result["algorithm_status"],

        "search_hint": result["search_hint"],

        "search_error": result["search_results"].get("error"),

        "start": result["start"],

        "target": result["target"],

        "bfs_path": result["bfs_path"],

        "dfs_path": result["dfs_path"],

        "astar_path": result["astar_path"],

        "bayesian_confidence": result["confidence"],

        "confidence_details": result["confidence_details"],

        "contradictions": result["contradictions"],

        "explanation": result["explanation"],

        "report": {
            "file": report_file,
            "message": (
                "Case re-analyzed; the PDF report was "
                "regenerated from the current search results."
                if report_file
                else "PDF report could not be regenerated."
            ),
        },
    }


@router.patch("/cases/{case_id}/status")
def update_case_status(case_id:int, payload:dict, credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    user,_=get_authenticated_user(credentials); status=str(payload.get("status","")).upper()
    if status not in {"ONGOING","CLOSED"}: raise HTTPException(400,"Status must be ONGOING or CLOSED.")
    conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("SELECT id FROM investigation_cases WHERE id=? AND username=?",(case_id,user["username"]))
        if not cur.fetchone(): raise HTTPException(404,"Case not found.")
        closed_at=datetime.now().isoformat() if status=="CLOSED" else None
        cur.execute("UPDATE investigation_cases SET status=?, updated_at=CURRENT_TIMESTAMP, closed_at=? WHERE id=? AND username=?",(status,closed_at,case_id,user["username"]))
        conn.commit()
        log_activity(user["username"],"CASE_STATUS_CHANGED",f"Case {case_id} changed to {status}.")
        return {"status":"success","case_status":status}
    finally: conn.close()


@router.delete("/cases/{case_id}")
def delete_case(case_id:int, credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    user,_=get_authenticated_user(credentials); conn=get_connection()
    try:
        cur=conn.cursor(); cur.execute("DELETE FROM investigation_cases WHERE id=? AND username=?",(case_id,user["username"]))
        if cur.rowcount==0: raise HTTPException(404,"Case not found.")
        conn.commit(); log_activity(user["username"],"CASE_DELETED",f"Case {case_id} deleted.")
        return {"status":"success","message":"Case deleted successfully."}
    finally: conn.close()


# ============================================================
# ACTIVITY LOGS
# ============================================================


@router.get("/auth/logs")
def get_logs(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
):
    """
    Return the latest 100 activity logs
    for the currently authenticated user.
    """

    user, token = get_authenticated_user(
        credentials
    )

    username = user["username"]

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                action,
                details,
                created_at
            FROM activity_logs
            WHERE username = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (username,),
        )

        logs = [
            dict(row)
            for row in cursor.fetchall()
        ]

    finally:

        connection.close()

    return {
        "status": "success",
        "logs": logs,
    }