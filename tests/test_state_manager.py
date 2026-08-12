"""Тесты FSM: состояния и временные данные."""

from src.bot import StateManager, States


def test_default_state_is_idle():
    sm = StateManager()
    assert sm.get_state(1) == States.IDLE


def test_set_and_get_state():
    sm = StateManager()
    sm.set_state(1, States.WAIT_AGE)
    assert sm.get_state(1) == States.WAIT_AGE


def test_states_independent_per_user():
    sm = StateManager()
    sm.set_state(1, States.BROWSING)
    sm.set_state(2, States.WAIT_CITY)
    assert sm.get_state(1) == States.BROWSING
    assert sm.get_state(2) == States.WAIT_CITY


def test_data_accumulates():
    sm = StateManager()
    sm.update_data(1, sex=1, age=25)
    sm.update_data(1, city="Москва")
    assert sm.get_data(1) == {"sex": 1, "age": 25, "city": "Москва"}


def test_reset_clears_state_and_data():
    sm = StateManager()
    sm.set_state(1, States.BROWSING)
    sm.update_data(1, sex=1)
    sm.reset(1)
    assert sm.get_state(1) == States.IDLE
    assert sm.get_data(1) == {}


def test_reset_does_not_touch_other_users():
    sm = StateManager()
    sm.set_state(1, States.BROWSING)
    sm.set_state(2, States.WAIT_AGE)
    sm.reset(1)
    assert sm.get_state(2) == States.WAIT_AGE