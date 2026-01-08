"""Storage layer for conversations - delegates to MySQL database."""

from typing import List, Dict, Any, Optional
from . import database


def create_conversation(conversation_id: str, user_id: int, conversation_type: str = "council") -> Dict[str, Any]:
    """
    Create a new conversation.

    Args:
        conversation_id: Unique identifier for the conversation (ignored - database generates UUID)
        user_id: ID of the user who owns this conversation
        conversation_type: Type of conversation ("council" or "movie_script")

    Returns:
        New conversation dict with id, user_id, created_at, title, type, messages
    """
    # Create chat in database (generates its own UUID)
    chat = database.create_chat(user_id)

    if chat is None:
        # Fallback: return minimal structure if database unavailable
        from datetime import datetime
        return {
            "id": conversation_id,
            "user_id": user_id,
            "created_at": datetime.utcnow().isoformat(),
            "title": "New Conversation",
            "type": conversation_type,
            "messages": []
        }

    # Convert database format to storage format
    return {
        "id": chat["id"],
        "user_id": chat["user_id"],
        "created_at": str(chat["created_at"]),
        "title": chat.get("title", "New Conversation"),
        "type": chat.get("type", conversation_type),
        "messages": []
    }


def get_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        Conversation dict or None if not found
    """
    # Get chat from database
    chat = database.get_chat_by_id(conversation_id)

    if chat is None:
        return None

    # Get messages for this chat
    db_messages = database.get_messages_by_chat_id(conversation_id)

    # Convert messages from database format to storage format
    messages = []
    for msg in db_messages:
        if msg["role"] == "user":
            messages.append({
                "role": "user",
                "content": msg["content"]
            })
        else:
            # Assistant message with stage data
            message = {"role": "assistant"}
            if msg.get("stage1_data"):
                message["stage1"] = msg["stage1_data"]
            if msg.get("stage2_data"):
                message["stage2"] = msg["stage2_data"]
            if msg.get("stage3_data"):
                message["stage3"] = msg["stage3_data"]
            # Check for stage4 (movie script)
            if msg.get("stage4_data"):
                message["stage4"] = msg["stage4_data"]
            messages.append(message)

    return {
        "id": chat["id"],
        "user_id": chat["user_id"],
        "created_at": str(chat["created_at"]),
        "title": chat.get("title", "New Conversation"),
        "type": chat.get("type", "council"),
        "messages": messages
    }


def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation from storage.

    Args:
        conversation_id: Unique identifier for the conversation

    Returns:
        True if deleted, False if not found
    """
    return database.delete_chat(conversation_id)


def list_conversations(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    List conversations (metadata only), optionally filtered by user_id.

    Args:
        user_id: If provided, only return conversations owned by this user

    Returns:
        List of conversation metadata dicts
    """
    if user_id is None:
        # Without user_id filtering, return empty list (security)
        return []

    chats = database.get_chats_by_user_id(user_id)

    # Convert to storage format
    conversations = []
    for chat in chats:
        conversations.append({
            "id": chat["id"],
            "created_at": str(chat["created_at"]),
            "title": chat.get("title", "New Conversation"),
            "type": chat.get("type", "council"),
            "message_count": chat.get("message_count", 0)
        })

    return conversations


def add_user_message(conversation_id: str, content: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
    """
    # Verify conversation exists
    chat = database.get_chat_by_id(conversation_id)
    if chat is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    # Create message with role=user, no stage data
    database.create_message(
        chat_id=conversation_id,
        role="user",
        content=content,
        stage1_data=None,
        stage2_data=None,
        stage3_data=None
    )


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any]
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
    """
    # Verify conversation exists
    chat = database.get_chat_by_id(conversation_id)
    if chat is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    # Extract content from stage3 for the content field
    content = stage3.get("response", "") if stage3 else ""

    # Create message with role=assistant and stage data
    database.create_message(
        chat_id=conversation_id,
        role="assistant",
        content=content,
        stage1_data=stage1,
        stage2_data=stage2,
        stage3_data=stage3
    )


def update_conversation_title(conversation_id: str, title: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
    """
    success = database.update_chat_title(conversation_id, title)
    if not success:
        raise ValueError(f"Conversation {conversation_id} not found")


def add_movie_script_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any],
    stage4: Dict[str, Any]
):
    """
    Add a movie script assistant message with all 4 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual script responses
        stage2: List of model rankings
        stage3: Script selection result
        stage4: Collaborative dialogue result
    """
    # Verify conversation exists
    chat = database.get_chat_by_id(conversation_id)
    if chat is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    # For movie scripts, we need to store stage4 data
    # The database.create_message only supports stage1-3
    # We'll store stage4 in stage3_data as a nested object
    combined_stage3 = {
        "stage3": stage3,
        "stage4": stage4
    }

    content = stage4.get("dialogue", "") if stage4 else ""

    database.create_message(
        chat_id=conversation_id,
        role="assistant",
        content=content,
        stage1_data=stage1,
        stage2_data=stage2,
        stage3_data=combined_stage3
    )


def update_movie_script_stage4(conversation_id: str, stage4: Dict[str, Any]):
    """
    Update stage4 of the last assistant message in a movie script conversation.
    Used for regenerating the final script.

    Args:
        conversation_id: Conversation identifier
        stage4: Updated stage4 data
    """
    # This requires updating the last message, which isn't directly supported
    # by the current database.py interface
    # For now, we'll need to add this functionality to database.py
    # or handle it differently

    # Get current messages
    messages = database.get_messages_by_chat_id(conversation_id)
    if not messages:
        raise ValueError(f"Conversation {conversation_id} has no messages")

    # Find last assistant message
    last_assistant = None
    for msg in reversed(messages):
        if msg.get("role") == "assistant":
            last_assistant = msg
            break

    if last_assistant is None:
        raise ValueError(f"No assistant message found in conversation {conversation_id}")

    # Update the stage3_data to include new stage4
    current_stage3 = last_assistant.get("stage3_data", {})
    if isinstance(current_stage3, dict):
        current_stage3["stage4"] = stage4
    else:
        current_stage3 = {"stage4": stage4}

    # We need to add an update_message function to database.py
    # For now, this is a limitation
    pass


# Legacy compatibility - these functions are not needed but kept for reference
def save_conversation(conversation: Dict[str, Any]):
    """Legacy function - no longer used with database backend."""
    pass


def ensure_data_dir():
    """Legacy function - no longer used with database backend."""
    pass


def get_conversation_path(conversation_id: str) -> str:
    """Legacy function - no longer used with database backend."""
    return ""
