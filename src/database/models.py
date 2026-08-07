from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class User:
    """Определяет структуру данных пользователя"""
    id: int
    vk_id: int
    first_name: str
    last_name: str
    age: int
    city: str
    sex: int
    registered_at: datetime

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        return cls(
            id=data['id'],
            vk_id=data['vk_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            city=data['city'],
            sex=data['sex'],
            registered_at=data['registered_at']
        )


@dataclass
class Candidate:
    """Модель кандидата"""
    id: int
    vk_id: int
    first_name: str
    last_name: str
    age: int
    city: str
    sex: int
    profile_link: str
    created_at: datetime

    @classmethod
    def from_dict(cls, data: Dict) -> 'Candidate':
        return cls(
            id=data['id'],
            vk_id=data['vk_id'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            age=data['age'],
            city=data['city'],
            sex=data['sex'],
            profile_link=data['profile_link'],
            created_at=data['created_at']
        )


@dataclass
class Photo:
    """Модель фотографии"""
    id: int
    candidate_id: int
    photo_url: str
    photo_id: str
    likes_count: int
    comments_count: int
    is_avatar: bool
    is_tagged: bool
    created_at: datetime

    @classmethod
    def from_dict(cls, data: Dict) -> 'Photo':
        return cls(
            id=data['id'],
            candidate_id=data['candidate_id'],
            photo_url=data['photo_url'],
            photo_id=data['photo_id'],
            likes_count=data['likes_count'],
            comments_count=data['comments_count'],
            is_avatar=data['is_avatar'],
            is_tagged=data['is_tagged'],
            created_at=data['created_at']
        )


@dataclass
class Favorite:
    """Модель избранного"""
    id: int
    user_id: int
    candidate_id: int
    added_at: datetime


@dataclass
class Blacklist:
    """Модель чёрного списка"""
    id: int
    user_id: int
    candidate_id: int
    added_at: datetime
