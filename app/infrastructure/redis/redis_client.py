"""
Redis Client Module
===================

Este módulo maneja la conexión y operaciones con Redis.

Redis se usa para:
1. Cache de sesiones/conversaciones (temporal)
2. Rate limiting
3. Datos que expiran automáticamente (TTL)

Ventajas de Redis:
- Muy rápido (in-memory)
- TTL automático (Time To Live)
- Estructuras de datos ricas (hash, list, set, etc.)
- Persistencia opcional
"""

import json
import redis
from typing import Optional, Any
from datetime import timedelta
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """
    Cliente Redis para gestionar conexiones y operaciones.
    
    Este cliente proporciona métodos de alto nivel para:
    - Almacenar/recuperar datos JSON
    - Gestionar TTL (expiración)
    - Rate limiting
    - Operaciones atómicas
    """
    
    def __init__(self):
        """Inicializa la conexión con Redis."""
        self._client: Optional[redis.Redis] = None
        self._is_connected = False
    
    def connect(self) -> None:
        """
        Establece conexión con Redis.
        
        Raises:
            redis.ConnectionError: Si no se puede conectar
        """
        try:
            # Parsear URL de Redis
            self._client = redis.from_url(
                settings.redis_url,
                password=settings.redis_password,
                decode_responses=True,  # Decodifica bytes a strings automáticamente
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Verificar conexión
            self._client.ping()
            self._is_connected = True
            
            logger.info(f"✅ Conectado a Redis: {settings.redis_url}")
            
        except redis.ConnectionError as e:
            logger.error(f"❌ Error conectando a Redis: {e}")
            self._is_connected = False
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado en Redis: {e}")
            self._is_connected = False
            raise
    
    def disconnect(self) -> None:
        """Cierra la conexión con Redis."""
        if self._client:
            self._client.close()
            self._is_connected = False
            logger.info("🔌 Desconectado de Redis")
    
    def is_connected(self) -> bool:
        """
        Verifica si Redis está conectado.
        
        Returns:
            True si está conectado
        """
        if not self._is_connected or not self._client:
            return False
        
        try:
            self._client.ping()
            return True
        except:
            self._is_connected = False
            return False
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Guarda un valor en Redis.
        
        Args:
            key: Clave única
            value: Valor (será serializado a JSON)
            expire: Tiempo de expiración en segundos (None = no expira)
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            # Serializar a JSON si no es string
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            
            if expire:
                self._client.setex(key, expire, value)
            else:
                self._client.set(key, value)
            
            logger.debug(f"📝 Redis SET: {key} (expire={expire}s)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error en Redis SET: {e}")
            return False
    
    def get(self, key: str, as_json: bool = True) -> Optional[Any]:
        """
        Recupera un valor de Redis.
        
        Args:
            key: Clave a buscar
            as_json: Si True, deserializa el valor como JSON
        
        Returns:
            Valor almacenado o None si no existe
        """
        try:
            value = self._client.get(key)
            
            if value is None:
                logger.debug(f"🔍 Redis GET: {key} -> No encontrado")
                return None
            
            # Deserializar JSON si se solicita
            if as_json:
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    # Si no es JSON válido, devolver como string
                    pass
            
            logger.debug(f"🔍 Redis GET: {key} -> Encontrado")
            return value
            
        except Exception as e:
            logger.error(f"❌ Error en Redis GET: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Elimina una clave de Redis.
        
        Args:
            key: Clave a eliminar
        
        Returns:
            True si se eliminó
        """
        try:
            result = self._client.delete(key)
            logger.debug(f"🗑️ Redis DELETE: {key}")
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Error en Redis DELETE: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verifica si una clave existe.
        
        Args:
            key: Clave a verificar
        
        Returns:
            True si existe
        """
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.error(f"❌ Error en Redis EXISTS: {e}")
            return False
    
    def expire(self, key: str, seconds: int) -> bool:
        """
        Establece expiración para una clave existente.
        
        Args:
            key: Clave a expirar
            seconds: Segundos hasta expiración
        
        Returns:
            True si se estableció la expiración
        """
        try:
            result = self._client.expire(key, seconds)
            logger.debug(f"⏰ Redis EXPIRE: {key} -> {seconds}s")
            return bool(result)
        except Exception as e:
            logger.error(f"❌ Error en Redis EXPIRE: {e}")
            return False
    
    def ttl(self, key: str) -> int:
        """
        Obtiene el tiempo de vida restante de una clave.
        
        Args:
            key: Clave a consultar
        
        Returns:
            Segundos restantes (-1 si no expira, -2 si no existe)
        """
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"❌ Error en Redis TTL: {e}")
            return -2
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Incrementa un contador.
        
        Útil para rate limiting y contadores.
        
        Args:
            key: Clave del contador
            amount: Cantidad a incrementar
        
        Returns:
            Nuevo valor del contador
        """
        try:
            result = self._client.incr(key, amount)
            logger.debug(f"➕ Redis INCR: {key} -> {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Error en Redis INCR: {e}")
            return None
    
    def get_keys_by_pattern(self, pattern: str) -> list[str]:
        """
        Busca claves por patrón.
        
        Args:
            pattern: Patrón de búsqueda (ej: "conversation:*")
        
        Returns:
            Lista de claves que coinciden
        """
        try:
            keys = self._client.keys(pattern)
            logger.debug(f"🔎 Redis KEYS: {pattern} -> {len(keys)} encontradas")
            return keys
        except Exception as e:
            logger.error(f"❌ Error en Redis KEYS: {e}")
            return []
    
    def flush_db(self) -> bool:
        """
        PELIGRO: Elimina TODAS las claves de la DB actual.
        
        Solo usar en desarrollo/testing.
        
        Returns:
            True si se limpió exitosamente
        """
        if settings.is_production:
            logger.error("❌ FLUSH_DB bloqueado en producción")
            return False
        
        try:
            self._client.flushdb()
            logger.warning("⚠️ Redis DB limpiada completamente")
            return True
        except Exception as e:
            logger.error(f"❌ Error en Redis FLUSHDB: {e}")
            return False


# Instancia global (Singleton)
_redis_client: Optional[RedisClient] = None


def get_redis_client() -> RedisClient:
    """
    Obtiene la instancia global del cliente Redis.
    
    Patrón Singleton: solo existe una instancia en toda la app.
    
    Returns:
        Cliente Redis
    """
    global _redis_client
    
    if _redis_client is None:
        _redis_client = RedisClient()
        _redis_client.connect()
    
    return _redis_client


def close_redis_client() -> None:
    """Cierra la conexión global de Redis."""
    global _redis_client
    
    if _redis_client:
        _redis_client.disconnect()
        _redis_client = None
