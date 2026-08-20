"""Keyboard definitions for bot messages."""

import json


def _button(label, payload=None, color="secondary"):
    """Собрать одну кнопку клавиатуры VK."""
    action = {"type": "text", "label": label}
    if payload is not None:
        action["payload"] = json.dumps(payload, ensure_ascii=False)
    return {"action": action, "color": color}


def _keyboard(rows, one_time=False):
    """Собрать схему клавиатуры VK из рядов кнопок."""
    return {"one_time": one_time, "buttons": rows}


def _inline_button(label, callback_id, color="primary"):
    """Собрать одну inline-кнопку."""
    action = {"type": "callback", "button": {"text": label, "color": color}}
    if callback_id is not None:
        action["callback_id"] = callback_id
    return action


# ============================================================
# СТАРТ И РЕГИСТРАЦИЯ
# ============================================================

def get_start_keyboard():
    """Стартовая клавиатура — одна кнопка 'Начать'."""
    return _keyboard([
        [_button("🚀 Начать", {"cmd": "start"}, "primary")]
    ], one_time=False)


def get_registration_cancel_keyboard():
    """Кнопка отмены при регистрации."""
    return _keyboard([
        [_button("❌ Отмена", {"cmd": "cancel_registration"}, "negative")]
    ])


# ============================================================
# ГЛАВНОЕ МЕНЮ
# ============================================================

def get_main_menu_keyboard():
    """Главное меню: Найти пару | Избранные | Черный список."""
    return _keyboard([
        [_button("🔍 Найти пару", {"cmd": "search"}, "primary")],
        [_button("❤️ Избранные", {"cmd": "favorites"}, "positive")],
        [_button("🚫 Черный список", {"cmd": "blacklist"}, "negative")],
    ])


def get_submenu_keyboard():
    """Подменю: Вернуться."""
    return _keyboard([
        [_button("⬅️ Назад", {"cmd": "back_to_main"}, "secondary")],
    ])


# ============================================================
# ПОИСК ПАРЫ
# ============================================================

def get_gender_search_keyboard():
    """Выбор пола для поиска."""
    return _keyboard([
        [_button("👩 Девушка", {"cmd": "gender_f"}, "positive")],
        [_button("👨 Парень", {"cmd": "gender_m"}, "primary")],
    ], one_time=True)


# ============================================================
# ПРОСМОТР АНКЕТ
# ============================================================

def get_browsing_keyboard():
    """Клавиатура просмотра анкеты."""
    rows = [
        [
            _button("❤️ Нравится", {"cmd": "like"}, "positive"),
            _button("👎 Не нравится", {"cmd": "dislike"}, "negative"),
        ],
        [
            _button("❤️ В избранные", {"cmd": "favorite"}, "positive"),
            _button("🚫 В черный список", {"cmd": "blacklist"}, "negative"),
        ],
        [
            _button("⬅️ Назад", {"cmd": "back_to_main"}, "secondary"),
        ],
    ]
    return _keyboard(rows)


# ============================================================
# СПИСКИ (ИЗБРАННЫЕ / ЧЕРНЫЙ СПИСОК)
# ============================================================

def get_list_back_keyboard():
    """Кнопка возврата в меню из списков."""
    return _keyboard([
        [_button("⬅️ В меню", {"cmd": "back_to_main"}, "secondary")]
    ])


# ============================================================
# ПОИСК ЗАВЕРШЁН (Никого не нашёл)
# ============================================================

def get_no_results_keyboard():
    """Клавиатура, когда никого не нашёл."""
    return _keyboard([
        [_button("🔍 Изменить параметры", {"cmd": "search"}, "primary")],
        [_button("🔍 Искать дальше", {"cmd": "search_broad"}, "positive")],
        [_button("⬅️ В меню", {"cmd": "back_to_main"}, "secondary")],
    ], one_time=True)
