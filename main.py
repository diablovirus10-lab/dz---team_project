"""Точка входа в бота."""
import os
import logging
from vk_api import VkApi
from vk_api.longpoll import VkLongPoll, VkEventType

from src.bot.bot_logic import BotLogic
from src.database.db_manager import Database
from src.vk_api_bot.vk_client import VKClient
from src.bot.state_manager import StateManager
from src.utils.logger import get_logger

# Настройка логгера
logger = get_logger(__name__)


def create_bot_instance():
    """Создать и настроить экземпляр бота."""
    # Инициализация клиентов
    vk_client = VKClient()
    database = Database()
    state_manager = StateManager()
    
    bot = BotLogic(database=database, vk_client=vk_client, state_manager=state_manager)
    return bot


def main():
    """Основная функция запуска бота."""
    logger.info("Запуск VK бота...")
    
    try:
        # Инициализация бота
        bot = create_bot_instance()
        logger.info("Бот успешно инициализирован")
        
        # Подключение к VK API через LongPoll
        vk_session = VkApi(token=os.getenv('VK_GROUP_TOKEN'))
        longpoll = VkLongPoll(vk_session, group_id=int(os.getenv('VK_GROUP_ID', '0')))
        
        logger.info("LongPoll подключен. Ожидание событий...")
        
        # Основной цикл обработки событий
        for event in longpoll.listen():
            try:
                if event.type == VkEventType.MESSAGE_NEW:
                    logger.debug(f"Получено новое сообщение от {event.obj.get('from_id')}")
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
