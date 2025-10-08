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
        
        Estructura:
        1. Contexto del sistema (instrucciones generales)
        2. Historial de conversación (últimos N mensajes)
        3. Indicador de respuesta del asistente
        
        Args:
            conversation: Conversación con historial
        
        Returns:
            Prompt formateado
        """
        prompt = self._system_context + "\n\n"
        
        # Añadir últimos mensajes (límite configurado)
        recent_messages = conversation.get_recent_messages(
            limit=settings.max_conversation_history
        )
        
        for msg in recent_messages:
            role_name = "Usuario" if msg.role == MessageRole.USER else "Asistente"
            prompt += f"{role_name}: {msg.content}\n"
        
        prompt += "Asistente:"
        
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
        
        # Generar con el modelo
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=self.tokenizer.eos_token_id,
                repetition_penalty=1.2  # Penaliza repeticiones
            )
        
        # Decodificar la respuesta
        full_response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extraer solo la parte nueva (después de "Asistente:")
        response = full_response.split("Asistente:")[-1].strip()
        
        # Limpiar la respuesta
        response = self._clean_response(response)
        
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
        # Truncar en el primer salto de línea doble (fin de párrafo)
        if "\n\n" in response:
            response = response.split("\n\n")[0]
        
        # Truncar en "Usuario:" si aparece (error del modelo)
        if "Usuario:" in response:
            response = response.split("Usuario:")[0]
        
        # Limpiar espacios extras
        response = " ".join(response.split())
        
        return response.strip()
    
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
