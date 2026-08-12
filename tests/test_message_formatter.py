"""Тесты форматирования сообщений."""

from src.bot import format_greeting, format_likes_list, format_message, format_profile


def make_profile(vk_id=222222222, **overrides):
    profile = {
        "vk_id": vk_id,
        "first_name": "Анна",
        "last_name": "Смирнова",
        "age": 24,
        "city": "Москва",
        "sex": 1,
        "profile_link": f"https://vk.com/id{vk_id}",
        "photos": [],
    }
    profile.update(overrides)
    return profile


def test_format_message_passthrough():
    assert format_message("привет") == "привет"


def test_format_message_substitution():
    assert format_message("Привет, {name}!", {"name": "Иван"}) == "Привет, Иван!"


def test_greeting_mentions_bot():
    assert "VKinder" in format_greeting()


def test_greeting_with_name():
    assert "Иван" in format_greeting("Иван")


def test_profile_contains_all_fields():
    text = format_profile(make_profile())
    assert "Анна Смирнова" in text
    assert "24" in text
    assert "Москва" in text
    assert "https://vk.com/id222222222" in text


def test_profile_without_optional_fields_no_crash():
    text = format_profile(make_profile(age=None, city=None, profile_link=None))
    assert "Анна Смирнова" in text
    assert "https://vk.com/id222222222" in text  # fallback-ссылка по vk_id
    assert "Возраст" not in text


def test_likes_list_empty():
    assert "пуст" in format_likes_list([])


def test_likes_list_numbered_with_links():
    text = format_likes_list([
        make_profile(),
        make_profile(333333333, first_name="Екатерина", last_name="Кузнецова"),
    ])
    assert "1." in text and "2." in text
    assert "Анна Смирнова" in text
    assert "Екатерина Кузнецова" in text
    assert "https://vk.com/id333333333" in text