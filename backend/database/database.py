"""
============================================================
DATABASE MODULE
============================================================

SQLite database management for the AI Crime Investigator.

This module handles:

    - SQLite connection
    - Database initialization
    - Users
    - Two-Factor Authentication (2FA)
    - Activity logs
    - Password reset tokens
    - Investigation cases
    - Database health checking
    - Database migrations
"""

import sqlite3
from pathlib import Path


# ============================================================
# DATABASE LOCATION
# ============================================================

# Project structure:
#
# Ai_Crime_investigator/
# │
# ├── app.py
# ├── crime_investigator.db
# │
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

    # Make sure the project directory exists.
    BASE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DATABASE_PATH),
        check_same_thread=False,
        timeout=30
    )

    # Return rows like dictionaries.
    connection.row_factory = sqlite3.Row

    # Enable foreign-key constraints.
    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    # Improve SQLite write reliability.
    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    # Wait for locked database briefly.
    connection.execute(
        "PRAGMA busy_timeout = 30000"
    )

    return connection


# ============================================================
# INITIALIZE DATABASE
# ============================================================

def init_database():
    """
    Create all required database tables.

    Safe to run multiple times.

    Existing users and investigation data
    are preserved.
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

                two_factor_enabled INTEGER
                    NOT NULL DEFAULT 0,

                two_factor_secret TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        # ====================================================
        # USERS TABLE MIGRATION
        # ====================================================

        cursor.execute(
            "PRAGMA table_info(users)"
        )

        existing_user_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        # ----------------------------------------------------
        # Add 2FA enabled column if missing
        # ----------------------------------------------------

        if "two_factor_enabled" not in existing_user_columns:

            cursor.execute(
                """
                ALTER TABLE users
                ADD COLUMN two_factor_enabled
                INTEGER NOT NULL DEFAULT 0
                """
            )

        # ----------------------------------------------------
        # Add 2FA secret column if missing
        # ----------------------------------------------------

        if "two_factor_secret" not in existing_user_columns:

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

                used INTEGER
                    NOT NULL DEFAULT 0,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # ====================================================
        # PASSWORD RESET TOKEN MIGRATION
        # ====================================================

        cursor.execute(
            "PRAGMA table_info(password_reset_tokens)"
        )

        existing_reset_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "used" not in existing_reset_columns:

            cursor.execute(
                """
                ALTER TABLE password_reset_tokens
                ADD COLUMN used
                INTEGER NOT NULL DEFAULT 0
                """
            )

        # ====================================================
        # INVESTIGATION CASES
        # ====================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS investigation_cases (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                case_name TEXT NOT NULL,

                case_text TEXT NOT NULL,

                username TEXT NOT NULL,

                status TEXT
                    NOT NULL DEFAULT 'ONGOING',

                entities_count INTEGER
                    NOT NULL DEFAULT 0,

                relations_count INTEGER
                    NOT NULL DEFAULT 0,

                confidence REAL
                    NOT NULL DEFAULT 0,

                contradictions_count INTEGER
                    NOT NULL DEFAULT 0,

                report_file TEXT,

                created_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                updated_at TIMESTAMP
                    DEFAULT CURRENT_TIMESTAMP,

                closed_at TIMESTAMP
            )
            """
        )

        # ====================================================
        # INVESTIGATION CASE MIGRATION
        # ====================================================

        cursor.execute(
            "PRAGMA table_info(investigation_cases)"
        )

        existing_case_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        # ----------------------------------------------------
        # Add case_name if missing
        # ----------------------------------------------------

        if "case_name" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN case_name TEXT
                """
            )

            cursor.execute(
                """
                UPDATE investigation_cases
                SET case_name = 'Untitled Investigation'
                WHERE case_name IS NULL
                """
            )

        # ----------------------------------------------------
        # Add case_text if missing
        # ----------------------------------------------------

        if "case_text" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN case_text TEXT
                """
            )

        # ----------------------------------------------------
        # Add username if missing
        # ----------------------------------------------------

        if "username" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN username TEXT
                """
            )

        # ----------------------------------------------------
        # Add status if missing
        # ----------------------------------------------------

        if "status" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN status TEXT
                NOT NULL DEFAULT 'ONGOING'
                """
            )

        # ----------------------------------------------------
        # Add entities_count if missing
        # ----------------------------------------------------

        if "entities_count" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN entities_count
                INTEGER NOT NULL DEFAULT 0
                """
            )

        # ----------------------------------------------------
        # Add relations_count if missing
        # ----------------------------------------------------

        if "relations_count" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN relations_count
                INTEGER NOT NULL DEFAULT 0
                """
            )

        # ----------------------------------------------------
        # Add confidence if missing
        # ----------------------------------------------------

        if "confidence" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN confidence
                REAL NOT NULL DEFAULT 0
                """
            )

        # ----------------------------------------------------
        # Add contradictions_count if missing
        # ----------------------------------------------------

        if "contradictions_count" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN contradictions_count
                INTEGER NOT NULL DEFAULT 0
                """
            )

        # ----------------------------------------------------
        # Add report_file if missing
        # ----------------------------------------------------

        if "report_file" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN report_file TEXT
                """
            )

        # ----------------------------------------------------
        # Add created_at if missing
        # ----------------------------------------------------

        if "created_at" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN created_at
                TIMESTAMP
                """
            )

        # ----------------------------------------------------
        # Add updated_at if missing
        # ----------------------------------------------------

        if "updated_at" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN updated_at
                TIMESTAMP
                """
            )

        # ----------------------------------------------------
        # Add closed_at if missing
        # ----------------------------------------------------

        if "closed_at" not in existing_case_columns:

            cursor.execute(
                """
                ALTER TABLE investigation_cases
                ADD COLUMN closed_at
                TIMESTAMP
                """
            )

        # ====================================================
        # CLEAN INVALID CASE STATUS VALUES
        # ====================================================

        cursor.execute(
            """
            UPDATE investigation_cases
            SET status = 'ONGOING'
            WHERE status IS NULL
               OR status NOT IN ('ONGOING', 'CLOSED')
            """
        )

        # ====================================================
        # INDEXES
        # ====================================================

        # ----------------------------------------------------
        # User email
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_email
            ON users(email)
            """
        )

        # ----------------------------------------------------
        # Username
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_users_username
            ON users(username)
            """
        )

        # ----------------------------------------------------
        # Activity username
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_activity_username
            ON activity_logs(username)
            """
        )

        # ----------------------------------------------------
        # Activity timestamp
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_activity_created_at
            ON activity_logs(created_at)
            """
        )

        # ----------------------------------------------------
        # Reset tokens by user
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_reset_tokens_user
            ON password_reset_tokens(user_id)
            """
        )

        # ----------------------------------------------------
        # Reset tokens by hash
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_reset_tokens_hash
            ON password_reset_tokens(token_hash)
            """
        )

        # ----------------------------------------------------
        # Reset tokens by expiry
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_reset_tokens_expiry
            ON password_reset_tokens(expires_at)
            """
        )

        # ----------------------------------------------------
        # Cases by username
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_username
            ON investigation_cases(username)
            """
        )

        # ----------------------------------------------------
        # Cases by status
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_status
            ON investigation_cases(status)
            """
        )

        # ----------------------------------------------------
        # Cases by creation date
        # ----------------------------------------------------

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_cases_created_at
            ON investigation_cases(created_at)
            """
        )

        # ====================================================
        # COMMIT EVERYTHING
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

    username = (
        str(username).strip()
        if username is not None
        else ""
    )

    action = (
        str(action).strip()
        if action is not None
        else ""
    )

    details = (
        str(details).strip()
        if details is not None
        else ""
    )

    if not action:
        return False

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

        return True

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
# DATABASE HEALTH CHECK
# ============================================================

def database_health():
    """
    Return a simple database health report.

    Returns:

        {
            "status": "online",
            "database": "...",
            "users": 10,
            "cases": 5,
            "activities": 20
        }
    """

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        # ----------------------------------------------------
        # Users
        # ----------------------------------------------------

        cursor.execute(
            "SELECT COUNT(*) AS count FROM users"
        )

        users_count = cursor.fetchone()["count"]

        # ----------------------------------------------------
        # Cases
        # ----------------------------------------------------

        cursor.execute(
            "SELECT COUNT(*) AS count FROM investigation_cases"
        )

        cases_count = cursor.fetchone()["count"]

        # ----------------------------------------------------
        # Activities
        # ----------------------------------------------------

        cursor.execute(
            "SELECT COUNT(*) AS count FROM activity_logs"
        )

        activities_count = cursor.fetchone()["count"]

        return {
            "status": "online",
            "database": str(DATABASE_PATH),
            "users": users_count,
            "cases": cases_count,
            "activities": activities_count
        }

    except sqlite3.Error as error:

        return {
            "status": "offline",
            "database": str(DATABASE_PATH),
            "error": str(error)
        }

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