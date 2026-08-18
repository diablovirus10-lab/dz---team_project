import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor, execute_values as pg_execute_values
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from .config import DatabaseConfig
from .exceptions import DatabaseError


class Database:
    def __init__(self):
        self.conn = None

    def __enter__(self):
        if not self.conn or self.conn.closed:
            self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.conn and not self.conn.closed:
            if exc_type:
                try:
                    self.conn.rollback()
                except psycopg2.Error:
                    pass
        self.close()
        return False

    def connect(self):
        """
        Устанавливает соединение с базой данных
        """
        try:
            self.conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
            self.conn.autocommit = False
            return True
        except psycopg2.Error as e:
            self.conn = None
            raise DatabaseError(f"Ошибка подключения к БД: {e}", original_error=e) from e
    def close(self):
        """
        Закрывает соединение с базой данных
        """
        if self.conn is not None:
            try:
                self.conn.close()
            except psycopg2.Error:
                pass
            finally:
                self.conn = None

    def _ensure_connection(self):
        if not self.conn or self.conn.closed:
            self.connect()

    def _rollback(self):
        if self.conn and not self.conn.closed:
            try:
                self.conn.rollback()
            except psycopg2.Error:
                pass

    def _get_cursor(self, dict_cursor=False):
        return self.conn.cursor(cursor_factory=RealDictCursor) if dict_cursor else self.conn.cursor()

    def fetch_one(self, query, params=None, dict_cursor=False):
        try:
            self._ensure_connection()
            with self._get_cursor(dict_cursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchone()
        except psycopg2.Error as e:
            self._rollback()
            raise DatabaseError(f"Ошибка выполнения запроса fetch_one: {e}", original_error=e) from e

    def fetch_all(self, query, params=None, dict_cursor=False):
        try:
            self._ensure_connection()
            with self._get_cursor(dict_cursor) as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except psycopg2.Error as e:
            self._rollback()
            raise DatabaseError(f"Ошибка выполнения запроса fetch_all: {e}", original_error=e) from e

    def execute_update(self, query, params=None, dict_cursor=False, returning=False):
        try:
            self._ensure_connection()
            with self._get_cursor(dict_cursor) as cursor:
                cursor.execute(query, params or ())
                result = cursor.fetchall() if returning else []
            self.conn.commit()
            return result
        except psycopg2.Error as e:
            self._rollback()
            raise DatabaseError(f"Ошибка выполнения запроса execute_update: {e}", original_error=e) from e

    def execute_values(self, query, values, template=None, page_size=100):
        try:
            self._ensure_connection()
            with self.conn.cursor() as cursor:
                pg_execute_values(cursor, query, values, template=template, page_size=page_size)
            self.conn.commit()
        except psycopg2.Error as e:
            self._rollback()
            raise DatabaseError(f"Ошибка выполнения запроса execute_values: {e}", original_error=e) from e

    def execute(self, query, params=None):
        stripped = query.strip().upper()
        if stripped.startswith('SELECT') or (stripped.startswith('WITH') and 'RETURNING' not in stripped):
            return self.fetch_all(query, params)
        return self.execute_update(query, params, returning='RETURNING' in stripped)

    def execute_dict(self, query, params=None):
        stripped = query.strip().upper()
        if stripped.startswith('SELECT') or (stripped.startswith('WITH') and 'RETURNING' not in stripped):
            return self.fetch_all(query, params, dict_cursor=True)
        return self.execute_update(query, params, dict_cursor=True, returning='RETURNING' in stripped)

    def get_or_create_user(self, vk_id, first_name=None, last_name=None, age=None, city=None, sex=None):
        """Создание пользователя или получение существующего.
        
        Контракт с bot_logic: принимает только vk_id (остальные параметры опциональны).
        Если пользователь не найден, создаётся запись с минимальными данными.
        
        Args:
            vk_id: ID пользователя ВКонтакте
            first_name, last_name, age, city, sex: Опциональные данные (могут быть заполнены позже)
        
        Returns:
            Словарь с данными пользователя или None при ошибке
        """
        query = "SELECT * FROM users WHERE vk_id = %s"
        result = self.execute_dict(query, (vk_id,))

        if result:
            return result[0]

        # Создаём нового пользователя с доступными данными
        query = """
            INSERT INTO users (vk_id, first_name, last_name, age, city, sex)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.execute_dict(
            query, 
            (vk_id, first_name, last_name, age, city, sex)
        )
        return result[0] if result else None


    def get_user(self, user_id):
        '''Получает пользователя по ID'''
        query = "SELECT * FROM users WHERE id = %s"
        result = self.execute_dict(query, (user_id,))
        return result[0] if result else None

    def get_user_by_vk(self, vk_id):
        """Получает пользователя по VK ID"""
        query = "SELECT * FROM users WHERE vk_id = %s"
        result = self.execute_dict(query, (vk_id,))
        return result[0] if result else None


    def save_candidate(self, vk_id, first_name, last_name, age, city, sex, profile_link):
        """Сохраняет кандидата в БД если нет то создаем нового"""
        query = "SELECT * FROM candidates WHERE vk_id = %s"
        result = self.execute_dict(query, (vk_id,))

        if result:
            return result[0]

        query = """
            INSERT INTO candidates (vk_id, first_name, last_name, age, city, sex, profile_link)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.execute_dict(query, (vk_id, first_name, last_name, age, city, sex, profile_link))
        return result[0] if result else None

    def get_candidate(self, candidate_id):
        """Получает кандидата по ID"""
        query = "SELECT * FROM candidates WHERE id = %s"
        result = self.execute_dict(query, (candidate_id,))
        return result[0] if result else None

    def get_candidates_for_user(self, user_id, limit=10):
        """Получает непросмотренных кандидатов"""
        query = """
            SELECT c.*
            FROM candidates c
            WHERE c.id NOT IN (
                SELECT candidate_id FROM viewed_candidates WHERE user_id = %s
                UNION
                SELECT candidate_id FROM favorites WHERE user_id = %s
                UNION
                SELECT candidate_id FROM blacklist WHERE user_id = %s
            )
            LIMIT %s
        """
        return self.execute_dict(query, (user_id, user_id, user_id, limit))


    def save_photo(self, candidate_id, photo_url, photo_id, likes_count=0, comments_count=0, is_avatar=False,
                   is_tagged=False):
        """Сохраняет ссылку фото кандидата"""
        query = """
            INSERT INTO photos (candidate_id, photo_url, photo_id, likes_count, 
                               comments_count, is_avatar, is_tagged)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (candidate_id, photo_id) DO UPDATE SET
                likes_count = EXCLUDED.likes_count,
                comments_count = EXCLUDED.comments_count
            RETURNING *
        """
        result = self.execute_dict(query, (candidate_id, photo_url, photo_id,
                                           likes_count, comments_count, is_avatar, is_tagged))
        return result[0] if result else None

    def get_top_photos(self, candidate_id, limit=3):
        """Получает топ-3 фото по лайкам"""
        query = """
            SELECT * FROM photos
            WHERE candidate_id = %s
            ORDER BY likes_count DESC
            LIMIT %s
        """
        return self.execute_dict(query, (candidate_id, limit))

    def get_photos_with_tagged(self, candidate_id, limit=3):
        """
        пока под вопросом где применять?
        Получаем фотографии кандидата (аватарки + те, где он отмечен)
        """
        query = """
            SELECT * FROM photos
            WHERE candidate_id = %s AND (is_avatar = TRUE OR is_tagged = TRUE)
            ORDER BY likes_count DESC
            LIMIT %s
        """
        return self.execute_dict(query, (candidate_id, limit))

    def add_to_favorites(self, user_id, candidate_id):
        """Добавляем кандидата в избранное"""
        try:
            query = """
                INSERT INTO favorites (user_id, candidate_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, candidate_id) DO NOTHING
            """
            self.execute(query, (user_id, candidate_id))
            return True
        except Exception:
            return False

    def add_favorite(self, user_id, profile):
        """Обёртка для совместимости с bot_logic.
        
        Args:
            user_id: ID пользователя ВКонтакте
            profile: Словарь с данными профиля кандидата (должен содержать 'vk_id')
        
        Returns:
            True если успешно, False иначе
        """
        candidate_vk_id = profile.get('vk_id')
        if not candidate_vk_id:
            return False
        # Получаем или создаём кандидата в БД
        candidate = self.get_user_by_vk(candidate_vk_id)
        if not candidate:
            candidate = self.save_candidate(
                vk_id=candidate_vk_id,
                first_name=profile.get('first_name', ''),
                last_name=profile.get('last_name', ''),
                age=profile.get('age'),
                city=profile.get('city', ''),
                sex=profile.get('sex'),
                profile_link=f"https://vk.com/id{candidate_vk_id}"
            )
        if not candidate:
            return False
        return self.add_to_favorites(user_id, candidate['id'])

    def remove_from_favorites(self, user_id, candidate_id):
        """Удаляем кандидата из избранного"""
        try:
            query = "DELETE FROM favorites WHERE user_id = %s AND candidate_id = %s"
            self.execute(query, (user_id, candidate_id))
            return True
        except Exception:
            return False

    def get_favorites(self, user_id):
        """Получаем список избранных кандидатов для пользователя"""
        query = """
            SELECT c.*, f.added_at
            FROM favorites f
            JOIN candidates c ON f.candidate_id = c.id
            WHERE f.user_id = %s
            ORDER BY f.added_at DESC
        """
        return self.execute_dict(query, (user_id,))

    def is_favorite(self, user_id, candidate_id):
        """Проверяем, есть ли кандидат в избранном"""
        query = "SELECT 1 FROM favorites WHERE user_id = %s AND candidate_id = %s"
        result = self.execute(query, (user_id, candidate_id))
        return len(result) > 0

    def add_to_blacklist(self, user_id, candidate_id):
        """Добавляем кандидата в чёрный список"""
        try:
            query = """
                INSERT INTO blacklist (user_id, candidate_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, candidate_id) DO NOTHING
            """
            self.execute(query, (user_id, candidate_id))
            return True
        except Exception:
            return False

    def add_blacklist(self, user_id, profile):
        """Обёртка для совместимости с bot_logic.
        
        Args:
            user_id: ID пользователя ВКонтакте
            profile: Словарь с данными профиля кандидата (должен содержать 'vk_id')
        
        Returns:
            True если успешно, False иначе
        """
        candidate_vk_id = profile.get('vk_id')
        if not candidate_vk_id:
            return False
        # Получаем или создаём кандидата в БД
        candidate = self.get_user_by_vk(candidate_vk_id)
        if not candidate:
            candidate = self.save_candidate(
                vk_id=candidate_vk_id,
                first_name=profile.get('first_name', ''),
                last_name=profile.get('last_name', ''),
                age=profile.get('age'),
                city=profile.get('city', ''),
                sex=profile.get('sex'),
                profile_link=f"https://vk.com/id{candidate_vk_id}"
            )
        if not candidate:
            return False
        return self.add_to_blacklist(user_id, candidate['id'])

    def remove_from_blacklist(self, user_id, candidate_id):
        """Удаляем кандидата из чёрного списка"""
        try:
            query = "DELETE FROM blacklist WHERE user_id = %s AND candidate_id = %s"
            self.execute(query, (user_id, candidate_id))
            return True
        except Exception:
            return False

    def get_blacklist(self, user_id):
        """Получаем чёрный список пользователя"""
        query = """
            SELECT c.*, b.added_at
            FROM blacklist b
            JOIN candidates c ON b.candidate_id = c.id
            WHERE b.user_id = %s
            ORDER BY b.added_at DESC
        """
        return self.execute_dict(query, (user_id,))

    def is_blacklisted(self, user_id, candidate_id):
        """Проверяем, есть ли кандидат в чёрном списке"""
        query = "SELECT 1 FROM blacklist WHERE user_id = %s AND candidate_id = %s"
        result = self.execute(query, (user_id, candidate_id))
        return len(result) > 0

    def mark_viewed(self, user_id, candidate_id):
        """Отмечаем кандидата как просмотренного"""
        try:
            query = """
                INSERT INTO viewed_candidates (user_id, candidate_id)
                VALUES (%s, %s)
                ON CONFLICT (user_id, candidate_id) DO NOTHING
            """
            self.execute(query, (user_id, candidate_id))
            return True
        except Exception:
            return False

    def mark_viewed_profile(self, user_id, profile):
        """Обёртка для совместимости с bot_logic.
        
        Args:
            user_id: ID пользователя ВКонтакте
            profile: Словарь с данными профиля кандидата (должен содержать 'vk_id')
        
        Returns:
            True если успешно, False иначе
        """
        candidate_vk_id = profile.get('vk_id')
        if not candidate_vk_id:
            return False
        # Получаем или создаём кандидата в БД
        candidate = self.get_user_by_vk(candidate_vk_id)
        if not candidate:
            candidate = self.save_candidate(
                vk_id=candidate_vk_id,
                first_name=profile.get('first_name', ''),
                last_name=profile.get('last_name', ''),
                age=profile.get('age'),
                city=profile.get('city', ''),
                sex=profile.get('sex'),
                profile_link=f"https://vk.com/id{candidate_vk_id}"
            )
        if not candidate:
            return False
        return self.mark_viewed(user_id, candidate['id'])

    def get_viewed(self, user_id):
        """Получаем список ID просмотренных кандидатов"""
        query = "SELECT candidate_id FROM viewed_candidates WHERE user_id = %s"
        result = self.execute(query, (user_id,))
        return [row[0] for row in result] if result else []

    def get_viewed_vk_ids(self, user_id):
        """Обёртка для совместимости с bot_logic.
        
        Возвращает множество VK IDs просмотренных кандидатов.
        
        Args:
            user_id: ID пользователя ВКонтакте
        
        Returns:
            set[int]: Множество VK IDs просмотренных кандидатов
        """
        viewed_db_ids = self.get_viewed(user_id)
        if not viewed_db_ids:
            return set()
        
        # Получаем VK IDs кандидатов из БД
        placeholders = ','.join('%s' for _ in viewed_db_ids)
        query = f"SELECT vk_id FROM candidates WHERE id IN ({placeholders})"
        result = self.execute(query, viewed_db_ids)
        return set(row[0] for row in result) if result else set()

    def save_user_interests(self, user_id, interests):
        """Сохраняем интересы пользователя атомарно (одной транзакцией)"""
        try:
            self._ensure_connection()
            with self.conn.cursor() as cursor:
                cursor.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))
                if interests:
                    values = [
                        (user_id, i['type'], i['value'], i.get('vk_entity_id'))
                        for i in interests
                    ]
                    pg_execute_values(
                        cursor,
                        "INSERT INTO user_interests (user_id, type, value, vk_entity_id) VALUES %s",
                        values,
                    )
            self.conn.commit()   
            return True
        except psycopg2.Error as e:
            self._rollback()
            raise DatabaseError(f"Ошибка сохранения интересов: {e}", original_error=e) from e

    def get_user_interests(self, user_id):
        """Получаем интересы пользователя"""
        query = "SELECT * FROM user_interests WHERE user_id = %s"
        return self.execute_dict(query, (user_id,))

    def save_candidate_interests(self, candidate_id, interests):
        """Сохраняем интересы кандидата"""
        try:
            if not interests:
                return True

            query = """
                INSERT INTO interests (candidate_id, type, value, vk_entity_id)
                VALUES %s
                ON CONFLICT (candidate_id, type, value) DO NOTHING
            """

            values = [
                (candidate_id, interest['type'], interest['value'], interest.get('vk_entity_id'))
                for interest in interests
            ]

            self.execute_values(query, values)
            return True
        except Exception:
            return False

    def get_candidate_interests(self, candidate_id):
        """Получаем интересы кандидата"""
        query = "SELECT * FROM interests WHERE candidate_id = %s"
        return self.execute_dict(query, (candidate_id,))

    def get_search_weights(self, user_id):
        """
        Получаем веса критериев для пользователя
        Для расчёта рейтинга кандидатов
        """
        query = "SELECT criterion_name, weight FROM search_weights WHERE user_id = %s"
        result = self.execute_dict(query, (user_id,))
        return {row['criterion_name']: float(row['weight']) for row in result}

    def set_search_weight(self, user_id, criterion_name, weight):
        """
        Устанавливаем вес критерия для пользователя
        Если пользователь меняет настройки поиска
        """
        try:
            query = """
                INSERT INTO search_weights (user_id, criterion_name, weight)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, criterion_name) DO UPDATE SET
                    weight = EXCLUDED.weight,
                    updated_at = CURRENT_TIMESTAMP
            """
            self.execute(query, (user_id, criterion_name, weight))
            return True
        except Exception:
            return False

    def get_search_offset(self, user_id):
        """
        Получаем параметры поиска для пользователя
        Для продолжения поиска после 1000 человек
        """
        query = "SELECT * FROM search_offsets WHERE user_id = %s"
        result = self.execute_dict(query, (user_id,))
        return result[0] if result else None

    def update_search_offset(self, user_id, offset_value, total_found=0, params=None):
        """
        Обновляем параметры поиска для пользователя
        Обновляет параметры обхода лимита
        После каждой порции поиска
        """
        try:
            search_params = json.dumps(params) if params else None
            query = """
                INSERT INTO search_offsets (user_id, offset_value, search_params, total_found, last_search_timestamp)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (user_id) DO UPDATE SET
                    offset_value = EXCLUDED.offset_value,
                    search_params = COALESCE(EXCLUDED.search_params, search_offsets.search_params),
                    total_found = EXCLUDED.total_found,
                    last_search_timestamp = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
            """
            self.execute(query, (user_id, offset_value, search_params, total_found))
            return True
        except Exception:
            return False


# Создаём один объект БД для всего проекта
db = Database()