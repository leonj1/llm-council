"""JSON-based storage for conversations with per-user isolation."""

import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .config import DATA_DIR


def validate_user_id(user_id: str) -> bool:
    """
    Validate user_id format matches Google OAuth 'sub' claim requirements.

    Google's 'sub' claim is a numeric string up to 255 characters.
    We allow alphanumeric plus common safe characters as defense-in-depth.
    """
    if not user_id or len(user_id) > 255:
        return False
    return all(c.isalnum() or c in '-_.' for c in user_id)


def get_user_dir(user_id: str) -> str:
    """Get the directory for a user's conversations."""
    if not validate_user_id(user_id):
        raise ValueError(f"Invalid user_id format")
    return os.path.join(DATA_DIR, user_id)


def ensure_user_dir(user_id: str):
    """Ensure the user's data directory exists."""
    Path(get_user_dir(user_id)).mkdir(parents=True, exist_ok=True)


def get_conversation_path(conversation_id: str, user_id: str) -> str:
    """Get the file path for a conversation."""
    return os.path.join(get_user_dir(user_id), f"{conversation_id}.json")


def create_conversation(conversation_id: str, user_id: str) -> Dict[str, Any]:
    """
    Create a new conversation for a user.

    Args:
        conversation_id: Unique identifier for the conversation
        user_id: User's Google 'sub' identifier

    Returns:
        New conversation dict
    """
    ensure_user_dir(user_id)

    conversation = {
        "id": conversation_id,
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "title": "New Conversation",
        "messages": []
    }

    # Save to file
    path = get_conversation_path(conversation_id, user_id)
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)

    return conversation


def get_conversation(conversation_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a conversation from storage (only if owned by user).

    Args:
        conversation_id: Unique identifier for the conversation
        user_id: User's Google 'sub' identifier

    Returns:
        Conversation dict or None if not found or not owned by user
    """
    path = get_conversation_path(conversation_id, user_id)

    if not os.path.exists(path):
        return None

    with open(path, 'r') as f:
        data = json.load(f)

    # Extra safety: verify user_id matches
    if data.get("user_id") != user_id:
        return None

    return data


def save_conversation(conversation: Dict[str, Any], user_id: str):
    """
    Save a conversation to storage.

    Args:
        conversation: Conversation dict to save
        user_id: User's Google 'sub' identifier
    """
    # Validate ownership before saving
    if conversation.get('user_id') != user_id:
        raise ValueError("Cannot save conversation owned by different user")

    ensure_user_dir(user_id)

    path = get_conversation_path(conversation['id'], user_id)
    with open(path, 'w') as f:
        json.dump(conversation, f, indent=2)


def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    """
    List all conversations for a user (metadata only).

    Args:
        user_id: User's Google 'sub' identifier

    Returns:
        List of conversation metadata dicts
    """
    user_dir = get_user_dir(user_id)

    if not os.path.exists(user_dir):
        return []

    conversations = []
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            path = os.path.join(user_dir, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                # Return metadata only
                conversations.append({
                    "id": data["id"],
                    "created_at": data["created_at"],
                    "title": data.get("title", "New Conversation"),
                    "message_count": len(data["messages"])
                })

    # Sort by creation time, newest first
    conversations.sort(key=lambda x: x["created_at"], reverse=True)

    return conversations


def add_user_message(conversation_id: str, content: str, user_id: str):
    """
    Add a user message to a conversation.

    Args:
        conversation_id: Conversation identifier
        content: User message content
        user_id: User's Google 'sub' identifier
    """
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "user",
        "content": content
    })

    save_conversation(conversation, user_id)


def add_assistant_message(
    conversation_id: str,
    stage1: List[Dict[str, Any]],
    stage2: List[Dict[str, Any]],
    stage3: Dict[str, Any],
    user_id: str
):
    """
    Add an assistant message with all 3 stages to a conversation.

    Args:
        conversation_id: Conversation identifier
        stage1: List of individual model responses
        stage2: List of model rankings
        stage3: Final synthesized response
        user_id: User's Google 'sub' identifier
    """
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["messages"].append({
        "role": "assistant",
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    })

    save_conversation(conversation, user_id)


def update_conversation_title(conversation_id: str, title: str, user_id: str):
    """
    Update the title of a conversation.

    Args:
        conversation_id: Conversation identifier
        title: New title for the conversation
        user_id: User's Google 'sub' identifier
    """
    conversation = get_conversation(conversation_id, user_id)
    if conversation is None:
        raise ValueError(f"Conversation {conversation_id} not found")

    conversation["title"] = title
    save_conversation(conversation, user_id)
