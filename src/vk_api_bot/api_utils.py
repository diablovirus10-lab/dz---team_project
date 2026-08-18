import logging
import time
from datetime import date
from functools import wraps
from typing import Any, Callable, Dict, List, NoReturn, Optional

from .exceptions import (
    VKAPIError,
    VKAccessDeniedError,
    VKAuthError,
    VKParamsError,
    VKRateLimitError,
)

logger = logging.getLogger(__name__)

RATE_LIMIT_CODES = (6, 29)                
AUTH_ERROR_CODES = (5,)                   
ACCESS_DENIED_CODES = (15, 18, 200, 203)  
PARAMS_ERROR_CODES = (100,)               

PHOTO_SIZE_PRIORITY = ('orig', 'photo_1280', 'photo_807', 'photo_604', 'photo_130')

BATCH_DELAY = 0.35


def calculate_age(bdate: Optional[str]) -> Optional[int]:
    if not bdate:
        return None

    parts = bdate.split('.')
    if len(parts) != 3:
        return None

    try:
        birth = date(year=int(parts[2]), month=int(parts[1]), day=int(parts[0]))
    except ValueError:
        return None

    today = date.today()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))

    return age if 0 <= age <= 120 else None


def parse_vk_user(user_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(user_data, dict) or 'id' not in user_data:
        return None

    if user_data.get('deactivated'):
        return None

    city = user_data.get('city')
    return {
        'vk_id': int(user_data['id']),
        'first_name': user_data.get('first_name', ''),
        'last_name': user_data.get('last_name', ''),
        'age': calculate_age(user_data.get('bdate')),
        'city': city.get('title') if isinstance(city, dict) else None,
        'sex': int(user_data.get('sex', 0) or 0),
        'profile_link': f"https://vk.com/id{user_data['id']}",
    }


# ============================================================
# 2. РАБОТА С ФОТОГРАФИЯМИ
# ============================================================

def get_best_photo_url(photo_data: Dict[str, Any]) -> Optional[str]:
    for size_key in PHOTO_SIZE_PRIORITY:
        url = photo_data.get(size_key)
        if url:
            return url
    return None


def parse_vk_photo(photo_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(photo_data, dict):
        return None

    photo_url = get_best_photo_url(photo_data)
    if not photo_url:
        return None

    likes = photo_data.get('likes', 0)
    likes_count = likes.get('count', 0) if isinstance(likes, dict) else int(likes or 0)

    comments = photo_data.get('comments', 0)
    comments_count = comments.get('count', 0) if isinstance(comments, dict) else int(comments or 0)

    owner_id = photo_data.get('owner_id')
    photo_pk = photo_data.get('id')

    return {
        'photo_url': photo_url,
        'photo_id': f'photo{owner_id}_{photo_pk}' if owner_id is not None and photo_pk is not None
                    else str(photo_pk),
        'likes_count': likes_count,
        'comments_count': comments_count,
        'is_avatar': False,
        'is_tagged': bool(photo_data.get('has_tags', 0)),
    }


def extract_error_code(error: Exception) -> int:
    payload = getattr(error, 'error', None)
    if isinstance(payload, dict):
        try:
            return int(payload.get('error_code', 0))
        except (TypeError, ValueError):
            return 0
    try:
        return int(getattr(error, 'code', 0))
    except (TypeError, ValueError):
        return 0


def extract_error_message(error: Exception) -> str:
    payload = getattr(error, 'error', None)
    if isinstance(payload, dict) and payload.get('error_msg'):
        return str(payload['error_msg'])
    return str(error)


def extract_request_params(error: Exception) -> Optional[Any]:
    payload = getattr(error, 'error', None)
    if isinstance(payload, dict):
        return payload.get('request_params')
    return None


def handle_vk_api_error(error: Exception) -> NoReturn:
    if isinstance(error, VKAPIError):
        raise error

    code = extract_error_code(error)
    message = extract_error_message(error)
    params = extract_request_params(error)

    logger.warning("VK API error: code=%s, message=%s", code, message)

    if code in AUTH_ERROR_CODES:
        raise VKAuthError(message, request_params=params)
    if code in RATE_LIMIT_CODES:
        raise VKRateLimitError(message, request_params=params)
    if code in ACCESS_DENIED_CODES:
        raise VKAccessDeniedError(message, code=code, request_params=params)
    if code in PARAMS_ERROR_CODES:
        raise VKParamsError(message, request_params=params)

    raise VKAPIError(message, code=code, request_params=params)


def retry_on_rate_limit(max_retries: int = 3, delay: float = 1.0):
    def decorator(func: Callable) -> Callable:
        @wraps(func) 
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except VKRateLimitError as error:
                    logger.warning(
                        "Лимит VK API в %s: попытка %d/%d, пауза %.1f c",
                        func.__name__, attempt + 1, max_retries, delay,
                    )
                    if attempt == max_retries - 1:
                        raise 
                    time.sleep(delay)
        return wrapper
    return decorator


def chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    if size <= 0:
        raise ValueError("size must be positive")
    return [items[i:i + size] for i in range(0, len(items), size)]


def batch_request(func: Callable[[List[Any]], List[Any]], items: List[Any],
                  batch_size: int = 100, delay: float = BATCH_DELAY) -> List[Any]:
    results: List[Any] = []
    for chunk in chunk_list(list(items), batch_size):
        results.extend(func(chunk))
        time.sleep(delay)
    return results
