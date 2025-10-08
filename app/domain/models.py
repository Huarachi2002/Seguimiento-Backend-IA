"""
Domain Models Module
====================

Este módulo contiene los modelos de dominio (entidades de negocio).

Diferencia entre Models y Schemas:
- Models (este archivo): Representan entidades del dominio de negocio
- Schemas: Representan la estructura de datos para API (request/response)

Por qué separar?
1. Domain Models: Lógica de negocio pura, independiente de la tecnología
2. Schemas: Cómo se serializan/deserializan los datos en la API
3. Database Models: Cómo se persisten en la base de datos

Esto sigue el principio de "Separation of Concerns".
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, field


class MessageRole(str, Enum):
    """
    Roles posibles en una conversación.
    
    Usar Enum en lugar de strings directos:
    - Previene errores de typo
    - Autocomplete en el IDE
    - Validación automática
    """
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Estado de una conversación"""
    ACTIVE = "active"
    CLOSED = "closed"
    WAITING = "waiting"  # Esperando respuesta del usuario


class AppointmentStatus(str, Enum):
    """Estado de una cita médica"""
    PENDING = "Pendiente"
    PROGRAMMED = "Programado"
    CONFIRMED = "Confirmado"
    ASISTED = "Asistido"
    LOST = "Perdido"
    REPROGRAMMED = "Reprogramado"
    CANCELLED = "Cancelado"


@dataclass
class Message:
    """
    Representa un mensaje individual en una conversación.
    
    @dataclass: Genera automáticamente __init__, __repr__, __eq__
    Esto reduce boilerplate code y hace el código más limpio.
    """
    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict] = None
    
    def is_from_user(self) -> bool:
        """Verifica si el mensaje es del usuario"""
        return self.role == MessageRole.USER
    
    def is_from_assistant(self) -> bool:
        """Verifica si el mensaje es del asistente"""
        return self.role == MessageRole.ASSISTANT


@dataclass
class Conversation:
    """
    Representa una conversación completa con un usuario.
    
    Una conversación puede tener múltiples mensajes y metadatos
    asociados (como ID del usuario, estado, etc.).
    """
    conversation_id: str
    user_id: str
    messages: List[Message] = field(default_factory=list)
    status: ConversationStatus = ConversationStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[dict] = None
    
    def add_message(self, role: MessageRole, content: str) -> Message:
        """
        Añade un mensaje a la conversación.
        
        Args:
            role: Rol del mensaje (user/assistant/system)
            content: Contenido del mensaje
        
        Returns:
            El mensaje creado
        """
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.updated_at = datetime.now()
        return message
    
    def get_recent_messages(self, limit: int = 10) -> List[Message]:
        """
        Obtiene los mensajes más recientes.
        
        Args:
            limit: Número máximo de mensajes a retornar
        
        Returns:
            Lista de mensajes recientes
        """
        return self.messages[-limit:] if len(self.messages) > limit else self.messages
    
    def close(self) -> None:
        """Cierra la conversación"""
        self.status = ConversationStatus.CLOSED
        self.updated_at = datetime.now()


@dataclass
class Patient:
    """
    Representa un paciente en el sistema.
    
    Contiene información básica del paciente necesaria
    para la verificación y gestión de citas.
    """
    patient_id: str
    phone_number: str
    name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    email: Optional[str] = None
    verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    def verify(self) -> None:
        """Marca al paciente como verificado"""
        self.verified = True
    
    def get_last_four_digits(self) -> str:
        """Obtiene los últimos 4 dígitos del teléfono"""
        return self.phone_number[-4:] if len(self.phone_number) >= 4 else ""


@dataclass
class Appointment:
    """
    Representa una cita médica.
    
    Esta es una de las entidades centrales del dominio,
    ya que el asistente está principalmente enfocado en
    gestión de citas.
    """
    appointment_id: str
    patient_id: str
    date: datetime
    provider_name: str
    location: str
    status: AppointmentStatus = AppointmentStatus.PENDING
    reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def confirm(self) -> None:
        """Confirma la cita"""
        self.status = AppointmentStatus.CONFIRMED
        self.updated_at = datetime.now()
    
    def cancel(self, reason: Optional[str] = None) -> None:
        """
        Cancela la cita.
        
        Args:
            reason: Razón de la cancelación
        """
        self.status = AppointmentStatus.CANCELLED
        if reason:
            self.notes = f"Cancelación: {reason}"
        self.updated_at = datetime.now()
    
    def reschedule(self, new_date: datetime) -> None:
        """
        Reprograma la cita.
        
        Args:
            new_date: Nueva fecha y hora
        """
        old_date = self.date
        self.date = new_date
        self.notes = f"Reprogramado de {old_date} a {new_date}"
        self.updated_at = datetime.now()
    
    def is_upcoming(self) -> bool:
        """Verifica si la cita es futura"""
        return self.date > datetime.now()


@dataclass
class ActionIntent:
    """
    Representa la intención de una acción detectada en el mensaje del usuario.
    
    El asistente debe poder identificar qué quiere hacer el usuario:
    - Agendar una cita
    - Cancelar una cita
    - Consultar próximas citas
    - etc.
    
    Esta clase encapsula esa intención.
    """
    action: str  # lookup_appointments, schedule_appointment, cancel_appointment, etc.
    params: dict = field(default_factory=dict)
    confidence: float = 1.0  # Confianza en la detección (0.0 - 1.0)
    
    def is_confident(self, threshold: float = 0.7) -> bool:
        """
        Verifica si la confianza supera el umbral.
        
        Args:
            threshold: Umbral de confianza (default: 0.7)
        
        Returns:
            True si la confianza es suficiente
        """
        return self.confidence >= threshold
