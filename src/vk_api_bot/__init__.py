"""VK API integration package."""

from .vk_client import VKClient
from .api_utils import parse_vk_user, parse_vk_photo
from .exceptions import VKAPIError

__all__ = ["VKClient", "parse_vk_user", "parse_vk_photo", "VKAPIError"]
