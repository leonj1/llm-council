"""MySQL database connection and user persistence for LLM Council."""

import os
import uuid
import json
import logging
import mysql.connector
from mysql.connector import Error
from typing import Optional, List
from contextlib import contextmanager

# Set up verbose database logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Ensure we have a handler if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(name)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)


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
        logger.debug(f"DB CONNECT: Attempting connection to {config['host']}:{config['port']}/{config['database']}")
        connection = mysql.connector.connect(**config)
        logger.info(f"DB CONNECT: Successfully connected to MySQL database '{config['database']}'")
        return connection
    except Error as e:
        logger.error(f"DB CONNECT ERROR: Failed to connect to MySQL: {e}")
        return None


@contextmanager
def get_db_cursor():
    """Context manager for database cursor with auto-commit."""
    connection = get_connection()
    if connection is None:
        logger.warning("DB CURSOR: No database connection available, yielding None")
        yield None
        return
    try:
        cursor = connection.cursor(dictionary=True)
        logger.debug("DB CURSOR: Created cursor, beginning transaction")
        yield cursor
        connection.commit()
        logger.debug("DB CURSOR: Transaction committed successfully")
    except Error as e:
        logger.error(f"DB CURSOR ERROR: Rolling back transaction due to: {e}")
        connection.rollback()
        raise e
    finally:
        cursor.close()
        connection.close()
        logger.debug("DB CURSOR: Cursor and connection closed")


def upsert_user(google_id: str, email: str, name: Optional[str], picture_url: Optional[str]) -> Optional[dict]:
    """
    Insert or update a user based on Google OAuth data.
    Returns the user record if successful, None otherwise.
    
    Note: New users are created with status='pending' by default.
    """
    logger.info(f"DB UPSERT_USER: Starting upsert for google_id={google_id}, email={email}")
    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB UPSERT_USER: Database not available, skipping user persistence")
            return None

        # Try to find existing user by google_id
        logger.debug(f"DB UPSERT_USER: Checking if user exists with google_id={google_id}")
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, status, created_at, updated_at FROM users WHERE google_id = %s",
            (google_id,)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            # Update existing user (do not change status on re-login)
            logger.info(f"DB UPDATE users: Updating existing user id={existing_user['id']}, google_id={google_id}")
            cursor.execute(
                """
                UPDATE users
                SET email = %s, name = %s, picture_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE google_id = %s
                """,
                (email, name, picture_url, google_id)
            )
            logger.debug(f"DB UPDATE users: Rows affected={cursor.rowcount}")
            # Fetch updated record
            cursor.execute(
                "SELECT id, google_id, email, name, picture_url, status, created_at, updated_at FROM users WHERE google_id = %s",
                (google_id,)
            )
            result = cursor.fetchone()
            logger.info(f"DB UPDATE users: Successfully updated user id={result['id']}, status={result['status']}")
            return result
        else:
            # Insert new user (status defaults to 'pending' via schema)
            logger.info(f"DB INSERT users: Creating new user with google_id={google_id}, email={email}")
            cursor.execute(
                """
                INSERT INTO users (google_id, email, name, picture_url)
                VALUES (%s, %s, %s, %s)
                """,
                (google_id, email, name, picture_url)
            )
            user_id = cursor.lastrowid
            logger.info(f"DB INSERT users: New user created with id={user_id}")
            cursor.execute(
                "SELECT id, google_id, email, name, picture_url, status, created_at, updated_at FROM users WHERE id = %s",
                (user_id,)
            )
            return cursor.fetchone()


