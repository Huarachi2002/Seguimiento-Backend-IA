"""
Appointment Service Module
============================

Servicio para manejar la logica de agendamiento de citas.

Flujo:
1. Detectar intencion de agendar
2. Extraer datos del mensaje
3. Pedir datos faltantes conversacionalmente
4. Validar datos
5. Enviar a NestJS para crear la cita
"""

from typing import Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from app.domain.models import Conversation, ConversationState, Message, MessageRole
from app.infrastructure.http import SeguimientoClient
from app.core.logging import get_logger

logger = get_logger(__name__)

class AppointmentService:
    """
    Servicio para gestionar agendamiento de citas con flujo conversacional.
    """

    def __init__(self, seguimiento_client: SeguimientoClient):
        self.seguimiento_client = seguimiento_client
        logger.info("AppointmentService inicializado")

    async def handle_schedule_request(
        self,
        conversation: Conversation,
        extracted_data: Dict[str, Any],
        missing_fields: list,
        patient_id: str
    ) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Maneja una solicitud de agendamiento de cita.

        Flujo:
        1. Si faltan datos, preguntar conversacionalmente
        2. Si hay todos los datos, validar
        3. Si es valido, crear cita en NestJS
        4. Retornar mensaje de confirmacion

        Args:
            conversation: Conversacion actual
            extracted_data: Datos extraidos del mensaje (fecha, hora, motivo)
            missing_fields: Lista de campos faltantes
            patient_id: ID del paciente

        Returns:
            Tupla (mensaje_respuesta, datos_cita_creada)
        """

        logger.info(f"Procesando solicitud de cita para paciente {patient_id}")
        logger.info(f"Datos extraidos: {extracted_data}, Campos faltantes: {missing_fields}")
        
        # Recuperar datos acumulados del estado de la conversacion
        accumulated_data = conversation.state_data.get("extracted_data", {})
        logger.info(f"Datos acumulados previos: {accumulated_data}")
        
        # Fusionar con datos actuales (priorizar datos nuevos)
        final_data = {**accumulated_data, **extracted_data}
        logger.info(f"Datos acumulados despues de fusionar: {final_data}")

        # Caso 1: Faltan datos - Pedir conversacionalmente
        if missing_fields:
            mensaje = self._ask_for_missing_data(final_data, missing_fields)
            
            # Persistir dato en el estado
            if conversation.state == ConversationState.IDLE:
                conversation.set_state(
                    ConversationState.RESCHEDULE_WAITING_DATE if "fecha" in missing_fields else ConversationState.RESCHEDULE_WAITING_TIME,
                    extracted_data = final_data
                )
            else:
                # Actualizar state_data sin cambiar estado
                conversation.state_data["extracted_data"] = final_data
                conversation.updated_at = datetime.now()
                
            logger.info(f"Estado actualizado: {conversation.state.value}, Data: {conversation.state_data}")
            return mensaje, None
        
        # Caso 2: Todos los datos presentes - Validar
        is_valid, validation_error = self._validate_appointment_data(extracted_data)
        if not is_valid:
            logger.info(f"Datos invalidos: {validation_error}")
            return validation_error, None
        
        # Crear cita en Seguimiento Cliente
        try:
            logger.info(f"Reprogramando cita en el sistema: {patient_id}, {extracted_data}")

            cita_reprogramada = await self._update_appointment(
                patient_id = patient_id,
                fecha = extracted_data["fecha"],
                hora = extracted_data["hora"],
                motivo = extracted_data.get("motivo", "Control de Tuberculosis")
            )

            if cita_reprogramada:
                logger.info(f"Cita reprogramada exitosamente: {cita_reprogramada}")

                conversation.clear_state()
                logger.info("Estado limpiado despues de reprogramar cita.")

                # Mensaje de confirmacion
                mensaje = self._format_confirmation_message(cita_reprogramada)

                return mensaje, cita_reprogramada
            else:
                return "Lo siento, no pude reprogramar la cita. Por favor intenta nuevamente.", None

        except Exception as e:
            logger.error(f"Error al reprogramar cita: {e}")
            return "Lo siento, ocurrió un error inesperado. Por favor intenta nuevamente.", None
        
    def _ask_for_missing_data(
        self,
        extracted_data: Dict[str, Any],
        missing_fields: list
    ) -> str:
        """
        Genera pregunta conversacional para pedir datos faltantes.

        Args:
            extracted_data: Datos ya extraidos
            missing_fields: Lista de campos que faltan

        Returns:
            Pregunta para el usuario
        """

        # Si faltan ambos (fecha y hora)
        if "fecha" in missing_fields and "hora" in missing_fields:
            return (
                "¡Perfecto! Te ayudo a agendar tu cita. "
                "¿Para qué día y hora la prefieres? "
                "(Ejemplo: mañana a las 10:00 o lunes 14:30)"
            )

        # Si solo falta fecah
        if "fecha" in missing_fields:
            hora = extracted_data.get("hora", "")
            return (
                f"Entendido, deseas cita a las {hora}."
                "¿Para qué día? (Ejemplo: mañana, lunes, o una fecha específica)"
            )
        
        # Si solo falta hora
        if "hora" in missing_fields:
            fecha = extracted_data.get("fecha", "")
            # Convertir fecha a formato legible

            try:
                fecha_obj = datetime.strptime(fecha, "%Y-%m-%d")
                fecha_legible = fecha_obj.strftime("%d de %B")
            except:
                fecha_legible = fecha

            return (
                f"Perfecto, para el {fecha_legible}."
                "¿A qué hora prefieres? (Ejemplo: 10:00, 14:30, o 'por la mañana')"
            )
    
        return "Por favor, dime la fecha y hora que prefieres."

    def _validate_appointment_data(
        self,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida los datos de la cita.

        Validaciones:
        - Fecha no puede ser pasada
        - Fecha no puede ser mas de 3 meses adelante
        - Hora debe estar en horario de atencion (07:00 - 19:00)
        - Hora debe ser en intervalos de 30 minutos

        Args:
            data: Datos a validar

        Returns:
            Tupla (es_valido, mensaje_error)
        """

        fecha_str = data.get("fecha")
        hora_str = data.get("hora")

        if not fecha_str or not hora_str:
            return False, "Faltan datos requeridos (fecha u hora)."

        try:
            # Validar fecha
            fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
            hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            if fecha < hoy:
                return False, "La fecha no puede ser en el pasado. Por favor elige otra fecha."
            
            if fecha > (hoy + timedelta(days=90)):
                return False, "Solo puedes agendar citas hasta 3 meses adelante."
            
            # Validar que no sea domingo
            if fecha.weekday() == 6:
                return False, "No atendemos los domingos. Por favor elige otro día."
            
            # Validar hora
            hora_obj = datetime.strptime(hora_str, "%H:%M")
            hora_num = hora_obj.hour * 100 + hora_obj.minute
            
            # Horario de atención: 07:00 - 19:00
            if hora_num < 700 or hora_num >= 1900:
                return False, "El horario de atención es de 07:00 a 19:00. Por favor elige otra hora."
            
            # Validar intervalos de 30 minutos
            if hora_obj.minute not in [0, 30]:
                return False, "Las citas son cada 30 minutos (ej: 10:00, 10:30). Por favor ajusta la hora."
            
            return True, None
        
        except Exception as e:
            logger.error(f"❌ Error validando datos: {e}")
            return False, f"Datos inválidos: {str(e)}"
        
    async def _update_appointment(
        self,
        patient_id: str,
        fecha: str,
        hora: str,
        motivo: str
    ) -> Optional[Dict[str, Any]]:
        """
        Reprogramar cita en el sistema NestJS via SeguimientoClient.

        Args:
            patient_id: ID del paciente
            fecha: Fecha de la cita (YYYY-MM-DD)
            hora: Hora de la cita (HH:MM)
            motivo: Motivo de la cita

        Returns:
            Datos de la cita reprogramada o None si fallo
        """

        # Combinar fecha y hora en timestamp
        fecha_hora_str = f"{fecha}T{hora}:00.000Z"

        payload = {
            "id_paciente": patient_id,
            "fecha_programada": fecha_hora_str,
            "motivo": motivo,
            "estado_id": 1 # Estado 'Programado'
        }

        logger.info(f"Reprogramando cita con payload: {payload}")
        
        try:
            cita_reprogramada = await self.seguimiento_client.update_appointment(payload)
            return cita_reprogramada
        except Exception as e:
            logger.error(f"Error reprogramando cita en NestJS: {e}")
            raise

    def _format_confirmation_message(self, cita: Dict[str, Any]) -> str:
        """
        Formatea mensaje de confirmacion de cita reprogramada.

        Args:
            cita: Datos de la cita reprogramada
        
        Returns:
            Mensaje formateado
        """

        try:
            fecha_programada = cita.get("fecha_programada", "")
            fecha_obj = datetime.fromisoformat(fecha_programada.replace("Z", "+00:00"))

            fecha_legible = fecha_obj.strftime("%d de %B de %Y")
            hora_legible = fecha_obj.strftime("%H:%M")

            motivo = cita.get("motivo")

            descripcion_motivo = motivo.get("descripcion", "Sin descripción")

            mensaje = (
                f"✅ ¡Cita reprogramada exitosamente!\n\n"
                f"📅 Fecha: {fecha_legible}\n"
                f"⏰ Hora: {hora_legible}\n"
                f"📝 Motivo: {descripcion_motivo}\n\n"
                f"Te esperamos en CAÑADA DEL CARMEN. No olvides traer tu carnet y medicación."
            )

            return mensaje
        except Exception as e:
            logger.error(f"Error formateando mensaje de confirmacion: {e}")
            return "✅ ¡Cita reprogramada exitosamente!"
        
# Instancia global
_appointment_service: Optional[AppointmentService] = None

def get_appointment_service() -> AppointmentService:
    """
    Obtiene la instancia global del servicio de citas.

    Returns:
        AppointmentService singleton
    """

    global _appointment_service

    if _appointment_service is None:
        from app.infrastructure.http import get_seguimiento_client

        seguimiento_client = get_seguimiento_client()
        _appointment_service = AppointmentService(seguimiento_client)

    return _appointment_service