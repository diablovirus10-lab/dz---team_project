"""State management for dialog flow."""


class States:
    """Состояния диалога (FSM)."""

    IDLE = "idle"                # главное меню
    WAIT_GENDER = "wait_gender"  # спрашиваем пол искомого (sex: 1/2)
    WAIT_AGE = "wait_age"        # спрашиваем возраст
    WAIT_CITY = "wait_city"      # спрашиваем город
    BROWSING = "browsing"        # показываем анкеты, ждём реакцию


class StateManager:
    """Хранит состояние и временные данные поиска по каждому пользователю."""

    def __init__(self):
        self.states = {}
        self.data = {}

    def get_state(self, user_id, default=States.IDLE):
        """Текущее состояние пользователя."""
        return self.states.get(user_id, default)

    def set_state(self, user_id, state):
        """Перевести пользователя в новое состояние."""
        self.states[user_id] = state

    def get_data(self, user_id):
        """Временные данные пользователя (создаёт dict при первом обращении)."""
        return self.data.setdefault(user_id, {})

    def update_data(self, user_id, **kwargs):
        """Обновить временные данные пользователя."""
        self.data.setdefault(user_id, {}).update(kwargs)

    def reset(self, user_id):
        """Вернуть в исходное состояние и стереть временные данные."""
        self.states.pop(user_id, None)
        self.data.pop(user_id, None)
