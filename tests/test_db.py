import json
import os
import sys

import psycopg2
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.config import DatabaseConfig


def test_connection():
    """Тест подключения к БД"""
    print("\n=== Тест подключения к БД ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        print("✅ Подключение успешно!")
        conn.close()
    except Exception as e:
        pytest.fail(f"❌ Ошибка подключения: {e}")


def test_tables():
    """Тест наличия всех таблиц"""
    print("\n=== Тест наличия таблиц ===")
    expected = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
                'user_interests', 'interests', 'search_weights',
                'viewed_candidates', 'search_offsets']

    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)

        tables = [row[0] for row in cursor.fetchall()]

        missing = [t for t in expected if t not in tables]
        cursor.close()
        conn.close()

        assert not missing, f"❌ Отсутствуют таблицы: {missing}"
        print(f"✅ Все 10 таблиц созданы: {', '.join(tables)}")
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"❌ Ошибка: {e}")


def test_data():
    """Тест наличия данных в таблицах"""
    print("\n=== Тест наличия данных ===")
    tables = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
              'user_interests', 'interests', 'search_weights',
              'viewed_candidates', 'search_offsets']

    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        empty_tables = []
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  ✅ {table}: {count} записей")
            else:
                print(f"  ⚠️ {table}: 0 записей (пусто)")
                empty_tables.append(table)

        cursor.close()
        conn.close()
        assert not empty_tables, f"❌ Пустые таблицы: {empty_tables}"
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"❌ Ошибка: {e}")


def test_photos():
    """Тест структуры таблицы photos"""
    print("\n=== Тест структуры photos ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'photos'
        """)
        columns = [row[0] for row in cursor.fetchall()]

        print(f"  Колонки в photos: {', '.join(columns)}")

        if 'is_tagged' in columns:
            print("  ✅ Есть колонка is_tagged")
        else:
            print("  ❌ Нет колонки is_tagged")

        if 'is_avatar' in columns:
            print("  ✅ Есть колонка is_avatar")
        else:
            print("  ❌ Нет колонки is_avatar")

        cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE is_avatar = TRUE) as avatars,
                COUNT(*) FILTER (WHERE is_tagged = TRUE) as tagged
            FROM photos
        """)
        avatars, tagged = cursor.fetchone()
        print(f"  Аватарок: {avatars}, Отмеченных фото: {tagged}")

        cursor.close()
        conn.close()

        assert 'is_tagged' in columns, "❌ Нет колонки is_tagged"
        assert 'is_avatar' in columns, "❌ Нет колонки is_avatar"
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"❌ Ошибка: {e}")


def test_foreign_keys():
    """Тест внешних ключей"""
    print("\n=== Тест внешних ключей ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
        """)

        fks = cursor.fetchall()
        print(f"  Найдено внешних ключей: {len(fks)}")
        for fk in fks:
            print(f"    {fk[0]}.{fk[1]} -> {fk[2]}.id")

        cursor.close()
        conn.close()
        assert len(fks) > 0, "❌ Внешние ключи не найдены"
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"❌ Ошибка: {e}")


def test_search_offsets():
    """Тест search_offsets"""
    print("\n=== Тест search_offsets ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_id, offset_value, search_params, total_found
            FROM search_offsets
            LIMIT 3
        """)
        results = cursor.fetchall()

        print(f"  Найдено записей в search_offsets: {len(results)}")
        for row in results:
            try:
                params = json.loads(row[2])
                print(
                    f"    user_id={row[0]}, offset={row[1]}, "
                    f"total={row[3]}, city={params.get('city', 'N/A')}"
                )
            except Exception:
                print(f"    user_id={row[0]}, offset={row[1]}, total={row[3]}")

        cursor.close()
        conn.close()
        assert len(results) > 0, "❌ В search_offsets нет записей"
    except AssertionError:
        raise
    except Exception as e:
        pytest.fail(f"❌ Ошибка: {e}")


def _run_single_test(test_func):
    """Запуск одного теста для режима python tests/test_db.py"""
    try:
        test_func()
        return True
    except Exception:
        return False


def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 50)

    tests = [
        ("Подключение", test_connection),
        ("Таблицы", test_tables),
        ("Данные", test_data),
        ("Photos", test_photos),
        ("Внешние ключи", test_foreign_keys),
        ("Search_offsets", test_search_offsets),
    ]

    results = [(name, _run_single_test(func)) for name, func in tests]

    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ")
    print("=" * 50)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    passed = sum(1 for _, r in results if r)
    total = len(results)
    print(f"\nИтого: {passed}/{total} тестов пройдено")

    return passed == total


if __name__ == '__main__':
    sys.exit(0 if run_all_tests() else 1)
