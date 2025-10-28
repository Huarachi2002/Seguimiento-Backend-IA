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
from datetime import datetime, timedelta
from app.domain.models import Conversation, ConversationState, Message, MessageRole, ConversationStatus
from app.domain.exceptions import ConversationNotFoundException
from app.services.ai_service import AIService
from app.infrastructure.redis import ConversationRepository
from app.core.logging import get_logger
from app.services.appointment_service import get_appointment_service
from app.services.reschedule_handlers import RescheduleHandlers

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
        conversation_repo: ConversationRepository,
        appointment_service=None
    ):
        """
        Inicializa el servicio de conversaciones.
        
        Args:
            ai_service: Servicio de IA para generar respuestas
            conversation_repo: Repositorio Redis para conversaciones
        """
        self.ai_service = ai_service
        self.repo = conversation_repo
        self.appointment_service = appointment_service or get_appointment_service()
        
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
        logger.info(f"🔍 Buscando conversación en Redis para user_id: {user_id}")
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
        # 1. Obtener conversacion existente (O crear si es primera vez)
        conversation = self.get_or_create_conversation(user_id)
        
        # 2. Limpiar solo el contenido del nuevo mensaje
        content_cleaned = self._clean_menssage_content(content)

        # 3. Agregar mensaje limpio al historial existente
        message = conversation.add_message(role=role, content=content_cleaned)

        # Persistir en Redis
        self.repo.save(conversation)
        
        logger.info(f"💬 Mensaje añadido a Redis: {role.value} | {content_cleaned}...")
        
        return message
    
    def _clean_menssage_content(self, content: str) -> str:
        """
        Limpia el contenido de un mensaje individual.
        
        No toca otros mensajes, solo limpia este texto.

        Limpia:
        - Prefijos incorrectos ("Asistente:", "User:", etc.)
        - Múltiples espacios
        - Saltos de línea dobles
        - Límite de longitud

        Args:
            content: Texto SIN LIMPIAR
        
        Returns:
            Texto LIMPIO
        """

        if not content:
            return ""
        
        # 1. Remover prefijos incorrectos que el modelo puede generar
        prefixes = [
            "Asistente:", "Assistant:", "Asistencia:",
            "Paciente:", "Pacientes:", "User:", "Usuario:"
        ]

        for prefix in prefixes:
            if content.startswith(prefix):
                content = content[len(prefix):].strip()

        # 2. Truncar en saltos de linea dobles
        if  "\n\n" in content:
            content = content.split("\n\n")[0]

        # 3. Truncar si aparece otro rol dentro del texto
        for delimiter in ["Paciente:", "Asistente:", "User:", "Assistant:"]:
            if delimiter in content:
                content = content.split(delimiter)[0]

        # 4. Limpiar espacios multiples
        content = " ".join(content.split())

        # 5. Limitar longitud (ej. 500 caracteres)
        MAX_LENGTH = 500
        if len(content) > MAX_LENGTH:
            logger.warning(f"⚠️ Mensaje muy largo ({len(content)} chars), truncando a {MAX_LENGTH}")
            content = content[:MAX_LENGTH] + "..."

        # 6. Asegurar que no este vacio
        if len(content.strip()) == 0:
            logger.warning(f"⚠️ Mensaje muy corto después de limpiar: '{content}'")
            return "..."  # Placeholder para evitar mensajes vacíos
        
        return content.strip()
    
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

    async def process_user_message(
        self,
        user_id: str,
        message_content: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> tuple[str, Optional[dict]]:
        """
        Procesa un mensaje del usuario con CONTROL DE FLUJO

        NUEVO FLUJO:
        1. Verificar si hay un estado activo
        2. Si hay estado, procesar segun el flujo controlado
        3. Si no hay estado, detectar nuevo intencion
        4. Solo usar modelo si no hay flujo activo
        """

        logger.info(f"Procesando mensaje de usuario: {user_id}")

        # 1. Añadir mensaje del usuario
        self.add_message(
            user_id=user_id,
            role=MessageRole.USER,
            content=message_content
        )

        # 2. Obtener conversacion
        conversation = self.get_or_create_conversation(user_id)
        logger.info(f"Estado actual: {conversation.state.value}")

        # 3. Si hay un flujo activo, procesarlo
        if conversation.is_in_flow():
            return await self._process_state_flow(
                conversation,
                user_id,
                message_content
            )
        
        # 4. Si no hay flujo, detectar nueva intención
        action = self.ai_service.detect_action(message_content, conversation)

        # ===== FLUJO: CONSULTAR PRÓXIMA CITA =====
        if action and action.action == "lookup_appointment":
            return await RescheduleHandlers.handle_lookup_appointment(
                self,
                conversation,
                user_id
            )

        # ===== FLUJO: REPROGRAMAR CITA =====
        if action and action.action == "reschedule_appointment":
            return await RescheduleHandlers.start_reschedule_flow(
                self,
                conversation,
                user_id,
                message_content,
                action.params
            )
        
        # 5. Flujo normal con modelo (solo si no hay estado activo)
        response = await self.ai_service.generate_response(
            conversation=conversation,
            user_id=user_id,
            max_tokens=max_tokens,
            temperature=temperature
        )

        self.add_message(user_id=user_id, role=MessageRole.ASSISTANT, content=response)

        return response, None
    
    async def _process_state_flow(
        self,
        conversation: Conversation,
        user_id: str,
        message: str
    ) -> tuple[str, Optional[dict]]:
        """
        Procesa el mensaje según el estado actual.
        """

        state = conversation.state

        # Mapa de estados -> handlers
        state_handlers = {
            ConversationState.RESCHEDULE_WAITING_DATE: lambda c, u, m: 
                RescheduleHandlers.handle_reschedule_date(self, c, u, m),
            ConversationState.RESCHEDULE_WAITING_TIME: lambda c, u, m:
                RescheduleHandlers.handle_reschedule_time(self, c, u, m),
            ConversationState.RESCHEDULE_CONFIRMING: lambda c, u, m:
                RescheduleHandlers.handle_reschedule_confirm(self, c, u, m),
        }

        handler = state_handlers.get(state)

        if handler:
            return await handler(conversation, user_id, message)
        
        # Fallback
        logger.warning(f"⚠️ Estado no manejado: {state}")
        conversation.clear_state()
        self.repo.save(conversation)

        return "Disculpa, hubo un error. ¿En qué puedo ayudarte?", None

    def _format_date(self, fecha: str) -> str:
        """Formatea una fecha para mostrar al usuario."""
        try:
            from datetime import datetime
            fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            return fecha_dt.strftime("%d de %B de %Y")
        except:
            return fecha

    def _format_time(self, hora: str) -> str:
        """Formatea una hora para mostrar al usuario."""
        try:
            hora_clean = hora.replace(':00.000Z', '').replace('T', ' ')
            return hora_clean.split(' ')[-1][:5]  # HH:MM
        except:
            return hora