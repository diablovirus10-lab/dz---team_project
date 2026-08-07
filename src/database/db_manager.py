import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from typing import Optional, List, Dict, Any
import json
from datetime import datetime

from .config import DatabaseConfig


class Database:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """
        Устанавливает соединение с базой данных
        """
        try:
            self.conn = psycopg2.connect(**DatabaseConfig.get_connection_params())
            self.cursor = self.conn.cursor()
            return True
        except Exception as e:
            print(f"Ошибка подключения к БД: {e}")
            return False

    def close(self):
        """
        Закрывает соединение с базой данных
        """
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def execute(self, query, params=None):
        try:
            if not self.conn or self.conn.closed:
                self.connect()
            self.cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            self.conn.commit()
            return []
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            raise

    def execute_dict(self, query, params=None):
        try:
            if not self.conn or self.conn.closed:
                self.connect()
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query, params or ())
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            self.conn.commit()
            return []
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка выполнения запроса: {e}")
            raise

    def get_or_create_user(self, vk_id, first_name, last_name, age, city, sex):
        """Создание пользователя, проверяет если нет создает"""
        query = "SELECT * FROM users WHERE vk_id = %s"
        result = self.execute_dict(query, (vk_id,))

        if result:
            return result[0]

        query = """
            INSERT INTO users (vk_id, first_name, last_name, age, city, sex)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING *
        """
        result = self.execute_dict(query, (vk_id, first_name, last_name, age, city, sex))
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

    def get_viewed(self, user_id):
        """Получаем список ID просмотренных кандидатов"""
        query = "SELECT candidate_id FROM viewed_candidates WHERE user_id = %s"
        result = self.execute(query, (user_id,))
        return [row[0] for row in result] if result else []

    def save_user_interests(self, user_id, interests):
        """Сохраняем интересы пользователя"""
        try:
            # Сначала удаляем старые интересы (чтобы не было дублей)
            self.execute("DELETE FROM user_interests WHERE user_id = %s", (user_id,))

            # Добавляем новые интересы
            for interest in interests:
                query = """
                    INSERT INTO user_interests (user_id, type, value, vk_entity_id)
                    VALUES (%s, %s, %s, %s)
                """
                self.execute(query, (user_id, interest['type'], interest['value'], interest.get('vk_entity_id')))
            return True
        except Exception:
            return False

    def get_user_interests(self, user_id):
        """Получаем интересы пользователя"""
        query = "SELECT * FROM user_interests WHERE user_id = %s"
        return self.execute_dict(query, (user_id,))

    def save_candidate_interests(self, candidate_id, interests):
        """Сохраняем интересы кандидата"""
        try:
            for interest in interests:
                query = """
                    INSERT INTO interests (candidate_id, type, value, vk_entity_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (candidate_id, type, value) DO NOTHING
                """
                self.execute(query, (candidate_id, interest['type'], interest['value'], interest.get('vk_entity_id')))
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