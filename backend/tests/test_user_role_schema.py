"""
BDD Tests for User Role Schema
Tests for V6 migration that adds role column to users table.

Feature: User Role Management
  As an administrator
  I want users to have a role field (user, moderator, admin, superadmin)
  So that I can control access levels within the application
"""

import pytest
from backend.database import (
    upsert_user,
    get_user_by_email,
    get_user_by_id,
    update_user_role,
    get_connection,
)


@pytest.fixture
def create_test_user():
    """Helper fixture to create a test user."""
    def _create(email_prefix: str = "test"):
        return upsert_user(
            google_id=f"google_{email_prefix}_role_123",
            email=f"{email_prefix}_role@example.com",
            name=email_prefix.title(),
            picture_url=None
        )
    return _create


class TestRoleColumnExists:
    """Tests that verify the role column exists in the schema."""

    @pytest.mark.unit
    def test_role_column_exists_in_users_table(self):
        """
        Scenario: Role column exists in users table
        Given the V6 migration has been applied
        When I inspect the users table schema
        Then the role column exists
        And it is an ENUM type with values 'user', 'moderator', 'admin', 'superadmin'
        """
        connection = get_connection()
        assert connection is not None, "Database connection required"
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("DESCRIBE users role")
            column_info = cursor.fetchone()
            
            assert column_info is not None, "Role column should exist"
            assert column_info['Field'] == 'role'
            assert "enum('user','moderator','admin','superadmin')" in column_info['Type'].lower()
            assert column_info['Default'] == 'user'
            cursor.close()
        finally:
            connection.close()

    @pytest.mark.unit
    def test_role_index_exists(self):
        """
        Scenario: Index exists on role column
        Given the V6 migration has been applied
        When I inspect the users table indexes
        Then an index on the role column exists
        """
        connection = get_connection()
        assert connection is not None, "Database connection required"
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SHOW INDEX FROM users WHERE Key_name = 'idx_users_role'")
            index_info = cursor.fetchone()
            
            assert index_info is not None, "Role index should exist"
            assert index_info['Column_name'] == 'role'
            cursor.close()
        finally:
            connection.close()


class TestRoleDefaultValue:
    """Tests that verify new users get 'user' role by default."""

    @pytest.mark.unit
    def test_new_user_has_user_role(self, create_test_user):
        """
        Scenario: New user has 'user' role by default
        Given no user exists with email "newroleuser@example.com"
        When I create a new user via OAuth login
        Then the user's role should be 'user'
        """
        user = create_test_user("newroleuser")
        
        assert user is not None, "User should be created"
        assert 'role' in user, "User dict should include role field"
        assert user['role'] == 'user', f"New user role should be 'user', got '{user['role']}'"

    @pytest.mark.unit
    def test_user_role_persists_through_fetch_by_email(self, create_test_user):
        """
        Scenario: User role is returned when fetching by email
        Given a user "fetchroletest@example.com" exists
        When I fetch the user by email
        Then the response includes the role field
        """
        created_user = create_test_user("fetchroletest")
        assert created_user is not None
        
        fetched_user = get_user_by_email("fetchroletest_role@example.com")
        
        assert fetched_user is not None, "User should be fetchable by email"
        assert 'role' in fetched_user, "Fetched user should include role"
        assert fetched_user['role'] == 'user'

    @pytest.mark.unit
    def test_user_role_persists_through_fetch_by_id(self, create_test_user):
        """
        Scenario: User role is returned when fetching by ID
        Given a user exists
        When I fetch the user by ID
        Then the response includes the role field
        """
        created_user = create_test_user("idroletest")
        assert created_user is not None
        
        fetched_user = get_user_by_id(created_user['id'])
        
        assert fetched_user is not None, "User should be fetchable by ID"
        assert 'role' in fetched_user, "Fetched user should include role"
        assert fetched_user['role'] == 'user'


class TestRoleUpdates:
    """Tests that verify role can be updated."""

    @pytest.mark.unit
    def test_update_user_role_to_moderator(self, create_test_user):
        """
        Scenario: Admin promotes a user to moderator
        Given a user exists with role 'user'
        When I update the user's role to 'moderator'
        Then the user's role should be 'moderator'
        """
        user = create_test_user("modtest")
        assert user is not None
        assert user['role'] == 'user'
        
        success = update_user_role(user['id'], 'moderator')
        assert success is True, "Role update should succeed"
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['role'] == 'moderator'

    @pytest.mark.unit
    def test_update_user_role_to_admin(self, create_test_user):
        """
        Scenario: Superadmin promotes a user to admin
        Given a user exists with role 'user'
        When I update the user's role to 'admin'
        Then the user's role should be 'admin'
        """
        user = create_test_user("admintest")
        assert user is not None
        
        success = update_user_role(user['id'], 'admin')
        assert success is True
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['role'] == 'admin'

    @pytest.mark.unit
    def test_update_user_role_to_superadmin(self, create_test_user):
        """
        Scenario: Superadmin promotes a user to superadmin
        Given a user exists with role 'user'
        When I update the user's role to 'superadmin'
        Then the user's role should be 'superadmin'
        """
        user = create_test_user("superadmintest")
        assert user is not None
        
        success = update_user_role(user['id'], 'superadmin')
        assert success is True
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['role'] == 'superadmin'

    @pytest.mark.unit
    def test_demote_user_back_to_user(self, create_test_user):
        """
        Scenario: Admin demotes a moderator back to user
        Given a user exists with role 'moderator'
        When I update the user's role to 'user'
        Then the user's role should be 'user'
        """
        user = create_test_user("demotetest")
        update_user_role(user['id'], 'moderator')
        
        success = update_user_role(user['id'], 'user')
        assert success is True
        
        updated_user = get_user_by_id(user['id'])
        assert updated_user['role'] == 'user'

    @pytest.mark.unit
    def test_update_role_invalid_value_raises(self, create_test_user):
        """
        Scenario: Updating role with invalid value fails
        Given a user exists
        When I try to update role to an invalid value
        Then a ValueError should be raised
        """
        user = create_test_user("invalidroletest")
        
        with pytest.raises(ValueError) as exc_info:
            update_user_role(user['id'], 'invalid_role')
        
        assert "Invalid role" in str(exc_info.value)

    @pytest.mark.unit
    def test_update_role_nonexistent_user(self):
        """
        Scenario: Updating role of non-existent user returns False
        Given no user with ID 99999 exists
        When I try to update that user's role
        Then the function should return False
        """
        success = update_user_role(99999, 'admin')
        assert success is False


