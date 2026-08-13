import psycopg2
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.config import DatabaseConfig


class TestDatabaseConnection:
    """Тесты подключения к базе данных"""

    def test_connection(self):
        """Тест: подключение к БД работает"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        assert conn is not None
        assert conn.autocommit is False
        conn.close()

    def test_connection_with_query(self):
        """Тест: можно выполнить запрос"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        assert result == (1,)

    def test_connection_params(self):
        """Тест: параметры подключения соответствуют .env"""
        params = DatabaseConfig.get_connection_params()

        assert params['host'] == DatabaseConfig.HOST
        assert params['port'] == DatabaseConfig.PORT
        assert params['database'] == DatabaseConfig.NAME
        assert params['user'] == DatabaseConfig.USER
        assert params['password'] == DatabaseConfig.PASSWORD
        assert len(params['password']) > 0


class TestTablesExist:
    """Тесты: проверка наличия всех таблиц"""

    EXPECTED_TABLES = {
        'users', 'candidates', 'photos', 'favorites', 'blacklist',
        'user_interests', 'interests', 'search_weights',
        'viewed_candidates', 'search_offsets'
    }

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def _get_existing_tables(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()
        return tables

    def test_all_tables_exist(self):
        """Тест: все 10 таблиц существуют"""
        tables = self._get_existing_tables()
        missing = self.EXPECTED_TABLES - tables
        assert not missing, f"Отсутствуют таблицы: {missing}"

    def test_table_count(self):
        """Тест: количество таблиц >= 10"""
        tables = self._get_existing_tables()
        assert len(tables) >= 10, f"Ожидается >= 10 таблиц, найдено {len(tables)}"


class TestTableStructure:
    """Тесты: проверка структуры таблиц"""

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def _get_columns(self, table_name):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = %s ORDER BY ordinal_position
        """, (table_name,))
        columns = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return columns

    def test_users_table_structure(self):
        """Тест: таблица users содержит обязательные колонки"""
        columns = self._get_columns('users')
        for col in ['id', 'vk_id', 'first_name', 'last_name', 'city', 'sex']:
            assert col in columns, f"Колонка '{col}' отсутствует в users"

    def test_candidates_table_structure(self):
        """Тест: таблица candidates содержит обязательные колонки"""
        columns = self._get_columns('candidates')
        for col in ['id', 'vk_id', 'first_name', 'city', 'sex', 'profile_link']:
            assert col in columns, f"Колонка '{col}' отсутствует в candidates"

    def test_photos_table_structure(self):
        """Тест: таблица photos содержит специальные колонки"""
        columns = self._get_columns('photos')
        for col in ['is_tagged', 'is_avatar', 'likes_count', 'photo_url', 'candidate_id']:
            assert col in columns, f"Колонка '{col}' отсутствует в photos"


class TestDataExists:
    """Тесты: проверка наличия тестовых данных"""

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def _count_rows(self, table):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    def test_users_have_data(self):
        """Тест: в users есть данные"""
        count = self._count_rows('users')
        assert count > 0, "Таблица users пуста"

    def test_candidates_have_data(self):
        """Тест: в candidates есть данные"""
        count = self._count_rows('candidates')
        assert count > 0, "Таблица candidates пуста"

    def test_photos_have_data(self):
        """Тест: в photos есть данные"""
        count = self._count_rows('photos')
        assert count > 0, "Таблица photos пуста"

    def test_favorites_have_data(self):
        """Тест: в favorites есть данные"""
        count = self._count_rows('favorites')
        assert count > 0, "Таблица favorites пуста"

    def test_blacklist_have_data(self):
        """Тест: в blacklist есть данные"""
        count = self._count_rows('blacklist')
        assert count > 0, "Таблица blacklist пуста"

    def test_all_tables_have_data(self):
        """Тест: во всех таблицах есть данные"""
        tables = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
                  'user_interests', 'interests', 'search_weights',
                  'viewed_candidates', 'search_offsets']
        empty = []
        for table in tables:
            if self._count_rows(table) == 0:
                empty.append(table)
        assert not empty, f"Пустые таблицы: {empty}"


class TestRelationships:
    """Тесты: проверка связей между таблицами"""

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def test_foreign_keys_exist(self):
        """Тест: внешние ключи существуют"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tc.table_name, kcu.column_name, ccu.table_name AS ref_table
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

        assert len(fks) > 0, "Внешние ключи не найдены"

        expected = [
            ('photos', 'candidate_id', 'candidates'),
            ('favorites', 'user_id', 'users'),
            ('blacklist', 'user_id', 'users'),
            ('search_weights', 'user_id', 'users'),
        ]

        for tbl, col, ref in expected:
            found = any(fk[0] == tbl and fk[1] == col and fk[2] == ref for fk in fks)
            assert found, f"Отсутствует связь {tbl}.{col} -> {ref}"

    def test_join_query(self):
        """Тест: JOIN-запрос выполняется успешно"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.first_name, c.first_name
            FROM favorites f
            JOIN users u ON f.user_id = u.id
            JOIN candidates c ON f.candidate_id = c.id
            LIMIT 1
        """)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        assert result is not None


class TestDatabaseOperations:
    """Тесты: основные операции с БД"""

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def test_select_query(self):
        """Тест: чтение данных из users"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, vk_id, first_name FROM users LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        assert result is not None
        assert len(result) == 3

    def test_photos_tagged_and_avatar(self):
        """Тест: есть аватарки и отмеченные фото"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) FILTER (WHERE is_avatar = TRUE),
                COUNT(*) FILTER (WHERE is_tagged = TRUE)
            FROM photos
        """)
        avatars, tagged = cursor.fetchone()
        cursor.close()
        conn.close()

        assert avatars > 0, "Нет аватарок"
        assert tagged > 0, "Нет отмеченных фото"

    def test_interests_have_data(self):
        """Тест: интересы записаны"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM user_interests")
        user_int = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM interests")
        interests = cursor.fetchone()[0]
        cursor.close()
        conn.close()

        assert user_int > 0, "Нет интересов пользователей"
        assert interests > 0, "Нет интересов кандидатов"

    def test_search_weights_have_data(self):
        """Тест: веса критериев есть"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_weights")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert count > 0, "Таблица search_weights пуста"


class TestSearchOffsets:
    """Тесты: таблица search_offsets"""

    def _get_connection(self):
        return psycopg2.connect(**DatabaseConfig.get_connection_params())

    def test_search_offsets_have_data(self):
        """Тест: search_offsets не пустая"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM search_offsets")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        assert count > 0

    def test_search_params_is_json(self):
        """Тест: search_params — валидный JSON"""
        import json
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT search_params FROM search_offsets WHERE search_params IS NOT NULL LIMIT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if result is None:
            pytest.skip("Нет записей с search_params")

        try:
            json.loads(result[0])
        except json.JSONDecodeError:
            pytest.fail("search_params не является валидным JSON")
