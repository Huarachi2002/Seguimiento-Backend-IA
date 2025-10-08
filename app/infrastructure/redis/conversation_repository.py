"""
Conversation Repository Module
================================

Repositorio para gestionar conversaciones en Redis.

Patrón Repository:
- Encapsula la lógica de acceso a datos
- Abstrae la implementación de almacenamiento
- Facilita testing (puedes crear un mock repository)
"""

from typing import Optional
from datetime import datetime
from app.domain.models import Conversation, Message, MessageRole
from app.infrastructure.redis.redis_client import RedisClient, get_redis_client
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConversationRepository:
    """
    Repositorio para gestionar conversaciones en Redis.
    
    Estructura de claves en Redis:
    - conversation:{user_id} -> JSON con toda la conversación
    - conversation_meta:{user_id} -> Metadata (última actividad, etc.)
    """
    
    def __init__(self, redis_client: RedisClient):
        """
        Inicializa el repositorio.
        
        Args:
            redis_client: Cliente de Redis
        """
        self.redis = redis_client
        self.ttl = settings.session_expire_time  # TTL por defecto
        
        logger.info("✅ ConversationRepository inicializado")
    
    def _get_key(self, user_id: str) -> str:
        """
        Genera la clave de Redis para una conversación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Clave de Redis
        """
        return f"conversation:{user_id}"
    
    def _get_meta_key(self, user_id: str) -> str:
        """
        Genera la clave de metadata.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Clave de metadata
        """
        return f"conversation_meta:{user_id}"
    
    def save(self, conversation: Conversation, ttl: Optional[int] = None) -> bool:
        """
        Guarda una conversación en Redis.
        
        Args:
            conversation: Conversación a guardar
            ttl: Tiempo de vida en segundos (None usa el default)
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            key = self._get_key(conversation.user_id)
            expire_time = ttl or self.ttl
            
            # Serializar conversación a dict
            conversation_data = {
                "conversation_id": conversation.conversation_id,
                "user_id": conversation.user_id,
                "status": conversation.status.value,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "messages": [
                    {
                        "message_id": msg.message_id,
                        "role": msg.role.value,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in conversation.messages
                ],
                "metadata": conversation.metadata
            }
            
            # Guardar en Redis con TTL
            success = self.redis.set(key, conversation_data, expire=expire_time)
            
            if success:
                # Actualizar metadata
                meta_key = self._get_meta_key(conversation.user_id)
                meta_data = {
                    "last_activity": datetime.now().isoformat(),
                    "message_count": len(conversation.messages)
                }
                self.redis.set(meta_key, meta_data, expire=expire_time)
                
                logger.debug(
                    f"💾 Conversación guardada: {conversation.user_id} "
                    f"({len(conversation.messages)} mensajes, TTL={expire_time}s)"
                )
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error guardando conversación: {e}")
            return False
    
    def get(self, user_id: str) -> Optional[Conversation]:
        """
        Recupera una conversación de Redis.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Conversación o None si no existe
        """
        try:
            key = self._get_key(user_id)
            data = self.redis.get(key, as_json=True)
            
            if not data:
                logger.debug(f"🔍 Conversación no encontrada: {user_id}")
                return None
            
            # Deserializar mensajes
            messages = [
                Message(
                    message_id=msg["message_id"],
                    role=MessageRole(msg["role"]),
                    content=msg["content"],
                    timestamp=datetime.fromisoformat(msg["timestamp"]),
                    metadata=msg.get("metadata")
                )
                for msg in data.get("messages", [])
            ]
            
            # Reconstruir conversación
            conversation = Conversation(
                conversation_id=data["conversation_id"],
                user_id=data["user_id"]
            )
            conversation.messages = messages
            conversation.created_at = datetime.fromisoformat(data["created_at"])
            conversation.updated_at = datetime.fromisoformat(data["updated_at"])
            conversation.metadata = data.get("metadata", {})
            
            logger.debug(
                f"📖 Conversación recuperada: {user_id} "
                f"({len(messages)} mensajes)"
            )
            
            return conversation
            
        except Exception as e:
            logger.error(f"❌ Error recuperando conversación: {e}")
            return None
    
    def exists(self, user_id: str) -> bool:
        """
        Verifica si existe una conversación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si existe
        """
        key = self._get_key(user_id)
        return self.redis.exists(key)
    
    def delete(self, user_id: str) -> bool:
        """
        Elimina una conversación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se eliminó
        """
        key = self._get_key(user_id)
        meta_key = self._get_meta_key(user_id)
        
        result1 = self.redis.delete(key)
        result2 = self.redis.delete(meta_key)
        
        if result1 or result2:
            logger.info(f"🗑️ Conversación eliminada: {user_id}")
        
        return result1
    
    def get_ttl(self, user_id: str) -> int:
        """
        Obtiene el TTL restante de una conversación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Segundos restantes (-1 si no expira, -2 si no existe)
        """
        key = self._get_key(user_id)
        return self.redis.ttl(key)
    
    def extend_ttl(self, user_id: str, seconds: Optional[int] = None) -> bool:
        """
        Extiende el TTL de una conversación.
        
        Útil cuando un usuario sigue activo.
        
        Args:
            user_id: ID del usuario
            seconds: Nuevos segundos de vida (None usa el default)
        
        Returns:
            True si se extendió
        """
        key = self._get_key(user_id)
        expire_time = seconds or self.ttl
        
        result = self.redis.expire(key, expire_time)
        
        if result:
            # También extender metadata
            meta_key = self._get_meta_key(user_id)
            self.redis.expire(meta_key, expire_time)
            logger.debug(f"⏰ TTL extendido: {user_id} -> {expire_time}s")
        
        return result
    
    def get_all_user_ids(self) -> list[str]:
        """
        Obtiene todos los user_ids con conversaciones activas.
        
        Returns:
            Lista de user_ids
        """
        pattern = "conversation:*"
        keys = self.redis.get_keys_by_pattern(pattern)
        
        # Extraer user_id de cada clave
        user_ids = [key.replace("conversation:", "") for key in keys]
        
        logger.debug(f"📋 {len(user_ids)} conversaciones activas")
        
        return user_ids
    
    def get_message_count(self, user_id: str) -> int:
        """
        Obtiene el número de mensajes de una conversación.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Número de mensajes
        """
        meta_key = self._get_meta_key(user_id)
        meta = self.redis.get(meta_key, as_json=True)
        
        if meta:
            return meta.get("message_count", 0)
        
        # Si no hay metadata, contar directamente
        conversation = self.get(user_id)
        return len(conversation.messages) if conversation else 0
    
    def clear_all(self) -> int:
        """
        PELIGRO: Elimina todas las conversaciones.
        
        Solo para desarrollo/testing.
        
        Returns:
            Número de conversaciones eliminadas
        """
        if settings.is_production:
            logger.error("❌ clear_all bloqueado en producción")
            return 0
        
        user_ids = self.get_all_user_ids()
        count = 0
        
        for user_id in user_ids:
            if self.delete(user_id):
                count += 1
        
        logger.warning(f"⚠️ {count} conversaciones eliminadas")
        
        return count


# Instancia global
_conversation_repository: Optional[ConversationRepository] = None


def get_conversation_repository() -> ConversationRepository:
    """
    Obtiene la instancia global del repositorio.
    
    Returns:
        ConversationRepository
    """
    global _conversation_repository
    
    if _conversation_repository is None:
        redis_client = get_redis_client()
        _conversation_repository = ConversationRepository(redis_client)
    
    return _conversation_repository
