<<<<<<< HEAD
def create_tables(self):
    """Создать таблицы из schema.sql"""
    try:
        with open('data/schema.sql', 'r', encoding='utf-8') as f:
            sql = f.read()
            self.cursor.execute(sql)
            self.connection.commit()
            print("✅ Таблицы созданы/проверены")
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        self.connection.rollback()
=======
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
>>>>>>> bfeabe0afb8fd4773c66918dba74d35e9443f319
