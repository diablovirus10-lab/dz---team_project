"""
Асинхронный менеджер базы данных для интеграционных тестов.
Использует asyncpg для работы с PostgreSQL.
"""
import asyncpg
from typing import Optional, List, Dict, Any
import json

from .config import DatabaseConfig
from .exceptions import DatabaseError


class DatabaseManager:
    """Асинхронный менеджер подключений к базе данных."""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Создает пул соединений с базой данных."""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                min_size=2,
                max_size=10
            )
        except asyncpg.PostgresError as e:
            raise DatabaseError(f"Ошибка подключения к БД: {e}", original_error=e) from e

    async def disconnect(self):
        """Закрывает пул соединений."""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def create_tables(self):
        """Создает все таблицы в базе данных."""
        async with self.pool.acquire() as conn:
            # Читаем SQL схему из файла
            schema_file = "data/schema.sql"
            try:
                with open(schema_file, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()

                # Выполняем схему (разделяем по точкам с запятой)
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    if not statement.startswith('--'):
                        try:
                            await conn.execute(statement)
                        except asyncpg.DuplicateTableError:
                            pass  # Таблица уже существует
            except FileNotFoundError:
                raise DatabaseError(f"Файл схемы не найден: {schema_file}")

    async def clear_all_tables(self):
        """Очищает все таблицы в правильном порядке (с учетом внешних ключей)."""
        async with self.pool.acquire() as conn:
            # Порядок важен из-за внешних ключей
            tables = [
                'api_logs', 'user_intentions', 'entities', 'intentions',
                'user_commands', 'commands', 'states', 'messages',
                'dialogs', 'users'
            ]

            for table in tables:
                try:
                    await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
                except asyncpg.UndefinedTableError:
                    pass  # Таблица не существует

    async def get_all_tables(self) -> List[str]:
        """Получает список всех таблиц в базе данных."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """
            rows = await conn.fetch(query)
            return [row['table_name'] for row in rows]

    # Методы для работы с пользователями
    async def create_user(self, vk_id: int, first_name: str, last_name: str,
                          age: Optional[int], city: str, sex: int) -> int:
        """Создает нового пользователя."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO users (vk_id, first_name, last_name, age, city, sex)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """
            row = await conn.fetchrow(query, vk_id, first_name, last_name, age, city, sex)
            return row['id']

    async def get_user_by_vk_id(self, vk_id: int) -> Optional[Dict[str, Any]]:
        """Получает пользователя по VK ID."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM users WHERE vk_id = $1"
            row = await conn.fetchrow(query, vk_id)
            return dict(row) if row else None

    async def get_or_create_user(self, vk_id: int, first_name: str, last_name: str,
                                 age: Optional[int], city: str, sex: int) -> Dict[str, Any]:
        """Получает или создает пользователя."""
        async with self.pool.acquire() as conn:
            # Сначала пробуем получить
            query = "SELECT * FROM users WHERE vk_id = $1"
            row = await conn.fetchrow(query, vk_id)
            if row:
                return dict(row)

            # Создаем нового
            query = """
                INSERT INTO users (vk_id, first_name, last_name, age, city, sex)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING *
            """
            row = await conn.fetchrow(query, vk_id, first_name, last_name, age, city, sex)
            return dict(row)

    async def get_all_users(self) -> List[Dict[str, Any]]:
        """Получает всех пользователей."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM users"
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]

    # Методы для работы с диалогами
    async def create_dialog(self, user_id: int) -> int:
        """Создает новый диалог."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO dialogs (user_id, is_active)
                VALUES ($1, TRUE)
                RETURNING id
            """
            row = await conn.fetchrow(query, user_id)
            return row['id']

    async def get_dialog(self, dialog_id: int) -> Optional[Dict[str, Any]]:
        """Получает диалог по ID."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM dialogs WHERE id = $1"
            row = await conn.fetchrow(query, dialog_id)
            return dict(row) if row else None

    async def close_dialog(self, dialog_id: int):
        """Завершает диалог."""
        async with self.pool.acquire() as conn:
            query = "UPDATE dialogs SET is_active = FALSE WHERE id = $1"
            await conn.execute(query, dialog_id)

    # Методы для работы с сообщениями
    async def add_message(self, dialog_id: int, text: str,
                          is_from_user: bool) -> int:
        """Добавляет сообщение в диалог."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO messages (dialog_id, text, is_from_user, timestamp)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                RETURNING id
            """
            row = await conn.fetchrow(query, dialog_id, text, is_from_user)
            return row['id']

    async def get_message_history(self, dialog_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает историю сообщений диалога."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM messages
                WHERE dialog_id = $1
                ORDER BY timestamp ASC
                LIMIT $2
            """
            rows = await conn.fetch(query, dialog_id, limit)
            return [dict(row) for row in rows]

    # Методы для работы с состояниями FSM
    async def set_user_state(self, user_id: int, state_name: str, data: Dict[str, Any]):
        """Устанавливает состояние пользователя."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO states (user_id, state_name, data, updated_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    state_name = EXCLUDED.state_name,
                    data = EXCLUDED.data,
                    updated_at = CURRENT_TIMESTAMP
            """
            await conn.execute(query, user_id, state_name, json.dumps(data))

    async def get_user_state(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает состояние пользователя."""
        async with self.pool.acquire() as conn:
            query = "SELECT * FROM states WHERE user_id = $1"
            row = await conn.fetchrow(query, user_id)
            if row:
                result = dict(row)
                result['data'] = json.loads(result['data']) if result['data'] else {}
                return result
            return None

    async def clear_user_state(self, user_id: int):
        """Очищает состояние пользователя."""
        async with self.pool.acquire() as conn:
            query = "DELETE FROM states WHERE user_id = $1"
            await conn.execute(query, user_id)

    # Методы для работы с командами
    async def register_command(self, command_name: str, description: str) -> int:
        """Регистрирует команду."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO commands (command_name, description)
                VALUES ($1, $2)
                RETURNING id
            """
            row = await conn.fetchrow(query, command_name, description)
            return row['id']

    async def log_user_command(self, user_id: int, command_id: int):
        """Логирует использование команды пользователем."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO user_commands (user_id, command_id, used_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
            """
            await conn.execute(query, user_id, command_id)

    async def get_user_commands(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает команды пользователя."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT uc.*, c.command_name
                FROM user_commands uc
                JOIN commands c ON uc.command_id = c.id
                WHERE uc.user_id = $1
                ORDER BY uc.used_at DESC
            """
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    # Методы для работы с намерениями
    async def create_intention(self, name: str, pattern: str) -> int:
        """Создает намерение."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO intentions (name, pattern)
                VALUES ($1, $2)
                RETURNING id
            """
            row = await conn.fetchrow(query, name, pattern)
            return row['id']

    async def log_user_intention(self, user_id: int, intention_id: int, confidence: float):
        """Логирует намерение пользователя."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO user_intentions (user_id, intention_id, confidence, detected_at)
                VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            """
            await conn.execute(query, user_id, intention_id, confidence)

    async def get_user_intentions(self, user_id: int) -> List[Dict[str, Any]]:
        """Получает намерения пользователя."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT ui.*, i.name as intention_name
                FROM user_intentions ui
                JOIN intentions i ON ui.intention_id = i.id
                WHERE ui.user_id = $1
                ORDER BY ui.detected_at DESC
            """
            rows = await conn.fetch(query, user_id)
            return [dict(row) for row in rows]

    # Методы для логирования API запросов
    async def log_api_request(self, endpoint: str, method: str,
                              request_data: Dict[str, Any], response_data: Dict[str, Any],
                              status_code: int, execution_time: float) -> int:
        """Логирует API запрос."""
        async with self.pool.acquire() as conn:
            query = """
                INSERT INTO api_logs
                (endpoint, method, request_data, response_data, status_code, execution_time, logged_at)
                VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP)
                RETURNING id
            """
            row = await conn.fetchrow(
                query, endpoint, method,
                json.dumps(request_data), json.dumps(response_data),
                status_code, execution_time
            )
            return row['id']

    async def get_api_logs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получает логи API запросов."""
        async with self.pool.acquire() as conn:
            query = """
                SELECT * FROM api_logs
                ORDER BY logged_at DESC
                LIMIT $1
            """
            rows = await conn.fetch(query, limit)
            logs = []
            for row in rows:
                log = dict(row)
                log['request_data'] = json.loads(log['request_data']) if log['request_data'] else {}
                log['response_data'] = json.loads(log['response_data']) if log['response_data'] else {}
                logs.append(log)
            return logs
