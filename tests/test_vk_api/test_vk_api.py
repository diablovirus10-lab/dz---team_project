import sys
import types
from datetime import date
from types import SimpleNamespace

import pytest

try:
    import vk_api
except ImportError:
    # Заглушка, если пакет vk_api не установлен — нужна для импорта VKClient
    vk_api = types.SimpleNamespace(VkApi=object, ApiError=Exception)
    sys.modules["vk_api"] = vk_api

from src.vk_api_bot import api_utils, exceptions
from src.vk_api_bot.exceptions import (
    VKAccessDeniedError,
    VKAPIError,
    VKAuthError,
    VKParamsError,
    VKRateLimitError,
    VKUserNotFoundError,
)
from src.vk_api_bot.vk_client import VKClient

# Патчим vk_api там, где его импортирует VKClient
VK_API_MODULE = "src.vk_api_bot.vk_client.vk_api"


class FakeVkApiError(Exception):
    pass


class FakeApi:
    def __init__(self):
        self.users = SimpleNamespace(get=None, search=None)
        self.database = SimpleNamespace(getCities=None)
        self.photos = SimpleNamespace(getAll=None)
        self.groups = SimpleNamespace(get=None)
        self.friends = SimpleNamespace(getMutual=None)


def make_client(monkeypatch, api):
    monkeypatch.setenv("VK_GROUP_TOKEN", "test-token")
    monkeypatch.setattr(
        f"{VK_API_MODULE}.VkApi",
        lambda *args, **kwargs: SimpleNamespace(get_api=lambda: api),
        raising=False,
    )
    monkeypatch.setattr(f"{VK_API_MODULE}.ApiError", FakeVkApiError, raising=False)
    return VKClient()


def make_error(error_code=None, error_msg=None, request_params=None, code=None):
    error = FakeVkApiError(error_msg or "vk api error")
    if error_code is not None or error_msg is not None or request_params is not None:
        error.error = {
            "error_code": error_code,
            "error_msg": error_msg,
            "request_params": request_params,
        }
    if code is not None:
        error.code = code
    return error


def test_calculate_age_valid_date():
    today = date.today()
    expected_age = today.year - 1990 - ((today.month, today.day) < (1, 1))
    assert api_utils.calculate_age("1.1.1990") == expected_age


def test_calculate_age_invalid_values():
    assert api_utils.calculate_age(None) is None
    assert api_utils.calculate_age("1.1") is None
    assert api_utils.calculate_age("31.02.2000") is None
    assert api_utils.calculate_age("1.1.1800") is None


def test_parse_vk_user_basic_profile():
    user_data = {
        "id": "100",
        "first_name": "Иван",
        "last_name": "Иванов",
        "bdate": "1.1.1990",
        "city": {"title": "Москва"},
        "sex": 2,
    }
    parsed = api_utils.parse_vk_user(user_data)

    assert parsed["vk_id"] == 100
    assert parsed["first_name"] == "Иван"
    assert parsed["last_name"] == "Иванов"
    assert parsed["city"] == "Москва"
    assert parsed["sex"] == 2
    assert parsed["profile_link"] == "https://vk.com/id100"
    assert isinstance(parsed["age"], int)


def test_parse_vk_user_invalid_profiles():
    assert api_utils.parse_vk_user(None) is None
    assert api_utils.parse_vk_user({}) is None
    assert api_utils.parse_vk_user({"id": 1, "deactivated": "deleted"}) is None
    assert api_utils.parse_vk_user({"id": 1, "city": "not-a-dict"})["city"] is None
    assert api_utils.parse_vk_user({"id": 2, "sex": ""})["sex"] == 0


def test_get_best_photo_url_priority():
    photo_data = {
        "photo_604": "url604",
        "photo_1280": "url1280",
        "photo_807": "url807",
    }
    assert api_utils.get_best_photo_url(photo_data) == "url1280"


def test_get_best_photo_url_no_sizes():
    assert api_utils.get_best_photo_url({}) is None


def test_parse_vk_photo_type_variants():
    photo_data = {
        "id": 12,
        "owner_id": 34,
        "photo_1280": "http://example.com/p.jpg",
        "likes": {"count": 5},
        "comments": {"count": 7},
        "has_tags": 1,
    }
    parsed = api_utils.parse_vk_photo(photo_data)

    assert parsed["photo_url"] == "http://example.com/p.jpg"
    assert parsed["photo_id"] == "photo34_12"
    assert parsed["likes_count"] == 5
    assert parsed["comments_count"] == 7
    assert parsed["is_avatar"] is False
    assert parsed["is_tagged"] is True


def test_parse_vk_photo_missing_url():
    assert api_utils.parse_vk_photo({"id": 1, "owner_id": 2}) is None


def test_extract_error_helpers():
    error = make_error(error_code=100, error_msg="Bad params", request_params=[{"key": "value"}])
    assert api_utils.extract_error_code(error) == 100
    assert api_utils.extract_error_message(error) == "Bad params"
    assert api_utils.extract_request_params(error) == [{"key": "value"}]

    error = FakeVkApiError("text error")
    error.code = 42
    assert api_utils.extract_error_code(error) == 42
    assert api_utils.extract_error_message(error) == "text error"
    assert api_utils.extract_request_params(error) is None


