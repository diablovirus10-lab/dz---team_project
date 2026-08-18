import os
import json
from typing import Any, Dict, List, Optional
import vk_api

from .api_utils import (
    batch_request,
    handle_vk_api_error,
    parse_vk_photo,
    parse_vk_user,
    retry_on_rate_limit,
)
from .exceptions import VKAccessDeniedError, VKAuthError, VKUserNotFoundError


class VKClient:
    PROFILE_FIELDS = 'bdate,city,sex'
    INTEREST_FIELDS = 'music,books,interests'
    INTEREST_TYPE_MAP = {'music': 'music', 'books': 'books', 'interests': 'interests'}

    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv('VK_GROUP_TOKEN')
        if not self.token:
            raise VKAuthError("VK_GROUP_TOKEN не найден в переменных окружения (.env)")

        group_id_raw = os.getenv('VK_GROUP_ID')
        self.group_id: Optional[int] = int(group_id_raw) if group_id_raw else None

        api_version = os.getenv('VK_API_VERSION', '5.131')

        self.session = vk_api.VkApi(token=self.token, api_version=api_version)
        self.api = self.session.get_api()

    @retry_on_rate_limit()
    def get_user_profile(self, vk_id: int) -> Dict[str, Any]:
        try:
            rows = self.api.users.get(user_ids=vk_id, fields=self.PROFILE_FIELDS)
        except vk_api.ApiError as error:
            handle_vk_api_error(error) 

        if not rows:
            raise VKUserNotFoundError(vk_id)

        parsed = parse_vk_user(rows[0])
        if parsed is None:
            raise VKUserNotFoundError(vk_id)
        return parsed

    @retry_on_rate_limit()
    def get_users_batch(self, vk_ids: List[int]) -> List[Dict[str, Any]]:
        def fetch_chunk(chunk: List[int]) -> List[Dict[str, Any]]:
            try:
                rows = self.api.users.get(
                    user_ids=','.join(str(i) for i in chunk),
                    fields=self.PROFILE_FIELDS,
                )
            except vk_api.ApiError as error:
                handle_vk_api_error(error)
            return [p for p in (parse_vk_user(r) for r in rows) if p]

        return batch_request(fetch_chunk, vk_ids, batch_size=100)

    @retry_on_rate_limit()
    def search_users(self, sex: int, age_from: int, age_to: int,
                     city_id: Optional[int] = None,
                     offset: int = 0, count: int = 20) -> Dict[str, Any]:
        params: Dict[str, Any] = {
            'sex': sex,
            'age_from': age_from,
            'age_to': age_to,
            'offset': offset,
            'count': count,
        }
        if city_id:
            params['city'] = city_id
        else:
            params['country'] = 1  

        try:
            response = self.api.users.search(**params)
        except vk_api.ApiError as error:
            handle_vk_api_error(error)

        items = [p for p in (parse_vk_user(u) for u in response.get('items', [])) if p]
        return {'items': items, 'total': response.get('count', 0)}

    def find_city_id(self, city_name: str) -> Optional[int]:
        if not city_name:
            return None
        try:
            response = self.api.database.getCities(country_id=1, q=city_name, count=1)
        except vk_api.ApiError as error:
            handle_vk_api_error(error)
        items = response.get('items', [])
        return items[0]['id'] if items else None

    @retry_on_rate_limit()
    def get_user_photos(self, vk_id: int, count: int = 10) -> List[Dict[str, Any]]:
        try:
            response = self.api.photos.getAll(
                owner_id=vk_id, extended=1, count=count,
            )
        except vk_api.ApiError as error:
            handle_vk_api_error(error)

        photos = [p for p in (parse_vk_photo(f) for f in response.get('items', [])) if p]

        if photos:
            photos[0]['is_avatar'] = True
        return photos

    @staticmethod
    def _split_interests_text(text: Optional[str]) -> List[str]:
        if not text:
            return []
        normalized = text.replace(';', ',').replace('|', ',')
        return [part.strip() for part in normalized.split(',') if part.strip()]

    @retry_on_rate_limit()
    def get_user_interests(self, vk_id: int) -> List[Dict[str, Any]]:
        interests: List[Dict[str, Any]] = []

        try:
            rows = self.api.users.get(user_ids=vk_id, fields=self.INTEREST_FIELDS)
        except vk_api.ApiError as error:
            handle_vk_api_error(error)

        if rows:
            profile = rows[0]
            for field, interest_type in self.INTEREST_TYPE_MAP.items():
                for value in self._split_interests_text(profile.get(field)):
                    interests.append({
                        'type': interest_type,
                        'value': value,
                        'vk_entity_id': None,
                    })

        try:
            groups = self.api.groups.get(user_id=vk_id, count=100)
            for group in groups.get('items', []):
                interests.append({
                    'type': 'groups',
                    'value': group.get('name', ''),
                    'vk_entity_id': f"group{group['id']}",
                })
        except vk_api.ApiError as error:
            if not isinstance(error, VKAccessDeniedError):
                try:
                    handle_vk_api_error(error)
                except VKAccessDeniedError:
                    pass
        except VKAccessDeniedError:
            pass

        return interests

    @retry_on_rate_limit()
    def get_common_friends_count(self, user_vk_id: int, candidate_vk_id: int) -> int:
        try:
            mutual = self.api.friends.getMutual(
                source_uid=user_vk_id, target_uid=candidate_vk_id,
            )
            return len(mutual or [])
        except vk_api.ApiError as error:
            try:
                handle_vk_api_error(error)
            except VKAccessDeniedError:
                return 0

    @retry_on_rate_limit()
    def send_message(self, user_id: int, text: str, keyboard=None, attachments=None) -> bool:
        """Отправить сообщение пользователю через VK API.
        
        Args:
            user_id: ID пользователя ВКонтакте
            text: Текст сообщения
            keyboard: Inline-клавиатура (словарь в формате VK)
            attachments: Список вложений (например, ["photo123_456", ...])
        
        Returns:
            True если сообщение отправлено успешно, False иначе
        """
        params: Dict[str, Any] = {
            'peer_id': user_id,
            'message': text,
            'random_id': 0,  # Будет заменён на уникальное значение
        }
        
        # Добавляем случайное число для random_id
        import random
        params['random_id'] = random.randint(-2**31, 2**31 - 1)
        
        # Добавляем клавиатуру если есть
        if keyboard is not None:
            params['keyboard'] = json.dumps(keyboard)
        
        # Добавляем вложения если есть
        if attachments:
            params['attachment'] = ','.join(str(a) for a in attachments)
        
        try:
            response = self.api.messages.send(**params)
            return response is not None and response != 0
        except vk_api.ApiError as error:
            handle_vk_api_error(error)
            return False
        except Exception:
            return False
