"""
Health Check Routes Module
===========================

Este módulo define endpoints para monitoreo y health checks.
Incluye endpoints de debug para Redis.
"""

from fastapi import APIRouter, Depends
from app.domain.schemas import HealthCheckResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.core.dependencies import get_redis, get_conv_repository
from app.infrastructure.redis import RedisClient, ConversationRepository

logger = get_logger(__name__)

router = APIRouter(
    tags=["Health"],
    responses={200: {"description": "Servicio funcionando correctamente"}}
)


@router.get("/", response_model=dict)
async def root():
    """
    Endpoint raíz - información básica de la API.
    
    Returns:
        Información general de la API
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "online",
        "environment": settings.environment,
        "medical_center": settings.medical_center_name
    }


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Health check completo del sistema.
    
    Este endpoint es crucial para:
    1. **Monitoreo**: Sistemas como Kubernetes lo usan para verificar si el pod está vivo
    2. **Load Balancers**: Para saber si enviar tráfico a esta instancia
    3. **CI/CD**: Para verificar que el deploy fue exitoso
    4. **Debugging**: Para verificar el estado del modelo y sistema
    
    **Qué verifica:**
    - Si el modelo de IA está cargado
    - En qué dispositivo está corriendo (CPU/GPU)
    - Versión de la API
    
    Returns:
        Estado detallado del sistema
    """
    from app.main import ai_service
    
    return HealthCheckResponse(
        status="healthy" if ai_service and ai_service.is_ready() else "degraded",
        model_loaded=ai_service.is_ready() if ai_service else False,
        device=str(ai_service.device) if ai_service else "not_initialized",
        version=settings.app_version
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check - verifica si el servicio está listo para recibir tráfico.
    
    **Diferencia entre liveness y readiness:**
    - **Liveness** (/health): ¿El proceso está vivo?
    - **Readiness** (/ready): ¿El proceso está listo para servir requests?
    
    Un servicio puede estar vivo pero no listo (ej: mientras carga el modelo).
    
    **Kubernetes usa esto para:**
    - No enviar tráfico hasta que el servicio esté listo
    - Remover temporalmente del load balancer si no está listo
    
    Returns:
        Estado de readiness
    """
    from app.main import ai_service
    
    is_ready = ai_service and ai_service.is_ready()
    
    if not is_ready:
        logger.warning("⚠️ Servicio no está listo - modelo no cargado")
    
    return {
        "ready": is_ready,
        "message": "Servicio listo" if is_ready else "Esperando carga del modelo"
    }


@router.get("/model/info")
async def model_info():
    """
    Información detallada sobre el modelo de IA.
    
    Útil para:
    - Debugging
    - Documentación
    - Verificar configuración
    
    Returns:
        Información del modelo
    """
    from app.infrastructure.ai.model_loader import ModelLoader
    
    info = ModelLoader.get_model_info()
    
    return {
        **info,
        "config": {
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "max_conversation_history": settings.max_conversation_history
        }
    }


@router.get("/redis/test")
async def test_redis(
    redis: RedisClient = Depends(get_redis),
    repo: ConversationRepository = Depends(get_conv_repository)
):
    """
    Endpoint de testing para Redis.
    
    Verifica:
    - Conectividad con Redis
    - Operaciones básicas (set/get)
    - Conversaciones activas
    - TTL
    
    Returns:
        Estado de Redis y estadísticas
    """
    try:
        # Test de conectividad
        is_connected = redis.is_connected()
        
        # Test de operaciones básicas
        test_key = "health_check_test"
        redis.set(test_key, {"status": "ok", "timestamp": "now"}, expire=10)
        test_value = redis.get(test_key)
        redis.delete(test_key)
        
        # Estadísticas de conversaciones
        active_users = repo.get_all_user_ids()
        
        # Info detallada de cada conversación
        conversations_info = []
        for user_id in active_users[:5]:  # Máximo 5 para no sobrecargar
            ttl = repo.get_ttl(user_id)
            msg_count = repo.get_message_count(user_id)
            conversations_info.append({
                "user_id": user_id,
                "ttl_seconds": ttl,
                "message_count": msg_count
            })
        
        return {
            "status": "success",
            "redis": {
                "connected": is_connected,
                "url": settings.redis_url.split("@")[-1] if "@" in settings.redis_url else settings.redis_url,  # Ocultar password
                "test_operation": "ok" if test_value else "failed"
            },
            "conversations": {
                "total_active": len(active_users),
                "session_expire_time": settings.session_expire_time,
                "details": conversations_info
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en Redis test: {e}")
        return {
            "status": "error",
            "error": str(e),
            "redis": {
                "connected": False
            }
        }


@router.get("/redis/stats")
async def redis_stats(redis: RedisClient = Depends(get_redis)):
    """
    Estadísticas detalladas de Redis.
    
    Returns:
        Información sobre uso de memoria, claves, etc.
    """
    try:
        # Obtener todas las claves de conversaciones
        conv_keys = redis.get_keys_by_pattern("conversation:*")
        meta_keys = redis.get_keys_by_pattern("conversation_meta:*")
        rate_limit_keys = redis.get_keys_by_pattern("rate_limit:*")
        
        return {
            "status": "success",
            "keys": {
                "conversations": len(conv_keys),
                "metadata": len(meta_keys),
                "rate_limits": len(rate_limit_keys),
                "total": len(conv_keys) + len(meta_keys) + len(rate_limit_keys)
            },
            "config": {
                "session_expire_time": f"{settings.session_expire_time}s ({settings.session_expire_time // 3600}h)",
                "rate_limit_per_minute": settings.rate_limit_per_minute
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo stats de Redis: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


@router.delete("/redis/clear")
async def clear_redis(
    confirm: bool = False,
    repo: ConversationRepository = Depends(get_conv_repository)
):
    """
    Limpia todas las conversaciones de Redis.
    
    ⚠️ PELIGRO: Esta acción es irreversible.
    Solo disponible en desarrollo.
    
    Args:
        confirm: Debe ser True para confirmar la acción
    
    Returns:
        Número de conversaciones eliminadas
    """
    if not confirm:
        return {
            "status": "error",
            "message": "Debes pasar confirm=true para confirmar esta acción",
            "example": "/redis/clear?confirm=true"
        }
    
    if settings.is_production:
        return {
            "status": "error",
            "message": "Esta acción está bloqueada en producción"
        }
    
    try:
        count = repo.clear_all()
        logger.warning(f"⚠️ Redis limpiado - {count} conversaciones eliminadas")
        
        return {
            "status": "success",
            "conversations_deleted": count,
            "message": f"Se eliminaron {count} conversaciones"
        }
        
    except Exception as e:
        logger.error(f"❌ Error limpiando Redis: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

