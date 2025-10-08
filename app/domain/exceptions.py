"""
Custom Exceptions Module
=========================

Este módulo define excepciones personalizadas para el dominio.

Por qué excepciones personalizadas?
1. Claridad: El nombre de la excepción describe el error
2. Control: Puedes manejar errores específicos de forma diferente
3. Información: Puedes añadir datos adicionales al error
4. Consistencia: Todas las excepciones del dominio en un lugar
"""


class DomainException(Exception):
    """
    Excepción base para errores de dominio.
    
    Todas las excepciones específicas heredan de esta.
    Esto permite capturar cualquier error de dominio con:
    except DomainException as e:
    """
    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ModelNotLoadedException(DomainException):
    """Se lanza cuando se intenta usar el modelo y no está cargado"""
    def __init__(self):
        super().__init__(
            message="El modelo de IA no está cargado",
            details={"suggestion": "Espera a que el modelo termine de cargar"}
        )


class ConversationNotFoundException(DomainException):
    """Se lanza cuando no se encuentra una conversación"""
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversación no encontrada: {conversation_id}",
            details={"conversation_id": conversation_id}
        )


class PatientNotFoundException(DomainException):
    """Se lanza cuando no se encuentra un paciente"""
    def __init__(self, identifier: str):
        super().__init__(
            message=f"Paciente no encontrado: {identifier}",
            details={"identifier": identifier}
        )


class PatientNotVerifiedException(DomainException):
    """Se lanza cuando un paciente no está verificado"""
    def __init__(self, patient_id: str):
        super().__init__(
            message="El paciente no ha sido verificado",
            details={
                "patient_id": patient_id,
                "suggestion": "Solicita verificación con últimos 4 dígitos del teléfono"
            }
        )


class AppointmentNotFoundException(DomainException):
    """Se lanza cuando no se encuentra una cita"""
    def __init__(self, appointment_id: str):
        super().__init__(
            message=f"Cita no encontrada: {appointment_id}",
            details={"appointment_id": appointment_id}
        )


class AppointmentConflictException(DomainException):
    """Se lanza cuando hay un conflicto con una cita (horario ocupado)"""
    def __init__(self, date: str, provider: str):
        super().__init__(
            message="Conflicto de horario para la cita",
            details={
                "date": date,
                "provider": provider,
                "suggestion": "Ofrece horarios alternativos"
            }
        )


class InvalidContextException(DomainException):
    """Se lanza cuando el mensaje está fuera del contexto permitido"""
    def __init__(self, message: str):
        super().__init__(
            message="Mensaje fuera del contexto permitido",
            details={
                "user_message": message,
                "suggestion": "Redirige al usuario al contexto de citas médicas"
            }
        )


class ValidationException(DomainException):
    """Se lanza cuando falla la validación de datos"""
    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Validación fallida para {field}",
            details={
                "field": field,
                "reason": reason
            }
        )


class RateLimitExceededException(DomainException):
    """Se lanza cuando se excede el límite de requests"""
    def __init__(self, user_id: str, limit: int):
        super().__init__(
            message="Límite de solicitudes excedido",
            details={
                "user_id": user_id,
                "limit_per_minute": limit,
                "suggestion": "Espera un momento antes de reintentar"
            }
        )


class ExternalServiceException(DomainException):
    """Se lanza cuando falla un servicio externo (n8n, DB, etc.)"""
    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"Error en servicio externo: {service}",
            details={
                "service": service,
                "reason": reason
            }
        )
