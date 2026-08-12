"""
Пакет utils — общие вспомогательные инструменты для всего проекта.

Что здесь есть:
    get_logger          — запись логов (logger.py)
    normalize_text      — убрать пробелы (helpers.py)
    parse_age           — достать возраст из текста (helpers.py)
    normalize_city      — привести город к нормальному виду (helpers.py)
    build_profile_link  — ссылка на профиль VK (helpers.py)
    validate_age        — проверить возраст (validators.py)
    validate_sex        — проверить пол (validators.py)
    validate_city       — проверить город (validators.py)
    validate_user_data  — проверить все данные сразу (validators.py)

Пример импорта в другом файле:
    from src.utils import get_logger, validate_age, parse_age
"""

from .logger import get_logger
from .helpers import normalize_text, parse_age, normalize_city, build_profile_link
from .validators import validate_age, validate_sex, validate_city, validate_user_data

__all__ = [
    # logger
    'get_logger',
    # helpers
    'normalize_text',
    'parse_age',
    'normalize_city',
    'build_profile_link',
    # validators
    'validate_age',
    'validate_sex',
    'validate_city',
    'validate_user_data',
]