def get_user_by_email(email: str) -> Optional[dict]:
    """Get a user by email address."""
    logger.debug(f"DB SELECT users: Looking up user by email={email}")
    with get_db_cursor() as cursor:
        if cursor is None:
            return None
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, status, created_at, updated_at FROM users WHERE email = %s",
            (email,)
        )
        result = cursor.fetchone()
        logger.debug(f"DB SELECT users: Found={'yes' if result else 'no'} for email={email}")
        return result


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Get a user by ID."""
    logger.debug(f"DB SELECT users: Looking up user by id={user_id}")
    with get_db_cursor() as cursor:
        if cursor is None:
            return None
        cursor.execute(
            "SELECT id, google_id, email, name, picture_url, status, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        result = cursor.fetchone()
        logger.debug(f"DB SELECT users: Found={'yes' if result else 'no'} for id={user_id}")
        return result


def update_user_status(user_id: int, status: str) -> bool:
    """
    Update the status of a user.
    
    Args:
        user_id: ID of the user to update
        status: New status ('pending', 'approved', or 'denied')
    
    Returns:
        True if user was updated, False otherwise.
    """
    if status not in ('pending', 'approved', 'denied'):
        raise ValueError(f"Invalid status: {status}. Must be 'pending', 'approved', or 'denied'")
    
    logger.info(f"DB UPDATE_USER_STATUS: Updating status for user_id={user_id} to '{status}'")
    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB UPDATE_USER_STATUS: Database not available, skipping status update")
            return False
        
        cursor.execute(
            "UPDATE users SET status = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
            (status, user_id)
        )
        
        success = cursor.rowcount > 0
        if success:
            logger.info(f"DB UPDATE users: Successfully updated status for user_id={user_id}, rows_affected={cursor.rowcount}")
        else:
            logger.warning(f"DB UPDATE users: No user found with id={user_id}, rows_affected=0")
        return success


def create_chat(user_id: int) -> Optional[dict]:
    """
    Create a new chat for the given user.

    Args:
        user_id: ID of the user creating the chat

    Returns the created chat record if successful, None otherwise.
    """
    logger.info(f"DB CREATE_CHAT: Starting chat creation for user_id={user_id}")
    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB CREATE_CHAT: Database not available, skipping chat creation")
            return None

        # Generate UUID for chat id
        chat_id = str(uuid.uuid4())
        logger.debug(f"DB CREATE_CHAT: Generated chat_id={chat_id}")

        # Insert new chat with default title and type
        logger.info(f"DB INSERT chats: Creating chat id={chat_id} for user_id={user_id}")
        cursor.execute(
            "INSERT INTO chats (id, user_id, title, type) VALUES (%s, %s, %s, %s)",
            (chat_id, user_id, "New Conversation", "council")
        )
        logger.debug(f"DB INSERT chats: Rows affected={cursor.rowcount}")

        # Fetch created record
        cursor.execute(
            "SELECT id, user_id, title, type, created_at FROM chats WHERE id = %s",
            (chat_id,)
        )
        result = cursor.fetchone()
        logger.info(f"DB INSERT chats: Successfully created chat id={chat_id}")
        return result


def get_chats_by_user_id(user_id: int) -> List[dict]:
    """
    Get all chats for the given user with message counts.
    Returns a list of chat records, empty list if none found or database unavailable.
    """
    logger.debug(f"DB SELECT chats: Fetching all chats for user_id={user_id}")
    with get_db_cursor() as cursor:
        if cursor is None:
            return []

        # Get chats with message counts via LEFT JOIN
        cursor.execute(
            """
            SELECT c.id, c.user_id, c.title, c.type, c.created_at,
                   COUNT(m.id) as message_count
            FROM chats c
            LEFT JOIN messages m ON c.id = m.chat_id
            WHERE c.user_id = %s
            GROUP BY c.id, c.user_id, c.title, c.type, c.created_at
            ORDER BY c.created_at DESC
            """,
            (user_id,)
        )
        result = cursor.fetchall()
        logger.debug(f"DB SELECT chats: Found {len(result) if result else 0} chats for user_id={user_id}")
        return result if result else []


def get_chat_by_id(chat_id: str) -> Optional[dict]:
    """
    Get a single chat by ID.
    Returns the chat record if found, None otherwise.
    """
    logger.debug(f"DB SELECT chats: Looking up chat by id={chat_id}")
    with get_db_cursor() as cursor:
        if cursor is None:
            return None

        cursor.execute(
            "SELECT id, user_id, title, type, created_at FROM chats WHERE id = %s",
            (chat_id,)
        )
        result = cursor.fetchone()
        logger.debug(f"DB SELECT chats: Found={'yes' if result else 'no'} for id={chat_id}")
        return result


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
    content_preview = content[:50] + "..." if len(content) > 50 else content
    logger.info(f"DB CREATE_MESSAGE: Starting message creation for chat_id={chat_id}, role={role}")
    logger.debug(f"DB CREATE_MESSAGE: Content preview: '{content_preview}'")
    logger.debug(f"DB CREATE_MESSAGE: stage1_data={'present' if stage1_data else 'None'}, stage2_data={'present' if stage2_data else 'None'}, stage3_data={'present' if stage3_data else 'None'}")

    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB CREATE_MESSAGE: Database not available, skipping message creation")
            return None

        # Insert new message with JSON serialization for stage data
        logger.info(f"DB INSERT messages: Creating {role} message for chat_id={chat_id}")
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
        logger.info(f"DB INSERT messages: Successfully created message id={message_id} for chat_id={chat_id}")
        logger.debug(f"DB INSERT messages: Rows affected={cursor.rowcount}")

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
    logger.debug(f"DB SELECT messages: Fetching all messages for chat_id={chat_id}")
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

        logger.debug(f"DB SELECT messages: Found {len(messages) if messages else 0} messages for chat_id={chat_id}")
        return messages if messages else []


def get_message_by_id(message_id: int) -> Optional[dict]:
    """
    Get a single message by ID.

    Args:
        message_id: Integer ID of the message

    Returns the message record if found with deserialized JSON fields, None otherwise.
    """
    logger.debug(f"DB SELECT messages: Looking up message by id={message_id}")
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

        logger.debug(f"DB SELECT messages: Found={'yes' if message else 'no'} for id={message_id}")
        return message


def update_chat_title(chat_id: str, title: str) -> bool:
    """
    Update the title of a chat.

    Args:
        chat_id: UUID of the chat to update
        title: New title for the chat

    Returns True if chat was updated, False otherwise.
    """
    logger.info(f"DB UPDATE_CHAT_TITLE: Updating title for chat_id={chat_id} to '{title}'")
    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB UPDATE_CHAT_TITLE: Database not available, skipping chat title update")
            return False

        cursor.execute(
            "UPDATE chats SET title = %s WHERE id = %s",
            (title, chat_id)
        )

        # Check if any rows were affected
        success = cursor.rowcount > 0
        if success:
            logger.info(f"DB UPDATE chats: Successfully updated title for chat_id={chat_id}, rows_affected={cursor.rowcount}")
        else:
            logger.warning(f"DB UPDATE chats: No chat found with id={chat_id}, rows_affected=0")
        return success


def delete_chat(chat_id: str) -> bool:
    """
    Delete a chat by ID.
    Messages are automatically cascade-deleted via foreign key constraint.

    Args:
        chat_id: UUID of the chat to delete

    Returns True if chat was deleted, False otherwise.
    """
    logger.info(f"DB DELETE_CHAT: Starting deletion for chat_id={chat_id}")
    with get_db_cursor() as cursor:
        if cursor is None:
            logger.warning("DB DELETE_CHAT: Database not available, skipping chat deletion")
            return False

        cursor.execute(
            "DELETE FROM chats WHERE id = %s",
            (chat_id,)
        )

        # Check if any rows were affected
        success = cursor.rowcount > 0
        if success:
            logger.info(f"DB DELETE chats: Successfully deleted chat_id={chat_id} (messages cascade-deleted), rows_affected={cursor.rowcount}")
        else:
            logger.warning(f"DB DELETE chats: No chat found with id={chat_id}, rows_affected=0")
        return success
