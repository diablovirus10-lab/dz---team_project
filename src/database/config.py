import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseConfig:

    HOST = os.getenv('DB_HOST', 'localhost')
    PORT = os.getenv('DB_PORT', '5432')
    NAME = os.getenv('DB_NAME', 'bot_db')
    USER = os.getenv('DB_USER', 'postgres')
    PASSWORD = os.getenv('DB_PASSWORD', '')

    @classmethod
    def get_connection_params(cls) -> dict:
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.NAME,
            'user': cls.USER,
            'password': cls.PASSWORD
        }
