"""VK API integration package."""

from .vk_client import VKClient
from .api_utils import parse_vk_response
from .exceptions import VKApiError

__all__ = ["VKClient", "parse_vk_response", "VKApiError"]
