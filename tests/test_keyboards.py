"""Тесты клавиатур: схема VK и наборы команд."""

import json

import pytest

from src.bot import (
    get_browsing_keyboard,
    get_cancel_keyboard,
    get_gender_keyboard,
    get_main_keyboard,
)

ALL_KEYBOARDS = [
    get_main_keyboard(),
    get_gender_keyboard(),
    get_cancel_keyboard(),
    get_browsing_keyboard(),
]
ALLOWED_COLORS = {"primary", "secondary", "positive", "negative"}


def _commands(keyboard):
    cmds = set()
    for row in keyboard["buttons"]:
        for btn in row:
            cmds.add(json.loads(btn["action"]["payload"])["cmd"])
    return cmds


@pytest.mark.parametrize("kb", ALL_KEYBOARDS)
def test_keyboard_schema_valid(kb):
    assert "one_time" in kb and "buttons" in kb
    assert isinstance(kb["buttons"], list) and kb["buttons"]
    for row in kb["buttons"]:
        assert isinstance(row, list) and row
        for btn in row:
            action = btn["action"]
            assert action["type"] == "text"
            assert isinstance(action["label"], str) and action["label"]
            assert btn["color"] in ALLOWED_COLORS
            assert "cmd" in json.loads(action["payload"])


def test_main_keyboard_commands():
    assert _commands(get_main_keyboard()) == {"search", "likes"}


def test_gender_keyboard_commands():
    assert _commands(get_gender_keyboard()) == {"gender_f", "gender_m"}


def test_browsing_keyboard_commands():
    assert _commands(get_browsing_keyboard()) == {"like", "dislike", "next", "menu", "photo_like"}


def test_cancel_keyboard_has_menu():
    assert _commands(get_cancel_keyboard()) == {"menu"}