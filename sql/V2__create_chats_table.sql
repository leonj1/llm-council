-- Flyway migration V2: Create chats table for user chat persistence
-- This table stores chat sessions associated with authenticated users

CREATE TABLE IF NOT EXISTS chats (
    id VARCHAR(36) PRIMARY KEY COMMENT 'UUID for chat session',
    user_id INT NOT NULL COMMENT 'Foreign key to users table',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Chat creation time',
    INDEX idx_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
