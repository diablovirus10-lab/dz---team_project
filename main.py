"""Точка входа в бота."""
import json
import os
import time
import requests
from dotenv import load_dotenv
from collections import defaultdict

# Загружаем переменные окружения из .env один раз при старте
load_dotenv()

import vk_api
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from src.bot.bot_logic import BotLogic
from src.database.db_manager import Database
from src.vk_api_bot.vk_client import VKClient
from src.bot.state_manager import StateManager
from src.utils.logger import get_logger
from src.database.config import LoggingConfig

logger = get_logger(__name__)


# ============================================================
# Rate limiting — защита от спама
# ============================================================

_user_ratelimit = defaultdict(list)
RATE_LIMIT_WINDOW = 2.0   # окно в секундах
RATE_LIMIT_MAX = 5        # макс. сообщений за окно


def _check_ratelimit(user_id: int) -> bool:
    """Возвращает True, если пользователь может отправлять сообщение."""
    now = time.time()
    # Очищаем старые записи
    _user_ratelimit[user_id] = [
        t for t in _user_ratelimit[user_id] if now - t < RATE_LIMIT_WINDOW
    ]
    if len(_user_ratelimit[user_id]) >= RATE_LIMIT_MAX:
        logger.warning(f"[{user_id}] Превышен rate limit ({RATE_LIMIT_MAX}/{RATE_LIMIT_WINDOW}s)")
        return False
    _user_ratelimit[user_id].append(now)
    return True


def create_bot_instance():
    vk_client = VKClient()
    database = Database()
    state_manager = StateManager()

    bot = BotLogic(database=database, vk_client=vk_client, state_manager=state_manager)
    return bot


# Формат LongPoll-события VK (список):
# [group_id, event_id, type, from_id, timestamp, text/payload, ...]

# Дедупликация: храним последние события по ключу (user_id + timestamp)
_seen_events: dict[str, float] = {}
SEEN_WINDOW = 5.0  # игнорировать дубликаты в течение 5 сек


def _get_event_key(event) -> str:
    """Уникальный ключ события для дедупликации.

    Использует (from_id, timestamp) из raw-данных VK LongPoll.
    timestamp уникален для каждого события, даже для callback-кнопок.
    """
    raw = getattr(event, 'raw', None)

    # Новый формат vk_api: raw — список [group_id, event_id, type, from_id, timestamp, ...]
    if isinstance(raw, list) and len(raw) >= 5:
        from_id = raw[3]        # from_id
        timestamp = raw[4]      # timestamp
        return f"{from_id}:{timestamp}"

    # Старый формат
    if hasattr(event, 'message') and isinstance(event.message, dict):
        from_id = event.message.get('from_id') or event.message.get('user_id')
        timestamp = event.message.get('timestamp', 0)
        if from_id:
            return f"{from_id}:{timestamp}"

    return None


def _is_duplicate(key: str) -> bool:
    """Проверить, был ли ключ события недавно."""
    if not key:
        return False
    now = time.time()
    # Очищаем старые ключи
    _to_remove = [k for k, t in _seen_events.items() if now - t > SEEN_WINDOW]
    for k in _to_remove:
        del _seen_events[k]
    return key in _seen_events


def _mark_seen(key: str):
    _seen_events[key] = time.time()


def _parse_vk_event(event):
    """Извлечь (user_id, text, payload, timestamp, is_mine) из события LongPoll VK."""
    raw = getattr(event, 'raw', None)

    # ---------- 1. new vk_api (1.0+): raw — список ----------
    if isinstance(raw, list) and len(raw) >= 7:
        from_id = raw[3]                          # <-- ID отправителя
        timestamp = raw[4]                        # timestamp события
        text_or_button = raw[5]                   # текст или название кнопки
        payload_dict = raw[6] if isinstance(raw[6], dict) else {}   # {'payload': '...'}
        is_mine = raw[7] if len(raw) > 7 else False  # флаг: отправлено ли ботом

        # payload может быть вложен глубже: {'payload': '{"cmd":"search"}'}
        raw_payload = payload_dict.get('payload') if isinstance(payload_dict, dict) else None
        if isinstance(raw_payload, str):
            # Ограничиваем размер payload (макс 4KB)
            if len(raw_payload) > 4096:
                logger.warning(f"Payload too large ({len(raw_payload)} bytes), skipping")
                payload = {}
            else:
                try:
                    payload = json.loads(raw_payload)
                except json.JSONDecodeError:
                    payload = {}
        else:
            payload = raw_payload or {}

        text = text_or_button if isinstance(text_or_button, str) else ''
        # Валидируем from_id
        try:
            return int(from_id), text, payload, timestamp, is_mine
        except (ValueError, TypeError):
            logger.warning(f"Invalid from_id: {from_id}")
            return None, text, payload, timestamp, False

    # ---------- 2. старый/альтернативный формат ----------
    message_data = {}

    if hasattr(event, 'message') and isinstance(event.message, dict):
        message_data = event.message
    elif hasattr(event, 'obj') and isinstance(event.obj, dict):
        message_data = event.obj
    elif hasattr(event, 'object'):
        obj = event.object
        if isinstance(obj, dict):
            message_data = obj
        elif hasattr(obj, 'message') and isinstance(obj.message, dict):
            message_data = obj.message

    from_id = message_data.get('from_id') or message_data.get('user_id') or message_data.get('id')
    timestamp = message_data.get('timestamp', 0)
    text = message_data.get('text', '')
    raw_payload = message_data.get('payload', {})
    is_mine = message_data.get('is_mine', False)  # флаг: отправлено ли ботом

    if isinstance(raw_payload, str):
        # Ограничиваем размер payload
        if len(raw_payload) > 4096:
            logger.warning(f"Payload too large ({len(raw_payload)} bytes), skipping")
            payload = {}
        else:
            try:
                payload = json.loads(raw_payload)
            except json.JSONDecodeError:
                payload = {}
    else:
        payload = raw_payload or {}

    # Валидируем from_id
    if from_id is not None:
        try:
            return int(from_id), text, payload, timestamp, is_mine
        except (ValueError, TypeError):
            logger.warning(f"Invalid from_id: {from_id}")
            return None, text, payload, timestamp, False

    return None, text, payload, timestamp, is_mine


