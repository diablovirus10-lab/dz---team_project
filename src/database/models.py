"""Database models and SQL definitions."""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    vk_id TEXT NOT NULL UNIQUE,
    first_name TEXT,
    last_name TEXT,
    gender TEXT,
    age INTEGER,
    created_at TEXT
);
"""


def create_tables(connection):
    """Create required tables in the database."""
    cursor = connection.cursor()
    cursor.execute(SCHEMA_SQL)
    connection.commit()
