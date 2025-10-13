"""
Dependencies Module
===================

Este módulo centraliza las dependencias de FastAPI.

¿Qué es Dependency Injection?
Es un patrón de diseño donde las dependencias de un objeto se inyectan
desde fuera en lugar de crearlas internamente.

Ventajas:
1. Testing más fácil (puedes inyectar mocks)
2. Reutilización de código
3. Menor acoplamiento
4. Gestión centralizada de recursos (ej: conexiones a DB)

FastAPI usa este patrón extensivamente con la función Depends().
"""

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger
from app.infrastructure.redis import (
    get_redis_client,
    get_conversation_repository,
    RedisClient,
    ConversationRepository
)
from app.services.ai_service import AIService
from app.services.conversation_service import ConversationService

logger = get_logger(__name__)


# ===== Dependencia: Redis Client =====
def get_redis() -> RedisClient:
    """
    Proporciona el cliente Redis.
    
    Returns:
        Cliente Redis conectado
    """
    return get_redis_client()


# ===== Dependencia: Conversation Repository =====
def get_conv_repository() -> ConversationRepository:
    """
    Proporciona el repositorio de conversaciones.
    
    Returns:
        ConversationRepository
    """
    return get_conversation_repository()


# ===== Dependencia: Database Session =====
def get_db() -> Generator:
    """
    Proporciona una sesión de base de datos.
    
    Esta función:
    1. Crea una sesión de base de datos
    2. La proporciona al endpoint
    3. La cierra automáticamente al terminar (incluso si hay error)
    
    El patrón yield es crucial aquí:
    - Código ANTES de yield: Se ejecuta antes del endpoint
    - yield: Proporciona la sesión al endpoint
    - Código DESPUÉS de yield: Se ejecuta después (cleanup)
    
    Uso en un endpoint:
    ```python
    @app.get("/users")
    def get_users(db: Session = Depends(get_db)):
        return db.query(User).all()
    ```
    
    Yields:
        Session de SQLAlchemy
    """
    # TODO: Implementar cuando tengamos la configuración de DB
    # from app.infrastructure.database.connection import SessionLocal
    # db = SessionLocal()
    # try:
    #     yield db
    # finally:
    #     db.close()
    
    # Por ahora, placeholder
    yield None


# ===== Dependencia: Verificación de Rate Limiting =====
async def verify_rate_limit(
    user_id: str,
    redis: RedisClient = Depends(get_redis)
) -> bool:
    """
    Verifica que el usuario no exceda el límite de requests.
    
    Rate limiting es importante para:
    1. Prevenir abuso del sistema
    2. Proteger contra ataques DDoS
    3. Asegurar distribución justa de recursos
    
    Args:
        user_id: Identificador del usuario
        redis: Cliente Redis (inyectado)
    
    Returns:
        True si el usuario está dentro del límite
    
    Raises:
        HTTPException: Si se excede el límite
    """
    key = f"rate_limit:{user_id}"
    
    # Incrementar contador
    count = redis.increment(key)
    
    # Si es el primer request, establecer expiración de 60 segundos
    if count == 1:
        redis.expire(key, 60)
    
    # Verificar límite
    if count and count > settings.rate_limit_per_minute:
        logger.warning(f"⚠️ Rate limit excedido para {user_id}: {count} requests/min")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiadas solicitudes. Por favor, espera un momento."
        )
    
    logger.debug(f"✅ Rate limit OK para {user_id}: {count}/{settings.rate_limit_per_minute}")
    
    return True


# ===== Dependencia: Validación de API Key (para n8n) =====
async def validate_api_key(api_key: Optional[str] = None) -> bool:
    """
    Valida el API key para peticiones de n8n.
    
    Seguridad: Solo n8n debería poder enviar mensajes al backend.
    Esto previene que usuarios externos abusen del sistema.
    
    Args:
        api_key: API key enviado en el header
    
    Returns:
        True si el API key es válido
    
    Raises:
        HTTPException: Si el API key es inválido
    """
    if not settings.n8n_api_key:
        # Si no hay API key configurado, permitir (solo desarrollo)
        if settings.is_development:
            logger.warning("⚠️ API key no configurado - modo desarrollo")
            return True
    
    if api_key != settings.n8n_api_key:
        logger.warning(f"❌ Intento de acceso con API key inválido")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválido"
        )
    
    return True


# ===== Dependencia: Configuración =====
def get_config():
    """
    Proporciona la configuración de la aplicación.
    
    Esto permite inyectar la configuración en los endpoints,
    facilitando el testing (puedes inyectar configuración mock).
    
    Returns:
        Settings instance
    """
    return settings


# ===== Dependencia: AI Service =====
def get_ai_service() -> AIService:
    """
    Proporciona el servicio de IA.

    Usa el servicio global creado en main.py durante el startup.
    
    Returns:
        AIService instance

    Raises:
        HTTPException: Si el servicio no está listo
    """
    from app.main import ai_service

    if ai_service is None:
        logger.error("❌ Servicio de IA no está listo")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de IA no está listo. Intenta nuevamente más tarde."
        )

    return ai_service


# ===== Dependencia: Conversation Service =====
def get_conversation_service(
    ai_service: AIService = Depends(get_ai_service),
    conv_repo: ConversationRepository = Depends(get_conv_repository)
) -> ConversationService:
    """
    Proporciona el servicio de conversaciones.

    Crea una nueva instancia del servicio con las dependencias inyectadas.
    
    Args:
        ai_service: Servicio de IA (inyectado)
        conv_repo: Repositorio de conversaciones (inyectado)
    
    Returns:
        ConversationService instance
    """
    return ConversationService(
        ai_service=ai_service,
        conversation_repo=conv_repo
    )
