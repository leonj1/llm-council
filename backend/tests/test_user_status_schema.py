"""
BDD Tests for User Status Schema
Tests for V5 migration that adds status column to users table.

Feature: User Authorization Status
  As an administrator
  I want users to have a status field (pending, approved, denied)
  So that I can control access to the application
"""

import pytest
from backend.database import (
    upsert_user,
    get_user_by_email,
    get_user_by_id,
    update_user_status,
    get_connection,
)


@pytest.fixture
def create_test_user():
    """Helper fixture to create a test user."""
    def _create(email_prefix: str = "test"):
        return upsert_user(
            google_id=f"google_{email_prefix}_123",
            email=f"{email_prefix}@example.com",
            name=email_prefix.title(),
            picture_url=None
        )
    return _create


class TestStatusColumnExists:
    """Tests that verify the status column exists in the schema."""

    @pytest.mark.unit
    def test_status_column_exists_in_users_table(self):
        """
        Scenario: Status column exists in users table
        Given the V5 migration has been applied
        When I inspect the users table schema
        Then the status column exists
        And it is an ENUM type with values 'pending', 'approved', 'denied'
        """
        connection = get_connection()
        assert connection is not None, "Database connection required"
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("DESCRIBE users status")
            column_info = cursor.fetchone()
            
            assert column_info is not None, "Status column should exist"
            assert column_info['Field'] == 'status'
            assert "enum('pending','approved','denied')" in column_info['Type'].lower()
            assert column_info['Default'] == 'pending'
            cursor.close()
        finally:
            connection.close()


class TestStatusDefaultValue:
    """Tests that verify new users get 'pending' status by default."""

    @pytest.mark.unit
    def test_new_user_has_pending_status(self, create_test_user):
        """
        Scenario: New user has pending status by default
        Given no user exists with email "newuser@example.com"
        When I create a new user via OAuth login
        Then the user's status should be 'pending'
        """
        user = create_test_user("newuser")
        
        assert user is not None, "User should be created"
        assert 'status' in user, "User dict should include status field"
        assert user['status'] == 'pending', f"New user status should be 'pending', got '{user['status']}'"

    @pytest.mark.unit
    def test_user_status_persists_through_fetch_by_email(self, create_test_user):
        """
        Scenario: User status is returned when fetching by email
        Given a user "fetchtest@example.com" exists
        When I fetch the user by email
        Then the response includes the status field
        """
        created_user = create_test_user("fetchtest")
        assert created_user is not None
        
        fetched_user = get_user_by_email("fetchtest@example.com")
        
        assert fetched_user is not None, "User should be fetchable by email"
        assert 'status' in fetched_user, "Fetched user should include status"
        assert fetched_user['status'] == 'pending'

    @pytest.mark.unit
    def test_user_status_persists_through_fetch_by_id(self, create_test_user):
        """
        Scenario: User status is returned when fetching by ID
        Given a user exists
        When I fetch the user by ID
        Then the response includes the status field
        """
        created_user = create_test_user("idtest")
        assert created_user is not None
        
        fetched_user = get_user_by_id(created_user['id'])
        
        assert fetched_user is not None, "User should be fetchable by ID"
        assert 'status' in fetched_user, "Fetched user should include status"
        assert fetched_user['status'] == 'pending'


class TestStatusUpdates:
    """Tests that verify status can be updated."""

    @pytest.mark.unit
    def test_update_user_status_to_approved(self, create_test_user):
        """
        Scenario: Admin approves a pending user
        Given a user exists with status 'pending'
        When I update the user's status to 'approved'
        Then the user's status should be 'approved'
        """
        user = create_test_user("approvetest")
        assert user is not None
        assert user['status'] == 'pending'
        
        success = update_user_status(user['id'], 'approved')
        assert success is True, "Status update should succeed"
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['status'] == 'approved'

    @pytest.mark.unit
    def test_update_user_status_to_denied(self, create_test_user):
        """
        Scenario: Admin denies a pending user
        Given a user exists with status 'pending'
        When I update the user's status to 'denied'
        Then the user's status should be 'denied'
        """
        user = create_test_user("denytest")
        assert user is not None
        
        success = update_user_status(user['id'], 'denied')
        assert success is True
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['status'] == 'denied'

    @pytest.mark.unit
    def test_update_status_back_to_pending(self, create_test_user):
        """
        Scenario: Admin reverts an approved user back to pending
        Given a user exists with status 'approved'
        When I update the user's status to 'pending'
        Then the user's status should be 'pending'
        """
        user = create_test_user("reverttest")
        update_user_status(user['id'], 'approved')
        
        success = update_user_status(user['id'], 'pending')
        assert success is True
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['status'] == 'pending'

    @pytest.mark.unit
    def test_update_status_invalid_value_raises(self, create_test_user):
        """
        Scenario: Updating status with invalid value fails
        Given a user exists
        When I try to update status to an invalid value
        Then a ValueError should be raised
        """
        user = create_test_user("invalidtest")
        
        with pytest.raises(ValueError) as exc_info:
            update_user_status(user['id'], 'invalid_status')
        
        assert "Invalid status" in str(exc_info.value)

    @pytest.mark.unit
    def test_update_status_nonexistent_user(self):
        """
        Scenario: Updating status of non-existent user returns False
        Given no user with ID 99999 exists
        When I try to update that user's status
        Then the function should return False
        """
        success = update_user_status(99999, 'approved')
        assert success is False


class TestStatusPreservedOnRelogin:
    """Tests that verify status is preserved when user logs in again."""

    @pytest.mark.unit
    def test_status_preserved_on_upsert(self, create_test_user):
        """
        Scenario: User status is preserved when they log in again
        Given a user exists with status 'approved'
        When the user logs in again (upsert is called)
        Then the user's status should still be 'approved'
        """
        # Create user and approve them
        user = create_test_user("preservetest")
        update_user_status(user['id'], 'approved')
        
        # Simulate re-login (upsert with same google_id)
        relogged_user = upsert_user(
            google_id="google_preservetest_123",
            email="preservetest@example.com",
            name="Preserve Test Updated",
            picture_url="https://example.com/new-picture.jpg"
        )
        
        assert relogged_user is not None
        assert relogged_user['status'] == 'approved', "Status should be preserved on re-login"
        # Verify other fields were updated
        assert relogged_user['name'] == "Preserve Test Updated"

    @pytest.mark.unit
    def test_denied_status_preserved_on_upsert(self, create_test_user):
        """
        Scenario: Denied status is preserved when user tries to log in again
        Given a user exists with status 'denied'
        When the user attempts to log in again
        Then the user's status should still be 'denied'
        """
        user = create_test_user("deniedpreserve")
        update_user_status(user['id'], 'denied')
        
        # Simulate re-login
        relogged_user = upsert_user(
            google_id="google_deniedpreserve_123",
            email="deniedpreserve@example.com",
            name="Denied User",
            picture_url=None
        )
        
        assert relogged_user is not None
        assert relogged_user['status'] == 'denied', "Denied status should persist"
