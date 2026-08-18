"""Custom VK API exceptions."""

from typing import Optional, Dict, Any


class VKAPIError(Exception):
    """Базовое исключение для всех ошибок VK API"""
    def __init__(self, message: str, code: int = 0, request_params: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.request_params = request_params
        super().__init__(self.__str__())

    def __str__(self):
        return f"[VK API Error {self.code}] {self.message}"


class VKAuthError(VKAPIError):
    """Ошибка авторизации (Код 5)"""
    def __init__(self, message: str = "Authorization failed", request_params=None):
        super().__init__(message, code=5, request_params=request_params)


class VKRateLimitError(VKAPIError):
    """Превышен лимит запросов (Код 6)"""
    def __init__(self, message: str = "Too many requests per second", request_params=None):
        super().__init__(message, code=6, request_params=request_params)


class VKAccessDeniedError(VKAPIError):
    """Доступ запрещен (Коды 15, 200)"""
    def __init__(self, message: str = "Access denied", code: int = 15, request_params=None):
        super().__init__(message, code=code, request_params=request_params)


class VKParamsError(VKAPIError):
    """Неверные параметры запроса (Код 100)"""
    def __init__(self, message: str = "One of the parameters specified was missing or invalid", request_params=None):
        super().__init__(message, code=100, request_params=request_params)


class VKUserNotFoundError(VKAPIError):
    """Пользователь не найден (Логическая ошибка приложения)"""
    def __init__(self, vk_id: int):
        super().__init__(f"User with vk_id {vk_id} not found", code=0)
        self.vk_id = vk_id


class VKPhotoError(VKAPIError):
    """Ошибка при работе с фотографиями"""
    def __init__(self, message: str = "Failed to fetch photos", request_params=None):
        super().__init__(message, code=0, request_params=request_params)
