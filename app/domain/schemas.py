"""
Pydantic Schemas Module
========================

Este módulo contiene los schemas de Pydantic para validación de datos de API.

Diferencia clave:
- Models (domain/models.py): Lógica de negocio
- Schemas (este archivo): Validación y serialización de datos API

Pydantic se encarga automáticamente de:
1. Validar tipos de datos
2. Convertir tipos cuando es posible
3. Generar documentación OpenAPI/Swagger
4. Proporcionar mensajes de error claros
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from app.domain.models import MessageRole, ConversationStatus, AppointmentStatus


# ===== Schemas para Mensajes =====

class MessageSchema(BaseModel):
    """
    Schema para un mensaje en una conversación.
    
    Field() permite añadir:
    - description: Para documentación
    - examples: Ejemplos en Swagger
    - ge/le: Validación de rangos numéricos
    - min_length/max_length: Para strings
    """
    role: MessageRole = Field(
        description="Rol del mensaje (user, assistant, system)",
        example="user"
    )
    content: str = Field(
        min_length=1,
        max_length=2000,
        description="Contenido del mensaje",
        example="Hola, quiero agendar una cita"
    )
    timestamp: Optional[datetime] = None
    
    class Config:
        """
        Configuración del schema.
        
        use_enum_values: Usa el valor del enum en lugar del nombre
        json_schema_extra: Añade ejemplos a la documentación
        """
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "Buenos días, necesito agendar una cita",
                "timestamp": "2025-10-04T10:30:00"
            }
        }


# ===== Schemas para Chat =====

class ChatRequest(BaseModel):
    """
    Schema para solicitud de chat.
    
    Esta es la estructura que n8n enviará al backend.
    """
    messages: List[MessageSchema] = Field(
        description="Historial de mensajes de la conversación",
        min_items=1
    )
    user_id: str = Field(
        description="ID único del usuario (generalmente el número de teléfono)",
        example="+59170123456"
    )
    max_tokens: Optional[int] = Field(
        default=150,
        ge=10,
        le=500,
        description="Máximo de tokens a generar en la respuesta"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Temperatura del modelo (0=determinístico, 1=creativo)"
    )
    
    @validator('user_id')
    def validate_user_id(cls, v):
        """
        Validador personalizado para user_id.
        
        Los validadores permiten lógica de validación compleja.
        Se ejecutan automáticamente cuando se crea una instancia.
        """
        if not v or len(v) < 3:
            raise ValueError('user_id debe tener al menos 3 caracteres')
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {"role": "user", "content": "Hola, quiero agendar una cita"}
                ],
                "user_id": "+59170123456",
                "max_tokens": 150,
                "temperature": 0.7
            }
        }


class ChatResponse(BaseModel):
    """Schema para respuesta de chat"""
    response: str = Field(
        description="Respuesta generada por el asistente"
    )
    user_id: str = Field(
        description="ID del usuario"
    )
    conversation_id: str = Field(
        description="ID de la conversación"
    )
    action: Optional[str] = Field(
        None,
        description="Acción detectada (si aplica)"
    )
    params: Optional[dict] = Field(
        None,
        description="Parámetros de la acción detectada"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp de la respuesta"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Claro, con gusto le ayudo a agendar su cita. ¿Para qué fecha desea la cita?",
                "user_id": "+59170123456",
                "conversation_id": "conv_59170123456",
                "action": "schedule_appointment",
                "params": {"status": "collecting_info"},
                "timestamp": "2025-10-04T10:30:05"
            }
        }


# ===== Schemas para Conversación =====

class ConversationSchema(BaseModel):
    """Schema para una conversación completa"""
    conversation_id: str
    user_id: str
    messages: List[MessageSchema]
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    
    class Config:
        use_enum_values = True


# ===== Schemas para Pacientes =====

class PatientCreate(BaseModel):
    """Schema para crear un paciente"""
    phone_number: str = Field(
        description="Número de teléfono del paciente",
        example="+59170123456"
    )
    name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=200,
        description="Nombre completo del paciente"
    )
    email: Optional[str] = Field(
        None,
        description="Email del paciente"
    )
    date_of_birth: Optional[datetime] = None
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Valida formato de teléfono"""
        # Remover espacios y caracteres especiales excepto +
        cleaned = ''.join(c for c in v if c.isdigit() or c == '+')
        if len(cleaned) < 8:
            raise ValueError('Número de teléfono inválido')
        return cleaned


class PatientSchema(PatientCreate):
    """Schema completo de paciente"""
    patient_id: str
    verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True  # Permite crear desde ORM models


# ===== Schemas para Citas =====

class AppointmentCreate(BaseModel):
    """Schema para crear una cita"""
    patient_id: str
    date: datetime = Field(
        description="Fecha y hora de la cita"
    )
    provider_name: str = Field(
        description="Nombre del profesional",
        example="Dr. Juan Pérez"
    )
    location: str = Field(
        description="Ubicación de la cita",
        example="Consultorio 201"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Motivo de la consulta"
    )
    
    @validator('date')
    def validate_date(cls, v):
        """Valida que la fecha sea futura"""
        if v < datetime.now():
            raise ValueError('La fecha de la cita debe ser futura')
        return v


class AppointmentSchema(AppointmentCreate):
    """Schema completo de cita"""
    appointment_id: str
    status: AppointmentStatus
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


class AppointmentUpdate(BaseModel):
    """Schema para actualizar una cita"""
    date: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None


# ===== Schemas para Respuestas Genéricas =====

class HealthCheckResponse(BaseModel):
    """Schema para health check"""
    status: str = Field(description="Estado del servicio")
    model_loaded: bool = Field(description="Si el modelo está cargado")
    device: str = Field(description="Dispositivo utilizado (cpu/cuda)")
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = Field(description="Versión de la API")


class ErrorResponse(BaseModel):
    """Schema para respuestas de error"""
    error: str = Field(description="Tipo de error")
    message: str = Field(description="Mensaje de error")
    detail: Optional[str] = Field(None, description="Detalles adicionales")
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Datos inválidos en la solicitud",
                "detail": "El campo 'user_id' es requerido",
                "timestamp": "2025-10-04T10:30:00"
            }
        }
