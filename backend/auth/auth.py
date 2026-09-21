"""
Authentication and Security Utilities
-------------------------------------

AI Crime Investigator authentication module.

This module handles:

    - Password hashing
    - Password verification
    - Session management
    - Pending 2FA challenges
    - TOTP secret generation
    - TOTP code generation
    - TOTP verification
    - Authenticator provisioning URI

No external authentication framework is required.

NOTE:
The session and pending-2FA stores are in-memory and are intended
for a local/demo deployment. They are cleared when the application
restarts.
"""

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote


# ============================================================
# PASSWORD HASHING CONFIGURATION
# ============================================================

PBKDF2_ITERATIONS = 120000
PASSWORD_SALT_BYTES = 16
PASSWORD_HASH_ALGORITHM = "sha256"


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(password: str) -> str:
    """
    Create a secure password hash using PBKDF2-HMAC-SHA256.

    Stored format:

        base64(salt):base64(hash)

    Example:

        abc123...:xyz789...
    """

    if password is None:
        raise ValueError("Password cannot be None.")

    if not isinstance(password, str):
        password = str(password)

    if not password:
        raise ValueError("Password cannot be empty.")

    salt = secrets.token_bytes(PASSWORD_SALT_BYTES)

    password_hash = hashlib.pbkdf2_hmac(
        PASSWORD_HASH_ALGORITHM,
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )

    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(password_hash).decode("ascii")

    return f"{salt_b64}:{hash_b64}"


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    stored_password: str
) -> bool:
    """
    Verify a plain-text password against a stored
    PBKDF2 password hash.

    Returns:

        True  -> password is correct
        False -> password is incorrect/invalid
    """

    try:
        if password is None:
            return False

        if stored_password is None:
            return False

        if not isinstance(password, str):
            password = str(password)

        if not isinstance(stored_password, str):
            stored_password = str(stored_password)

        parts = stored_password.split(":")

        if len(parts) != 2:
            return False

        salt_b64, hash_b64 = parts

        if not salt_b64 or not hash_b64:
            return False

        salt = base64.b64decode(
            salt_b64,
            validate=True
        )

        expected_hash = base64.b64decode(
            hash_b64,
            validate=True
        )

        if not salt or not expected_hash:
            return False

        actual_hash = hashlib.pbkdf2_hmac(
            PASSWORD_HASH_ALGORITHM,
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False

    except Exception:
        return False


# ============================================================
# SESSION MANAGEMENT
# ============================================================

"""
Active session structure:

    {
        "random-session-token": {
            "username": "user1",
            "created_at": 1234567890,
            "last_activity": 1234567890
        }
    }

Sessions are intentionally stored in memory for this project.
"""

ACTIVE_SESSIONS = {}

# Session lifetime:
# 8 hours
SESSION_TIMEOUT = 8 * 60 * 60


# ============================================================
# CREATE SESSION
# ============================================================

def create_session(username: str) -> str:
    """
    Create a new authenticated session.

    Returns:
        session token
    """

    if username is None:
        raise ValueError("Username is required.")

    username = str(username).strip()

    if not username:
        raise ValueError("Username cannot be empty.")

    token = secrets.token_urlsafe(32)

    now = time.time()

    ACTIVE_SESSIONS[token] = {
        "username": username,
        "created_at": now,
        "last_activity": now
    }

    return token


# ============================================================
# GET SESSION USER
# ============================================================

def get_session_user(token):
    """
    Get the username associated with a session token.

    Automatically removes expired sessions.

    Returns:

        username -> valid session
        None     -> invalid/expired session
    """

    if not token:
        return None

    token = str(token).strip()

    session = ACTIVE_SESSIONS.get(token)

    if not session:
        return None

    now = time.time()

    created_at = session.get("created_at", now)
    last_activity = session.get(
        "last_activity",
        created_at
    )

    # Absolute session lifetime
    if now - created_at > SESSION_TIMEOUT:
        ACTIVE_SESSIONS.pop(token, None)
        return None

    # Inactivity timeout
    if now - last_activity > SESSION_TIMEOUT:
        ACTIVE_SESSIONS.pop(token, None)
        return None

    session["last_activity"] = now

    return session.get("username")


# ============================================================
# REMOVE SESSION
# ============================================================

def remove_session(token) -> bool:
    """
    Remove an active session.

    Returns:

        True  -> session existed and was removed
        False -> session did not exist
    """

    if not token:
        return False

    token = str(token).strip()

    if token in ACTIVE_SESSIONS:
        del ACTIVE_SESSIONS[token]
        return True

    return False


# ============================================================
# REMOVE ALL USER SESSIONS
# ============================================================

def remove_user_sessions(username: str) -> int:
    """
    Remove all active sessions belonging to a username.

    Useful after:

        - password changes
        - password resets
        - security events
        - account deactivation
    """

    if not username:
        return 0

    username = str(username).strip()

    tokens_to_remove = [
        token
        for token, session in ACTIVE_SESSIONS.items()
        if session.get("username") == username
    ]

    for token in tokens_to_remove:
        ACTIVE_SESSIONS.pop(token, None)

    return len(tokens_to_remove)


# ============================================================
# TWO-FACTOR AUTHENTICATION
# ============================================================

"""
Pending 2FA structure:

    {
        "temporary-token": {
            "username": "user1",
            "created_at": 1234567890
        }
    }
"""

PENDING_2FA = {}

# 2FA challenge lifetime:
# 5 minutes
TWO_FA_CHALLENGE_TIMEOUT = 5 * 60


# ============================================================
# CREATE 2FA CHALLENGE
# ============================================================

def create_2fa_challenge(username: str) -> str:
    """
    Create a temporary challenge after successful
    password authentication.

    The user must complete 2FA before receiving
    a normal authenticated session.
    """

    if username is None:
        raise ValueError("Username is required.")

    username = str(username).strip()

    if not username:
        raise ValueError("Username cannot be empty.")

    token = secrets.token_urlsafe(32)

    PENDING_2FA[token] = {
        "username": username,
        "created_at": time.time()
    }

    return token


# ============================================================
# GET 2FA CHALLENGE
# ============================================================

def get_2fa_challenge(token):
    """
    Get the username associated with a pending
    2FA challenge.

    Expired challenges are automatically removed.

    Returns:

        username -> valid challenge
        None     -> invalid/expired challenge
    """

    if not token:
        return None

    token = str(token).strip()

    challenge = PENDING_2FA.get(token)

    if not challenge:
        return None

    created_at = challenge.get(
        "created_at",
        0
    )

    if time.time() - created_at > TWO_FA_CHALLENGE_TIMEOUT:
        PENDING_2FA.pop(token, None)
        return None

    return challenge.get("username")


# ============================================================
# CONSUME 2FA CHALLENGE
# ============================================================

def consume_2fa_challenge(token):
    """
    Consume a completed 2FA challenge.

    Once consumed, the same challenge cannot be reused.

    Returns:

        username -> valid challenge
        None     -> invalid/expired/already consumed
    """

    if not token:
        return None

    token = str(token).strip()

    challenge = PENDING_2FA.get(token)

    if not challenge:
        return None

    created_at = challenge.get(
        "created_at",
        0
    )

    if time.time() - created_at > TWO_FA_CHALLENGE_TIMEOUT:
        PENDING_2FA.pop(token, None)
        return None

    username = challenge.get("username")

    # Remove before returning so it cannot be reused.
    PENDING_2FA.pop(token, None)

    return username


# ============================================================
# REMOVE USER'S PENDING 2FA CHALLENGES
# ============================================================

def remove_user_2fa_challenges(username: str) -> int:
    """
    Remove all pending 2FA challenges belonging
    to a username.
    """

    if not username:
        return 0

    username = str(username).strip()

    tokens_to_remove = [
        token
        for token, challenge in PENDING_2FA.items()
        if challenge.get("username") == username
    ]

    for token in tokens_to_remove:
        PENDING_2FA.pop(token, None)

    return len(tokens_to_remove)


# ============================================================
# TOTP CONFIGURATION
# ============================================================

TOTP_INTERVAL = 30
TOTP_DIGITS = 6
TOTP_SECRET_BYTES = 20

# Standard TOTP uses HMAC-SHA1.
TOTP_HASH_ALGORITHM = hashlib.sha1


# ============================================================
# GENERATE TOTP SECRET
# ============================================================

def generate_totp_secret() -> str:
    """
    Generate a Base32 TOTP secret.

    Compatible with authenticator applications such as:

        - Google Authenticator
        - Microsoft Authenticator
        - Authy
        - Other standard TOTP applications

    Returns:

        Base32 encoded secret without '=' padding.
    """

    secret = base64.b32encode(
        secrets.token_bytes(
            TOTP_SECRET_BYTES
        )
    ).decode("ascii").rstrip("=")

    return secret


# ============================================================
# NORMALIZE / DECODE TOTP SECRET
# ============================================================

def _decode_totp_secret(secret):
    """
    Decode a Base32 TOTP secret.

    Internal helper.
    """

    if secret is None:
        raise ValueError(
            "TOTP secret is required."
        )

    secret = str(secret).strip()

    # Authenticator secrets are commonly displayed
    # with spaces for readability.
    secret = secret.replace(" ", "").upper()

    if not secret:
        raise ValueError(
            "TOTP secret cannot be empty."
        )

    # Restore Base32 padding.
    padding = "=" * (
        (8 - len(secret) % 8) % 8
    )

    return base64.b32decode(
        secret + padding,
        casefold=True
    )


# ============================================================
# GENERATE TOTP CODE
# ============================================================

def totp_code(
    secret,
    for_time=None
) -> str:
    """
    Generate a 6-digit TOTP code.

    A new code is generated every 30 seconds.

    Args:

        secret:
            Base32 TOTP secret.

        for_time:
            Optional Unix timestamp.
            Current time is used if omitted.

    Returns:

        Six-digit string.

    Example:

        "482193"
    """

    key = _decode_totp_secret(secret)

    if for_time is None:
        for_time = int(time.time())
    else:
        for_time = int(for_time)

    counter = int(
        for_time // TOTP_INTERVAL
    )

    counter_bytes = struct.pack(
        ">Q",
        counter
    )

    digest = hmac.new(
        key,
        counter_bytes,
        TOTP_HASH_ALGORITHM
    ).digest()

    offset = digest[-1] & 0x0F

    binary_code = struct.unpack(
        ">I",
        digest[offset:offset + 4]
    )[0] & 0x7FFFFFFF

    code = binary_code % (
        10 ** TOTP_DIGITS
    )

    return f"{code:0{TOTP_DIGITS}d}"


# ============================================================
# VERIFY TOTP CODE
# ============================================================

def verify_totp(
    secret,
    code,
    window=1
) -> bool:
    """
    Verify a TOTP authenticator code.

    Default:

        window=1

    checks:

        previous 30 seconds
        current 30 seconds
        next 30 seconds

    Returns:

        True  -> valid
        False -> invalid
    """

    try:
        if not secret:
            return False

        if code is None:
            return False

        code = str(code).strip()

        if len(code) != TOTP_DIGITS:
            return False

        if not code.isdigit():
            return False

        window = int(window)

        # Prevent an unnecessarily large
        # verification window.
        window = max(0, min(window, 5))

        now = int(time.time())

        for step in range(
            -window,
            window + 1
        ):
            generated_code = totp_code(
                secret,
                now + (
                    step * TOTP_INTERVAL
                )
            )

            if hmac.compare_digest(
                generated_code,
                code
            ):
                return True

        return False

    except (ValueError, TypeError):
        return False

    except Exception:
        return False


# ============================================================
# TOTP AUTHENTICATOR SETUP URI
# ============================================================

def totp_provisioning_uri(
    secret,
    email,
    issuer="AI Crime Investigator"
) -> str:
    """
    Generate an otpauth:// URI.

    Authenticator applications can use this URI
    to configure the TOTP account.

    Example:

        otpauth://totp/Issuer:email
        ?secret=SECRET
        &issuer=Issuer
        &algorithm=SHA1
        &digits=6
        &period=30
    """

    if not secret:
        raise ValueError(
            "TOTP secret is required."
        )

    if not email:
        raise ValueError(
            "Email is required."
        )

    if not issuer:
        issuer = "AI Crime Investigator"

    secret = str(secret).strip()
    email = str(email).strip()
    issuer = str(issuer).strip()

    if not secret:
        raise ValueError(
            "TOTP secret cannot be empty."
        )

    if not email:
        raise ValueError(
            "Email cannot be empty."
        )

    if not issuer:
        issuer = "AI Crime Investigator"

    label = f"{issuer}:{email}"

    encoded_label = quote(
        label,
        safe=""
    )

    encoded_issuer = quote(
        issuer,
        safe=""
    )

    encoded_secret = quote(
        secret,
        safe=""
    )

    return (
        "otpauth://totp/"
        f"{encoded_label}"
        f"?secret={encoded_secret}"
        f"&issuer={encoded_issuer}"
        f"&algorithm=SHA1"
        f"&digits={TOTP_DIGITS}"
        f"&period={TOTP_INTERVAL}"
    )


# ============================================================
# CLEANUP EXPIRED SECURITY DATA
# ============================================================

def cleanup_expired_security_data() -> dict:
    """
    Remove expired in-memory sessions and 2FA challenges.

    Returns:

        {
            "sessions_removed": int,
            "challenges_removed": int
        }
    """

    now = time.time()

    sessions_removed = 0
    challenges_removed = 0

    # --------------------------------------------------------
    # Expired sessions
    # --------------------------------------------------------

    session_tokens = list(
        ACTIVE_SESSIONS.keys()
    )

    for token in session_tokens:

        session = ACTIVE_SESSIONS.get(token)

        if not session:
            continue

        created_at = session.get(
            "created_at",
            now
        )

        last_activity = session.get(
            "last_activity",
            created_at
        )

        if (
            now - created_at > SESSION_TIMEOUT
            or
            now - last_activity > SESSION_TIMEOUT
        ):
            ACTIVE_SESSIONS.pop(
                token,
                None
            )
            sessions_removed += 1

    # --------------------------------------------------------
    # Expired 2FA challenges
    # --------------------------------------------------------

    challenge_tokens = list(
        PENDING_2FA.keys()
    )

    for token in challenge_tokens:

        challenge = PENDING_2FA.get(token)

        if not challenge:
            continue

        created_at = challenge.get(
            "created_at",
            now
        )

        if (
            now - created_at
            > TWO_FA_CHALLENGE_TIMEOUT
        ):
            PENDING_2FA.pop(
                token,
                None
            )
            challenges_removed += 1

    return {
        "sessions_removed": sessions_removed,
        "challenges_removed": challenges_removed
    }