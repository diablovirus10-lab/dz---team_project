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


def get_main_keyboard():
    """Главное меню бота."""
    return _keyboard([
        [
            _button("🔍 Найти пару", {"cmd": "search"}, "primary"),
            _button("❤️ Мои лайки", {"cmd": "likes"}, "positive"),
        ],
    ])


def get_gender_keyboard():
    """Клавиатура шага выбора пола."""
    return _keyboard([
        [_button("👩 Девушку", {"cmd": "gender_f"}, "primary")],
        [_button("👨 Парня", {"cmd": "gender_m"}, "primary")],
    ], one_time=True)


def get_cancel_keyboard():
    """Кнопка возврата в меню для шагов со свободным вводом."""
    return _keyboard([
        [_button("🏠 В меню", {"cmd": "menu"}, "secondary")],
    ])


def get_browsing_keyboard():
    """Клавиатура шага просмотра анкет."""
    return _keyboard([
        [
            _button("👍 Нравится", {"cmd": "like"}, "positive"),
            _button("👎 Не нравится", {"cmd": "dislike"}, "negative"),
        ],
        [
            _button("⏭ Ещё анкета", {"cmd": "next"}, "primary"),
            _button("🏠 В меню", {"cmd": "menu"}, "secondary"),
        ],
    ])