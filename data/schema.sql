-- SQL schema for chatbot database
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vk_id TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    age INTEGER,
    created_at TEXT
);
