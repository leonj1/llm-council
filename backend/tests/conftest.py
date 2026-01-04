"""
Pytest configuration and fixtures for LLM Council tests.
"""

import pytest


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (require running server and API keys)"
    )
    config.addinivalue_line(
        "markers",
        "unit: marks tests as unit tests (fast, no external dependencies)"
    )


@pytest.fixture
def base_url():
    """Base URL for the backend API."""
    return "http://localhost:8004"


@pytest.fixture
def movie_script_prompt():
    """Default movie script prompt for testing."""
    return "Create a movie script that combines John Wick and Terminator."


@pytest.fixture
def movie_length():
    """Default movie length for testing."""
    return 90


@pytest.fixture
def num_turns():
    """Default number of dialogue turns for testing."""
    return 3
