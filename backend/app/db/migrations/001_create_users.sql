-- db/migrations/001_create_users.sql
-- Role: Raw SQL migration to create the users table.
-- Run manually or via init_db() in db/base.py on first startup.

CREATE TABLE IF NOT EXISTS users (
  id         TEXT PRIMARY KEY,           -- UUID, generated in Python
  email      TEXT NOT NULL UNIQUE,
  password   TEXT NOT NULL,              -- bcrypt hash, NEVER plaintext
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
