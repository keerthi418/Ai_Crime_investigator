import hashlib
import secrets
import base64


def hash_password(password: str):

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        120000
    )

    return (
        base64.b64encode(salt).decode()
        + ":"
        + base64.b64encode(password_hash).decode()
    )


def verify_password(password: str, stored_password: str):

    try:

        salt_b64, hash_b64 = stored_password.split(":")

        salt = base64.b64decode(salt_b64)

        expected_hash = base64.b64decode(hash_b64)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            120000
        )

        return secrets.compare_digest(
            actual_hash,
            expected_hash
        )

    except Exception:

        return False


# Simple offline session storage
ACTIVE_SESSIONS = {}


def create_session(username):

    token = secrets.token_urlsafe(32)

    ACTIVE_SESSIONS[token] = username

    return token


def get_session_user(token):

    return ACTIVE_SESSIONS.get(token)


def remove_session(token):

    if token in ACTIVE_SESSIONS:

        del ACTIVE_SESSIONS[token]