"""
Pytest configuration and fixtures for LLM Council tests.
"""

import pytest
from mysql.connector import Error
from ..database import get_connection


@pytest.fixture(autouse=True)
def cleanup_database(request):
    """Clean up database tables before each test for isolation.

    Skips cleanup if the test uses mocking (doesn't need real database).
    """
    # Check if test file uses mocking - skip database cleanup for mocked tests
    if hasattr(request, 'node') and request.node.get_closest_marker('usefixtures'):
        # Skip for fixture-only tests
        yield
        return

    connection = get_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # Disable foreign key checks to allow truncation
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
            cursor.execute("TRUNCATE TABLE messages")
            cursor.execute("TRUNCATE TABLE chats")
            cursor.execute("TRUNCATE TABLE users")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
            connection.commit()
            cursor.close()
        except Error as e:
            print(f"Warning: Could not clean up database: {e}")
            connection.rollback()
        finally:
            connection.close()
    else:
        # For tests that mock storage/database, allow running without database
        # Only fail if environment explicitly requires database
        import os
        if os.getenv("REQUIRE_DATABASE", "false").lower() == "true":
            pytest.fail("Database connection unavailable - cannot ensure test isolation")
        else:
            print("Warning: Database unavailable - skipping cleanup (tests will use mocks)")
    yield


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
