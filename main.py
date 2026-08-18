"""Точка входа бота VKinder: связывает BotLogic с командными vk_client и БД.

Адаптеры ниже приводят API командных модулей к контракту BotLogic,
поэтому src/bot и тесты не меняются.
"""

import json
import os
import random

from dotenv import load_dotenv
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll

from src.bot import BotLogic, StateManager
from src.vk_api_bot.vk_client import VKClient

load_dotenv()


# ---------------------------------------------------------------------------
# Адаптер VK: добавляет send_message и приводит search_users к контракту бота
# ---------------------------------------------------------------------------
class VKClientAdapter:
    def __init__(self, client: VKClient):
        self._client = client
        self.session = client.session      # нужно для VkBotLongPoll
        self.api = client.api
        self.group_id = client.group_id

    def send_message(self, user_id, text, keyboard=None, attachments=None):
        """BotLogic contract: отправка сообщения сообществом."""
        payload = {"user_id": user_id, "message": text, "random_id": random.getrandbits(31)}
        if keyboard:
            payload["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
        if attachments:
            payload["attachment"] = ",".join(attachments)
        self.api.messages.send(**payload)

    def search_users(self, sex, age, city, count=5):
        """BotLogic contract: список профилей с топ-3 фото."""
        age = age or 18
        result = self._client.search_users(
            sex=sex or 0,
            age_from=max(14, age - 3),
            age_to=min(99, age + 3),
            city_id=self._client.find_city_id(city),
            count=count,
        )
        profiles = []
        for item in result.get("items", []):
            profile = dict(item)
            vk_id = profile.get("vk_id") or profile.get("id")
            profile["vk_id"] = vk_id
            profile.setdefault("profile_link", f"https://vk.com/id{vk_id}")
            photos = self._client.get_user_photos(vk_id, count=10)
            photos.sort(
                key=lambda p: p.get("likes_count", 0) + p.get("comments_count", 0),
                reverse=True,
            )
            profile["photos"] = photos[:3]
            profiles.append(profile)
        return profiles


# ---------------------------------------------------------------------------
# Адаптер БД: переводит vk_id <-> внутренние id, profile <-> candidate_id
# ---------------------------------------------------------------------------
class DatabaseAdapter:
    def __init__(self, db):
        self._db = db

    def get_or_create_user(self, vk_id, **fields):
        row = self._db.get_user_by_vk(vk_id)
        if row is None:
            row = self._db.get_or_create_user(
                vk_id,
                fields.get("first_name"), fields.get("last_name"),
                fields.get("age"), fields.get("city"), fields.get("sex"),
            )
        return row

    def _save_candidate(self, profile):
        vk_id = profile.get("vk_id") or profile.get("id")
        row = self._db.save_candidate(
            vk_id,
            profile.get("first_name"), profile.get("last_name"),
            profile.get("age"), profile.get("city"), profile.get("sex"),
            profile.get("profile_link") or f"https://vk.com/id{vk_id}",
        )
        for ph in profile.get("photos", [])[:3]:
            try:
                self._db.save_photo(
                    row["id"], ph.get("photo_url"), ph.get("photo_id"),
                    ph.get("likes_count", 0), ph.get("comments_count", 0),
                    ph.get("is_avatar", False), ph.get("is_tagged", False),
                )
            except Exception:
                pass  # фото без URL и т.п. — не критично
        return row

    def add_favorite(self, user_vk_id, profile):
        user = self.get_or_create_user(user_vk_id)
        cand = self._save_candidate(profile)
        self._db.add_to_favorites(user["id"], cand["id"])

    def add_blacklist(self, user_vk_id, profile):
        user = self.get_or_create_user(user_vk_id)
        cand = self._save_candidate(profile)
        self._db.add_to_blacklist(user["id"], cand["id"])

    def mark_viewed(self, user_vk_id, profile):
        user = self.get_or_create_user(user_vk_id)
        cand = self._save_candidate(profile)
        self._db.mark_viewed(user["id"], cand["id"])

    def get_favorites(self, user_vk_id):
        user = self._db.get_user_by_vk(user_vk_id)
        return self._db.get_favorites(user["id"]) if user else []

    def get_viewed_vk_ids(self, user_vk_id):
        user = self._db.get_user_by_vk(user_vk_id)
        if not user:
            return set()
        vk_ids = set()
        for cand_id in self._db.get_viewed(user["id"]):
            row = self._db.get_candidate(cand_id)
            if row:
                vk_ids.add(row["vk_id"])
        return vk_ids


# ---------------------------------------------------------------------------
# Сборка и запуск
# ---------------------------------------------------------------------------
def build_vk_client():
    token = os.getenv("VK_GROUP_TOKEN")
    if not token:
        raise SystemExit("❌ Нет VK_GROUP_TOKEN — заполни .env по образцу .env.example")
    return VKClientAdapter(VKClient(token=token))


def build_database():
    """Подключаем БД команды; если недоступна — бот всё равно работает."""
    try:
        from src.database.db_manager import Database
        db = Database()
        db.connect()  # упадёт с DatabaseError, если PostgreSQL недоступен
        return DatabaseAdapter(db)
    except Exception as exc:
        print("⚠️ БД недоступна, работаем без сохранений:", exc)
        return None


def get_group_id(vk):
    if vk.group_id:
        return vk.group_id
    short = os.getenv("VK_GROUP_SHORT_NAME", "club240686337")
    return vk.api.groups.getById(group_id=short)[0]["id"]


def main():
    vk = build_vk_client()
    database = build_database()
    logic = BotLogic(database=database, vk_client=vk, state_manager=StateManager())

    longpoll = VkBotLongPoll(vk.session, get_group_id(vk))
    print("✅ Бот запущен — напиши ему в сообщения группы.")

    while True:
        try:
            for event in longpoll.listen():
                if event.type == VkBotEventType.MESSAGE_NEW:
                    try:
                        logic.handle_event(event)   # ← вся логика бота
                    except Exception as exc:
                        print("❌ Ошибка в обработчике:", exc)
        except Exception as exc:
            print("⚠️ LongPoll переподключается:", exc)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен пользователем.")
