-- Flyway migration V6: Add role column to users table for access control
-- Role determines what actions a user can perform in the application

ALTER TABLE users 
ADD COLUMN role ENUM('user', 'moderator', 'admin', 'superadmin') DEFAULT 'user'
COMMENT 'User role determining access level';

CREATE INDEX idx_users_role ON users(role);
