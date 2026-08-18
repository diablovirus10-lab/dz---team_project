"""
Интеграционные тесты для базы данных.

Эти тесты проверяют взаимодействие с реальной базой данных PostgreSQL,
включая миграции, целостность данных и транзакции.
"""
import pytest
import asyncio
from typing import AsyncGenerator
from src.database.async_db_manager import DatabaseManager
from src.database.config import DatabaseConfig


@pytest.fixture(scope="module")
def db_config() -> DatabaseConfig:
    """Конфигурация БД для интеграционных тестов."""
    return DatabaseConfig(
        host="localhost",
        port=5432,
        database="vk_bot_test",
        user="postgres",
        password="postgres"
    )


@pytest.fixture(scope="module")
async def db_manager(db_config: DatabaseConfig) -> AsyncGenerator[DatabaseManager, None]:
    """Фикстура для создания и очистки менеджера БД."""
    manager = DatabaseManager(db_config)
    await manager.connect()
    await manager.create_tables()
    
    yield manager
    
    # Очистка после тестов
    await manager.disconnect()


@pytest.fixture
async def clean_db(db_manager: DatabaseManager) -> DatabaseManager:
    """Фикстура для очистки БД перед каждым тестом."""
    await db_manager.clear_all_tables()
    yield db_manager


