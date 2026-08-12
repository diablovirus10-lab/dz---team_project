"""
Модуль проверки данных (validators).

Проверяет, можно ли доверять вводу пользователя:
    - возраст — число от 14 до 99;
    - пол — только 1 (жен) или 2 (муж), как во ВКонтакте;
    - город — не пустой.

Если данные плохие — пишем в лог и возвращаем False.
"""

from .helpers import normalize_text, parse_age
from .logger import get_logger

logger = get_logger('validators')

# Допустимый диапазон возраста (как в bot_logic.py)
MIN_AGE = 14
MAX_AGE = 99


def validate_age(text):
    """
    Проверяет, подходит ли возраст для поиска.

    Параметры:
        text — то, что написал пользователь (строка)

    Возвращает:
        (True, возраст)  — если всё ок
        (False, None)    — если возраст неправильный
    """
    age = parse_age(text)

    if age is None:
        logger.warning(f'validate_age: не удалось распознать возраст из "{text}"')
        return False, None

    if age < MIN_AGE or age > MAX_AGE:
        logger.warning(f'validate_age: возраст {age} вне диапазона {MIN_AGE}-{MAX_AGE}')
        return False, None

    logger.info(f'validate_age: возраст {age} — OK')
    return True, age


def validate_sex(sex):
    """
    Проверяет пол для поиска.

    Во ВКонтакте:
        1 — женский
        2 — мужской

    Параметры:
        sex — число (1 или 2)

    Возвращает:
        True — если пол правильный, False — если нет
    """
    if sex in (1, 2):
        logger.info(f'validate_sex: пол {sex} — OK')
        return True

    logger.warning(f'validate_sex: неправильный пол {sex}, нужно 1 или 2')
    return False


def validate_city(city):
    """
    Проверяет название города.

    Параметры:
        city — строка с названием города

    Возвращает:
        (True, город)   — если город нормальный
        (False, None)   — если город пустой или слишком короткий
    """
    city = normalize_text(city)

    if len(city) < 2:
        logger.warning(f'validate_city: слишком короткое название "{city}"')
        return False, None

    logger.info(f'validate_city: город "{city}" — OK')
    return True, city


def validate_user_data(user_data):
    """
    Проверяет все данные пользователя для поиска сразу.

    Ожидаемый словарь user_data:
        {
            'sex':  1 или 2,
            'age':  число или строка с возрастом,
            'city': название города
        }

    Параметры:
        user_data — словарь с данными

    Возвращает:
        (True, '')           — всё хорошо
        (False, 'текст ошибки') — что-то не так (текст можно показать пользователю)
    """
    if not isinstance(user_data, dict):
        logger.error('validate_user_data: user_data не является словарём')
        return False, 'Внутренняя ошибка: неверный формат данных'

    # --- проверяем пол ---
    sex = user_data.get('sex')
    if not validate_sex(sex):
        return False, 'Укажи пол кнопкой: девушку или парня'

    # --- проверяем возраст ---
    age = user_data.get('age')
    # age может быть уже числом (из state_manager) или строкой (из чата)
    if isinstance(age, int):
        if age < MIN_AGE or age > MAX_AGE:
            logger.warning(f'validate_user_data: возраст {age} вне диапазона')
            return False, f'Возраст должен быть от {MIN_AGE} до {MAX_AGE}'
    else:
        ok, parsed_age = validate_age(str(age))
        if not ok:
            return False, f'Возраст нужно указать числом от {MIN_AGE} до {MAX_AGE}'

    # --- проверяем город ---
    city = user_data.get('city', '')
    ok, _ = validate_city(city)
    if not ok:
        return False, 'Напиши название города (минимум 2 буквы)'

    logger.info(f'validate_user_data: все данные OK — sex={sex}, age={age}, city={city}')
    return True, ''
