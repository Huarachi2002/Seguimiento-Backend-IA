"""
Chat Routes Module
==================

Este módulo define los endpoints relacionados con el chat.
Ahora integrado con Redis para contexto conversacional.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.domain.schemas import ChatRequest, ChatResponse
from app.domain.exceptions import ModelNotLoadedException, DomainException
from app.core.dependencies import (
    verify_rate_limit,
    get_conversation_service,
    get_redis
)
from app.services.conversation_service import ConversationService
from app.infrastructure.redis import RedisClient
from app.core.logging import get_logger

logger = get_logger(__name__)

# Crear el router
# prefix="/chat" significa que todas las rutas aquí tendrán /chat como prefijo
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],  # Para agrupar en la documentación Swagger
    responses={
        503: {"description": "Modelo no disponible"},
        429: {"description": "Demasiadas solicitudes"},
        500: {"description": "Error interno del servidor"}
    }
)


@router.post("/", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(
    request: ChatRequest,
    conversation_service: ConversationService = Depends(get_conversation_service)
) -> ChatResponse:
    """
    Endpoint principal para procesar mensajes de chat.
    
    Este endpoint:
    1. Recibe un mensaje del usuario (vía n8n)
    2. Procesa el mensaje con el modelo de IA
    3. Detecta intenciones/acciones
    4. Retorna la respuesta generada
    
    Ahora usa Redis para almacenar el contexto conversacional con TTL automático.
    
    **Flujo de integración con n8n:**
    ```
    WhatsApp -> n8n Webhook -> Este Endpoint -> Respuesta -> n8n -> WhatsApp
    ```
    
    **Args:**
    - request: Objeto ChatRequest con:
        - messages: Historial de mensajes
        - user_id: ID del usuario (número de teléfono)
        - max_tokens: Opcional, tokens máximos para respuesta
        - temperature: Opcional, creatividad del modelo
    
    **Returns:**
    - ChatResponse con:
        - response: Respuesta generada
        - user_id: ID del usuario
        - conversation_id: ID de la conversación
        - action: Acción detectada (si aplica)
        - params: Parámetros de la acción
    
    **Errores posibles:**
    - 503: Si el modelo no está cargado
    - 429: Si se excede el límite de requests
    - 500: Error interno al procesar
    """
    try:
        logger.info(f"📨 Solicitud de chat recibida de usuario: {request.user_id}")
        
        # Verificar rate limiting
        redis = get_redis()
        await verify_rate_limit(request.user_id, redis)
        logger.info(f"✅ Rate limit verificado para usuario: {request.user_id}")
        
        # Obtener el último mensaje del usuario
        last_message = request.messages[-1]
        logger.info(f"📝 Último mensaje del usuario: {last_message.content[:50]}...")
        
        if not last_message.content.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El mensaje no puede estar vacío"
            )
        
        # Procesar el mensaje (ahora consulta BD para verificar paciente)
        response_text, action_data = await conversation_service.process_user_message(
            user_id=request.user_id,
            message_content=last_message.content,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )

        logger.info(f"🤖 Respuesta generada: {response_text}")
        
        # Obtener la conversación para el ID
        conversation = conversation_service.get_or_create_conversation(request.user_id)
        
        # Construir respuesta
        response = ChatResponse(
            response=response_text,
            user_id=request.user_id,
            conversation_id=conversation.conversation_id,
            action=action_data.get("action") if action_data else None,
            params=action_data.get("params") if action_data else None
        )
        
        logger.info(f"✅ Respuesta generada exitosamente para {request.user_id}")
        logger.info(f" Estado actual: {conversation.state.value}, Data: {conversation.state_data}")
        
        return response
        
    except ModelNotLoadedException as e:
        logger.error(f"❌ Modelo no cargado: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo de IA aún no está disponible. Por favor, intenta en unos momentos."
        )
    
    except DomainException as e:
        logger.error(f"❌ Error de dominio: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    
    except Exception as e:
        logger.error(f"❌ Error inesperado en /chat: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error procesando la solicitud. Por favor, intenta nuevamente."
        )


@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    limit: int = 10,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Obtiene el historial de chat de un usuario desde Redis.
    
    Útil para:
    - Debugging
    - Análisis de conversaciones
    - Dashboard de administración
    
    Args:
        user_id: ID del usuario
        limit: Número máximo de mensajes a retornar
    
    Returns:
        Lista de mensajes del usuario
    """
    try:
        messages = conversation_service.get_conversation_history(
            user_id=user_id,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "message_count": len(messages),
            "messages": [
                {
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat()
                }
                for msg in messages
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo historial: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró historial para el usuario {user_id}"
        )


@router.delete("/conversation/{user_id}")
async def close_conversation(user_id: str):
    """
    Cierra una conversación activa.
    
    Útil cuando:
    - El usuario finaliza explícitamente la conversación
    - Se detecta inactividad prolongada
    - El usuario solicita eliminar su historial
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Confirmación de cierre
    """
    try:
        from app.main import conversation_service
        
        conversation_service.close_conversation(user_id)
        
        return {
            "message": "Conversación cerrada exitosamente",
            "user_id": user_id
        }
        
    except Exception as e:
        logger.error(f"❌ Error cerrando conversación: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró conversación activa para {user_id}"
        )
    

@router.delete("/{user_id}/reset", status_code=200)
async def reset_conversation(
    user_id: str,
    conversation_service: ConversationService = Depends(get_conversation_service)
):
    """
    Resetea la conversación de un usuario (limpia Redis).
    
    Útil cuando:
    - El historial está corrupto (mensajes mal formateados)
    - Se quiere empezar desde cero
    - Debugging/testing
    
    Args:
        user_id: ID del usuario
    
    Returns:
        Confirmación de eliminación
    
    Example:
        DELETE http://localhost:8000/api/v1/chat/76023033/reset
    """
    logger.info(f"🗑️ Reseteando conversación para: {user_id}")
    
    try:
        deleted = conversation_service.delete_conversation(user_id)
        
        if deleted:
            return {
                "message": f"Conversación de {user_id} eliminada exitosamente",
                "user_id": user_id,
                "status": "reset"
            }
        
        return {
            "message": f"No había conversación activa para {user_id}",
            "user_id": user_id,
            "status": "not_found"
        }
        
    except Exception as e:
        logger.error(f"❌ Error reseteando conversación: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al resetear conversación: {str(e)}"
        )