class TestRolePreservedOnRelogin:
    """Tests that verify role is preserved when user logs in again."""

    @pytest.mark.unit
    def test_role_preserved_on_upsert(self, create_test_user):
        """
        Scenario: User role is preserved when they log in again
        Given a user exists with role 'admin'
        When the user logs in again (upsert is called)
        Then the user's role should still be 'admin'
        """
        # Create user and promote to admin
        user = create_test_user("preserveroletest")
        update_user_role(user['id'], 'admin')
        
        # Simulate re-login (upsert with same google_id)
        relogged_user = upsert_user(
            google_id="google_preserveroletest_role_123",
            email="preserveroletest_role@example.com",
            name="Preserve Role Test Updated",
            picture_url="https://example.com/new-picture.jpg"
        )
        
        assert relogged_user is not None
        assert relogged_user['role'] == 'admin', "Role should be preserved on re-login"
        # Verify other fields were updated
        assert relogged_user['name'] == "Preserve Role Test Updated"

    @pytest.mark.unit
    def test_superadmin_role_preserved_on_upsert(self, create_test_user):
        """
        Scenario: Superadmin role is preserved when user logs in again
        Given a user exists with role 'superadmin'
        When the user logs in again
        Then the user's role should still be 'superadmin'
        """
        user = create_test_user("superadminpreserve")
        update_user_role(user['id'], 'superadmin')
        
        # Simulate re-login
        relogged_user = upsert_user(
            google_id="google_superadminpreserve_role_123",
            email="superadminpreserve_role@example.com",
            name="Superadmin User",
            picture_url=None
        )
        
        assert relogged_user is not None
        assert relogged_user['role'] == 'superadmin', "Superadmin role should persist"

    @pytest.mark.unit
    def test_moderator_role_preserved_on_upsert(self, create_test_user):
        """
        Scenario: Moderator role is preserved when user logs in again
        Given a user exists with role 'moderator'
        When the user logs in again
        Then the user's role should still be 'moderator'
        """
        user = create_test_user("modpreserve")
        update_user_role(user['id'], 'moderator')
        
        # Simulate re-login
        relogged_user = upsert_user(
            google_id="google_modpreserve_role_123",
            email="modpreserve_role@example.com",
            name="Moderator User",
            picture_url=None
        )
        
        assert relogged_user is not None
        assert relogged_user['role'] == 'moderator', "Moderator role should persist"


class TestRoleAndStatusIndependent:
    """Tests that verify role and status are independent fields."""

    @pytest.mark.unit
    def test_role_and_status_can_be_set_independently(self, create_test_user):
        """
        Scenario: Role and status can be set independently
        Given a user exists
        When I update both role and status
        Then each field should reflect its own value
        """
        from backend.database import update_user_status
        
        user = create_test_user("independenttest")
        
        # Update role to admin
        update_user_role(user['id'], 'admin')
        # Update status to approved
        update_user_status(user['id'], 'approved')
        
        updated_user = get_user_by_id(user['id'])
        
        assert updated_user['role'] == 'admin'
        assert updated_user['status'] == 'approved'

    @pytest.mark.unit
    def test_changing_role_does_not_affect_status(self, create_test_user):
        """
        Scenario: Changing role does not affect status
        Given a user exists with status 'approved'
        When I change the user's role
        Then the status should remain unchanged
        """
        from backend.database import update_user_status
        
        user = create_test_user("rolenotstatustest")
        update_user_status(user['id'], 'approved')
        
        # Change role
        update_user_role(user['id'], 'moderator')
        
        updated_user = get_user_by_id(user['id'])
        
        assert updated_user['role'] == 'moderator'
        assert updated_user['status'] == 'approved', "Status should not change when role changes"

    @pytest.mark.unit
    def test_changing_status_does_not_affect_role(self, create_test_user):
        """
        Scenario: Changing status does not affect role
        Given a user exists with role 'admin'
        When I change the user's status
        Then the role should remain unchanged
        """
        from backend.database import update_user_status
        
        user = create_test_user("statusnotroletest")
        update_user_role(user['id'], 'admin')
        
        # Change status
        update_user_status(user['id'], 'denied')
        
        updated_user = get_user_by_id(user['id'])
        
        assert updated_user['status'] == 'denied'
        assert updated_user['role'] == 'admin', "Role should not change when status changes"
