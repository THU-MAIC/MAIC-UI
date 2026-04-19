-- PostgreSQL Database Initialization Script for Learn Your Way
-- This script runs automatically when the database container starts for the first time

-- Create database if it doesn't exist (already created by POSTGRES_DB environment variable)
-- CREATE DATABASE IF NOT EXISTS lear_your_way;

-- Set database encoding
SET client_encoding = 'UTF8';

-- Create extensions if needed
-- CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- You can add initial data or custom schema modifications here
-- Example:
-- INSERT INTO users (id, email, hashed_password, grade_level, created_at)
-- VALUES ('00000000-0000-0000-0000-000000000001', 'admin@example.com', '$2b$12$...', '10', NOW())
-- ON CONFLICT (id) DO NOTHING;

-- Comment out any user-specific initial data for security reasons
-- The application schema will be created by SQLAlchemy automatically