"""
Модуль для записи логов (журнала событий программы).

Зачем нужен лог:
    - видеть, что происходит в боте, пока он работает;
    - находить ошибки, когда что-то сломалось;
    - не использовать print() — print не пишет время и уровень ошибки.

Как пользоваться в других файлах:
    from src.utils.logger import get_logger

    logger = get_logger('bot')          # имя модуля — любое понятное
    logger.info('Бот запущен')          # обычное сообщение
    logger.warning('Странный ввод')     # предупреждение
    logger.error('Не удалось подключиться к БД')  # ошибка
"""

import logging
import os

# Путь к корню проекта (папка, где лежат main.py, src/, tests/)
# __file__ — это путь к текущему файлу logger.py
# поднимаемся на два уровня вверх: utils -> src -> корень проекта
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Папка для файлов логов (создаётся автоматически при первом запуске)
LOG_DIR = os.path.join(BASE_DIR, 'logs')

# Имя файла, куда сохраняются все записи
LOG_FILE = os.path.join(LOG_DIR, 'vkinder.log')

# Как выглядит строка в логе:
# 2026-08-12 15:30:00 | INFO | bot | Пользователь начал поиск
LOG_FORMAT = '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def get_logger(name):
    """
    Создаёт логгер и возвращает его.

    Параметры:
        name (str) — имя модуля, например 'bot', 'database', 'vk_api'.
                     По нему видно, из какой части программы пришло сообщение.

    Возвращает:
        объект logging.Logger — через него вызываем .info(), .error() и т.д.
    """
    # Получаем логгер с нужным именем (или создаём новый)
    logger = logging.getLogger(name)

    # Если обработчики уже добавлены — не настраиваем повторно,
    # иначе одно сообщение будет дублироваться много раз
    if logger.handlers:
        return logger

    # Уровень DEBUG — пишем всё подробно в файл;
    # в консоль пойдут только INFO и выше (см. ниже)
    logger.setLevel(logging.DEBUG)

    # Форматтер — «шаблон» строки лога
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # --- Обработчик 1: вывод в консоль (терминал) ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)   # в терминал — только важное
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # --- Обработчик 2: запись в файл logs/vkinder.log ---
    os.makedirs(LOG_DIR, exist_ok=True)    # создаём папку logs, если её нет
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)   # в файл — всё, включая отладку
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
