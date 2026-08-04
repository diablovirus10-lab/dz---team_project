"""Database manager implementation."""

class Database:
    def __init__(self, config):
        self.config = config
        self.connection = None

    def connect(self):
        """Connect to the database."""
        raise NotImplementedError("Database.connect must be implemented")

    def close(self):
        """Close the database connection."""
        raise NotImplementedError("Database.close must be implemented")

    def execute(self, query, params=None):
        """Execute a database query."""
        raise NotImplementedError("Database.execute must be implemented")
