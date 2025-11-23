"""
Reschedule Handlers Module
===========================

Handlers para el flujo de reprogramación de citas.

Este módulo contiene todos los handlers necesarios para:
1. Consultar próxima cita
2. Reprogramar cita (solicitar fecha, hora, confirmar)
"""

from app.infrastructure.http.seguimiento_client import SeguimientoClient
from typing import Optional, Dict, Tuple
from datetime import datetime, timedelta
from app.domain.models import Conversation, MessageRole, ConversationState
from app.core.logging import get_logger

logger = get_logger(__name__)


class RescheduleHandlers:
    """
    Clase con todos los handlers del flujo de reprogramación.
    
    Se pueden agregar como métodos al ConversationService.
    """
    
    @staticmethod
    async def handle_lookup_appointment(
        conversation_service,
        conversation: Conversation,
        user_id: str
    ) -> Tuple[str, Optional[Dict]]:
        """
        Maneja la consulta de próxima cita.
        
        Args:
            conversation_service: Instancia de ConversationService
            conversation: Conversación actual
            user_id: ID del usuario
        
        Returns:
            Tupla (respuesta, datos_acción)
        """
        logger.info("=====Consultando próxima cita=====")
        
        # Obtener información del paciente
        from app.services.patient_service import get_patient_service
        patient_service = get_patient_service()
        
        patient_registered, patient_data = await patient_service.verify_patient(
            phone_number=user_id
        )
        logger.info(f"Patient registered: {patient_registered}")
        logger.info(f"Patient data: {patient_data}")
        
        if not patient_registered or not patient_data:
            logger.info("Paciente no registrado o sin datos")
            response = (
                "No encuentro tu registro en el sistema. "
                "Por favor comunícate al centro de salud para más información."
            )
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            return response, None
        
        logger.info("Paciente registrado y con datos")
        # Obtener próxima cita
        proxima_cita = patient_data.get('proxima_cita')
        
        if not proxima_cita:
            logger.info("No tienes citas programadas")
            response = (
                f"Hola {patient_data.get('nombre', 'paciente')}, "
                f"no tienes citas programadas en este momento."
            )
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            return response, None
        
        logger.info("Tienes citas programadas")
        # Formatear información
        try:
            fecha_programada = proxima_cita.get('fecha_programada', '')
            fecha_obj = datetime.fromisoformat(fecha_programada.replace('Z', '+00:00'))
            logger.info(f"Fecha programada: {fecha_obj}")
            
            fecha_legible = fecha_obj.strftime("%d de %B de %Y")
            hora_legible = fecha_obj.strftime("%H:%M")
            logger.info(f"Fecha legible: {fecha_legible}")
            logger.info(f"Hora legible: {hora_legible}")
            
            estado = proxima_cita.get('estado', {})
            estado_desc = estado.get('descripcion', 'Programado')
            logger.info(f"Estado: {estado_desc}")

            tipo = proxima_cita.get('tipo', {})
            tipo_desc = tipo.get('descripcion', 'Control de Tuberculosis')
            logger.info(f"Tipo: {tipo_desc}")
            
            logger.info("Formateando información")
            logger.info("Generando respuesta")
            response = (
                f"Tu próxima cita:\n\n"
                f"Fecha: {fecha_legible}\n"
                f"Hora: {hora_legible}\n"
                f"Tipo: {tipo_desc}\n"
                f"Estado: {estado_desc}\n\n"
                f"Te esperamos en CAÑADA DEL CARMEN. Si necesitas reprogramar, dímelo."
            )
            logger.info(f"Respuesta generada: {response}")
        except Exception as e:
            logger.info(f"Error formateando cita: {e}")
            response = (
                f"Hola {patient_data.get('nombre', 'paciente')}, "
                f"tienes una cita programada. Comunícate al centro para más detalles."
            )
        
        logger.info("Agregando respuesta al chat")
        conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
        
        logger.info("Generando datos de acción")
        logger.info("========Fin de la consulta de próxima cita========")
        return response, {
            "action": "lookup_appointment",
            "cita": proxima_cita
        }
    
    @staticmethod
    async def start_reschedule_flow(
        conversation_service,
        conversation: Conversation,
        user_id: str,
        message: str,
        params: Dict
    ) -> Tuple[str, Optional[Dict]]:
        """
        Inicia el flujo de reprogramación.
        
        Args:
            conversation_service: Instancia de ConversationService
            conversation: Conversación actual
            user_id: ID del usuario
            message: Mensaje del usuario
            params: Parámetros extraídos
        
        Returns:
            Tupla (respuesta, datos_acción)
        """
        logger.info("=====Iniciando flujo de reprogramación======")
        
        # Verificar paciente
        from app.services.patient_service import get_patient_service
        patient_service = get_patient_service()
        patient_registered, patient_data = await patient_service.verify_patient(
            phone_number=user_id
        )

        logger.info(f"Patient registered: {patient_registered}")
        logger.info(f"Patient data: {patient_data}")
        
        if not patient_registered:
            logger.info("Paciente no registrado")

            response = "No encuentro tu registro. Comunícate al centro de salud."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            return response, None
        
        logger.info("Paciente registrado")
        # Verificar cita existente
        proxima_cita = patient_data.get('proxima_cita')

        logger.info(f"Proxima cita: {proxima_cita}")
        if not proxima_cita:
            logger.info("No tienes citas para reprogramar")

            response = (
                f"Hola {patient_data.get('nombre', 'paciente')}, "
                f"no tienes citas para reprogramar."
            )
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            return response, None
        
        logger.info("Tienes citas para reprogramar")
        # Extraer datos
        extracted_data = params.get("extracted_data", {})
        patient_id = patient_data.get("id")
        logger.info(f"Patient id: {patient_id}")
        cita_id = proxima_cita.get("id")

        logger.info(f"Cita id: {cita_id}")
        
        # Guardar estado
        logger.info("Guardando estado en Conversation" + ConversationState.RESCHEDULE_WAITING_DATE.name)

        conversation.set_state(
            ConversationState.RESCHEDULE_WAITING_DATE,
            patient_id=patient_id,
            patient_name=patient_data.get("nombre"),
            cita_id=cita_id,
            cita_actual=proxima_cita,
            extracted_data=extracted_data
        )

        logger.info("Estado guardado")
        
        # Si tiene fecha
        logger.info("Verificando fecha")
        if extracted_data.get("fecha"):
            logger.info("Tiene fecha")

            conversation.state_data["fecha"] = extracted_data["fecha"]
            conversation.state_data["extracted_data"] = extracted_data
            conversation.state = ConversationState.RESCHEDULE_WAITING_TIME

            logger.info("Estado actualizado")
            
            if extracted_data.get("hora"):
                logger.info("Tiene hora")

                conversation.state_data["hora"] = extracted_data["hora"]
                conversation.state_data["extracted_data"] = extracted_data
                conversation.state = ConversationState.RESCHEDULE_CONFIRMING

                logger.info("Estado actualizado")

                conversation_service.repo.save(conversation)

                logger.info("Conversation guardada")
                
                logger.info(f"Pasando a confirmación con fecha={extracted_data['fecha']}, hora={extracted_data['hora']}")
                logger.info(f"State data guardado: {conversation.state_data}")
                
                return await RescheduleHandlers.handle_reschedule_confirm(
                    conversation_service, conversation, user_id, message
                )
            conversation_service.repo.save(conversation)

            logger.info(f"Esperando hora. Fecha guardada: {extracted_data['fecha']}")
            
            response = (
                f"Perfecto, para el {RescheduleHandlers._format_date(extracted_data['fecha'])}. "
                f"¿A qué hora? (7:00 - 19:00)"
            )
        else:
            # Pedir fecha
            logger.info("Pedir fecha")
            try:
                fecha_actual = proxima_cita.get('fecha_programada', '')
                fecha_obj = datetime.fromisoformat(fecha_actual.replace('Z', '+00:00'))
                fecha_legible = fecha_obj.strftime("%d de %B a las %H:%M")
                
                logger.info(f"Fecha actual: {fecha_legible}")

                response = (
                    f"Tu cita actual es el {fecha_legible}. "
                    f"¿Para qué día la reprogramamos? (Ej: mañana, lunes)"
                )
            except:
                logger.info("Error al obtener fecha actual")
                response = "¿Para qué día quieres reprogramar tu cita?"
        
        logger.info("Guardando conversation")
        
        conversation_service.repo.save(conversation)

        logger.info("Guardando message")

        conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
        
        logger.info("========Fin del handle_reschedule_date========")
        
        return response, {"action": "reschedule_appointment", "status": "in_progress"}
    
    @staticmethod
    async def handle_reschedule_date(
        conversation_service,
        conversation: Conversation,
        user_id: str,
        message: str
    ) -> Tuple[str, Optional[Dict]]:
        """Procesa la fecha ingresada."""
        logger.info("======Procesando fecha para reprogramación======")
        
        # Extraer fecha
        logger.info("Extraer fecha")

        extracted_data = conversation_service.ai_service._extract_appointment_data(message)
        fecha = extracted_data.get("fecha")
        
        logger.info(f"Fecha extraida: {fecha}")
        
        if not fecha:
            logger.info("No entendí la fecha")
            response = (
                "No entendí la fecha. Intenta con:\n"
                "Mañana\n"
                "Lunes\n"
                "25 de noviembre"
            )
            logger.info("Guardando message")
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            logger.info("======Fin del handle_reschedule_date======")
            return response, None
        
        # Validar
        logger.info("Validar")
        try:
            fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
            fecha_dt = fecha_dt.replace(tzinfo=None)
            
            logger.info(f"Fecha validada: {fecha_dt}")

            if fecha_dt < hoy:

                logger.info("La fecha no puede ser en el pasado")
                
                response = "La fecha no puede ser en el pasado."
                
                logger.info("Guardando message")

                conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
                
                logger.info("======Fin del handle_reschedule_date======")
                
                return response, None
            
            if fecha_dt.weekday() == 6:
                logger.info("No atendemos los domingos")

                response = "No atendemos los domingos."

                logger.info("Guardando message")
                
                conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

                logger.info("======Fin del handle_reschedule_date======")
                
                return response, None
        except Exception as e:
            logger.info(f"Error validando: {e}")

            response = "Fecha inválida. Intenta de nuevo."
            
            logger.info("Guardando message")
            
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            return response, None
        
        # Guardar en state_data y actualizar estado
        current_data = conversation.state_data.get("extracted_data", {})
        current_data["fecha"] = fecha

        logger.info(f"Guardando fecha en state_data: {current_data}")
        
        conversation.set_state(
            ConversationState.RESCHEDULE_WAITING_TIME,
            fecha=fecha,
            extracted_data=current_data
        )
        
        conversation_service.repo.save(conversation)

        logger.info(f"Datos guardados en state_data: {conversation.state_data}")
        
        response = f"Perfecto, para el {RescheduleHandlers._format_date(fecha)}. ¿A qué hora?"
        conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

        logger.info("======Fin del handle_reschedule_date======")
        
        return response, None
    
    @staticmethod
    async def handle_reschedule_time(
        conversation_service,   
        conversation: Conversation,
        user_id: str,
        message: str
    ) -> Tuple[str, Optional[Dict]]:
        """Procesa la hora ingresada."""
        logger.info("======Procesando hora======")
        logger.info(f"Mensaje recibido: {message}")
        
        # Extraer hora
        extracted_data = conversation_service.ai_service._extract_appointment_data(message)
        hora = extracted_data.get("hora")
        
        logger.info(f"Hora extraída: {hora}")
        
        if not hora:
            logger.info("No entendí la hora")

            response = "No entendí la hora. Intenta: 10:00, 14:30, o indica AM/PM"
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            
            logger.info("======Fin del handle_reschedule_time======")
            
            return response, None
        
        # Validar - Limpiar hora primero
        try:
            hora_clean = hora.replace('.000Z', '').replace('T', '')

            logger.info(f"Hora limpia: {hora_clean}")
            
            if hora_clean.count(':') == 2:
                hora_dt = datetime.strptime(hora_clean, "%H:%M:%S")

                logger.info(f"Hora parseada: {hora_dt.hour}:{hora_dt.minute:02d}")
            elif hora_clean.count(':') == 1:
                hora_dt = datetime.strptime(hora_clean, "%H:%M")

                logger.info(f"Hora parseada: {hora_dt.hour}:{hora_dt.minute:02d}")
            else:
                raise ValueError(f"Formato de hora no reconocido: {hora_clean}")
            
            if hora_dt.hour < 7 or hora_dt.hour >= 19:
                logger.info("La hora no está dentro del horario de atención")   

                response = "El horario de atención es de 7:00 a 19:00. Por favor elige otra hora."
                conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
                
                logger.info("======Fin del handle_reschedule_time======")
                
                return response, None
            
            if hora_dt.minute not in [0, 30]:
                logger.info("La hora no es cada 30 minutos")

                response = "Las citas son cada 30 minutos (ej: 10:00, 10:30). Por favor ajusta la hora."
                conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
                
                logger.info("======Fin del handle_reschedule_time======")
                
                return response, None
                
        except Exception as e:
            logger.error(f"Error validando hora: {e}")
            logger.error(f"Hora recibida: {hora}")

            response = "Hora inválida. Intenta con formato 10:00 o 14:30, puedes usar AM/PM."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

            logger.info("======Fin del handle_reschedule_time======")
            
            return response, None
        
        # Guardar y confirmar
        current_data = conversation.state_data.get("extracted_data", {})
        current_data["hora"] = hora

        logger.info(f"Datos guardados en state_data: {current_data}")
        
        conversation.set_state(
            ConversationState.RESCHEDULE_CONFIRMING,
            hora=hora,
            extracted_data=current_data
        )
        conversation_service.repo.save(conversation)
        
        logger.info(f"Datos completos guardados: {conversation.state_data}")
        
        fecha = current_data.get("fecha")
        
        response = (
            f"Nueva cita:\n"
            f"{RescheduleHandlers._format_date(fecha)} a las {RescheduleHandlers._format_time(hora)}\n\n"
            f"¿Confirmas? (sí/no)"
        )

        logger.info(f"Respuesta enviada: {response}")

        conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
        
        logger.info("======Fin del handle_reschedule_confirm======")
        
        return response, None
    
    @staticmethod
    async def handle_reschedule_confirm(
        conversation_service,
        conversation: Conversation,
        user_id: str,
        message: str
    ) -> Tuple[str, Optional[Dict]]:
        """Procesa la confirmación."""
        logger.info("======Procesando confirmación======")
        
        # Validar que message no sea None
        if not message or message.strip() == "":
            logger.info("No recibí tu respuesta. Por favor responde 'sí' o 'no'.")

            response = "No recibí tu respuesta. Por favor responde 'sí' o 'no'."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            
            logger.info("======Fin del handle_reschedule_confirm======")
            
            return response, None
        
        message_lower = message.lower().strip()

        logger.info(f"Mensaje recibido: {message_lower}")
        
        confirmations = ['si', 'sí', 'yes', 'ok', 'confirmo', 'confirmar', 'dale', 'perfecto', 'está bien', 'esta bien']
        cancellations = ['no', 'cancelar', 'espera', 'mejor no', 'no gracias']
        
        if any(word in message_lower for word in cancellations):
            conversation.clear_state()
            conversation_service.repo.save(conversation)
            
            response = "Tu cita se mantiene sin cambios."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

            logger.info("Tu cita se mantiene sin cambios.")
            
            logger.info("======Fin del handle_reschedule_confirm======")
            
            return response, None
        
        if not any(word in message_lower for word in confirmations):
            response = "Por favor responde 'sí' para confirmar o 'no' para cancelar."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

            logger.info("Por favor responde 'sí' para confirmar o 'no' para cancelar.")
            
            logger.info("======Fin del handle_reschedule_confirm======")
            
            return response, None
        
        # Reprogramar - Validar que existan los datos en el estado
        extracted_data = conversation.state_data.get("extracted_data", {})
        fecha = conversation.state_data.get("fecha") or extracted_data.get("fecha")
        hora = conversation.state_data.get("hora") or extracted_data.get("hora")
        
        patient_id = conversation.state_data.get("patient_id")
        cita_id = conversation.state_data.get("cita_id")

        logger.info(f"Datos recuperados para confirmacion: fecha={fecha}, hora={hora}, patient_id={patient_id}, cita_id={cita_id}")
        logger.info(f"State data completo: {conversation.state_data}")

        if not fecha or not hora or not patient_id:
            logger.error(f"Datos faltantes en estado: fecha={fecha}, hora={hora}, patient_id={patient_id}")
            logger.error(f"State data actual: {conversation.state_data}")

            conversation.clear_state()
            conversation_service.repo.save(conversation)
            response = "Hubo un error. Por favor intenta reprogramar de nuevo."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

            logger.info("Hubo un error. Por favor intenta reprogramar de nuevo.")
            logger.info("======Fin del handle_reschedule_confirm======")

            return response, None
        
        try:
            fecha_clean = fecha.split('T')[0] if 'T' in fecha else fecha
            hora_clean = hora.split('.')[0].split('T')[-1] if 'Z' in hora or 'T' in hora else hora
            
            logger.info(f"Datos limpios: fecha={fecha_clean}, hora={hora_clean}")
            
            # Validar formato de hora
            if ':' not in hora_clean:
                hora_clean = hora_clean[:2] + ':' + hora_clean[2:4] + ':' + hora_clean[4:] if len(hora_clean) >= 6 else hora_clean + ':00:00'
                logger.info(f"Hora limpiada: {hora_clean}")
            
            from app.services.appointment_service import get_appointment_service
            appointment_service = get_appointment_service()
            
            logger.info(f"Reprogramando: patient_id={patient_id}, fecha={fecha_clean}, hora={hora_clean}")
            
            cita = await appointment_service._update_appointment(
                patient_id=str(patient_id),
                fecha=fecha_clean,
                hora=hora_clean,
                motivo="Control de Tuberculosis"
            )

            logger.info(f"Cita reprogramada: {cita}")
            
            if cita:
                response = (
                    f"¡Cita reprogramada!\n\n"
                    f"{RescheduleHandlers._format_date(fecha)}\n"
                    f"{RescheduleHandlers._format_time(hora)}\n\n"
                    f"Te esperamos en CAÑADA DEL CARMEN."
                )

                logger.info("Cita reprogramada exitosamente.")

                action_data = {"action": "reschedule_appointment", "status": "completed", "cita": cita}
            else:
                response = "Error al reprogramar. Intenta de nuevo."
                
                logger.info("Error al reprogramar.")
                
                action_data = None
        except Exception as e:
            logger.error(f"Error reprogramando: {e}")
            import traceback
            logger.error(traceback.format_exc())
            response = "Ocurrió un error. Intenta de nuevo."
            action_data = None
        
        # Limpiar
        logger.info("Limpiando estado...")

        conversation.clear_state()
        conversation_service.repo.save(conversation)
        
        logger.info("Estado limpiado.")
        
        conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

        logger.info("Mensaje enviado: {response}")        
        logger.info("======Fin del handle_reschedule_confirm======")
        
        return response, action_data

    # Metodo para capturar cuando un paciente esta en riesgo de salud o pide urgencia de atencion de un supervisor
    @staticmethod
    async def handle_urgent_request(
        conversation_service,
        conversation: Conversation,
        user_id: str, 
        message: str
    ) -> Tuple[str, Optional[Dict]]:
        """Procesando solicitud de atencion urgente"""
        logger.info("======Inicio del handle_urgent_request======")

        if not message or message.strip() == "":
            logger.info("No se proporciono un mensaje.")

            response = "Por favor proporciona un mensaje."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)
            logger.info("======Fin del handle_urgent_request======")
            
            return response, None

        message_lower = message.lower().strip()

        logger.info(f"Mensaje en minusculas: {message_lower}")

        # Keywords para detectar si el paciente esta en riesgo de salud mediante el mensaje que el nos envia
        urgent_keywords = [
            "me siento mal",
            "me siento enfermo",
            "creo que me siento mal",
            "creo que me siento enfermo",
            "es posible contactarme con alguien",
            "mi salud",
            "mi salud decayo",
            "me siento decaido"
        ]

        if any(word in message_lower for word in urgent_keywords):
            conversation.clear_state()
            conversation_service.repo.save(conversation)

            logger.info("Solicitud de atencion urgente detectada.")

            response = "Ya designamos a un supervisor para atender tu solicitud."
            conversation_service.add_message(user_id, MessageRole.ASSISTANT, response)

            # Enviar notificacion al supervisor mediante el servicio de seguimiento
            seguimiento_client = SeguimientoClient()
            await seguimiento_client.notification_paciente_urgent(user_id)
            
            logger.info("======Fin del handle_urgent_request======")
            return response, None

        logger.info("======Fin del handle_urgent_request======")
        
        return None, None
    
    @staticmethod
    def _format_date(fecha: str) -> str:
        """Formatea fecha."""
        try:
            fecha_dt = datetime.fromisoformat(fecha.replace('Z', '+00:00'))
            return fecha_dt.strftime("%d de %B de %Y")
        except:
            return fecha
    
    @staticmethod
    def _format_time(hora: str) -> str:
        """Formatea hora."""
        try:
            hora_clean = hora.replace(':00.000Z', '').replace('T', ' ')
            return hora_clean.split(' ')[-1][:5]
        except:
            return hora
