import psycopg2
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database.config import DatabaseConfig


def test_connection():
    """Тест подключения к БД"""
    print("\n=== Тест подключения к БД ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        print("✅ Подключение успешно!")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False


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
        if missing:
            print(f"❌ Отсутствуют таблицы: {missing}")
            return False

        print(f"✅ Все 10 таблиц созданы: {', '.join(tables)}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_data():
    """Тест наличия данных в таблицах"""
    print("\n=== Тест наличия данных ===")
    tables = ['users', 'candidates', 'photos', 'favorites', 'blacklist',
              'user_interests', 'interests', 'search_weights',
              'viewed_candidates', 'search_offsets']

    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        all_ok = True
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            if count > 0:
                print(f"  ✅ {table}: {count} записей")
            else:
                print(f"  ⚠️ {table}: 0 записей (пусто)")
                all_ok = False

        cursor.close()
        conn.close()
        return all_ok
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def test_photos():
    """Тест структуры таблицы photos"""
    print("\n=== Тест структуры photos ===")
    try:
        conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
        cursor = conn.cursor()

        # Проверяем наличие is_tagged и is_avatar
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

        # Проверяем количество аватарок и отмеченных фото
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
        return 'is_tagged' in columns and 'is_avatar' in columns
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


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
        return len(fks) > 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


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
                print(f"    user_id={row[0]}, offset={row[1]}, total={row[3]}, city={params.get('city', 'N/A')}")
            except:
                print(f"    user_id={row[0]}, offset={row[1]}, total={row[3]}")

        cursor.close()
        conn.close()
        return len(results) > 0
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def run_all_tests():
    """Запуск всех тестов"""
    print("=" * 50)
    print("ТЕСТИРОВАНИЕ БАЗЫ ДАННЫХ")
    print("=" * 50)

    results = []

    results.append(("Подключение", test_connection()))
    results.append(("Таблицы", test_tables()))
    results.append(("Данные", test_data()))
    results.append(("Photos", test_photos()))
    results.append(("Внешние ключи", test_foreign_keys()))
    results.append(("Search_offsets", test_search_offsets()))

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