def test_handle_vk_api_error_maps_exceptions():
    with pytest.raises(VKAuthError):
        api_utils.handle_vk_api_error(make_error(error_code=5, error_msg="auth failed"))

    with pytest.raises(VKRateLimitError):
        api_utils.handle_vk_api_error(make_error(error_code=6, error_msg="rate limit"))

    with pytest.raises(VKAccessDeniedError) as exc_info:
        api_utils.handle_vk_api_error(make_error(error_code=15, error_msg="access denied"))
    assert exc_info.value.code == 15

    with pytest.raises(VKParamsError):
        api_utils.handle_vk_api_error(make_error(error_code=100, error_msg="invalid params"))

    with pytest.raises(VKAPIError) as generic_info:
        api_utils.handle_vk_api_error(make_error(error_code=999, error_msg="unknown"))
    assert generic_info.value.code == 999


def test_handle_vk_api_error_rethrows_vkapi_error():
    original = VKAPIError("original", code=123)
    with pytest.raises(VKAPIError) as exc_info:
        api_utils.handle_vk_api_error(original)
    assert exc_info.value is original


def test_retry_on_rate_limit_retries_until_success(monkeypatch):
    calls = {"count": 0}

    @api_utils.retry_on_rate_limit(max_retries=3, delay=0.0)
    def stub():
        calls["count"] += 1
        if calls["count"] < 3:
            raise VKRateLimitError("retry")
        return "ok"

    monkeypatch.setattr(api_utils.time, "sleep", lambda *_args, **_kwargs: None)
    assert stub() == "ok"
    assert calls["count"] == 3


def test_retry_on_rate_limit_raises_after_retries(monkeypatch):
    @api_utils.retry_on_rate_limit(max_retries=2, delay=0.0)
    def stub():
        raise VKRateLimitError("fail")

    monkeypatch.setattr(api_utils.time, "sleep", lambda *_args, **_kwargs: None)
    with pytest.raises(VKRateLimitError):
        stub()


