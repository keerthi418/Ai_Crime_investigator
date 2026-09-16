"""
Database Module
---------------

SQLite database management for the AI Crime Investigator.

This module handles:

    - SQLite connection
    - Database initialization
    - Users
    - Two-Factor Authentication (2FA)
    - Activity logs
    - Password reset tokens
    - Database health checking
"""

import sqlite3
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

# Current file:
#
# Ai_Crime_investigator/
# └── backend/
#     └── database/
#         └── database.py
#
# parents[0] -> database
# parents[1] -> backend
# parents[2] -> project root

BASE_DIR = Path(__file__).resolve().parents[2]

DATABASE_PATH = BASE_DIR / "crime_investigator.db"


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    """
    Create and return a SQLite database connection.

    Row factory allows:

        row["username"]

    instead of:

        row[1]
    """

    connection = sqlite3.connect(
        DATABASE_PATH,
        check_same_thread=False,
        timeout=10
    )

    connection.row_factory = sqlite3.Row

    # Enable foreign-key constraints.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():
    """
    Create all required database tables.

    Safe to run multiple times.
    Existing users and data are preserved.
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        # ====================================================
        # USERS TABLE
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT UNIQUE NOT NULL,

                email TEXT UNIQUE NOT NULL,

                password_hash TEXT NOT NULL,

                two_factor_enabled INTEGER DEFAULT 0,

                two_factor_secret TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # MIGRATION FOR EXISTING DATABASE
        # ====================================================

        cursor.execute(
            "PRAGMA table_info(users)"
        )

        existing_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        # Add 2FA enabled column if missing.
        if "two_factor_enabled" not in existing_columns:

            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN two_factor_enabled
                INTEGER DEFAULT 0
                """
            )

        # Add 2FA secret column if missing.
        if "two_factor_secret" not in existing_columns:

            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN two_factor_secret
                TEXT
                """
            )

        # ====================================================
        # ACTIVITY LOG TABLE
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT,

                action TEXT NOT NULL,

                details TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # PASSWORD RESET TOKEN TABLE
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                token_hash TEXT NOT NULL,

                expires_at TIMESTAMP NOT NULL,

                used INTEGER DEFAULT 0,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # INDEXES
        # ====================================================

        # Faster email lookup during login.

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_email
            ON users(email)
            """
        )

        # Faster username lookup.

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_username
            ON users(username)
            """
        )

        # Faster activity-log lookup.

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_activity_username
            ON activity_logs(username)
            """
        )

        # Faster reset-token lookup.

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_reset_tokens_user
            ON password_reset_tokens(user_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_reset_tokens_hash
            ON password_reset_tokens(token_hash)
            """
        )

        # ====================================================
        # COMMIT
        # ====================================================

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# ACTIVITY LOGGER
# ============================================================

def log_activity(
    username,
    action,
    details=""
):
    """
    Store an activity log.

    Example:

        log_activity(
            "keerthi",
            "LOGIN_SUCCESS",
            "User logged in successfully"
        )
    """

    connection = get_connection()

    try:

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO activity_logs
            (
                username,
                action,
                details
            )
            VALUES (?, ?, ?)
            """,
            (
                username,
                action,
                details
            )
        )

        connection.commit()

    except Exception:

        connection.rollback()

        raise

    finally:

        connection.close()


# ============================================================
# DATABASE EXISTS
# ============================================================

def database_exists():
    """
    Check whether the database file exists.

    Returns:
        True  -> database exists
        False -> database does not exist
    """

    return DATABASE_PATH.exists()


# ============================================================
# DATABASE CONNECTION TEST
# ============================================================

def test_database_connection():
    """
    Test whether the SQLite database is accessible.

    Returns:
        True  -> connection successful
        False -> connection failed
    """

    connection = None

    try:

        connection = get_connection()

        connection.execute(
            "SELECT 1"
        )

        return True

    except sqlite3.Error:

        return False

    finally:

        if connection is not None:
            connection.close()


# ============================================================
# GET DATABASE PATH
# ============================================================

def get_database_path():
    """
    Return the absolute database path.
    """

    return str(
        DATABASE_PATH
    )


# ============================================================
# AUTO INITIALIZATION
# ============================================================

# Initialize the database when this module is imported.

init_database()