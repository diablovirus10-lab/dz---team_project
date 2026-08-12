"""Core bot logic."""

import json

from .keyboards import (
    get_browsing_keyboard,
    get_cancel_keyboard,
    get_gender_keyboard,
    get_main_keyboard,
)
from .message_formatter import format_greeting, format_likes_list, format_profile
from .state_manager import States


class BotLogic:
    """Маршрутизатор диалога: проводит пользователя по состояниям FSM.

    Контракт с модулями команды (реализации — в src/database и src/vk_api):
      vk_client:
        - send_message(user_id, text, keyboard=None, attachments=None)
        - search_users(sex, age, city) -> list[dict]   (профили в формате candidates)
      database:
        - get_or_create_user(vk_id) -> int
        - add_favorite(user_vk_id, profile)      # таблица favorites
        - add_blacklist(user_vk_id, profile)     # таблица blacklist
        - mark_viewed(user_vk_id, profile)       # таблица viewed_candidates
        - get_favorites(user_vk_id) -> list[dict]
        - get_viewed_vk_ids(user_vk_id) -> set[int]
    """

    def __init__(self, database, vk_client, state_manager):
        self.database = database
        self.vk_client = vk_client
        self.state_manager = state_manager

    # ------------------------------------------------------------------
    # Входная точка
    # ------------------------------------------------------------------
    def handle_event(self, event):
        """Обработать одно входящее событие LongPoll."""
        user_id, text, payload = self._extract_event(event)
        if user_id is None or user_id < 0:  # игнорируем чаты и сообщества
            return

        self._ensure_user(user_id)  # регистрация в таблице users

        cmd = (payload or {}).get("cmd")
        low = text.lower()

        # глобальные команды — работают из любого состояния
        if cmd == "start" or low in ("начать", "start", "меню"):
            self.state_manager.reset(user_id)
            self._send(user_id, format_greeting(), get_main_keyboard())
            return

        state = self.state_manager.get_state(user_id)

        if state == States.WAIT_GENDER:
            self._handle_gender(user_id, low, cmd)
        elif state == States.WAIT_AGE:
            self._handle_age(user_id, text, cmd)
        elif state == States.WAIT_CITY:
            self._handle_city(user_id, text, cmd)
        elif state == States.BROWSING:
            self._handle_browsing(user_id, cmd)
        else:
            self._handle_idle(user_id, cmd)

    # ------------------------------------------------------------------
    # Обработчики состояний
    # ------------------------------------------------------------------
    def _handle_idle(self, user_id, cmd):
        """Главное меню."""
        if cmd == "search":
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.WAIT_GENDER)
            self._send(user_id, "Кого будем искать? Выбери пол 👇", get_gender_keyboard())
        elif cmd == "likes":
            liked = self._db_call("get_favorites", user_id) or []
            self._send(user_id, format_likes_list(liked), get_main_keyboard())
        else:
            self._send(user_id, "Не понял 🙈 Выбери действие в меню:", get_main_keyboard())

    def _handle_gender(self, user_id, low, cmd):
        """Шаг 1: пол искомого (sex как в ВК: 1 — жен, 2 — муж)."""
        if cmd == "gender_f" or "девуш" in low:
            sex = 1
        elif cmd == "gender_m" or "парн" in low or "муж" in low:
            sex = 2
        else:
            self._send(user_id, "Пожалуйста, выбери вариант кнопкой 👇", get_gender_keyboard())
            return
        self.state_manager.update_data(user_id, sex=sex)
        self.state_manager.set_state(user_id, States.WAIT_AGE)
        self._send(user_id, "Теперь укажи возраст (числом) 👇", get_cancel_keyboard())

    def _handle_age(self, user_id, text, cmd):
        """Шаг 2: возраст."""
        if cmd == "menu":
            return self._to_menu(user_id)
        age = self._parse_age(text)
        if age is None:
            self._send(user_id, "Возраст нужно указать числом от 14 до 99 🙂", get_cancel_keyboard())
            return
        self.state_manager.update_data(user_id, age=age)
        self.state_manager.set_state(user_id, States.WAIT_CITY)
        self._send(user_id, "Из какого ты города? Напиши название 👇", get_cancel_keyboard())

    def _handle_city(self, user_id, text, cmd):
        """Шаг 3: город, после него — запуск поиска."""
        if cmd == "menu":
            return self._to_menu(user_id)
        self.state_manager.update_data(user_id, city=text.strip())
        self._start_search(user_id)

    def _handle_browsing(self, user_id, cmd):
        """Реакция на показанную анкету."""
        current = self.state_manager.get_data(user_id).get("current")

        if cmd == "like" and current:
            self._db_call("add_favorite", user_id, current)   # favorites
            self._send(user_id, "❤️ Анкета сохранена в лайки!")
            self._show_next_profile(user_id)
        elif cmd in ("dislike", "next"):
            if cmd == "dislike" and current:
                self._db_call("add_blacklist", user_id, current)  # blacklist
            self._show_next_profile(user_id)
        elif cmd == "menu":
            self._to_menu(user_id)
        else:
            self._send(user_id, "Используй кнопки под сообщением 👇", get_browsing_keyboard())

    # ------------------------------------------------------------------
    # Поиск и выдача анкет
    # ------------------------------------------------------------------
    def _start_search(self, user_id):
        data = self.state_manager.get_data(user_id)
        profiles = self._vk_search(data)

        # не показываем уже просмотренных (viewed_candidates)
        viewed = self._db_call("get_viewed_vk_ids", user_id) or set()
        profiles = [p for p in profiles if p.get("vk_id") not in viewed]

        if not profiles:
            self._to_menu(user_id, "Никого не нашёл 😔 Попробуй другие параметры.")
            return

        self.state_manager.update_data(user_id, queue=list(profiles))
        self.state_manager.set_state(user_id, States.BROWSING)
        self._show_next_profile(user_id)

    def _show_next_profile(self, user_id):
        data = self.state_manager.get_data(user_id)
        queue = data.get("queue") or []
        if not queue:
            self._to_menu(user_id, "Анкеты закончились 🙂")
            return

        current = queue.pop(0)
        self.state_manager.update_data(user_id, queue=queue, current=current)
        self._db_call("mark_viewed", user_id, current)

        # до 3 фото — вложениями (photo_id хранится в формате "photo<owner>_<id>")
        attachments = [ph["photo_id"] for ph in current.get("photos", [])[:3] if ph.get("photo_id")]
        self._send(user_id, format_profile(current), get_browsing_keyboard(), attachments=attachments)

    # ------------------------------------------------------------------
    # Хелперы и интеграция с чужими модулями
    # ------------------------------------------------------------------
    def _to_menu(self, user_id, text=None):
        self.state_manager.reset(user_id)
        self._send(user_id, text or "Главное меню 👇", get_main_keyboard())

    @staticmethod
    def _parse_age(text):
        digits = "".join(ch for ch in text if ch.isdigit())
        if not digits:
            return None
        age = int(digits)
        return age if 14 <= age <= 99 else None

    @staticmethod
    def _extract_event(event):
        """Достать (user_id, text, payload) из события LongPoll."""
        message = getattr(event.obj, "message", None) or getattr(event, "message", None) or {}
        user_id = message.get("from_id") or getattr(event.obj, "from_id", None)
        text = (message.get("text") or "").strip()
        payload = message.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError:
                payload = None
        return user_id, text, payload

    def _ensure_user(self, user_id):
        self._db_call("get_or_create_user", user_id)

    def _db_call(self, method, *args):
        """Безопасный вызов метода database (модуль может быть ещё не готов)."""
        if self.database is None:
            return None
        try:
            return getattr(self.database, method)(*args)
        except Exception as exc:
            print(f"DB error ({method}):", exc)
            return None

    def _vk_search(self, params):
        """Безопасный вызов поиска VK."""
        if self.vk_client is None:
            return []
        try:
            return self.vk_client.search_users(
                sex=params.get("sex"),
                age=params.get("age"),
                city=params.get("city"),
            ) or []
        except Exception as exc:
            print("VK search error:", exc)
            return []

    def _send(self, user_id, text, keyboard=None, attachments=None):
        if self.vk_client is None:
            print(f"[{user_id}] {text}")  # дебаг-режим без ВК
            return
        self.vk_client.send_message(user_id, text, keyboard=keyboard, attachments=attachments)