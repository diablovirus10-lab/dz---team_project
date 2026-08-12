from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any

MIN_AGE = 14
MAX_AGE = 100
VALID_SEX_VALUES = (0, 1, 2)

def _check_positive_int(value: Any, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"Поле '{field_name}' должно быть положительным int, получено: {value!r}")

def _check_non_negative_int(value: Any, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Поле '{field_name}' должно быть целым >= 0, получено: {value!r}")

def _check_non_empty_str(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Поле '{field_name}' должно быть непустой строкой, получено: {value!r}")

def _check_optional_str(value: Any, field_name: str) -> None:
    if value is not None:
        _check_non_empty_str(value, field_name)

def _check_age(value: Any) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or not MIN_AGE <= value <= MAX_AGE:
        raise ValueError(f"Возраст должен быть в диапазоне {MIN_AGE}..{MAX_AGE} или None, получено: {value!r}")

def _check_sex(value: Any) -> None:
    if value not in VALID_SEX_VALUES:
        raise ValueError(f"Пол должен быть одним из {VALID_SEX_VALUES}, получено: {value!r}")

def _check_bool(value: Any, field_name: str) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"Поле '{field_name}' должно быть bool, получено: {value!r}")

def _check_datetime(value: Any, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise ValueError(f"Поле '{field_name}' должно быть datetime, получено: {value!r}")

def _check_weight(value: Any, field_name: str) -> None:
    """Проверка веса критерия (от 0.0 до 1.0)"""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"Поле '{field_name}' должно быть float/int, получено: {value!r}")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"Поле '{field_name}' должно быть в диапазоне от 0.0 до 1.0, получено: {value!r}")


@dataclass
class User:
    id: int
    vk_id: int
    first_name: str
    last_name: Optional[str]
    age: Optional[int]
    city: Optional[str]
    sex: int
    registered_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.vk_id, 'vk_id')
        _check_non_empty_str(self.first_name, 'first_name')
        _check_optional_str(self.last_name, 'last_name')
        _check_age(self.age)
        _check_optional_str(self.city, 'city')
        _check_sex(self.sex)
        _check_datetime(self.registered_at, 'registered_at')

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() if self.last_name else self.first_name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


@dataclass
class Candidate:
    id: int
    vk_id: int
    first_name: str
    last_name: Optional[str]
    age: Optional[int]
    city: Optional[str]
    sex: int
    profile_link: Optional[str]
    created_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.vk_id, 'vk_id')
        _check_non_empty_str(self.first_name, 'first_name')
        _check_optional_str(self.last_name, 'last_name')
        _check_age(self.age)
        _check_optional_str(self.city, 'city')
        _check_sex(self.sex)
        _check_optional_str(self.profile_link, 'profile_link')
        _check_datetime(self.created_at, 'created_at')

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() if self.last_name else self.first_name

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        return cls(**data)


@dataclass
class Photo:
    id: int
    candidate_id: int
    photo_url: str
    photo_id: str
    likes_count: int
    comments_count: int
    is_avatar: bool
    is_tagged: bool
    created_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.candidate_id, 'candidate_id')
        _check_non_empty_str(self.photo_url, 'photo_url')
        _check_non_empty_str(self.photo_id, 'photo_id')
        _check_non_negative_int(self.likes_count, 'likes_count')
        _check_non_negative_int(self.comments_count, 'comments_count')
        _check_bool(self.is_avatar, 'is_avatar')
        _check_bool(self.is_tagged, 'is_tagged')
        _check_datetime(self.created_at, 'created_at')

    @property
    def popularity(self) -> int:
        return self.likes_count + self.comments_count

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Photo':
        return cls(**data)


@dataclass
class Favorite:
    id: int
    user_id: int
    candidate_id: int
    added_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_positive_int(self.candidate_id, 'candidate_id')
        _check_datetime(self.added_at, 'added_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Favorite':
        return cls(**data)


@dataclass
class Blacklist:
    id: int
    user_id: int
    candidate_id: int
    added_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_positive_int(self.candidate_id, 'candidate_id')
        _check_datetime(self.added_at, 'added_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Blacklist':
        return cls(**data)


@dataclass
class UserInterest:
    id: int
    user_id: int
    type: str
    value: str
    vk_entity_id: Optional[str]
    created_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_non_empty_str(self.type, 'type')
        _check_non_empty_str(self.value, 'value')
        _check_optional_str(self.vk_entity_id, 'vk_entity_id')
        _check_datetime(self.created_at, 'created_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserInterest':
        return cls(**data)


@dataclass
class CandidateInterest:
    id: int
    candidate_id: int
    type: str
    value: str
    vk_entity_id: Optional[str]
    created_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.candidate_id, 'candidate_id')
        _check_non_empty_str(self.type, 'type')
        _check_non_empty_str(self.value, 'value')
        _check_optional_str(self.vk_entity_id, 'vk_entity_id')
        _check_datetime(self.created_at, 'created_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CandidateInterest':
        return cls(**data)


@dataclass
class SearchWeight:
    id: int
    user_id: int
    criterion_name: str
    weight: float
    updated_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_non_empty_str(self.criterion_name, 'criterion_name')
        _check_weight(self.weight, 'weight')
        _check_datetime(self.updated_at, 'updated_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchWeight':
        # Приводим weight к float, так как из БД может прийти Decimal
        data['weight'] = float(data['weight'])
        return cls(**data)


@dataclass
class ViewedCandidate:
    id: int
    user_id: int
    candidate_id: int
    viewed_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_positive_int(self.candidate_id, 'candidate_id')
        _check_datetime(self.viewed_at, 'viewed_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ViewedCandidate':
        return cls(**data)


@dataclass
class SearchOffset:
    id: int
    user_id: int
    offset_value: int
    batch_size: int
    search_params: Optional[str]
    total_found: int
    last_search_timestamp: Optional[datetime]
    updated_at: datetime

    def __post_init__(self) -> None:
        _check_positive_int(self.id, 'id')
        _check_positive_int(self.user_id, 'user_id')
        _check_non_negative_int(self.offset_value, 'offset_value')
        _check_positive_int(self.batch_size, 'batch_size')
        _check_optional_str(self.search_params, 'search_params')
        _check_non_negative_int(self.total_found, 'total_found')
        if self.last_search_timestamp is not None:
            _check_datetime(self.last_search_timestamp, 'last_search_timestamp')
        _check_datetime(self.updated_at, 'updated_at')

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchOffset':
        return cls(**data)