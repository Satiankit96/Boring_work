-- Database Migration: Create Users Table
-- =======================================
-- Migration 001: Initial users table for authentication module.
-- Uses TEXT for all fields (SQLite compatible).
-- UUID generated in Python, not by the database.

CREATE TABLE IF NOT EXISTS users (
    id         TEXT PRIMARY KEY,           -- UUID, generated in Python
    email      TEXT NOT NULL UNIQUE,       -- User's email address
    password   TEXT NOT NULL,              -- bcrypt hash, NEVER plaintext
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Index for fast email lookups during login
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
