-- Flyway migration V4: Add title and type columns to chats table
-- These fields support conversation metadata for list views

ALTER TABLE chats
ADD COLUMN title VARCHAR(255) DEFAULT 'New Conversation' COMMENT 'Chat session title',
ADD COLUMN type VARCHAR(50) DEFAULT 'council' COMMENT 'Chat type: council or movie_script';
