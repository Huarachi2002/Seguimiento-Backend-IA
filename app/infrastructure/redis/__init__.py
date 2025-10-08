"""
Redis Infrastructure Package
=============================

Exporta el cliente Redis y repositorios relacionados.
"""

from app.infrastructure.redis.redis_client import (
    RedisClient,
    get_redis_client,
    close_redis_client
)
from app.infrastructure.redis.conversation_repository import (
    ConversationRepository,
    get_conversation_repository
)

__all__ = [
    "RedisClient",
    "get_redis_client",
    "close_redis_client",
    "ConversationRepository",
    "get_conversation_repository"
]
