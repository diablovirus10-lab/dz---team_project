class DatabaseError(Exception):
    """Базовая ошибка слоя работы с базой данных"""
    def __init__(self, message: str, original_error: Exception | None = None):
        self.original_error = original_error
        super().__init__(message)
