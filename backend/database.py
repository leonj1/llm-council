"""MySQL database connection and user persistence for LLM Council."""

import os
import uuid
import json
import mysql.connector
from mysql.connector import Error
from typing import Optional, List
from contextlib import contextmanager

def _get_db_config():
    """Get database configuration from environment at runtime.

    Railway uses DB_* vars, local dev may use MYSQL_* vars.
    Reading at runtime ensures env vars are available after container starts.
    """
    return {
        "host": os.getenv("DB_HOST") or os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT") or os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("DB_USER") or os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("DB_PASSWORD") or os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("DB_NAME") or os.getenv("MYSQL_DATABASE", "llm_council"),
    }


def get_connection():
    """Create and return a MySQL connection."""
    try:
        config = _get_db_config()
        connection = mysql.connector.connect(**config)
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


def create_message(
    chat_id: str,
    role: str,
    content: str,
    stage1_data: Optional[dict],
    stage2_data: Optional[dict],
    stage3_data: Optional[dict]
) -> Optional[dict]:
    """
    Create a new message for the given chat.

    Args:
        chat_id: UUID of the chat
        role: 'user' or 'assistant'
        content: Message text content
        stage1_data: Stage 1 data (model responses) - JSON serializable dict or None
        stage2_data: Stage 2 data (rankings) - JSON serializable dict or None
        stage3_data: Stage 3 data (synthesis) - JSON serializable dict or None

    Returns the created message record if successful, None otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            print("Warning: Database not available, skipping message creation")
            return None

        # Insert new message with JSON serialization for stage data
        cursor.execute(
            """
            INSERT INTO messages (chat_id, role, content, stage1_data, stage2_data, stage3_data)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                chat_id,
                role,
                content,
                json.dumps(stage1_data) if stage1_data else None,
                json.dumps(stage2_data) if stage2_data else None,
                json.dumps(stage3_data) if stage3_data else None
            )
        )

        message_id = cursor.lastrowid

        # Fetch created record
        cursor.execute(
            """
            SELECT id, chat_id, role, content, stage1_data, stage2_data, stage3_data, created_at
            FROM messages WHERE id = %s
            """,
            (message_id,)
        )
        message = cursor.fetchone()

        # Deserialize JSON fields
        if message:
            if message['stage1_data']:
                message['stage1_data'] = json.loads(message['stage1_data'])
            if message['stage2_data']:
                message['stage2_data'] = json.loads(message['stage2_data'])
            if message['stage3_data']:
                message['stage3_data'] = json.loads(message['stage3_data'])

        return message


def get_messages_by_chat_id(chat_id: str) -> List[dict]:
    """
    Get all messages for the given chat in chronological order.

    Args:
        chat_id: UUID of the chat

    Returns a list of message records ordered by created_at ascending, empty list if none found or database unavailable.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            return []

        cursor.execute(
            """
            SELECT id, chat_id, role, content, stage1_data, stage2_data, stage3_data, created_at
            FROM messages
            WHERE chat_id = %s
            ORDER BY created_at ASC
            """,
            (chat_id,)
        )
        messages = cursor.fetchall()

        # Deserialize JSON fields for each message
        if messages:
            for message in messages:
                if message['stage1_data']:
                    message['stage1_data'] = json.loads(message['stage1_data'])
                if message['stage2_data']:
                    message['stage2_data'] = json.loads(message['stage2_data'])
                if message['stage3_data']:
                    message['stage3_data'] = json.loads(message['stage3_data'])

        return messages if messages else []


def get_message_by_id(message_id: int) -> Optional[dict]:
    """
    Get a single message by ID.

    Args:
        message_id: Integer ID of the message

    Returns the message record if found with deserialized JSON fields, None otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            return None

        cursor.execute(
            """
            SELECT id, chat_id, role, content, stage1_data, stage2_data, stage3_data, created_at
            FROM messages WHERE id = %s
            """,
            (message_id,)
        )
        message = cursor.fetchone()

        # Deserialize JSON fields
        if message:
            if message['stage1_data']:
                message['stage1_data'] = json.loads(message['stage1_data'])
            if message['stage2_data']:
                message['stage2_data'] = json.loads(message['stage2_data'])
            if message['stage3_data']:
                message['stage3_data'] = json.loads(message['stage3_data'])

        return message


def delete_chat(chat_id: str) -> bool:
    """
    Delete a chat by ID.
    Messages are automatically cascade-deleted via foreign key constraint.

    Args:
        chat_id: UUID of the chat to delete

    Returns True if chat was deleted, False otherwise.
    """
    with get_db_cursor() as cursor:
        if cursor is None:
            print("Warning: Database not available, skipping chat deletion")
            return False

        cursor.execute(
            "DELETE FROM chats WHERE id = %s",
            (chat_id,)
        )

        # Check if any rows were affected
        return cursor.rowcount > 0
