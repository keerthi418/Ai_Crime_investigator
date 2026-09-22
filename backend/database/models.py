"""
============================================================
DATABASE MODELS
============================================================

Database operations for the AI Crime Investigator.

This module handles:

    - User creation
    - User lookup
    - Password updates
    - Two-Factor Authentication (2FA)
    - Password reset tokens
    - Password reset token validation
    - Password reset token consumption
    - Password reset token invalidation
"""

from backend.database.database import get_connection


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    username,
    email,
    password_hash
):
    """
    Create a new user.

    Returns:
        user_id -> successful creation
        None    -> creation failed
    """

    username = str(username).strip()
    email = str(email).strip().lower()

    if not username or not email or not password_hash:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (
                username,
                email,
                password_hash
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                password_hash
            )
        )

        connection.commit()

        return cursor.lastrowid

    except Exception:
        connection.rollback()
        return None

    finally:
        connection.close()


# ============================================================
# GET USER BY USERNAME
# ============================================================

def get_user_by_username(username):
    """
    Find a user using username.

    Returns:
        sqlite3.Row -> user found
        None        -> user not found
    """

    username = str(username).strip()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
            LIMIT 1
            """,
            (username,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# GET USER BY EMAIL
# ============================================================

def get_user_by_email(email):
    """
    Find a user using email.

    Returns:
        sqlite3.Row -> user found
        None        -> user not found
    """

    email = str(email).strip().lower()

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            LIMIT 1
            """,
            (email,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# GET USER BY ID
# ============================================================

def get_user_by_id(user_id):
    """
    Find a user using their database ID.

    Returns:
        sqlite3.Row -> user found
        None        -> user not found
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# UPDATE PASSWORD
# ============================================================

def update_password(
    user_id,
    password_hash
):
    """
    Update a user's password.

    Returns:
        True  -> password updated
        False -> update failed/user not found
    """

    if not user_id or not password_hash:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (
                password_hash,
                user_id
            )
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        return False

    finally:
        connection.close()


# ============================================================
# GET 2FA STATUS
# ============================================================

def get_2fa_status(user_id):
    """
    Get 2FA status and secret for a user.

    Returns:
        sqlite3.Row containing:
            two_factor_enabled
            two_factor_secret

        or None if user doesn't exist.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                two_factor_enabled,
                two_factor_secret
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# GET 2FA SECRET
# ============================================================

def get_2fa_secret(user_id):
    """
    Get only the 2FA secret for a user.

    Returns:
        secret -> string
        None   -> no secret/user
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT two_factor_secret
            FROM users
            WHERE id = ?
            LIMIT 1
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return None

        return user["two_factor_secret"]

    finally:
        connection.close()


# ============================================================
# ENABLE / DISABLE 2FA
# ============================================================

def set_2fa(
    user_id,
    enabled,
    secret=None
):
    """
    Enable or disable 2FA.

    If a secret is supplied, both the secret and
    enabled status are updated.

    If secret is None, only the enabled status changes.

    Returns:
        True  -> update successful
        False -> update failed
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        if secret is not None:

            cursor.execute(
                """
                UPDATE users
                SET
                    two_factor_enabled = ?,
                    two_factor_secret = ?
                WHERE id = ?
                """,
                (
                    1 if enabled else 0,
                    secret,
                    user_id
                )
            )

        else:

            cursor.execute(
                """
                UPDATE users
                SET two_factor_enabled = ?
                WHERE id = ?
                """,
                (
                    1 if enabled else 0,
                    user_id
                )
            )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        return False

    finally:
        connection.close()


# ============================================================
# DISABLE 2FA AND CLEAR SECRET
# ============================================================

def disable_2fa(user_id):
    """
    Disable 2FA and remove the stored secret.

    Returns:
        True  -> successful
        False -> error/user not found
    """

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET
                two_factor_enabled = 0,
                two_factor_secret = NULL
            WHERE id = ?
            """,
            (user_id,)
        )

        connection.commit()

        return cursor.rowcount > 0

    except Exception:
        connection.rollback()
        return False

    finally:
        connection.close()


# ============================================================
# CREATE PASSWORD RESET TOKEN
# ============================================================

def create_reset_token(
    user_id,
    token_hash,
    expires_at
):
    """
    Create a new password-reset token.

    Any previous unused tokens for the same user
    are invalidated first.

    Returns:
        True  -> token created
        False -> failed
    """

    if not user_id or not token_hash or not expires_at:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Invalidate previous unused tokens
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE user_id = ?
            AND used = 0
            """,
            (user_id,)
        )

        # ----------------------------------------------------
        # Create new token
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO password_reset_tokens
            (
                user_id,
                token_hash,
                expires_at,
                used
            )
            VALUES (?, ?, ?, 0)
            """,
            (
                user_id,
                token_hash,
                expires_at
            )
        )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        return False

    finally:
        connection.close()


# ============================================================
# GET RESET TOKEN
# ============================================================

def get_reset_token(token_hash):
    """
    Find an active password-reset token.

    IMPORTANT:
        This function DOES NOT consume the token.

    The caller can use this function to check:
        - token exists
        - token has not been used
        - token has not expired

    Returns:
        sqlite3.Row -> token found
        None        -> token not found/already used
    """

    if not token_hash:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT *
            FROM password_reset_tokens
            WHERE token_hash = ?
            AND used = 0
            LIMIT 1
            """,
            (token_hash,)
        )

        return cursor.fetchone()

    finally:
        connection.close()


# ============================================================
# CONSUME PASSWORD RESET TOKEN
# ============================================================

def consume_reset_token(
    token_hash
):
    """
    Find an unused password-reset token and mark it
    as used.

    IMPORTANT:
        This should only be called AFTER the caller has
        verified that the token has not expired.

    Returns:
        sqlite3.Row -> successfully consumed token
        None        -> token doesn't exist/already used
    """

    if not token_hash:
        return None

    connection = get_connection()

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # Find unused token
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT *
            FROM password_reset_tokens
            WHERE token_hash = ?
            AND used = 0
            LIMIT 1
            """,
            (token_hash,)
        )

        token = cursor.fetchone()

        if not token:
            return None

        # ----------------------------------------------------
        # Mark token as used
        # ----------------------------------------------------

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE id = ?
            AND used = 0
            """,
            (token["id"],)
        )

        # Make sure token was actually consumed.

        if cursor.rowcount == 0:
            connection.rollback()
            return None

        connection.commit()

        return token

    except Exception:
        connection.rollback()
        return None

    finally:
        connection.close()


# ============================================================
# INVALIDATE USER RESET TOKENS
# ============================================================

def invalidate_reset_tokens(
    user_id
):
    """
    Invalidate all unused password-reset tokens
    belonging to a user.

    Returns:
        True  -> successful
        False -> error
    """

    if not user_id:
        return False

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE password_reset_tokens
            SET used = 1
            WHERE user_id = ?
            AND used = 0
            """,
            (user_id,)
        )

        connection.commit()

        return True

    except Exception:
        connection.rollback()
        return False

    finally:
        connection.close()