def main():
    logger.info("Запуск VK бота...")

    # Убеждаемся, что папка для логов существует
    LoggingConfig().ensure_log_directory()

    # Максимальное количество попыток переподключения при ошибках сети
    MAX_RETRY_ATTEMPTS = 5
    retry_count = 0

    while retry_count < MAX_RETRY_ATTEMPTS:
        try:
            bot = create_bot_instance()
            logger.info("Бот успешно инициализирован")

            vk_session = VkApi(token=os.getenv('VK_GROUP_TOKEN'))
            longpoll = VkLongPoll(vk_session, group_id=int(os.getenv('VK_GROUP_ID', '0')))

            logger.info("LongPoll подключен. Ожидание событий...")
            retry_count = 0  # сброс счётчика при успешном подключении

            # Используем longpoll.listen() — generator, возвращает события по мере поступления
            while True:
                for event in longpoll.listen():
                    try:
                        event_type = getattr(event, 'type', '')
                        # Разрешаем обычные сообщения и события от кнопок
                        allowed_types = (
                            VkEventType.MESSAGE_NEW,
                            'message_new',
                            'message_new.MessageNew',
                            'message_new.Callback',
                            'message_new.CallbackKeyboard',
                            'message_new.PrimaryKeyboard',
                        )
                        if event_type not in allowed_types:
                            continue

                        user_id, text, payload, timestamp, is_mine = _parse_vk_event(event)

                        # Пропускаем heartbeat VK — пустые события без нагрузки
                        if not (text or '').strip() and not payload:
                            logger.debug(f"Пропущен heartbeat от {user_id}")
                            continue

                        if user_id is None:
                            logger.warning(f"Не удалось извлечь user_id из события")
                            continue

                        # Пропускаем сообщения, отправленные самим ботом
                        if is_mine:
                            logger.debug(f"Пропущено собственное сообщение от {user_id}")
                            continue

                        # Rate limiting — защита от спама
                        if not _check_ratelimit(user_id):
                            continue

                        # Дедупликация: не обрабатывать одно и то же событие повторно
                        key = _get_event_key(event)
                        if _is_duplicate(key):
                            logger.debug(f"Пропущен дубликат события: key={key}")
                            continue
                        _mark_seen(key)

                        logger.debug(f"Получено сообщение от {user_id}: text={text!r}, payload={payload}")

                        # Передаём event как раньше — bot_logic извлекает данные сам
                        event.user_id = user_id
                        event.text = text
                        event.payload = payload
                        bot.handle_event(event)

                    except Exception as e:
                        logger.error(f"Ошибка при обработке события: {e}", exc_info=True)

        # ---------- Обработка ошибок сети / SSL ----------
        except requests.exceptions.SSLError as e:
            retry_count += 1
            logger.warning(f"SSL-ошибка (попытка {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
            logger.info(f"Переподключение через 10 секунд...")
            time.sleep(10)

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            retry_count += 1
            logger.warning(f"Ошибка соединения (попытка {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
            logger.info(f"Переподключение через 10 секунд...")
            time.sleep(10)

        except vk_api.exceptions.ApiError as e:
            retry_count += 1
            logger.warning(f"Ошибка VK API (попытка {retry_count}/{MAX_RETRY_ATTEMPTS}): {e}")
            logger.info(f"Переподключение через 10 секунд...")
            time.sleep(10)

        except KeyboardInterrupt:
            logger.info("Бот остановлен пользователем")
            break

        if retry_count >= MAX_RETRY_ATTEMPTS:
            logger.error(f"Достигнуто максимальное количество попыток ({MAX_RETRY_ATTEMPTS}). Завершение.")
            break


if __name__ == '__main__':
    main()
