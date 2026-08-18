"""Bot logic tests: полный сценарий диалога на фейковых vk_client и database."""
"""Запуск pip install pytest python -m pytest tests -v"""


from src.bot import States, get_browsing_keyboard, get_gender_keyboard, get_main_keyboard


def last_sent(fake_vk):
    assert fake_vk.sent, "бот ничего не отправил"
    return fake_vk.sent[-1]


def run_search_flow(logic, event_factory, sex_cmd="gender_f", age="25", city="Москва"):
    """Проходит шаги: меню -> пол -> возраст -> город."""
    logic.handle_event(event_factory(cmd="search"))
    logic.handle_event(event_factory(cmd=sex_cmd))
    logic.handle_event(event_factory(text=age))
    logic.handle_event(event_factory(text=city))


class TestMenu:
    def test_start_shows_greeting_and_main_keyboard(self, logic, fake_vk, state_manager, event_factory):
        logic.handle_event(event_factory(cmd="start"))
        msg = last_sent(fake_vk)
        assert "VKinder" in msg["text"]
        assert msg["keyboard"] == get_main_keyboard()
        assert state_manager.get_state(1) == States.IDLE

    def test_text_start_also_works(self, logic, fake_vk, event_factory):
        logic.handle_event(event_factory(text="начать"))
        assert "VKinder" in last_sent(fake_vk)["text"]

    def test_unknown_text_in_idle(self, logic, fake_vk, event_factory):
        logic.handle_event(event_factory(text="бла-бла"))
        assert "меню" in last_sent(fake_vk)["text"].lower()

    def test_negative_user_id_ignored(self, logic, fake_vk, event_factory):
        logic.handle_event(event_factory(user_id=-1, text="привет"))
        assert fake_vk.sent == []

    def test_user_registered_in_database(self, logic, fake_db, event_factory):
        logic.handle_event(event_factory(user_id=42, cmd="start"))
        assert 42 in fake_db.users


class TestSearchFlow:
    def test_search_asks_gender(self, logic, fake_vk, state_manager, event_factory):
        logic.handle_event(event_factory(cmd="search"))
        assert state_manager.get_state(1) == States.WAIT_GENDER
        assert last_sent(fake_vk)["keyboard"] == get_gender_keyboard()

    def test_full_flow_shows_first_profile(self, logic, fake_vk, state_manager,
                                           event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111), profile_factory(222)]
        run_search_flow(logic, event_factory)
        assert state_manager.get_state(1) == States.BROWSING
        msg = last_sent(fake_vk)
        assert "https://vk.com/id111" in msg["text"]
        assert msg["keyboard"] == get_browsing_keyboard()
        assert msg["attachments"] == ["photo111_1"]  # до 3 фото вложениями

    def test_search_params_passed_to_vk(self, logic, fake_vk, event_factory):
        run_search_flow(logic, event_factory, sex_cmd="gender_m", age="30", city="Казань")
        call = fake_vk.search_calls[0]
        assert call["sex"] == 2
        assert call["age_from"] == 30
        assert call["age_to"] == 30
        assert call["city_id"] == 1  # find_city_id возвращает 1 для "Казань"

    def test_no_results_returns_to_menu(self, logic, fake_vk, state_manager, event_factory):
        fake_vk.profiles = []
        run_search_flow(logic, event_factory)
        assert state_manager.get_state(1) == States.IDLE
        assert "не нашёл" in last_sent(fake_vk)["text"].lower()

    def test_profile_marked_as_viewed(self, logic, fake_vk, fake_db,
                                      event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111)]
        run_search_flow(logic, event_factory)
        assert (1, 111) in fake_db.viewed

    def test_viewed_profiles_skipped(self, logic, fake_vk, fake_db,
                                     event_factory, profile_factory):
        fake_db.viewed_ids[1] = {111}  # 111 уже показывали
        fake_vk.profiles = [profile_factory(111), profile_factory(222)]
        run_search_flow(logic, event_factory)
        assert "https://vk.com/id222" in last_sent(fake_vk)["text"]


class TestBrowsing:
    def test_like_saves_and_shows_next(self, logic, fake_vk, fake_db,
                                       event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111), profile_factory(222)]
        run_search_flow(logic, event_factory)
        logic.handle_event(event_factory(cmd="like"))
        assert (1, 111) in fake_db.favorites
        assert "❤️" in fake_vk.sent[-2]["text"]
        assert "https://vk.com/id222" in last_sent(fake_vk)["text"]

    def test_dislike_adds_to_blacklist(self, logic, fake_vk, fake_db,
                                       event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111), profile_factory(222)]
        run_search_flow(logic, event_factory)
        logic.handle_event(event_factory(cmd="dislike"))
        assert (1, 111) in fake_db.blacklist
        assert "https://vk.com/id222" in last_sent(fake_vk)["text"]

    def test_queue_end_returns_to_menu(self, logic, fake_vk, state_manager,
                                       event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111)]
        run_search_flow(logic, event_factory)
        logic.handle_event(event_factory(cmd="next"))
        assert state_manager.get_state(1) == States.IDLE
        assert "закончились" in last_sent(fake_vk)["text"]
        assert last_sent(fake_vk)["keyboard"] == get_main_keyboard()

    def test_menu_button_stops_browsing(self, logic, fake_vk, state_manager,
                                        event_factory, profile_factory):
        fake_vk.profiles = [profile_factory(111)]
        run_search_flow(logic, event_factory)
        logic.handle_event(event_factory(cmd="menu"))
        assert state_manager.get_state(1) == States.IDLE
        assert last_sent(fake_vk)["keyboard"] == get_main_keyboard()


class TestInputValidation:
    def _enter_age_state(self, logic, event_factory):
        logic.handle_event(event_factory(cmd="search"))
        logic.handle_event(event_factory(cmd="gender_f"))

    def test_invalid_age_asked_again(self, logic, fake_vk, state_manager, event_factory):
        self._enter_age_state(logic, event_factory)
        logic.handle_event(event_factory(text="двадцать"))
        assert state_manager.get_state(1) == States.WAIT_AGE
        assert "числом" in last_sent(fake_vk)["text"]

    def test_age_out_of_range(self, logic, state_manager, event_factory):
        self._enter_age_state(logic, event_factory)
        logic.handle_event(event_factory(text="13"))
        assert state_manager.get_state(1) == States.WAIT_AGE
        logic.handle_event(event_factory(text="100"))
        assert state_manager.get_state(1) == States.WAIT_AGE

    def test_valid_age_moves_to_city(self, logic, state_manager, event_factory):
        self._enter_age_state(logic, event_factory)
        logic.handle_event(event_factory(text="25"))
        assert state_manager.get_state(1) == States.WAIT_CITY

    def test_menu_button_cancels_input(self, logic, fake_vk, state_manager, event_factory):
        self._enter_age_state(logic, event_factory)
        logic.handle_event(event_factory(cmd="menu"))
        assert state_manager.get_state(1) == States.IDLE
        assert last_sent(fake_vk)["keyboard"] == get_main_keyboard()


class TestLikesList:
    def test_empty_likes(self, logic, fake_vk, event_factory):
        logic.handle_event(event_factory(cmd="likes"))
        assert "пуст" in last_sent(fake_vk)["text"]

    def test_likes_list_shown(self, logic, fake_vk, fake_db, event_factory, profile_factory):
        fake_db.add_favorite(1, profile_factory(111, first_name="Юлия"))
        logic.handle_event(event_factory(cmd="likes"))
        text = last_sent(fake_vk)["text"]
        assert "Юлия" in text
        assert "https://vk.com/id111" in text