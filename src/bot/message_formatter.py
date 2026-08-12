"""Message formatting helpers."""


def format_message(text, user_data=None):
    """Базовый форматтер: подставляет {плейсхолдеры} из user_data."""
    if user_data:
        return text.format(**user_data)
    return text


def format_greeting(name=""):
    """Приветствие и подсказка по меню."""
    suffix = f", {name}" if name else ""
    return (
        f"Привет{suffix}! 👋 Я VKinder — бот для знакомств.\n"
        "Нажми «🔍 Найти пару», чтобы подобрать анкеты, "
        "или «❤️ Мои лайки», чтобы посмотреть сохранённых."
    )


def _profile_link(profile):
    return profile.get("profile_link") or f"https://vk.com/id{profile.get('vk_id')}"


def format_profile(profile):
    """Карточка анкеты. Ключи — как в таблице candidates:
    vk_id, first_name, last_name, age, city, sex, profile_link, photos."""
    full_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()
    lines = [f"👤 {full_name}"]
    if profile.get("age"):
        lines.append(f"🎂 Возраст: {profile['age']}")
    if profile.get("city"):
        lines.append(f"🏙 Город: {profile['city']}")
    lines.append(f"🔗 {_profile_link(profile)}")
    return "\n".join(lines)


def format_likes_list(profiles):
    """Список лайкнутых анкет (из таблицы favorites)."""
    if not profiles:
        return "Список лайков пока пуст 🙂 Нажми «🔍 Найти пару», чтобы начать."
    lines = ["❤️ Твои сохранённые анкеты:", ""]
    for num, p in enumerate(profiles, start=1):
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        lines.append(f"{num}. {name} — {_profile_link(p)}")
    return "\n".join(lines)


def format_error(text="Что-то пошло не так 🙈 Попробуй ещё раз."):
    """Сообщение об ошибке."""
    return text