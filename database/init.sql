-- Database initialization script for NoPhish Professional
-- This script creates the database schema and initial data

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create user_roles table
CREATE TABLE IF NOT EXISTS user_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    permissions JSONB
);

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role_id INTEGER REFERENCES user_roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    telegram_chat_id VARCHAR(50)
);

-- Create campaigns table
CREATE TABLE IF NOT EXISTS campaigns (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    domain VARCHAR(200) NOT NULL,
    target_url VARCHAR(500) NOT NULL,
    num_users INTEGER DEFAULT 1,
    browser_type VARCHAR(20) DEFAULT 'firefox',
    ssl_enabled BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'created',
    admin_password VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create campaign_sessions table
CREATE TABLE IF NOT EXISTS campaign_sessions (
    id SERIAL PRIMARY KEY,
    campaign_id INTEGER REFERENCES campaigns(id),
    user_num INTEGER NOT NULL,
    container_name VARCHAR(100) NOT NULL,
    container_type VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP,
    browser VARCHAR(20)  -- For browser-specific logging
);

-- Create session_logs table
CREATE TABLE IF NOT EXISTS session_logs (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES campaign_sessions(id),
    log_type VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    type VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    telegram_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_campaigns_created_by ON campaigns(created_by);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns(status);
CREATE INDEX IF NOT EXISTS idx_sessions_campaign_id ON campaign_sessions(campaign_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON campaign_sessions(status);
CREATE INDEX IF NOT EXISTS idx_logs_session_id ON session_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_logs_type ON session_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);

-- Create default roles
INSERT INTO user_roles (name, description, permissions) VALUES
('admin', 'Full system access', '{
    "users": ["create", "read", "update", "delete"],
    "campaigns": ["create", "read", "update", "delete"],
    "monitoring": ["read", "write"],
    "system": ["read", "write"]
}'),
('user', 'Standard user access', '{
    "users": ["read"],
    "campaigns": ["create", "read", "update", "delete"],
    "monitoring": ["read"],
    "system": ["read"]
}'),
('viewer', 'Read-only access', '{
    "users": ["read"],
    "campaigns": ["read"],
    "monitoring": ["read"],
    "system": ["read"]
}')
ON CONFLICT (name) DO NOTHING;

-- Create default admin user (password will be set via environment variable)
INSERT INTO users (username, email, password_hash, role_id, full_name, is_active)
VALUES ('admin', 'admin@nophish.local', '$2b$12$placeholder_hash', 1, 'System Administrator', TRUE)
ON CONFLICT (username) DO NOTHING;

-- Create update trigger for campaigns table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nophish_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nophish_user;