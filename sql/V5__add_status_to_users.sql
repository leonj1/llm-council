-- Flyway migration V5: Add status column to users table for authorization
-- Status controls whether a user can access the application

ALTER TABLE users 
ADD COLUMN status ENUM('pending', 'approved', 'denied') DEFAULT 'pending'
COMMENT 'User authorization status: pending (awaiting approval), approved (can access), denied (blocked)';
