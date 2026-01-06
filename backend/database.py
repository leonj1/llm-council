"""MySQL database connection and user persistence for LLM Council."""

import os
import uuid
import mysql.connector
from mysql.connector import Error
from typing import Optional, List
from contextlib import contextmanager

# Database configuration from environment
DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "llm_council")


def get_connection():
    """Create and return a MySQL connection."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


@contextmanager
def get_db_cursor():
    """Context manager for database cursor with auto-commit."""
    connection = get_connection()
    if connection is None:
        yield None
        return
    try:
        cursor = connection.cursor(dictionary=True)
        yield cursor
        connection.commit()
    except Error as e:
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()


def upsert_user(google_id: str, email: str, name: Optional[str], picture_url: Optional[str]) -> Optional[dict]:
    """
    Insert or update a user based on Google OAuth data.
    Returns the user record if successful, None otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            print("Warning: Database not available, skipping user persistence")
            return None

        # Try to find existing user by google_id
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, created_at, updated_at FROM users WHERE google_id = %s",
            (google_id,)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            # Update existing user
            cursor.execute(
                """
                UPDATE users
                SET email = %s, name = %s, picture_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE google_id = %s
                """,
                (email, name, picture_url, google_id)
            )
            # Fetch updated record
            cursor.execute(
                "SELECT id, google_id, email, name, picture_url, created_at, updated_at FROM users WHERE google_id = %s",
                (google_id,)
            )
            return cursor.fetchone()
        else:
            # Insert new user
            cursor.execute(
                """
                INSERT INTO users (google_id, email, name, picture_url)
                VALUES (%s, %s, %s, %s)
                """,
                (google_id, email, name, picture_url)
            )
            user_id = cursor.lastrowid
            cursor.execute(
                "SELECT id, google_id, email, name, picture_url, created_at, updated_at FROM users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()


def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email address."""
    with get_db_cursor() as cursor:
        if cursor is None:
            return None
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, created_at, updated_at FROM users WHERE email = %s",
            (email,)
        )
        return cursor.fetchone()


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get a user by ID."""
    with get_db_cursor() as cursor:
        if cursor is None:
            return None
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        return cursor.fetchone()


def create_chat(user_id: int) -> Optional[dict]:
    """
    Create a new chat for the given user.
    Returns the created chat record if successful, None otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            print("Warning: Database not available, skipping chat creation")
            return None

        # Generate UUID for chat id
        chat_id = str(uuid.uuid4())

        # Insert new chat
        cursor.execute(
            "INSERT INTO chats (id, user_id) VALUES (%s, %s)",
            (chat_id, user_id)
        )

        # Fetch created record
        cursor.execute(
            "SELECT id, user_id, created_at FROM chats WHERE id = %s",
            (chat_id,)
        )
        return cursor.fetchone()


def get_chats_by_user_id(user_id: int) -> List[dict]:
    """
    Get all chats for the given user.
    Returns a list of chat records, empty list if none found or database unavailable.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            return []

        cursor.execute(
            "SELECT id, user_id, created_at FROM chats WHERE user_id = %s ORDER BY created_at DESC",
            (user_id,)
        )
        result = cursor.fetchall()
        return result if result else []


def get_chat_by_id(chat_id: str) -> Optional[dict]:
    """
    Get a single chat by ID.
    Returns the chat record if found, None otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            return None

        cursor.execute(
            "SELECT id, user_id, created_at FROM chats WHERE id = %s",
            (chat_id,)
        )
        return cursor.fetchone()
