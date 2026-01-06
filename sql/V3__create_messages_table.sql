-- Flyway migration V3: Create messages table for user message persistence
-- This table stores both user queries and assistant responses with stage data

CREATE TABLE IF NOT EXISTS messages (
    id INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Auto-increment primary key for messages',
    chat_id VARCHAR(36) NOT NULL COMMENT 'Foreign key to chats table',
    role ENUM('user', 'assistant') NOT NULL COMMENT 'Message role: user or assistant',
    content TEXT NOT NULL COMMENT 'Message content',
    stage1_data JSON DEFAULT NULL COMMENT 'Stage 1 data (model responses) for assistant messages',
    stage2_data JSON DEFAULT NULL COMMENT 'Stage 2 data (rankings) for assistant messages',
    stage3_data JSON DEFAULT NULL COMMENT 'Stage 3 data (synthesis) for assistant messages',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'Message creation time',
    INDEX idx_chat_id (chat_id),
    FOREIGN KEY (chat_id) REFERENCES chats(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