class TestDatabaseIntegration:
    """Интеграционные тесты для базы данных."""

    @pytest.mark.asyncio
    async def test_create_tables_success(self, db_manager: DatabaseManager):
        """Тест успешного создания таблиц."""
        # Таблицы уже созданы в фикстуре db_manager
        # Проверяем, что они существуют
        tables = await db_manager.get_all_tables()
        
        expected_tables = {
            'users', 'dialogs', 'messages', 'states',
            'commands', 'user_commands', 'intentions',
            'entities', 'user_intentions', 'api_logs'
        }
        
        assert len(tables) >= len(expected_tables)
        for table in expected_tables:
            assert table in tables, f"Таблица {table} не найдена"

    @pytest.mark.asyncio
    async def test_user_crud_operations(self, clean_db: DatabaseManager):
        """Тест операций CRUD для пользователей."""
        # Create
        user_id = await clean_db.create_user(
            vk_id=12345,
            first_name="Иван",
            last_name="Иванов",
            age=25,
            city="Москва",
            sex=1
        )
        assert user_id > 0
        
        # Read
        user = await clean_db.get_user_by_vk_id(12345)
        assert user is not None
        assert user['vk_id'] == 12345
        assert user['first_name'] == "Иван"
        
        # Update (через get_or_create)
        updated_user = await clean_db.get_or_create_user(
            vk_id=12345,
            first_name="Иван Обновленный",
            last_name="Иванов",
            age=26,
            city="Санкт-Петербург",
            sex=1
        )
        assert updated_user['first_name'] == "Иван Обновленный"
        assert updated_user['city'] == "Санкт-Петербург"

    @pytest.mark.asyncio
    async def test_dialog_management(self, clean_db: DatabaseManager):
        """Тест управления диалогами."""
        # Создаем пользователя
        user_id = await clean_db.create_user(
            vk_id=54321,
            first_name="Петр",
            last_name="Петров",
            age=30,
            city="Казань",
            sex=1
        )
        
        # Создаем диалог
        dialog_id = await clean_db.create_dialog(user_id)
        assert dialog_id > 0
        
        # Получаем диалог
        dialog = await clean_db.get_dialog(dialog_id)
        assert dialog is not None
        assert dialog['user_id'] == user_id
        assert dialog['is_active'] is True
        
        # Завершаем диалог
        await clean_db.close_dialog(dialog_id)
        closed_dialog = await clean_db.get_dialog(dialog_id)
        assert closed_dialog['is_active'] is False

    @pytest.mark.asyncio
    async def test_message_history(self, clean_db: DatabaseManager):
        """Тест истории сообщений."""
        # Создаем пользователя и диалог
        user_id = await clean_db.create_user(
            vk_id=99999,
            first_name="Тест",
            last_name="Тестов",
            age=20,
            city="Тестовск",
            sex=1
        )
        dialog_id = await clean_db.create_dialog(user_id)
        
        # Добавляем сообщения
        msg1_id = await clean_db.add_message(
            dialog_id=dialog_id,
            text="Привет!",
            is_from_user=True
        )
        msg2_id = await clean_db.add_message(
            dialog_id=dialog_id,
            text="Здравствуйте!",
            is_from_user=False
        )
        
        assert msg1_id > 0
        assert msg2_id > 0
        
        # Получаем историю
        history = await clean_db.get_message_history(dialog_id, limit=10)
        assert len(history) == 2
        assert history[0]['text'] == "Привет!"
        assert history[1]['text'] == "Здравствуйте!"

    @pytest.mark.asyncio
    async def test_state_management(self, clean_db: DatabaseManager):
        """Тест управления состояниями FSM."""
        # Создаем пользователя
        user_id = await clean_db.create_user(
            vk_id=77777,
            first_name="Стейт",
            last_name="Тестов",
            age=22,
            city="Москва",
            sex=1
        )
        
        # Устанавливаем состояние
        await clean_db.set_user_state(user_id, "waiting_for_age", {"step": 1})
        
        # Получаем состояние
        state = await clean_db.get_user_state(user_id)
        assert state is not None
        assert state['state_name'] == "waiting_for_age"
        assert state['data']['step'] == 1
        
        # Очищаем состояние
        await clean_db.clear_user_state(user_id)
        cleared_state = await clean_db.get_user_state(user_id)
        assert cleared_state is None

    @pytest.mark.asyncio
    async def test_command_tracking(self, clean_db: DatabaseManager):
        """Тест отслеживания команд."""
        # Создаем пользователя
        user_id = await clean_db.create_user(
            vk_id=88888,
            first_name="Комманд",
            last_name="Тестов",
            age=28,
            city="СПб",
            sex=1
        )
        
        # Регистрируем команду
        command_id = await clean_db.register_command("start", "/start - запуск бота")
        assert command_id > 0
        
        # Отмечаем использование команды
        await clean_db.log_user_command(user_id, command_id)
        
        # Получаем статистику
        user_commands = await clean_db.get_user_commands(user_id)
        assert len(user_commands) > 0
        assert any(cmd['command_name'] == 'start' for cmd in user_commands)

    @pytest.mark.asyncio
    async def test_intention_handling(self, clean_db: DatabaseManager):
        """Тест обработки намерений."""
        # Создаем пользователя
        user_id = await clean_db.create_user(
            vk_id=66666,
            first_name="Интеншн",
            last_name="Тестов",
            age=33,
            city="Екб",
            sex=1
        )
        
        # Создаем намерение
        intention_id = await clean_db.create_intention(
            name="greeting",
            pattern="привет|здравствуй|hello"
        )
        assert intention_id > 0
        
        # Логируем намерение пользователя
        await clean_db.log_user_intention(user_id, intention_id, confidence=0.95)
        
        # Получаем намерения пользователя
        intentions = await clean_db.get_user_intentions(user_id)
        assert len(intentions) > 0
        assert any(intent['intention_name'] == 'greeting' for intent in intentions)

    @pytest.mark.asyncio
    async def test_transaction_rollback(self, clean_db: DatabaseManager):
        """Тест отката транзакций при ошибках."""
        initial_users = await clean_db.get_all_users()
        initial_count = len(initial_users)
        
        try:
            # Начинаем транзакцию с ошибкой
            async with clean_db.pool.acquire() as conn:
                async with conn.transaction():
                    # Создаем пользователя
                    await conn.execute("""
                        INSERT INTO users (vk_id, first_name, last_name, age, city, sex)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, 11111, "Транзакция", "Тестов", 25, "Москва", 1)
                    
                    # Вызываем ошибку
                    raise Exception("Искусственная ошибка для теста")
        except Exception:
            pass  # Ожидаем ошибку
        
        # Проверяем, что пользователь не был создан
        final_users = await clean_db.get_all_users()
        assert len(final_users) == initial_count

    @pytest.mark.asyncio
    async def test_data_integrity_constraints(self, clean_db: DatabaseManager):
        """Тест ограничений целостности данных."""
        # Тест уникальности vk_id
        user_id1 = await clean_db.create_user(
            vk_id=22222,
            first_name="Уник",
            last_name="Тестов",
            age=25,
            city="Москва",
            sex=1
        )
        
        with pytest.raises(Exception):
            # Попытка создать пользователя с тем же vk_id должна вызвать ошибку
            await clean_db.create_user(
                vk_id=22222,
                first_name="Дубль",
                last_name="Тестов",
                age=30,
                city="СПб",
                sex=1
            )
        
        # Тест внешних ключей - нельзя создать диалог для несуществующего пользователя
        with pytest.raises(Exception):
            await clean_db.create_dialog(999999999)  # Пользователь не существует

    @pytest.mark.asyncio
    async def test_api_logging(self, clean_db: DatabaseManager):
        """Тест логирования API запросов."""
        # Логируем запрос
        log_id = await clean_db.log_api_request(
            endpoint="/messages.send",
            method="POST",
            request_data={"user_id": 123, "message": "test"},
            response_data={"status": "ok"},
            status_code=200,
            execution_time=0.15
        )
        
        assert log_id > 0
        
        # Получаем логи
        logs = await clean_db.get_api_logs(limit=10)
        assert len(logs) > 0
        assert any(log['endpoint'] == '/messages.send' for log in logs)

    @pytest.mark.asyncio
    async def test_database_connection_pool(self, db_config: DatabaseConfig):
        """Тест пула соединений."""
        manager = DatabaseManager(db_config)
        await manager.connect()
        
        # Проверяем, что пул создан
        assert manager.pool is not None
        
        # Выполняем несколько параллельных запросов
        tasks = []
        for i in range(5):
            task = manager.get_all_tables()
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # Все запросы должны успешно выполниться
        assert all(len(result) > 0 for result in results)
        
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_clear_all_tables(self, clean_db: DatabaseManager):
        """Тест полной очистки базы данных."""
        # Создаем тестовые данные
        user_id = await clean_db.create_user(
            vk_id=33333,
            first_name="Очистка",
            last_name="Тестов",
            age=40,
            city="Новосибирск",
            sex=1
        )
        dialog_id = await clean_db.create_dialog(user_id)
        await clean_db.add_message(dialog_id, "Тест", True)
        
        # Очищаем все таблицы
        await clean_db.clear_all_tables()
        
        # Проверяем, что данные удалены
        users = await clean_db.get_all_users()
        assert len(users) == 0
