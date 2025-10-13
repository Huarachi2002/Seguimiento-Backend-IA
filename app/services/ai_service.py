"""
AI Service Module
=================

Este servicio encapsula toda la lógica relacionada con la inteligencia artificial.

Responsabilidades:
1. Generar respuestas usando el modelo de lenguaje
2. Detectar intenciones en los mensajes del usuario
3. Mantener el contexto de la conversación
4. Aplicar el prompt del sistema

Patrón Service:
Separa la lógica de negocio compleja de los controllers (endpoints).
Hace el código más testeable y reutilizable.
"""

import re
import json
from typing import List, Optional, Tuple
from app.domain.models import Message, MessageRole, ActionIntent, Conversation
from app.domain.exceptions import ModelNotLoadedException, InvalidContextException
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIService:
    """
    Servicio para interactuar con el modelo de IA.
    
    Este servicio actúa como una capa de abstracción sobre el modelo.
    Si en el futuro cambias de modelo (ej: OpenAI GPT), solo modificas
    este servicio, no todo el código.
    """
    
    def __init__(self, model, tokenizer, device):
        """
        Inicializa el servicio de IA.
        
        Args:
            model: Modelo de lenguaje cargado
            tokenizer: Tokenizer del modelo
            device: Dispositivo (cpu/cuda)
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self._system_context = settings.get_system_context()
        
        logger.info(f"✅ AIService inicializado en dispositivo: {device}")
    
    def is_ready(self) -> bool:
        """
        Verifica si el servicio está listo para procesar.
        
        Returns:
            True si el modelo está cargado
        """
        return self.model is not None and self.tokenizer is not None
    
    def generate_response(
        self,
        conversation: Conversation,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """
        Genera una respuesta basada en la conversación.
        
        Este es el método principal del servicio. Toma una conversación
        completa y genera la siguiente respuesta del asistente.
        
        Args:
            conversation: Objeto Conversation con el historial
            max_tokens: Máximo de tokens a generar (usa config si es None)
            temperature: Temperatura del modelo (usa config si es None)
        
        Returns:
            Respuesta generada como string
        
        Raises:
            ModelNotLoadedException: Si el modelo no está cargado
        """
        if not self.is_ready():
            raise ModelNotLoadedException()
        
        # Usar valores por defecto de configuración si no se especifican
        max_tokens = max_tokens or settings.max_tokens
        temperature = temperature or settings.temperature
        
        logger.info(f"🤖 Generando respuesta para conversación {conversation.conversation_id}")
        
        try:
            # 1. Construir el prompt con contexto del sistema + historial
            prompt = self._build_prompt(conversation)
            
            # 2. Validar que el contexto es apropiado
            if not self._is_valid_context(conversation.messages[-1].content):
                return self._get_out_of_context_response()
            
            # 3. Generar respuesta con el modelo
            response = self._generate_with_model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"✅ Respuesta generada exitosamente")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías reformularlo?"
    
    def detect_action(self, message: str, conversation: Conversation) -> Optional[ActionIntent]:
        """
        Detecta si el mensaje del usuario tiene una intención de acción.
        
        Ejemplos de acciones:
        - "Quiero agendar una cita" -> action: schedule_appointment
        - "Cancelar mi cita" -> action: cancel_appointment
        - "¿Cuándo es mi próxima cita?" -> action: lookup_appointments
        
        Args:
            message: Mensaje del usuario
            conversation: Conversación completa para contexto
        
        Returns:
            ActionIntent si se detecta una acción, None si no
        """
        message_lower = message.lower()
        
        # Detección de intención de agendar
        if any(word in message_lower for word in ['agendar', 'programar', 'cita nueva', 'reservar']):
            logger.info("🎯 Acción detectada: schedule_appointment")
            return ActionIntent(
                action="schedule_appointment",
                params={"status": "collecting_info"},
                confidence=0.9
            )
        
        # Detección de intención de cancelar
        if any(word in message_lower for word in ['cancelar', 'anular']):
            logger.info("🎯 Acción detectada: cancel_appointment")
            return ActionIntent(
                action="cancel_appointment",
                params={"status": "collecting_info"},
                confidence=0.85
            )
        
        # Detección de intención de reprogramar
        if any(word in message_lower for word in ['reprogramar', 'cambiar', 'mover cita']):
            logger.info("🎯 Acción detectada: reschedule_appointment")
            return ActionIntent(
                action="reschedule_appointment",
                params={"status": "collecting_info"},
                confidence=0.85
            )
        
        # Detección de consulta de citas
        if any(word in message_lower for word in ['próxima cita', 'mis citas', 'cuándo', 'cuando']):
            logger.info("🎯 Acción detectada: lookup_appointments")
            return ActionIntent(
                action="lookup_appointments",
                params={},
                confidence=0.8
            )
        
        # Detección de verificación de identidad
        if re.search(r'\d{4}', message):  # Si contiene 4 dígitos
            logger.info("🎯 Acción detectada: verify_patient")
            digits = re.findall(r'\d{4}', message)[0]
            return ActionIntent(
                action="verify_patient",
                params={"last_four_digits": digits},
                confidence=0.75
            )
        
        return None
    
    def extract_structured_data(self, text: str) -> Optional[dict]:
        """
        Extrae datos estructurados (JSON) de la respuesta del modelo.
        
        A veces el modelo genera respuestas con formato JSON para
        integraciones. Esta función los extrae.
        
        Args:
            text: Texto que puede contener JSON
        
        Returns:
            Dict con los datos si se encuentran, None si no
        """
        try:
            # Buscar JSON en el texto
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, text)
            
            if matches:
                # Intentar parsear el primer match
                data = json.loads(matches[0])
                logger.info(f"📊 Datos estructurados extraídos: {data}")
                return data
        except Exception as e:
            logger.debug(f"No se pudo extraer JSON: {e}")
        
        return None
    
    # ===== Métodos Privados =====
    
    def _build_prompt(self, conversation: Conversation) -> str:
        """
        Construye el prompt completo para el modelo.
        
        CRÍTICO: Este formato DEBE coincidir EXACTAMENTE con el usado en entrenamiento.
        
        Estructura (igual que tuberculosis_conversations_v2.json):
        1. Contexto del sistema con reglas embebidas
        2. Estado del paciente (REGISTRADO/NO REGISTRADO)
        3. Información de cita si está registrado
        4. Historial de conversación
        5. Indicador "Asistente:" para generar respuesta
        
        Args:
            conversation: Conversación con historial
        
        Returns:
            Prompt formateado EXACTAMENTE como en entrenamiento
        """
        # 1. Sistema + Reglas (igual que dataset)
        prompt = (
            "Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis "
            f"del centro de salud {settings.medical_center_name}.\n\n"
            "REGLAS IMPORTANTES:\n"
            "1. SOLO atiendes consultas sobre TUBERCULOSIS\n"
            "2. Máximo 2 oraciones por respuesta\n"
            "3. Usa el nombre del paciente si lo conoces\n"
            "4. Sé profesional y empático\n"
            "5. Si preguntan por otro servicio, redirige amablemente\n\n"
        )
        
        # 2. Estado del paciente
        # TODO: Cuando implementes la BD, aquí verificas si está registrado
        # Por ahora, asume NO REGISTRADO
        patient_registered = False  # Obtener de BD en el futuro
        
        if patient_registered:
            # Si está registrado, incluir info de cita (obtener de BD)
            prompt += "Paciente REGISTRADO\n"
            prompt += "Próxima cita: [FECHA] a las [HORA]\n\n"
        else:
            prompt += "Paciente NO REGISTRADO\n\n"
        
        # 3. Historial de conversación (últimos N mensajes)
        recent_messages = conversation.get_recent_messages(
            limit=settings.max_conversation_history
        )
        
        for msg in recent_messages:
            role_name = "Paciente" if msg.role == MessageRole.USER else "Asistente"
            prompt += f"{role_name}: {msg.content}\n"
        
        # 4. Indicador de respuesta (igual que dataset)
        prompt += "Asistente:"

        logger.debug(f"📝 Prompt construido (primeros 500 chars):\n{prompt[:500]}...")
        
        return prompt
    
    def _generate_with_model(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Genera texto usando el modelo de lenguaje.
        
        Args:
            prompt: Prompt completo
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura del modelo
        
        Returns:
            Texto generado
        """
        import torch
        
        # Tokenizar el prompt
        inputs = self.tokenizer.encode(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True
        ).to(self.device)

        # Obtener la longitud del prompt para extraer solo lo nuevo
        prompt_length = inputs.shape[1]
        
        # Generar con el modelo
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2,  # Penaliza repeticiones
                no_repeat_ngram_size=3  # Evita n-gramas repetidos
            )
        
        # Decodificar SOLO los tokens nuevos (no el prompt completo)
        generated_tokens = outputs[0][prompt_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        logger.debug(f"📝 Respuesta bruta del modelo: {response[:100]}...")
        
        # Limpiar la respuesta
        response = self._clean_response(response)

        if not response or len(response.strip()) < 5:
            logger.warning("⚠️ Respuesta vacía o muy corta, usando respuesta por defecto")
            # Generar respuesta contextual basada en el último mensaje
            last_message = prompt.split("Usuario:")[-1].strip() if "Usuario:" in prompt else ""
            response = self._get_fallback_response(last_message)
        
        return response
    
    def _clean_response(self, response: str) -> str:
        """
        Limpia la respuesta del modelo.
        
        - Remueve repeticiones
        - Trunca en puntos de corte naturales
        - Remueve caracteres extraños
        
        Args:
            response: Respuesta sin limpiar
        
        Returns:
            Respuesta limpia
        """
        # 1. Remover prefijos comunes que el modelo puede generar 
        prefixes_to_remove = ["Asistente:", "Assistant:", "Bot:", "AI:"]
        for prefix in prefixes_to_remove:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()

        # 2. Truncar en el primer salto de línea doble (fin de párrafo)
        if "\n\n" in response:
            response = response.split("\n\n")[0]

        # 3. Truncar en "Usuario:" si aparece (error del modelo)
        if "Usuario:" in response:
            response = response.split("Usuario:")[0]

        # 4. Truncas en "User:" tambien
        if "User:" in response:
            response = response.split("User:")[0]
        
        # 5. Limpiar espacios extras
        response = " ".join(response.split())
        
        # 6. Asegurar que termina con puntuacion
        if response and response[-1] not in '.!?':
            # Truncar en la ultima frase completa
            for punct in ['.', '!', '?']:
                if punct in response:
                    response = response[:response.rfind(punct)+1]
                    break

        return response.strip()
    
    def _get_fallback_response(self, last_message: str) -> str:
        """
        Genera una respuesta de respaldo cuando el modelo falla.
        
        Args:
            last_message: Último mensaje del usuario
        
        Returns:
            Respuesta contextual
        """
        last_message_lower = last_message.lower()
        
        # Respuestas contextuales según palabras clave
        if any(word in last_message_lower for word in ['agendar', 'cita', 'programar']):
            return (
                f"¡Claro! Te ayudo a agendar una cita en {settings.medical_center_name}. "
                f"¿Para qué especialidad necesitas la cita?"
            )
        
        if any(word in last_message_lower for word in ['cancelar', 'anular']):
            return (
                "Entiendo que necesitas cancelar una cita. "
                "Para verificar tu identidad, ¿me puedes dar los últimos 4 dígitos de tu número de teléfono?"
            )
        
        if any(word in last_message_lower for word in ['reprogramar', 'cambiar']):
            return (
                "Te ayudo a reprogramar tu cita. "
                "Primero, ¿me das los últimos 4 dígitos de tu teléfono para verificarte?"
            )
        
        if any(word in last_message_lower for word in ['hola', 'buenos', 'buenas']):
            return (
                f"¡Hola! Bienvenido al asistente virtual de {settings.medical_center_name}. "
                f"¿En qué puedo ayudarte hoy? Puedo ayudarte a:\n"
                f"• Agendar una cita\n"
                f"• Consultar tus próximas citas\n"
                f"• Cancelar o reprogramar una cita"
            )
        
        # Respuesta genérica
        return (
            f"Entiendo. ¿Podrías darme más detalles? "
            f"Puedo ayudarte con citas médicas en {settings.medical_center_name}."
        )
    
    def _is_valid_context(self, message: str) -> bool:
        """
        Valida que el mensaje esté dentro del contexto permitido.
        
        Args:
            message: Mensaje del usuario
        
        Returns:
            True si el mensaje es válido
        """
        # Palabras clave del dominio
        keywords = [
            'cita', 'agendar', 'reprogramar', 'cancelar', 'recordatorio',
            'próxima', 'doctor', 'médico', 'consulta', 'paciente',
            settings.medical_center_name.lower()
        ]
        
        message_lower = message.lower()
        
        # Si contiene alguna palabra clave, es válido
        if any(keyword in message_lower for keyword in keywords):
            return True
        
        # Si es un saludo o mensaje corto, es válido
        greetings = ['hola', 'buenos', 'buenas', 'saludos', 'hi', 'hello']
        if any(greeting in message_lower for greeting in greetings):
            return True
        
        # Si es muy corto (< 50 caracteres), permitir (puede ser respuesta)
        if len(message) < 50:
            return True
        
        return False
    
    def _get_out_of_context_response(self) -> str:
        """
        Retorna mensaje para contexto inválido.
        
        Returns:
            Mensaje de redirección
        """
        return (
            f"Lo siento, solo puedo asistir con citas, recordatorios o "
            f"información del {settings.medical_center_name}. "
            f"¿En qué puedo ayudarte con tu cita?"
        )
