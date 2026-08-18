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
        - toggle_photo_like(user_id, photo_db_id, candidate_id) -> bool|None  # таблица photo_likes
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
            self._send(
                user_id,
                "Кого будем искать? Выбери пол 👇",
                get_gender_keyboard())
        elif cmd == "likes":
            liked = self._db_call("get_favorites", user_id) or []
            self._send(user_id, format_likes_list(liked), get_main_keyboard())
        else:
            self._send(
                user_id,
                "Не понял 🙈 Выбери действие в меню:",
                get_main_keyboard())

    def _handle_gender(self, user_id, low, cmd):
        """Шаг 1: пол искомого (sex как в ВК: 1 — жен, 2 — муж)."""
        if cmd == "gender_f" or "девуш" in low:
            sex = 1
        elif cmd == "gender_m" or "парн" in low or "муж" in low:
            sex = 2
        else:
            self._send(
                user_id,
                "Пожалуйста, выбери вариант кнопкой 👇",
                get_gender_keyboard())
            return
        self.state_manager.update_data(user_id, sex=sex)
        self.state_manager.set_state(user_id, States.WAIT_AGE)
        self._send(
            user_id,
            "Теперь укажи возраст (числом) 👇",
            get_cancel_keyboard())

    def _handle_age(self, user_id, text, cmd):
        """Шаг 2: возраст."""
        if cmd == "menu":
            return self._to_menu(user_id)
        age = self._parse_age(text)
        if age is None:
            self._send(
                user_id,
                "Возраст нужно указать числом от 14 до 99 🙂",
                get_cancel_keyboard())
            return
        self.state_manager.update_data(user_id, age=age)
        self.state_manager.set_state(user_id, States.WAIT_CITY)
        self._send(
            user_id,
            "Из какого ты города? Напиши название 👇",
            get_cancel_keyboard())

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
        elif cmd == "photo_like":
            # Лайк конкретной фотографии
            photo_data = self.state_manager.get_data(
                user_id).get("photo_like_data")
            if photo_data and current:
                photo_id = photo_data.get("photo_id")
                photo_db_id = photo_data.get("photo_db_id")
                candidate_id = current.get("id")
                if photo_id and photo_db_id and candidate_id:
                    result = self._db_call(
                        "toggle_photo_like", user_id, photo_db_id, candidate_id)
                    if result is True:
                        self._send(user_id, "❤️ Лайк поставлен!")
                    elif result is False:
                        self._send(user_id, "💔 Лайк убран.")
                    else:
                        self._send(user_id, "⚠️ Не удалось изменить лайк.")
                else:
                    self._send(user_id, "⚠️ Данные фотографии не найдены.")
            else:
                self._send(user_id, "⚠️ Нельзя лайкнуть фото: нет данных.")
        elif cmd == "menu":
            self._to_menu(user_id)
        else:
            self._send(
                user_id,
                "Используй кнопки под сообщением 👇",
                get_browsing_keyboard())

    # ------------------------------------------------------------------
    # Поиск и выдача анкет
    # ------------------------------------------------------------------
    def _start_search(self, user_id):
        data = self.state_manager.get_data(user_id)

        # Находим ID города перед поиском
        city_name = data.get("city")
        city_id = None
        if city_name and self.vk_client:
            try:
                city_id = self.vk_client.find_city_id(city_name)
            except Exception as exc:
                print(f"City search error: {exc}")
                city_id = None

        profiles_result = self._vk_search(data, city_id)

        # profiles_result теперь dict {'items': [...], 'total': ...}
        profiles = profiles_result.get(
            "items", []) if isinstance(
            profiles_result, dict) else []

        # не показываем уже просмотренных (viewed_candidates)
        viewed = self._db_call("get_viewed_vk_ids", user_id) or set()
        profiles = [p for p in profiles if p.get("vk_id") not in viewed]

        if not profiles:
            self._to_menu(
                user_id, "Никого не нашёл 😔 Попробуй другие параметры.")
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
        self._db_call("mark_viewed_profile", user_id, current)

        # до 3 фото — вложениями (photo_id хранится в формате
        # "photo<owner>_<id>")
        photos = current.get("photos", [])[:3]
        attachments = [ph["photo_id"] for ph in photos if ph.get("photo_id")]

        # Сохраняем данные о фотографиях для возможности лайка
        photo_like_data = []
        for idx, ph in enumerate(photos):
            if ph.get("photo_id") and ph.get("id"):
                photo_like_data.append({
                    "photo_id": ph["photo_id"],
                    "photo_db_id": ph["id"],
                    "index": idx
                })
        self.state_manager.update_data(
            user_id, photo_like_data=photo_like_data)

        self._send(
            user_id,
            format_profile(current),
            get_browsing_keyboard(),
            attachments=attachments)

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
        # В новых версиях vk_api данные сообщения находятся в event.message
        # В старых версиях - в event.obj
        message = getattr(event, "message", None) or getattr(
            event, "obj", {}).get("message", {}) or {}
        user_id = message.get("from_id") or getattr(getattr(event, "obj", None), "from_id", None)
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

    def _vk_search(self, params, city_id=None):
        """Безопасный вызов поиска VK.

        Args:
            params: dict с параметрами sex, age, city (название)
            city_id: найденный ID города (или None)

        Returns:
            dict от VKClient: {'items': [...], 'total': ...}
        """
        if self.vk_client is None:
            return {'items': [], 'total': 0}
        try:
            # age в params хранится как одно число, используем как age_from и
            # age_to
            age = params.get("age")
            if age is None:
                return {'items': [], 'total': 0}

            return self.vk_client.search_users(
                sex=params.get("sex"),
                age_from=age,
                age_to=age,
                city_id=city_id,
                offset=0,
                count=20,
            )
        except Exception as exc:
            print("VK search error:", exc)
            return {'items': [], 'total': 0}

    def _send(self, user_id, text, keyboard=None, attachments=None):
        if self.vk_client is None:
            print(f"[{user_id}] {text}")  # дебаг-режим без ВК
            return
        self.vk_client.send_message(
            user_id,
            text,
            keyboard=keyboard,
            attachments=attachments)
