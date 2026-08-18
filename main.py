"""Точка входа в бота."""
import os
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from src.bot.bot_logic import BotLogic
from src.database.db_manager import Database
from src.vk_api_bot.vk_client import VKClient
from src.bot.state_manager import StateManager
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_bot_instance():
    vk_client = VKClient()
    database = Database()
    state_manager = StateManager()

    bot = BotLogic(database=database, vk_client=vk_client, state_manager=state_manager)
    return bot


def main():
    logger.info("Запуск VK бота...")

    try:
        bot = create_bot_instance()
        logger.info("Бот успешно инициализирован")

        vk_session = VkApi(token=os.getenv('VK_GROUP_TOKEN'))
        longpoll = VkLongPoll(vk_session, group_id=int(os.getenv('VK_GROUP_ID', '0')))

        logger.info("LongPoll подключен. Ожидание событий...")

        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    # В новых версиях vk_api структура события может отличаться
                    # Пробуем разные варианты получения данных сообщения
                    if hasattr(event, 'message') and isinstance(event.message, dict):
                        message_data = event.message
                    elif hasattr(event, 'obj') and isinstance(event.obj, dict):
                        message_data = event.obj
                    elif hasattr(event, 'message'):
                        # Если message не dict, пробуем получить данные через raw
                        message_data = event.raw.get('object', {}) if hasattr(event, 'raw') else {}
                    else:
                        logger.warning(f"Неизвестная структура события: {type(event)}")
                        continue
                    
                    from_id = message_data.get('from_id') or message_data.get('user_id')
                    logger.debug(f"Получено новое сообщение от {from_id}")
                    bot.handle_event(event)

            except Exception as e:
                logger.error(f"Ошибка при обработке события: {e}", exc_info=True)

    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
