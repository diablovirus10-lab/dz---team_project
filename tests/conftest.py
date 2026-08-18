"""Общие фикстуры и фейки для тестов пакета bot."""

import json
import os
import sys
from types import SimpleNamespace

import pytest

# чтобы импорт src.bot работал при запуске pytest из корня проекта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.bot import BotLogic, StateManager  # noqa: E402


class FakeVKClient:
    """Заглушка vk_client: копит отправленные сообщения, отдаёт готовые профили."""

    def __init__(self):
        self.sent = []
        self.profiles = []
        self.search_calls = []

    def send_message(self, user_id, text, keyboard=None, attachments=None):
        self.sent.append({
            "user_id": user_id,
            "text": text,
            "keyboard": keyboard,
            "attachments": attachments,
        })

    def search_users(self, sex, age, city):
        self.search_calls.append({"sex": sex, "age": age, "city": city})
        return list(self.profiles)


class FakeDatabase:
    """Заглушка database: хранит всё в памяти, контракт как у реальной БД."""

    def __init__(self):
        self.users = {}
        self.favorites = []          # (user_vk_id, candidate_vk_id)
        self.blacklist = []
        self.viewed = []
        self._favorite_profiles = {}
        self.viewed_ids = {}

    def get_or_create_user(self, vk_id, **fields):
        self.users.setdefault(vk_id, fields)
        return vk_id

    def add_favorite(self, user_vk_id, profile):
        self.favorites.append((user_vk_id, profile["vk_id"]))
        self._favorite_profiles.setdefault(user_vk_id, []).append(profile)

    def add_blacklist(self, user_vk_id, profile):
        self.blacklist.append((user_vk_id, profile["vk_id"]))

    def mark_viewed_profile(self, user_vk_id, profile):
        """Обёртка для совместимости с bot_logic (принимает профиль вместо candidate_id)."""
        self.viewed.append((user_vk_id, profile["vk_id"]))
        self.viewed_ids.setdefault(user_vk_id, set()).add(profile["vk_id"])

    def get_favorites(self, user_vk_id):
        return list(self._favorite_profiles.get(user_vk_id, []))

    def get_viewed_vk_ids(self, user_vk_id):
        return set(self.viewed_ids.get(user_vk_id, set()))


def make_event(user_id=1, text="", cmd=None):
    """Событие, похожее на событие VkBotLongPoll (MESSAGE_NEW)."""
    payload = json.dumps({"cmd": cmd}) if cmd else None
    message = {"from_id": user_id, "text": text, "payload": payload}
    return SimpleNamespace(obj=SimpleNamespace(message=message, from_id=user_id))


def make_profile(vk_id, first_name="Анна", last_name="Смирнова",
                 age=24, city="Москва", sex=1):
    """Профиль в формате таблицы candidates (schema.sql)."""
    return {
        "vk_id": vk_id,
        "first_name": first_name,
        "last_name": last_name,
        "age": age,
        "city": city,
        "sex": sex,
        "profile_link": f"https://vk.com/id{vk_id}",
        "photos": [
            {
                "photo_url": f"https://example.com/{vk_id}.jpg",
                "photo_id": f"photo{vk_id}_1",
                "likes_count": 100,
                "comments_count": 5,
                "is_avatar": True,
                "is_tagged": False,
            }
        ],
    }


@pytest.fixture
def state_manager():
    return StateManager()


@pytest.fixture
def fake_db():
    return FakeDatabase()


@pytest.fixture
def fake_vk():
    return FakeVKClient()


@pytest.fixture
def logic(fake_db, fake_vk, state_manager):
    return BotLogic(database=fake_db, vk_client=fake_vk, state_manager=state_manager)


@pytest.fixture
def event_factory():
    return make_event


@pytest.fixture
def profile_factory():
    return make_profile