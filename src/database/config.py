"""
Модуль конфигурации проекта VK бота знакомств.
"""

import os
import logging
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class DatabaseConfig:
    HOST: str = os.getenv('DB_HOST', 'localhost')
    PORT: int = int(os.getenv('DB_PORT', '5432'))
    NAME: str = os.getenv('DB_NAME', 'bot_db')
    USER: str = os.getenv('DB_USER', 'postgres')
    PASSWORD: str = os.getenv('DB_PASSWORD', '')
    
    @classmethod
    def get_connection_params(cls) -> dict:
        return {
            'host': cls.HOST,
            'port': cls.PORT,
            'database': cls.NAME,
            'user': cls.USER,
            'password': cls.PASSWORD
        }
    
    def get_dsn(self) -> str:
        return f"postgresql://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"


@dataclass
class VKConfig:
    TOKEN: str = os.getenv('VK_TOKEN', '') or os.getenv('VK_GROUP_TOKEN', '')
    GROUP_ID: int = int(os.getenv('VK_GROUP_ID', '0') or '0')
    API_VERSION: str = os.getenv('VK_API_VERSION', '5.199')
    
    def __post_init__(self):
        # Не вызываем ошибку при инициализации модуля, чтобы разрешить импорт без .env
        # Валидация будет выполнена при создании экземпляра бота
        pass
    
    def is_valid(self) -> bool:
        return bool(self.TOKEN and self.GROUP_ID > 0)
    
    def validate(self):
        """Явная валидация конфигурации."""
        if not self.TOKEN:
            raise ValueError(
                "VK_TOKEN не установлен в .env файле. "
                "Используйте переменные VK_TOKEN или VK_GROUP_TOKEN."
            )
        if self.GROUP_ID <= 0:
            raise ValueError(
                "VK_GROUP_ID должен быть положительным числом. "
                "ID группы можно найти в настройках сообщества VK."
            )


@dataclass
class LoggingConfig:
    LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    FILE_PATH: str = os.getenv('LOG_FILE_PATH', 'logs/bot.log')
    FORMAT: str = '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'
    
    def get_level(self) -> int:
        return getattr(logging, self.LEVEL.upper(), logging.INFO)
    
    def ensure_log_directory(self):
        log_dir = os.path.dirname(self.FILE_PATH)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)


db_config = DatabaseConfig()
vk_config = VKConfig()
logging_config = LoggingConfig()
