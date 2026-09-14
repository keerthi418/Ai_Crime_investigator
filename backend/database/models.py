from backend.database.database import get_connection


def create_user(username, email, password_hash):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (
                username,
                email,
                password_hash
            )
        )

        connection.commit()

        user_id = cursor.lastrowid

        return user_id

    except Exception:
        return None

    finally:
        connection.close()


def get_user_by_username(username):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    )

    user = cursor.fetchone()

    connection.close()

    return user


def get_user_by_email(email):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    )

    user = cursor.fetchone()

    connection.close()

    return user