def test_chunk_list_divides_correctly():
    assert api_utils.chunk_list([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_chunk_list_invalid_size():
    with pytest.raises(ValueError):
        api_utils.chunk_list([1, 2, 3], 0)


def test_batch_request_calls_batches(monkeypatch):
    chunks = []

    def handler(items):
        chunks.append(list(items))
        return ["x"] * len(items)

    monkeypatch.setattr(api_utils.time, "sleep", lambda *_args, **_kwargs: None)
    result = api_utils.batch_request(handler, [1, 2, 3, 4, 5], batch_size=2, delay=0.0)

    assert result == ["x", "x", "x", "x", "x"]
    assert chunks == [[1, 2], [3, 4], [5]]


def test_vk_client_init_requires_token(monkeypatch):
    monkeypatch.delenv("VK_GROUP_TOKEN", raising=False)
    monkeypatch.delenv("VK_GROUP_ID", raising=False)
    monkeypatch.setattr(
        f"{VK_API_MODULE}.VkApi",
        lambda *args, **kwargs: SimpleNamespace(get_api=lambda: None),
        raising=False,
    )
    with pytest.raises(VKAuthError):
        VKClient()


def test_vk_client_init_reads_group_id(monkeypatch):
    api = FakeApi()
    monkeypatch.delenv("VK_GROUP_ID", raising=False)
    client = make_client(monkeypatch, api)
    assert client.token == "test-token"
    assert client.group_id is None

    monkeypatch.setenv("VK_GROUP_ID", "321")
    client = make_client(monkeypatch, api)
    assert client.group_id == 321


def test_get_user_profile_returns_parsed_user(monkeypatch):
    api = FakeApi()

    def users_get(user_ids, fields):
        assert user_ids == 123
        assert "bdate" in fields
        return [{"id": 123, "first_name": "Анна", "last_name": "Смирнова", "bdate": "1.1.1990", "city": {"title": "Москва"}, "sex": 1}]

    api.users.get = users_get
    client = make_client(monkeypatch, api)
    result = client.get_user_profile(123)

    assert result["vk_id"] == 123
    assert result["first_name"] == "Анна"


def test_get_user_profile_raises_not_found(monkeypatch):
    api = FakeApi()
    api.users.get = lambda user_ids, fields: []
    client = make_client(monkeypatch, api)

    with pytest.raises(VKUserNotFoundError):
        client.get_user_profile(123)


def test_get_user_profile_raises_auth_error(monkeypatch):
    api = FakeApi()

    def users_get(*args, **kwargs):
        raise make_error(error_code=5, error_msg="auth failed")

    api.users.get = users_get
    client = make_client(monkeypatch, api)

    with pytest.raises(VKAuthError):
        client.get_user_profile(123)


def test_get_users_batch_parses_multiple_profiles(monkeypatch):
    api = FakeApi()

    def users_get(user_ids, fields):
        assert user_ids == "1,2,3"
        return [
            {"id": 1, "first_name": "А", "last_name": "Б", "bdate": "1.1.1990", "city": {"title": "Москва"}, "sex": 1},
            {"id": 2, "first_name": "В", "last_name": "Г", "bdate": "2.2.1991", "city": {"title": "Питер"}, "sex": 2},
            {"id": 3, "first_name": "Д", "last_name": "Е", "bdate": "3.3.1992", "city": {"title": "Казань"}, "sex": 1},
        ]

    api.users.get = users_get
    client = make_client(monkeypatch, api)
    result = client.get_users_batch([1, 2, 3])

    assert len(result) == 3
    assert result[0]["vk_id"] == 1
    assert result[1]["city"] == "Питер"


def test_search_users_returns_items_and_total(monkeypatch):
    api = FakeApi()

    def users_search(**params):
        assert params["sex"] == 1
        assert params["age_from"] == 20
        assert params["age_to"] == 30
        assert params["count"] == 5
        assert params["country"] == 1
        return {"items": [{"id": 5, "first_name": "Кирилл", "last_name": "Иванов", "bdate": "10.10.1995", "city": {"title": "Киев"}, "sex": 2}], "count": 1}

    api.users.search = users_search
    client = make_client(monkeypatch, api)
    result = client.search_users(sex=1, age_from=20, age_to=30, count=5)

    assert result["total"] == 1
    assert result["items"][0]["vk_id"] == 5


def test_search_users_uses_city_id_when_provided(monkeypatch):
    api = FakeApi()

    def users_search(**params):
        assert params["city"] == 77
        assert "country" not in params
        return {"items": [], "count": 0}

    api.users.search = users_search
    client = make_client(monkeypatch, api)
    client.search_users(sex=1, age_from=18, age_to=25, city_id=77)


def test_find_city_id_returns_id(monkeypatch):
    api = FakeApi()
    api.database.getCities = lambda country_id, q, count: {"items": [{"id": 456}]}
    client = make_client(monkeypatch, api)
    assert client.find_city_id("Москва") == 456


def test_find_city_id_returns_none_for_empty_query(monkeypatch):
    api = FakeApi()
    api.database.getCities = lambda country_id, q, count: {"items": []}
    client = make_client(monkeypatch, api)
    assert client.find_city_id("") is None


def test_get_user_photos_marks_first_avatar(monkeypatch):
    api = FakeApi()
    api.photos.getAll = lambda owner_id, extended, count: {
        "items": [
            {"id": 1, "owner_id": 2, "photo_604": "url1", "likes": 0, "comments": 0},
            {"id": 2, "owner_id": 2, "photo_1280": "url2", "likes": {"count": 1}, "comments": {"count": 1}},
        ]
    }
    client = make_client(monkeypatch, api)
    photos = client.get_user_photos(2, count=2)

    assert photos[0]["is_avatar"] is True
    assert photos[1]["photo_url"] == "url2"


def test_split_interests_text_normalizes_delimiters():
    assert VKClient._split_interests_text("rock; pop|jazz, classical") == ["rock", "pop", "jazz", "classical"]
    assert VKClient._split_interests_text(None) == []


def test_get_user_interests_includes_profile_and_groups(monkeypatch):
    api = FakeApi()

    api.users.get = lambda user_ids, fields: [{
        "music": "rock;pop",
        "books": "fiction",
        "interests": "travel|sport",
    }]
    api.groups.get = lambda user_id, count: {"items": [{"id": 10, "name": "Friends"}]}

    client = make_client(monkeypatch, api)
    interests = client.get_user_interests(123)

    assert any(item["type"] == "music" and item["value"] == "rock" for item in interests)
    assert any(item["type"] == "books" and item["value"] == "fiction" for item in interests)
    assert any(item["type"] == "groups" and item["value"] == "Friends" for item in interests)


def test_get_user_interests_ignores_groups_access_denied(monkeypatch):
    api = FakeApi()

    api.users.get = lambda user_ids, fields: [{"music": "pop"}]

    def raise_error(*args, **kwargs):
        raise make_error(error_code=15, error_msg="access denied")

    api.groups.get = raise_error
    client = make_client(monkeypatch, api)
    interests = client.get_user_interests(123)

    assert interests == [{"type": "music", "value": "pop", "vk_entity_id": None}]


def test_get_common_friends_count_returns_len(monkeypatch):
    api = FakeApi()
    api.friends.getMutual = lambda source_uid, target_uid: [1, 2, 3]
    client = make_client(monkeypatch, api)

    assert client.get_common_friends_count(1, 2) == 3


def test_get_common_friends_count_returns_zero_on_access_denied(monkeypatch):
    api = FakeApi()

    def raise_error(*args, **kwargs):
        raise make_error(error_code=15, error_msg="access denied")

    api.friends.getMutual = raise_error
    client = make_client(monkeypatch, api)

    assert client.get_common_friends_count(1, 2) == 0
