import pytest
import psycopg2
from psycopg2 import sql
import sys
import os

# Добавляем путь к src для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.config import DatabaseConfig


class TestDatabaseConnection:
    """Тесты подключения к базе данных"""

    def test_connection(self):
        """Тест: подключение к БД работает"""
        try:
            conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.fail(f"Не удалось подключиться к БД: {e}")

    def test_connection_params(self):
        """Тест: параметры подключения корректны"""
        params = DatabaseConfig.get_connection_params()
        assert params['host'] == 'localhost' or params['host'] == '127.0.0.1'
        assert params['port'] == '5432'
        assert params['database'] == 'bot_db'
        assert params['user'] == 'postgres'


class TestTablesExist:
    """Тесты: проверка наличия всех таблиц"""

    EXPECTED_TABLES = {
        'users',
        'candidates',
        'photos',
        'favorites',
        'blacklist',
        'user_interests',
        'interests',
        'search_weights',
        'viewed_candidates',
        'search_offsets'
    }

    def test_all_tables_exist(self):
        """Тест: все 10 таблиц существуют"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tables = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()

        missing_tables = self.EXPECTED_TABLES - tables
        assert not missing_tables, f"Отсутствуют таблицы: {missing_tables}"

    def test_table_count(self):
        """Тест: количество таблиц = 10"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)

        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count == 10, f"Ожидается 10 таблиц, найдено {count}"


class TestTableStructure:
    """Тесты: проверка структуры таблиц"""

    def test_users_table_structure(self):
        """Тест: структура таблицы users"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """)

        columns = cursor.fetchall()
        cursor.close()
        conn.close()

        column_names = [col[0] for col in columns]
        expected = ['id', 'vk_id', 'first_name', 'last_name', 'age', 'city', 'sex', 'registered_at']

        for col in expected:
            assert col in column_names, f"Колонка {col} отсутствует в таблице users"

    def test_candidates_table_structure(self):
        """Тест: структура таблицы candidates (есть поле sex)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'candidates'
        """)

        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        assert 'sex' in columns, "Колонка sex отсутствует в таблице candidates"
        assert 'profile_link' in columns, "Колонка profile_link отсутствует в таблице candidates"

    def test_photos_table_structure(self):
        """Тест: структура таблицы photos (есть is_tagged и is_avatar)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'photos'
        """)

        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()

        assert 'is_tagged' in columns, "Колонка is_tagged отсутствует в таблице photos"
        assert 'is_avatar' in columns, "Колонка is_avatar отсутствует в таблице photos"
        assert 'likes_count' in columns, "Колонка likes_count отсутствует в таблице photos"


class TestDataExists:
    """Тесты: проверка наличия тестовых данных"""

    def test_users_have_data(self):
        """Тест: в таблице users есть данные (5 записей)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count == 5, f"Ожидается 5 пользователей, найдено {count}"

    def test_candidates_have_data(self):
        """Тест: в таблице candidates есть данные (10 записей)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM candidates")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count == 10, f"Ожидается 10 кандидатов, найдено {count}"

    def test_photos_have_data(self):
        """Тест: в таблице photos есть данные (минимум 28 записей)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM photos")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count >= 28, f"Ожидается минимум 28 фото, найдено {count}"

    def test_favorites_have_data(self):
        """Тест: в таблице favorites есть данные"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM favorites")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count > 0, "В таблице favorites нет данных"

    def test_blacklist_have_data(self):
        """Тест: в таблице blacklist есть данные"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM blacklist")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count > 0, "В таблице blacklist нет данных"

    def test_all_tables_have_data(self):
        """Тест: во всех таблицах есть данные"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        tables = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
                  'user_interests', 'interests', 'search_weights',
                  'viewed_candidates', 'search_offsets']

        empty_tables = []
        for table in tables:
            cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
            count = cursor.fetchone()[0]
            if count == 0:
                empty_tables.append(table)

        cursor.close()
        conn.close()

        assert not empty_tables, f"Пустые таблицы: {empty_tables}"


class TestRelationships:
    """Тесты: проверка связей между таблицами"""

    def test_foreign_keys_exist(self):
        """Тест: внешние ключи созданы"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
        """)

        fks = cursor.fetchall()
        cursor.close()
        conn.close()

        expected_relations = [
            ('photos', 'candidate_id', 'candidates'),
            ('favorites', 'user_id', 'users'),
            ('favorites', 'candidate_id', 'candidates'),
            ('blacklist', 'user_id', 'users'),
            ('blacklist', 'candidate_id', 'candidates'),
            ('user_interests', 'user_id', 'users'),
            ('interests', 'candidate_id', 'candidates'),
            ('search_weights', 'user_id', 'users'),
            ('viewed_candidates', 'user_id', 'users'),
            ('viewed_candidates', 'candidate_id', 'candidates'),
            ('search_offsets', 'user_id', 'users'),
        ]

        for table, column, ref_table in expected_relations:
            found = any(
                fk[0] == table and fk[1] == column and fk[2] == ref_table
                for fk in fks
            )
            assert found, f"Связь {table}.{column} -> {ref_table} отсутствует"


class TestDatabaseOperations:
    """Тесты: основные операции с БД"""

    def test_select_query(self):
        """Тест: выполнение SELECT-запроса"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT id, vk_id, first_name, last_name FROM users LIMIT 1")
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        assert result is not None
        assert len(result) == 4
        assert isinstance(result[0], int)
        assert isinstance(result[1], int)

    def test_join_query(self):
        """Тест: выполнение JOIN-запроса (связь favorites + users + candidates)"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                u.first_name as user_name,
                c.first_name as candidate_name
            FROM favorites f
            JOIN users u ON f.user_id = u.id
            JOIN candidates c ON f.candidate_id = c.id
            LIMIT 1
        """)

        result = cursor.fetchone()
        cursor.close()
        conn.close()

        assert result is not None
        assert len(result) == 2

    def test_photos_with_tagged(self):
        """Тест: проверка фото с is_tagged и is_avatar"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE is_avatar = TRUE) as avatars,
                COUNT(*) FILTER (WHERE is_tagged = TRUE) as tagged
            FROM photos
        """)

        avatars, tagged = cursor.fetchone()
        cursor.close()
        conn.close()

        assert avatars > 0, "Нет аватарок в таблице photos"
        assert tagged > 0, "Нет отмеченных фото в таблице photos"

    def test_interests_have_data(self):
        """Тест: у пользователей и кандидатов есть интересы"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM user_interests")
        user_interests_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM interests")
        interests_count = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        assert user_interests_count > 0, "Нет интересов у пользователей"
        assert interests_count > 0, "Нет интересов у кандидатов"

    def test_search_weights_have_data(self):
        """Тест: у пользователей есть веса критериев"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM search_weights")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count >= 20, f"Ожидается минимум 20 записей весов, найдено {count}"


class TestSearchOffsets:
    """Тесты: проверка таблицы search_offsets"""

    def test_search_offsets_have_data(self):
        """Тест: в таблице search_offsets есть данные"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM search_offsets")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert count > 0, "В таблице search_offsets нет данных"

    def test_search_params_is_json(self):
        """Тест: search_params содержит валидный JSON"""
        import json
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("SELECT search_params FROM search_offsets LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        assert result is not None
        try:
            json.loads(result[0])
        except json.JSONDecodeError:
            pytest.fail("search_params не является валидным JSON")


def run_tests():
    """Запуск всех тестов"""
    result = pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-s',
    ])
    return result


if __name__ == '__main__':
    sys.exit(run_tests())