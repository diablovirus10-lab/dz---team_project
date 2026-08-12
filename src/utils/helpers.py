"""
Вспомогательные функции (helpers).

Здесь лежат простые «инструменты», которые готовят данные:
    - убирают лишние пробелы;
    - достают число возраста из текста;
    - собирают ссылку на профиль VK.

Helpers НЕ проверяют, правильные ли данные — это делает validators.py
"""

from .logger import get_logger

# Логгер для этого модуля
logger = get_logger('helpers')


def normalize_text(text):
    """
    Убирает пробелы по краям строки.

    Параметры:
        text — любой текст (может быть None, если пользователь ничего не написал)

    Возвращает:
        строку без пробелов по краям; если text = None, вернёт пустую строку ''
    """
    if text is None:
        logger.debug('normalize_text: получен None, возвращаем пустую строку')
        return ''
    result = text.strip()
    logger.debug(f'normalize_text: "{text}" -> "{result}"')
    return result


def parse_age(text):
    """
    Достаёт число возраста из текста пользователя.

    Примеры:
        "25"       -> 25
        "мне 25"   -> 25
        "  30 лет" -> 30
        "привет"   -> None (числа нет)

    Параметры:
        text — то, что написал пользователь

    Возвращает:
        число (int) или None, если возраст не удалось распознать
    """
    text = normalize_text(text)

    # Собираем только цифры из строки
    digits = ''.join(ch for ch in text if ch.isdigit())

    if not digits:
        logger.warning(f'parse_age: не нашли цифры в тексте "{text}"')
        return None

    age = int(digits)
    logger.info(f'parse_age: из текста "{text}" получили возраст {age}')
    return age


def normalize_city(city):
    """
    Приводит название города к аккуратному виду.

    Примеры:
        "  москва  " -> "Москва"
        "СПБ"        -> "Спб"

    Параметры:
        city — название города от пользователя

    Возвращает:
        строку с заглавной первой буквой
    """
    city = normalize_text(city)

    if not city:
        logger.warning('normalize_city: город пустой')
        return ''

    # capitalize() — первая буква заглавная, остальные строчные
    result = city.capitalize()
    logger.info(f'normalize_city: "{city}" -> "{result}"')
    return result


def build_profile_link(vk_id, profile_link=None):
    """
    Собирает ссылку на профиль пользователя ВКонтакте.

    Параметры:
        vk_id         — числовой id пользователя VK
        profile_link  — готовая ссылка (если уже есть в БД)

    Возвращает:
        строку-ссылку, например https://vk.com/id123456

    Пример:
        build_profile_link(123456) -> 'https://vk.com/id123456'
    """
    # Если ссылка уже есть — используем её
    if profile_link:
        logger.debug(f'build_profile_link: используем готовую ссылку {profile_link}')
        return profile_link

    link = f'https://vk.com/id{vk_id}'
    logger.debug(f'build_profile_link: собрали ссылку {link}')
    return link
