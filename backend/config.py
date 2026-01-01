"""Configuration for the LLM Council."""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
REQUESTY_API_KEY = os.getenv("REQUESTY_API_KEY")

# API Endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
REQUESTY_API_URL = "https://router.requesty.ai/v1/chat/completions"

# Chairman model - synthesizes final response
CHAIRMAN_MODEL = "google/gemini-3-pro-preview"

# LLM Council Models - each model has a primary and backup provider configuration
LLM_COUNCIL_MODELS = [
    {
        "primary": {
            "provider": "openrouter",
            "model": "openai/gpt-5.1"
        },
        "backup": {
            "provider": "requestyai",
            "model": "openai/gpt-5"
        }
    },
    {
        "primary": {
            "provider": "openrouter",
            "model": "google/gemini-3-pro-preview"
        },
        "backup": {
            "provider": "requestyai",
            "model": "google/gemini-3-pro-preview"
        }
    },
    {
        "primary": {
            "provider": "openrouter",
            "model": "anthropic/claude-opus-4.5"
        },
        "backup": {
            "provider": "requestyai",
            "model": "anthropic/claude-opus-4-5"
        }
    },
    {
        "primary": {
            "provider": "openrouter",
            "model": "x-ai/grok-4"
        },
        "backup": {
            "provider": "requestyai",
            "model": "xai/grok-4-1-fast-non-reasoning"
        }
    }
]

# Data directory for conversation storage
DATA_DIR = "data/conversations"

# Movie Script Configuration
MOVIE_SCRIPT_DEFAULT_TURNS = 3
MOVIE_SCRIPT_MAX_TURNS = 7


# Helper functions to work with the model configuration

def get_primary_models() -> List[str]:
    """Get list of primary model identifiers (for backward compatibility)."""
    return [m["primary"]["model"] for m in LLM_COUNCIL_MODELS]


def get_model_config(primary_model: str) -> Optional[Dict[str, Any]]:
    """Get the full configuration for a model by its primary model identifier."""
    for config in LLM_COUNCIL_MODELS:
        if config["primary"]["model"] == primary_model:
            return config
    return None


def get_backup_model(primary_model: str) -> Optional[Dict[str, str]]:
    """Get the backup provider and model for a given primary model."""
    config = get_model_config(primary_model)
    if config:
        return config.get("backup")
    return None
