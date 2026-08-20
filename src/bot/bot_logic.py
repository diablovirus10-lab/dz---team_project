"""Core bot logic."""

import json

from src.utils.logger import get_logger

from src.utils.helpers import normalize_city, parse_age as helpers_parse_age

from .keyboards import (
    get_browsing_keyboard,
    get_gender_search_keyboard as get_gender_keyboard,
    get_main_menu_keyboard as get_main_keyboard,
    get_registration_cancel_keyboard,
    get_start_keyboard,
    get_no_results_keyboard,
)
from .message_formatter import format_greeting, format_likes_list, format_profile, format_blacklist_list
from .state_manager import States

logger = get_logger(__name__)


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

        db_user_id = self._ensure_user(user_id)  # регистрация в таблице users
        if db_user_id is None:
            return

        self.state_manager.get_data(user_id).setdefault("_db_user_id", db_user_id)
        cmd = (payload or {}).get("cmd")
        low = text.lower()

        logger.debug(f"[{user_id}] event: text={text!r}, payload={payload}, cmd={cmd}, state={self.state_manager.get_state(user_id)}")

        # глобальные команды — работают из любого состояния
        if cmd == "restart" or low in ("меню"):
            logger.info(f"[{user_id}] restart/menu command")
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.IDLE)
            self._send(user_id, format_greeting(), get_main_keyboard())
            return

        # Команда "меню" по кнопке или тексту
        if cmd == "menu" or low == "меню":
            logger.info(f"[{user_id}] menu command")
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.IDLE)
            self._send(user_id, format_greeting(), get_main_keyboard())
            return

        state = self.state_manager.get_state(user_id)

        if state == States.START_SCREEN:
            self._handle_start_screen(user_id, cmd)
        elif state == States.WAIT_GENDER:
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
    # Начальный экран
    # ------------------------------------------------------------------
    def _handle_start_screen(self, user_id, cmd):
        """Стартовый экран — показываем кнопку 'Начать'."""
        # Если пользователь нажал «Изменить параметры» — начинаем поиск
        if cmd == "search":
            logger.info(f"[{user_id}] changed search params")
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.WAIT_GENDER)
            self._send(
                user_id,
                "Кого будем искать? Выбери пол 👇",
                get_gender_keyboard())
            return

        # Если пользователь нажал «Искать дальше» — ищем без фильтрации
        if cmd == "search_broad":
            logger.info(f"[{user_id}] broad search")
            self.state_manager.update_data(user_id, search_broad=True)
            self.state_manager.set_state(user_id, States.BROWSING)
            self._start_search(user_id)
            return

        # Если пользователь уже нажал «Начать» — показываем меню
        if cmd == "start" or cmd == "restart":
            logger.info(f"[{user_id}] started from start screen")
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.IDLE)
            self._send(user_id, format_greeting(), get_main_keyboard())
            return

        # Если пользователь нажал «В меню» — показываем главное меню
        if cmd == "back_to_main":
            logger.info(f"[{user_id}] back to main menu")
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.IDLE)
            self._send(user_id, format_greeting(), get_main_keyboard())
            return

        # Иначе оставляем ту же клавиатуру
        self._send(user_id, format_greeting(), get_start_keyboard())

    # ------------------------------------------------------------------
    # Обработчики состояний
    # ------------------------------------------------------------------
    def _handle_idle(self, user_id, cmd):
        """Главное меню — пользователь может перейти в поиск."""
        if cmd == "search":
            self.state_manager.reset(user_id)
            self.state_manager.set_state(user_id, States.WAIT_GENDER)
            self._send(
                user_id,
                "Кого будем искать? Выбери пол 👇",
                get_gender_keyboard())
            return

        if cmd == "favorites":
            db_user_id = self._get_db_user_id(user_id)
            liked = self._db_call("get_favorites", user_id) or []
            self._send(user_id, format_likes_list(liked), get_main_keyboard())
            return

        if cmd == "blacklist":
            db_user_id = self._get_db_user_id(user_id)
            blocked = self._db_call("get_blacklist_vk", user_id) or []
            self._send(user_id, format_blacklist_list(blocked), get_main_keyboard())
            return

        # Старый cmd "likes" для обратной совместимости
        if cmd == "likes":
            db_user_id = self._get_db_user_id(user_id)
            liked = self._db_call("get_favorites", db_user_id) or []
            self._send(user_id, format_likes_list(liked), get_main_keyboard())
            return

        # Любой другой ввод или cmd=None — просто показываем меню
        self._send(
            user_id,
            "Выбери действие в меню:",
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
            get_registration_cancel_keyboard())

    def _handle_age(self, user_id, text, cmd):
        """Шаг 2: возраст."""
        if cmd == "menu":
            return self._to_menu(user_id)
        age = helpers_parse_age(text)
        if age is None:
            self._send(
                user_id,
                "Возраст нужно указать числом от 14 до 99 🙂",
                get_registration_cancel_keyboard())
            return
        self.state_manager.update_data(user_id, age=age)
        self.state_manager.set_state(user_id, States.WAIT_CITY)
        self._send(
            user_id,
            "Из какого ты города? Напиши название 👇",
            get_registration_cancel_keyboard())

    def _handle_city(self, user_id, text, cmd):
        """Шаг 3: город, после него — запуск поиска."""
        if cmd == "menu":
            return self._to_menu(user_id)
        city = normalize_city(text)
        if len(city) < 2:
            self._send(
                user_id,
                "Город слишком короткий, введите название заново 👇",
                get_registration_cancel_keyboard())
            return
        self.state_manager.update_data(user_id, city=city)
        self._start_search(user_id)

    def _handle_browsing(self, user_id, cmd):
        """Реакция на показанную анкету."""
        current = self.state_manager.get_data(user_id).get("current")

        if cmd == "like" and current:
            db_user_id = self._get_db_user_id(user_id)
            self._db_call("add_favorite", db_user_id, current)   # favorites
            self._send(user_id, "❤️ Анкета сохранена в лайки!")
            self._show_next_profile(user_id)
        elif cmd == "favorite" and current:
            db_user_id = self._get_db_user_id(user_id)
            self._db_call("add_favorite", db_user_id, current)   # favorites
            self._send(user_id, "💖 Добавлено в избранные!")
            self._show_next_profile(user_id)
        elif cmd == "blacklist" and current:
            db_user_id = self._get_db_user_id(user_id)
            self._db_call("add_blacklist", db_user_id, current)  # blacklist
            self._send(user_id, "🚫 Добавлено в черный список!")
            self._show_next_profile(user_id)
        elif cmd in ("dislike",):
            db_user_id = self._get_db_user_id(user_id)
            if current:
                self._db_call("add_blacklist", db_user_id, current)  # blacklist
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
        elif cmd == "back_to_main" or cmd == "menu":
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
        search_broad = data.get("search_broad", False)

        # Находим ID города перед поиском
        city_name = data.get("city")
        city_id = None
        if city_name and self.vk_client:
            try:
                city_id = self.vk_client.find_city_id(city_name)
            except Exception as exc:
                logger.error(f"City search error for user {user_id}: {exc}", exc_info=True)
                city_id = None

        profiles_result = self._vk_search(data, city_id)

        # profiles_result теперь dict {'items': [...], 'total': ...}
        profiles = profiles_result.get(
            "items", []) if isinstance(
            profiles_result, dict) else []

        # В обычном режиме не показываем уже просмотренных/лайкнутых/заблокированных
        # В режиме "search_broad" показываем ВСЕ анкеты, даже уже просмотренные
        if not search_broad:
            viewed = self._db_call("get_viewed_vk_ids", user_id) or set()
            profiles = [p for p in profiles if p.get("vk_id") not in viewed]

        if not profiles:
            # Сохраняем данные поиска (sex, age, city), чтобы не потерять их
            self.state_manager.update_data(user_id, search_broad=False)
            self.state_manager.set_state(user_id, States.START_SCREEN)
            self._send(
                user_id,
                "Никого не нашёл 😔 Даже среди всех анкет. Попробуйте изменить параметры.",
                get_no_results_keyboard())
            return

        self.state_manager.update_data(user_id, queue=list(profiles))
        self.state_manager.set_state(user_id, States.BROWSING)
        # Сбрасываем флаг расширенного поиска
        if search_broad:
            self.state_manager.update_data(user_id, search_broad=False)
        self._show_next_profile(user_id)

    def _show_next_profile(self, user_id):
        data = self.state_manager.get_data(user_id)
        queue = data.get("queue") or []
        if not queue:
            self._to_menu(user_id, "Анкеты закончились 🙂")
            return

        current = queue.pop(0)
        self.state_manager.update_data(user_id, queue=queue, current=current)
        db_user_id = self._get_db_user_id(user_id)
        self._db_call("mark_viewed_profile", db_user_id, current)

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
        self.state_manager.set_state(user_id, States.START_SCREEN)
        self._send(
            user_id,
            text or "Диалог очищен. Нажмите кнопку ниже 👇",
            get_start_keyboard())

    @staticmethod
    def _extract_event(event):
        """Достать (user_id, text, payload) из события LongPoll.

        Поддерживает два формата:
        1. Новый (из main.py): event.user_id, event.text, event.payload
        2. Старый (напрямую от vk_api): event.message, event.raw, event.obj
        """
        # 1. Если main.py уже распарсил — используем готовые атрибуты
        if hasattr(event, 'user_id'):
            text = (getattr(event, 'text', '') or '').strip()[:2000]
            payload = getattr(event, 'payload', None)
            # Парсим payload из строки JSON если нужно
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except (json.JSONDecodeError, ValueError):
                    payload = {}
            elif payload is None:
                payload = {}
            return int(event.user_id), text, payload

        # 2. fallback — парсим как раньше (для совместимости)
        message = None

        if hasattr(event, 'message') and isinstance(event.message, dict):
            message = event.message
        elif hasattr(event, 'obj') and isinstance(event.obj, dict):
            message = event.obj.get('message', {}) or event.obj
        elif hasattr(event, 'raw') and isinstance(event.raw, dict):
            message = event.raw.get('object', {}).get('message', {}) or {}
        else:
            message = {}

        user_id = message.get('from_id') or message.get('user_id')
        text = (message.get('text') or '').strip()
        payload = message.get('payload')

        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except ValueError:
                payload = None

        return user_id, text, payload

    def _ensure_user(self, vk_id):
        """Создать или получить пользователя, вернуть database user_id."""
        user = self._db_call("get_or_create_user", vk_id)
        if user:
            return user.get("id") or user.get("vk_id")
        return None

    def _get_db_user_id(self, vk_id):
        """Получить database user_id, использовать сохранённый или запросить."""
        data = self.state_manager.get_data(vk_id)
        db_user_id = data.get("_db_user_id")
        if db_user_id:
            return db_user_id
        user = self._db_call("get_or_create_user", vk_id)
        if user:
            data["_db_user_id"] = user.get("id") or user.get("vk_id")
            return data["_db_user_id"]
        return vk_id

    def _db_call(self, method, *args):
        """Безопасный вызов метода database (модуль может быть ещё не готов)."""
        if self.database is None:
            return None
        try:
            return getattr(self.database, method)(*args)
        except Exception as exc:
            logger.error(f"DB error ({method}): {exc}", exc_info=True)
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
            logger.error(f"VK search error: {exc}", exc_info=True)
            return {'items': [], 'total': 0}

    def _send(self, user_id, text, keyboard=None, attachments=None):
        if self.vk_client is None:
            logger.debug(f"[{user_id}] {text}")  # дебаг-режим без ВК
            return
        self.vk_client.send_message(
            user_id,
            text,
            keyboard=keyboard,
            attachments=attachments)
