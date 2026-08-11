import psycopg2
import json
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.config import DatabaseConfig


class TestDatabaseConnection:
    """Тесты подключения к БД (пошаговая проверка)"""

    def test_connection(self):
        """Подключение к БД устанавливается"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        assert conn is not None
        conn.close()

    def test_tables_exist(self):
        """Все ожидаемые таблицы созданы"""
        expected = {'users', 'candidates', 'photos', 'favorites', 'blacklist',
                    'user_interests', 'interests', 'search_weights',
                    'viewed_candidates', 'search_offsets'}

        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
        tables = {row[0] for row in cursor.fetchall()}
        cursor.close()
        conn.close()

        missing = expected - tables
        assert not missing, f"Отсутствуют таблицы: {missing}"

    def test_data_in_tables(self):
        """Во всех таблицах есть тестовые данные"""
        tables = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
                  'user_interests', 'interests', 'search_weights',
                  'viewed_candidates', 'search_offsets']

        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        empty_tables = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count == 0:
                empty_tables.append(table)

        cursor.close()
        conn.close()

        assert not empty_tables, f"Пустые таблицы: {empty_tables}"

    def test_photos_structure(self):
        """Таблица photos содержит is_tagged и is_avatar"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'photos'
        """)
        columns = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT COUNT(*) FILTER (WHERE is_avatar = TRUE),
                   COUNT(*) FILTER (WHERE is_tagged = TRUE)
            FROM photos
        """)
        avatars, tagged = cursor.fetchone()
        cursor.close()
        conn.close()

        assert 'is_tagged' in columns, "Колонка is_tagged отсутствует"
        assert 'is_avatar' in columns, "Колонка is_avatar отсутствует"
        assert avatars > 0, "Нет аватарок"
        assert tagged > 0, "Нет отмеченных фото"

    def test_foreign_keys(self):
        """Внешние ключи настроены"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
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

        # Проверяем наличие ключевых связей
        required = [('favorites', 'user_id'), ('favorites', 'candidate_id'),
                    ('blacklist', 'user_id'), ('blacklist', 'candidate_id'),
                    ('photos', 'candidate_id')]

        for tbl, col in required:
            found = any(fk[0] == tbl and fk[1] == col for fk in fks)
            assert found, f"Отсутствует FK: {tbl}.{col}"

    def test_search_offsets(self):
        """Таблица search_offsets содержит данные"""
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, offset_value, search_params, total_found
            FROM search_offsets
            LIMIT 3
        """)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        assert len(results) > 0, "search_offsets пуста"

        for row in results:
            if row[2]:
                try:
                    params = json.loads(row[2])
                    assert 'city' in params or isinstance(params, dict)
                except json.JSONDecodeError:
                    pytest.fail(f"search_params не является валидным JSON: {row[2]}")
