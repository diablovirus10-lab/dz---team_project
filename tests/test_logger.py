"""
Тесты модуля logger (запись логов).

Проверяем простые вещи:
    - get_logger() возвращает логгер;
    - логгер имеет имя модуля;
    - сообщение попадает в файл logs/vkinder.log;
    - папка logs создаётся автоматически;
    - повторный вызов не дублирует обработчики.
"""

import os

from src.utils.logger import LOG_DIR, LOG_FILE, get_logger


def test_get_logger_returns_logger():
    """get_logger должен вернуть объект логгера с нужным именем."""
    logger = get_logger('test_module')

    assert logger is not None
    assert logger.name == 'test_module'


def test_logger_has_handlers():
    """У логгера должны быть обработчики (консоль и/или файл)."""
    logger = get_logger('test_handlers')

    # handlers — список «куда писать лог» (консоль, файл и т.д.)
    assert len(logger.handlers) >= 1


def test_logs_folder_exists():
    """Папка logs должна создаваться автоматически."""
    get_logger('test_folder')  # при первом вызове создаёт папку logs

    assert os.path.isdir(LOG_DIR)


def test_log_writes_to_file():
    """Сообщение logger.info() должно попасть в файл vkinder.log."""
    logger = get_logger('test_file')

    # Уникальный текст, чтобы не перепутать с другими записями
    test_message = 'ТЕСТ_ЛОГЕРА: проверка записи в файл'

    logger.info(test_message)

    # Файл лога должен существовать
    assert os.path.exists(LOG_FILE)

    # Читаем файл и ищем наше сообщение
    with open(LOG_FILE, 'r', encoding='utf-8') as file:
        content = file.read()

    assert test_message in content


def test_log_error_also_writes_to_file():
    """Ошибки (logger.error) тоже должны попадать в файл."""
    logger = get_logger('test_error')

    test_message = 'ТЕСТ_ЛОГЕРА: проверка ошибки'

    logger.error(test_message)

    with open(LOG_FILE, 'r', encoding='utf-8') as file:
        content = file.read()

    assert test_message in content
    assert 'ERROR' in content


def test_same_name_no_duplicate_handlers():
    """
    Если вызвать get_logger('bot') два раза,
    обработчики не должны добавляться повторно.
    """
    name = 'test_no_duplicate'

    logger1 = get_logger(name)
    handlers_count = len(logger1.handlers)

    logger2 = get_logger(name)

    # Это один и тот же объект
    assert logger1 is logger2
    # Количество обработчиков не выросло
    assert len(logger2.handlers) == handlers_count
