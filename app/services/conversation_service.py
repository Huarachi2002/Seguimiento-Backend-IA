"""
Conversation Service Module
============================

Este servicio maneja toda la lógica relacionada con conversaciones.

Responsabilidades:
1. Crear y gestionar conversaciones
2. Almacenar/recuperar mensajes
3. Mantener el estado de la conversación
4. Integrar con el AIService para generar respuestas

Ahora usa Redis para persistencia temporal de conversaciones.
"""

from typing import Optional
from datetime import datetime
from app.domain.models import Conversation, Message, MessageRole, ConversationStatus
from app.domain.exceptions import ConversationNotFoundException
from app.services.ai_service import AIService
from app.infrastructure.redis import ConversationRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConversationService:
    """
    Servicio para gestionar conversaciones con Redis.
    
    Las conversaciones se almacenan en Redis con TTL automático,
    perfecto para contexto conversacional temporal.
    """
    
    def __init__(
        self,
        ai_service: AIService,
        conversation_repo: ConversationRepository
    ):
        """
        Inicializa el servicio de conversaciones.
        
        Args:
            ai_service: Servicio de IA para generar respuestas
            conversation_repo: Repositorio Redis para conversaciones
        """
        self.ai_service = ai_service
        self.repo = conversation_repo
        
        logger.info("✅ ConversationService inicializado con Redis")
    
    def get_or_create_conversation(self, user_id: str) -> Conversation:
        """
        Obtiene una conversación existente o crea una nueva.
        
        Ahora usa Redis para persistencia.
        
        Args:
            user_id: ID del usuario (número de teléfono)
        
        Returns:
            Conversación del usuario
        """
        # Intentar obtener de Redis
        conversation = self.repo.get(user_id)
        
        if conversation is None:
            # Crear nueva conversación
            conversation = Conversation(
                conversation_id=f"conv_{user_id}_{int(datetime.now().timestamp())}",
                user_id=user_id
            )
            # Guardar en Redis
            self.repo.save(conversation)
            logger.info(f"📝 Nueva conversación creada en Redis: {conversation.conversation_id}")
        else:
            # Extender TTL si existe (usuario activo)
            self.repo.extend_ttl(user_id)
            logger.debug(f"📖 Conversación recuperada de Redis: {conversation.conversation_id}")
        
        return conversation
    
    def add_message(
        self,
        user_id: str,
        role: MessageRole,
        content: str
    ) -> Message:
        """
        Añade un mensaje a una conversación.
        
        Args:
            user_id: ID del usuario
            role: Rol del mensaje (user/assistant/system)
            content: Contenido del mensaje
        
        Returns:
            Mensaje creado
        """
        conversation = self.get_or_create_conversation(user_id)
        message = conversation.add_message(role=role, content=content)
        
        # Persistir en Redis
        self.repo.save(conversation)
        
        logger.info(f"💬 Mensaje añadido a Redis: {role.value} | {content[:50]}...")
        
        return message
    
    def process_user_message(
        self,
        user_id: str,
        message_content: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> tuple[str, Optional[dict]]:
        """
        Procesa un mensaje del usuario y genera una respuesta.
        
        Este es el método principal del servicio. Realiza:
        1. Añade el mensaje del usuario a la conversación
        2. Detecta intenciones/acciones
        3. Genera respuesta con IA
        4. Añade la respuesta a la conversación
        
        Args:
            user_id: ID del usuario
            message_content: Contenido del mensaje del usuario
            max_tokens: Máximo de tokens para la respuesta
            temperature: Temperatura del modelo
        
        Returns:
            Tupla (respuesta_generada, acción_detectada)
        """
        logger.info(f"🔄 Procesando mensaje de usuario: {user_id}")
        
        # 1. Añadir mensaje del usuario
        self.add_message(
            user_id=user_id,
            role=MessageRole.USER,
            content=message_content
        )
        
        # 2. Obtener conversación
        conversation = self.get_or_create_conversation(user_id)
        
        # 3. Detectar acciones/intenciones
        action = self.ai_service.detect_action(message_content, conversation)
        action_data = None
        if action and action.is_confident():
            action_data = {
                "action": action.action,
                "params": action.params
            }
            logger.info(f"🎯 Acción detectada con confianza: {action.action}")
        
        # 4. Generar respuesta con IA
        response = self.ai_service.generate_response(
            conversation=conversation,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # 5. Añadir respuesta del asistente
        self.add_message(
            user_id=user_id,
            role=MessageRole.ASSISTANT,
            content=response
        )
        
        logger.info(f"✅ Mensaje procesado exitosamente")
        
        return response, action_data
    
    def get_conversation(self, user_id: str) -> Conversation:
        """
        Obtiene una conversación por user_id.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            Conversación del usuario
        
        Raises:
            ConversationNotFoundException: Si no existe
        """
        conversation = self.repo.get(user_id)
        
        if conversation is None:
            raise ConversationNotFoundException(user_id)
        
        return conversation
    
    def close_conversation(self, user_id: str) -> None:
        """
        Cierra una conversación.
        
        Args:
            user_id: ID del usuario
        """
        conversation = self.get_conversation(user_id)
        conversation.close()
        
        # Persistir en Redis
        self.repo.save(conversation)
        
        logger.info(f"🔒 Conversación cerrada: {conversation.conversation_id}")
    
    def get_conversation_history(
        self,
        user_id: str,
        limit: Optional[int] = None
    ) -> list[Message]:
        """
        Obtiene el historial de una conversación.
        
        Args:
            user_id: ID del usuario
            limit: Número máximo de mensajes a retornar
        
        Returns:
            Lista de mensajes
        """
        conversation = self.get_conversation(user_id)
        
        if limit:
            return conversation.get_recent_messages(limit)
        
        return conversation.messages
    
    def clear_old_conversations(self, hours: int = 24) -> int:
        """
        Limpia conversaciones antiguas para liberar memoria.
        
        Con Redis, el TTL automático maneja esto, pero este método
        permite limpieza manual si es necesario.
        
        Args:
            hours: Horas de inactividad para considerar una conversación antigua
        
        Returns:
            Número de conversaciones eliminadas
        """
        from datetime import timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        to_remove = []
        
        # Obtener todas las conversaciones activas
        user_ids = self.repo.get_all_user_ids()
        
        for user_id in user_ids:
            conversation = self.repo.get(user_id)
            if conversation and conversation.updated_at < cutoff_time:
                to_remove.append(user_id)
        
        # Eliminar conversaciones antiguas
        for user_id in to_remove:
            self.repo.delete(user_id)
            logger.info(f"🗑️ Conversación antigua eliminada: {user_id}")
        
        logger.info(f"🧹 {len(to_remove)} conversaciones antiguas eliminadas")
        
        return len(to_remove)
    
    def get_active_conversations_count(self) -> int:
        """
        Obtiene el número de conversaciones activas en Redis.
        
        Returns:
            Número de conversaciones activas
        """
        return len(self.repo.get_all_user_ids())
    
    def delete_conversation(self, user_id: str) -> bool:
        """
        Elimina completamente una conversación de Redis.
        
        Args:
            user_id: ID del usuario
        
        Returns:
            True si se eliminó exitosamente
        """
        result = self.repo.delete(user_id)
        
        if result:
            logger.info(f"🗑️ Conversación eliminada: {user_id}")
        
        return result
