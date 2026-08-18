"""Database adapter for bot logic."""

from typing import List, Dict, Any, Optional, Set


class DatabaseAdapter:
    """Адаптер между Database и интерфейсом, ожидаемым BotLogic.
    
    BotLogic ожидает:
      - get_or_create_user(vk_id) -> int
      - add_favorite(user_vk_id, profile)
      - add_blacklist(user_vk_id, profile)
      - mark_viewed(user_id, profile)
      - get_favorites(user_id) -> list[dict]
      - get_viewed_vk_ids(user_id) -> set[int]
    """

    def __init__(self, database):
        self.database = database

    def get_or_create_user(self, vk_id: int) -> Optional[int]:
        """Создать или получить пользователя."""
        user = self.database.get_user_by_vk(vk_id)
        if user:
            return user.get('id') or user.get('vk_id')
        
        # Создаем пользователя с минимальными данными
        return vk_id  # возвращаем vk_id как ID для бота

    def add_favorite(self, user_vk_id: int, profile: Dict[str, Any]):
        """Добавить кандидата в избранное."""
        candidate_id = profile.get("vk_id")
        if candidate_id:
            self.database.add_to_favorites(user_vk_id, candidate_id)

    def add_blacklist(self, user_vk_id: int, profile: Dict[str, Any]):
        """Добавить кандидата в черный список."""
        candidate_id = profile.get("vk_id")
        if candidate_id:
            self.database.add_to_blacklist(user_vk_id, candidate_id)

    def mark_viewed(self, user_id: int, profile: Dict[str, Any]):
        """Отметить кандидата как просмотренного."""
        candidate_id = profile.get("vk_id")
        if candidate_id:
            self.database.mark_viewed(user_id, candidate_id)

    def get_favorites(self, user_vk_id: int) -> List[Dict[str, Any]]:
        """Получить список избранных кандидатов."""
        favorites = self.database.get_favorites(user_vk_id)
        # Преобразуем в формат, понятный bot_logic
        return [
            {
                "vk_id": fav.get("vk_id") or fav.get("candidate_id"),
                "first_name": fav.get("first_name", ""),
                "last_name": fav.get("last_name", ""),
                "age": fav.get("age"),
                "city": fav.get("city"),
                "sex": fav.get("sex"),
                "profile_link": fav.get("profile_link"),
                "photos": [],
            }
            for fav in favorites
        ]

    def get_viewed_vk_ids(self, user_id: int) -> Set[int]:
        """Получить множество просмотренных vk_id."""
        viewed = self.database.get_viewed(user_id)
        return set(viewed)
