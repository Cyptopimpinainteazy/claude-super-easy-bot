-- PostgreSQL initialization script for Arbitrage Bot database
-- Runs automatically on first container startup

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create enum types
CREATE TYPE execution_status AS ENUM ('pending', 'success', 'failed', 'reverted');
CREATE TYPE risk_level AS ENUM ('low', 'medium', 'high');
CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'error', 'critical');

-- Grant privileges to arbitrage_user
GRANT ALL PRIVILEGES ON DATABASE arbitrage_bot TO arbitrage_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO arbitrage_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO arbitrage_user;

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create basic indices (advanced indices will be added by Alembic migrations)
-- This ensures the database is ready for schema creation via Alembic
