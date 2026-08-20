"""Message formatting helpers for dating bot."""


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
        "«❤️ Избранные», чтобы посмотреть сохранённые, "
        "или «🚫 Черный список», чтобы увидеть заблокированных."
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


def format_registration_complete(user_data):
    """Форматирование подтверждения завершения регистрации."""
    name = user_data.get('first_name', 'Пользователь')
    age = user_data.get('age', '??')
    city = user_data.get('city', 'не указан')
    photo_count = user_data.get('photo_count', 0)

    return (
        f"✅ Регистрация завершена, {name}!\n\n"
        f"🎂 Возраст: {age}\n"
        f"🏙 Город: {city}\n"
        f"📸 Фотографий: {photo_count}\n\n"
        "Твой профиль создан! Теперь можешь искать пару 🙂"
    )


def format_profile_needed(missing_fields, vk_profile=None):
    """Форматирование запроса недостающих полей."""
    if vk_profile:
        lines = ["📋 Данные твоего VK профиля:", ""]
        if vk_profile.get('first_name'):
            lines.append(f"👤 Имя: {vk_profile['first_name']}")
        if vk_profile.get('age'):
            lines.append(f"🎂 Возраст: {vk_profile['age']}")
        if vk_profile.get('city'):
            lines.append(f"🏙 Город: {vk_profile['city']}")
        lines.append("")

    field_names = {
        'first_name': '👤 Имя',
        'last_name': '📝 Фамилия',
        'age': '🎂 Возраст',
        'city': '🏙 Город',
    }

    lines = []
    if not vk_profile:
        lines.append("🔒 Профиль недоступен, нужна регистрация 🙂")
        lines.append("")

    lines.append("❓ Укажи недостающие данные:")
    for field in missing_fields:
        lines.append(f"  • {field_names.get(field, field)}")

    lines.append("")
    lines.append("Начнём с первого поля 👇")
    return "\n".join(lines)


def format_blacklist_list(profiles):
    """Список заблокированных анкет."""
    if not profiles:
        return "🚫 Твой черный список пуст 🙂"

    lines = ["🚫 Заблокированные анкеты:", ""]
    for num, p in enumerate(profiles, start=1):
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        age = p.get('age', '??')
        city = p.get('city', '')
        lines.append(f"{num}. {name}, {age} лет, {city}")

    lines.append("")
    lines.append("Нажми «⬅️ В меню» для возврата.")
    return "\n".join(lines)


def format_error(text="Что-то пошло не так 🙈 Попробуй ещё раз."):
    """Сообщение об ошибке."""
    return text
