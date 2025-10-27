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

from email.mime import message
import re
import json
from typing import List, Optional, Tuple
from urllib import response
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
    
    def __init__(self, model, tokenizer, device, patient_service=None):
        """
        Inicializa el servicio de IA.
        
        Args:
            model: Modelo de lenguaje cargado
            tokenizer: Tokenizer del modelo
            device: Dispositivo (cpu/cuda)
            patient_service: Servicio para consultar información de pacientes
        """
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.patient_service = patient_service
        self._system_context = settings.get_system_context()
        
        logger.info(f"✅ AIService inicializado en dispositivo: {device}")
    
    def is_ready(self) -> bool:
        """
        Verifica si el servicio está listo para procesar.
        
        Returns:
            True si el modelo está cargado
        """
        return self.model is not None and self.tokenizer is not None
    
    async def generate_response(
        self,
        conversation: Conversation,
        user_id: str,
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """
        Genera una respuesta basada en la conversación.
        
        Este es el método principal del servicio. Toma una conversación
        completa y genera la siguiente respuesta del asistente.
        
        AHORA consulta la BD para verificar si el paciente está registrado.
        
        Args:
            conversation: Objeto Conversation con el historial
            user_id: ID del usuario (teléfono) para consultar BD
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
            # 1. Validar Contexto antes de construir el prompt
            last_message = conversation.messages[-1].content if conversation.messages else ""

            if not self._is_valid_tuberculosis_context(last_message):
                logger.warning(f"⚠️ Mensaje fuera de contexto detectado: {last_message}")
                return self._get_out_of_context_response()

            # 2. Construir el prompt con contexto del sistema + historial + BD
            prompt = await self._build_prompt(conversation, user_id)
            
            # 3. Validar que el contexto es apropiado
            if not self._is_valid_context(conversation.messages[-1].content):
                return self._get_out_of_context_response()

            # 4. Generar respuesta con el modelo
            response = self._generate_with_model(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )

            if not self._is_valid_response(response):
                logger.warning(f"⚠️ Respuesta inválida detectada, usando respuesta por defecto")
                return self._get_fallback_response(last_message)
            
            logger.info(f"✅ Respuesta generada exitosamente")
            return response
            
        except Exception as e:
            logger.error(f"❌ Error generando respuesta: {e}")
            return "Lo siento, tuve un problema procesando tu mensaje. ¿Podrías reformularlo?"
    
    def _is_valid_tuberculosis_context(self, message: str) -> bool:
        """
        Valida que el mensaje sea sobre TUBERCULOSIS.
        
        Returns:
            True si es valido, False si esta fuera de contexto
        """

        message_lower = message.lower()

        # Saludos siempre son validos
        greetings = ['hola', 'buenos dias', 'buenas tardes', 'buenas noches', 'saludos', 'hi', 'hello']
        if any(greeting in message_lower for greeting in greetings):
            return True
        
        tb_keywords = [
            'tuberculosis', 'tb', 'tos', 'fiebre', 'sudor', 'peso', 'respirar',
            'cita', 'control', 'tratamiento', 'medicamento', 'pastilla',
            'agendar', 'cancelar', 'reprogramar', 'cuando', 'cuándo',
            'salud', 'síntoma', 'dolor', 'pecho', 'sangre'
        ]

        if any(keyword in message_lower for keyword in tb_keywords):
            return True

        if len(message.strip()) < 20 and "?" in message:
            return True
        
        out_of_context_keywords = [
            'hipotenusa', 'matemática', 'trigonometría', 'física', 'química',
            'odontología', 'dentista', 'muela', 'diente',
            'embarazo', 'ginecología', 'pediatría', 'niño',
            'fútbol', 'deporte', 'política', 'clima'
        ]

        if any(keyword in message_lower for keyword in out_of_context_keywords):
            logger.info("🎯 Mensaje identificado como fuera de contexto por palabras clave")
            return False
        
        # ⚠️ Mensajes largos sin palabras clave (probablemente fuera de contexto)
        if len(message.strip()) > 100:
            return False
        
        return True
    
    def _is_valid_response(self, response: str) -> bool:
        """
        Valida que la respuesta generada sea coherente

        Detecta:
        - Fechas inventadas (ej: "140032/10/2025")
        - Nombres incorrectos repetidos (ej: Diego Diego Diego)
        - Numeros absurdos (ej: "1491/20759/2010")
        - Palabras inventadas (ej: "TUBERACION")

        Returns:
            True si la respuesta es valida
        """

        # Detectar fechas absurdas (dias > 31, meses > 12)
        import re
        date_pattern = r'\d{2,}/\d{2,}/\d{2,}'
        dates = re.findall(date_pattern, response)

        for date_str in dates:
            parts = date_str.split('/')
            try:
                day = int(parts[0])
                month = int(parts[1]) if len(parts) > 1 else 0
                year = int(parts[2])
                if day > 31 or month > 12 or year > 2100 or day > 1000:
                    logger.warning(f"⚠️ Fecha absurda detectada: {date_str}")
                    return False
            except:
                logger.warning(f"⚠️ Fecha inválida detectada: {date_str}")
                pass

        # Detectar palabras repetidas 3 veces seguidas
        words = response.split()
        for i in range(len(words) - 2):
            if words[i] == words[i+1] == words[i+2]:
                logger.warning(f"⚠️ Palabra repetida detectada: {words[i]}")
                return False
            
        # Detectar palabras inventadas conocidas
        invalid_words = ['tuberación', 'tuberculos', 'cañadi', 'carmi']
        if any(word in response.lower() for word in invalid_words):
            logger.warning(f"⚠️ Palabra inventada detectada")
            return False      

        # Respuesta demasiado larga (indica generacion descontrolada)
        if len(response) > 400:
            logger.warning(f"⚠️ Respuesta demasiado larga detectada")
            return False

        return True

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
        agendar_keywords = ['agendar', 'programar', 'cita nueva', 'reservar', 'quiero cita']
        if any(word in message_lower for word in agendar_keywords):
            logger.info("🎯 Acción detectada: schedule_appointment")

            # Extraer datos del mensaje
            extracted_data = self._extract_appointment_data(message)
            logger.info(f"📊 Datos extraídos para agendar: {extracted_data}")
            # Determinar que datos faltan
            missing_fields = []
            if not extracted_data.get("fecha"):
                missing_fields.append("fecha")
            if not extracted_data.get("hora"):
                missing_fields.append("hora")

            return ActionIntent(
                action="schedule_appointment",
                params={
                    "status": "collecting_info" if missing_fields else "ready",
                    "extracted_data": extracted_data,
                    "missing_fields": missing_fields 
                    },
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
    
    def _extract_appointment_data(self, message: str) -> dict:
        """
        Extrae fecha, hora y motivo del mensaje del usuario

        Ejemplo: 
        - "Quiero agendar para el lunes 25 a las 10:00"
        - "Agendar cita mañana 14:40"
        - "Quiero cita el 2025-11-20 por la mañana"

        Returns:
            dict con keys: fecha, hora, motivo
        """

        import re
        from datetime import datetime, timedelta

        extracted = {
            "fecha": None,
            "hora": None,
            "motivo": None
        }

        message_lower = message.lower()
        logger.info(f"📊 Extrayendo datos de mensaje: {message_lower}")

        # Extraer fecha: 2025-10-20T04:00:00.000Z
        fecha_iso = re.search(r'(\d{2}-\d{2}-\d{2})', message_lower)
        if fecha_iso:
            extracted["fecha"] = fecha_iso.group(0)
            logger.info(f"📊 Fecha extraída (ISO): {extracted['fecha']}")
        
        # Patron: 2025-10-20T04:00:00.000Z
        fecha_slash = re.search(r'(\d{4}/\d{2}/\d{2})', message_lower)
        if fecha_slash and not extracted["fecha"]:
            fecha_str = fecha_slash.group(0)
            logger.info(f"📊 Fecha extraída (Slash): {extracted['fecha']}")
            try:
                # convertir a formato ISO
                if '/' in fecha_str:
                    parts: fecha_str.split('/')
                else:
                    parts = fecha_str.split('-')
                dia = int(parts[0])
                mes = int(parts[1])
                anio = int(parts[2])

                if anio < 100:
                    anio += 2000  # Asumir siglo 2000

                fecha = datetime(anio, mes, dia)
                extracted["fecha"] = f"{anio}-{mes:02d}-{dia:02d}T00:00:00.000Z"
                logger.info(f"📊 Fecha extraída (ISO): {extracted['fecha']}")
            except:
                pass

        # Palabras clave temporales
        if not extracted['fecha']:
            hoy = datetime.now()

            if any(word in message_lower for word in ['hoy', 'hoi']):
                extracted['fecha'] = hoy.strftime("%Y-%m-%dT00:00:00.000Z")
                logger.info(f"📊 Fecha extraída (Hoy): {extracted['fecha']}")

            elif any(word in message_lower for word in ['mañana', 'manana']):
                manana = hoy + timedelta(days=1)
                extracted['fecha'] = manana.strftime("%Y-%m-%dT00:00:00.000Z")
                logger.info(f"📊 Fecha extraída (Mañana): {extracted['fecha']}")

            elif 'pasado mañana' in message_lower:
                pasado_manana = hoy + timedelta(days=2)
                extracted['fecha'] = pasado_manana.strftime("%Y-%m-%dT00:00:00.000Z")
                logger.info(f"📊 Fecha extraída (Pasado Mañana): {extracted['fecha']}")

            dias_semana = {
                'lunes': 0, 'martes': 1, 'miércoles': 2, 'miercoles': 2,
                'jueves': 3, 'viernes': 4, 'sábado': 5, 'sabado': 5, 'domingo': 6
            }

            for dia_nombre, dia_num in dias_semana.items():
                if dia_nombre in message_lower:
                    dias_a_sumar = (dia_num - hoy.weekday() + 7) % 7
                    if dias_a_sumar == 0:
                        dias_a_sumar = 7  # Próximo semana
                    fecha_dia = hoy + timedelta(days=dias_a_sumar)
                    extracted['fecha'] = fecha_dia.strftime("%Y-%m-%dT00:00:00.000Z")
                    logger.info(f"📊 Fecha extraída ({dia_nombre.capitalize()}): {extracted['fecha']}")
                    break
        # Extraer hora: formato 04:00:00.000Z o 14:30
        hora_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2}(?:\.\d{3}Z)?)?)', message_lower)
        if hora_match:
            hora = int(hora_match.group(1).split(':')[0])
            minuto = int(hora_match.group(1).split(':')[1])
            periodo = 'AM' if hora < 12 else 'PM'
            logger.info(f"📊 Hora extraída: {hora}:{minuto:02d} {periodo}")

            #Convertir a 24h si es am/pm
            if 'pm' in message_lower and hora < 12:
                hora += 12
            elif 'am' in message_lower and hora == 12:
                hora = 0

            extracted['hora'] = f"{hora:02d}:{minuto:02d}:00.000Z"
            logger.info(f"📊 Hora extraída (24h): {extracted['hora']}")

        # Horarios textuales
        horarios_text = {
            'mañana': '09:00:00.000Z',
            'tarde': '15:00:00.000Z',
            'noche': '19:00:00.000Z',
        }

        if not extracted["hora"]:
            for texto, hora in horarios_text.items():
                if texto in message_lower:
                    extracted['hora'] = hora
                    logger.info(f"📊 Hora extraída (Texto): {extracted['hora']}")
                    break
        
        # Extraccion de motivo

        motivos_keywords = {
            'control': 'Control de rutina',
            'revision': 'Revision medica',
            'sintomas': 'Consulta por sintomas',
            'medicacion': 'Consulta de medicacion',
            'resultados': 'Consulta de resultados',
            'emergencia': 'Emergencia'
        }

        for keyword, motivo in motivos_keywords.items():
            if keyword in message_lower:
                extracted['motivo'] = motivo
                logger.info(f"📊 Motivo extraído: {motivo}")
                break

        return extracted

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
    
    async def _build_prompt(
        self,
        conversation: Conversation,
        user_id: str
    ) -> str:
        """
        Construye el prompt con FORMATO ESTRUCTURADO.
        
        NUEVO FORMATO alineado con el modelo fine-tuned estructurado:
        <SYS>
        ... instrucciones del sistema ...
        </SYS>
        
        <DATA>
        Paciente_registrado = True/False
        Nombre = "Nombre Real" o None
        Citas = [...] o []
        Ultima_visita = "fecha" o None
        </DATA>
        
        <USER>: mensaje
        <ASSISTANT>:
        
        Args:
            conversation: Conversación con historial
            user_id: ID del usuario (teléfono) para consultar BD
        
        Returns:
            Prompt estructurado completo
        """
        # 1. BLOQUE <SYS> - Instrucciones del sistema
        system_block = f"""<SYS>
Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud {settings.medical_center_name}.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta.
Si preguntan algo fuera de Tuberculosis, responde: "Lo siento, solo atiendo consultas sobre Tuberculosis".
</SYS>"""
        
        # 2. BLOQUE <DATA> - Consultar paciente en BD
        patient_data = None
        patient_registered = False
        
        if self.patient_service:
            try:
                patient_registered, patient_data = await self.patient_service.verify_patient(
                    phone_number=user_id
                )
            except Exception as e:
                logger.warning(f"⚠️ Error consultando BD: {e}")
        
        # Construir bloque <DATA> estructurado
        data_lines = []
        data_lines.append(f"Paciente_registrado = {patient_registered}")
        
        if patient_registered and patient_data:
            nombre = patient_data.get('nombre', 'N/A')
            data_lines.append(f'Nombre = "{nombre}"')
            
            # Obtener próxima cita
            proxima_cita = patient_data.get('proxima_cita')
            if proxima_cita and isinstance(proxima_cita, dict):
                logger.info(f"📊 Próxima cita encontrada: {proxima_cita}")
                fecha_programada = proxima_cita.get('fecha_programada', 'N/A')
                fecha = fecha_programada.split('T')[0] if 'T' in fecha_programada else fecha_programada
                hora = fecha_programada.split('T')[1].split('.')[0] if 'T' in fecha_programada else 'N/A'
                estado = proxima_cita.get('estado')
                estado_desc = estado.get('descripcion', 'N/A') if estado else 'N/A'
                logger.info(f"📊 Próxima cita - Fecha: {fecha}, Hora: {hora}, Estado: {estado_desc}")
                data_lines.append(f'Citas = [{{fecha: "{fecha}", hora: "{hora}", estado: "{estado_desc}"}}]')
            else:
                data_lines.append("Citas = []")
                logger.info("📊 Sin próximas citas encontradas")
            
            # Última visita (si está disponible)
            ultima_visita = patient_data.get('ultima_visita')
            if ultima_visita:
                logger.info(f"📊 Última visita: {ultima_visita}")
                data_lines.append(f'Ultima_visita = "{ultima_visita}"')
            else:
                logger.info("📊 Sin última visita registrada")
                data_lines.append("Ultima_visita = None")
        else:
            # Paciente NO registrado
            data_lines.append("Nombre = None")
            data_lines.append("Citas = []")
            data_lines.append("Ultima_visita = None")
            logger.info("📊 Paciente no registrado, datos por defecto en <DATA>")
        
        data_block = "\n".join(data_lines)
        logger.info(f"📊 Bloque <DATA> construido:\n{data_block}")
        
        # 3. HISTORIAL - Solo último mensaje del usuario (el actual)
        recent_messages = conversation.get_recent_messages(limit=10)
        logger.info(f"📊 Mensajes recientes obtenidos: {len(recent_messages)}")

        # Filtrar mensajes válidos (sin corrupción)
        valid_messages = []
        for msg in recent_messages:
            # Saltar mensajes corruptos
            if any(word in msg.content.lower() for word in ['tuberación', 'tuberculos', 'diego', '14003']):
                logger.warning(f"⚠️ Mensaje corrupto saltado: {msg.content[:50]}")
                continue
            
            # Saltar mensajes muy largos
            if len(msg.content) > 200:
                logger.warning(f"⚠️ Mensaje muy largo saltado")
                continue
            
            valid_messages.append(msg)

        # Construir historial
        history_lines = []

        if len(valid_messages) > 1:
            # Tomar todos EXCEPTO el ultimo
            for msg in valid_messages[:-1]:
                if msg.role == MessageRole.USER:
                    history_lines.append(f"<USER>: {msg.content}")
                elif msg.role == MessageRole.ASSISTANT:
                    history_lines.append(f"<ASSISTANT>: {msg.content}")
        history_block = "\n".join(history_lines) if history_lines else ""
        
        last_user_message = ""
        if valid_messages:
            last_msg = valid_messages[-1]
            if last_msg.role == MessageRole.USER:
                last_user_message = last_msg.content
            else:
                for msg in reversed(valid_messages):
                    if msg.role == MessageRole.USER:
                        last_user_message = msg.content
                        break
        
        if not last_user_message:
            last_user_message = "Hola"

        # 4. Construir prompt completo
        if history_block:
            prompt = f"""{system_block}

<DATA>
{data_block}
</DATA>

<HISTORY>
{history_block}
</HISTORY>

<USER>: {last_user_message}
<ASSISTANT>:"""
            
        else:
            prompt = f"""{system_block}

<DATA>
{data_block}
</DATA>

<USER>: {last_user_message}
<ASSISTANT>:"""
        
        logger.info(f"� Prompt estructurado construido (longitud: {len(prompt)} chars)")
        logger.info(f"Historial incluido: {'Si' if history_block else 'No'} ({len(history_lines)} mensajes)")
        logger.info(f"Prompt completo:\n{prompt}")
        
        return prompt
    
    def _generate_with_model(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """
        Genera texto usando el modelo de lenguaje con formato estructurado.
        
        Args:
            prompt: Prompt completo con formato <SYS>, <DATA>, <USER>
            max_tokens: Máximo de tokens a generar
            temperature: Temperatura del modelo
        
        Returns:
            Texto generado
        """
        import torch
        
        # Tokenizar el prompt con attention_mask
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            max_length=512,
            truncation=True,
            padding=True,
            return_attention_mask=True  # ✅ CRÍTICO: Evita warnings
        )

        # Mover a dispositivo
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Obtener la longitud del prompt para extraer solo lo nuevo
        prompt_length = inputs['input_ids'].shape[1]
        
        # Agregar tokens de detencion
        stop_tokens = [
            self.tokenizer.encode("\n\n", add_special_tokens=False)[0],
            self.tokenizer.encode("\n:", add_special_tokens=False)[0],
            self.tokenizer.encode("<USER>", add_special_tokens=False)[0],
            self.tokenizer.eos_token_id,
        ]
        
        # Generar con el modelo
        with torch.no_grad():
            outputs = self.model.generate(
                input_ids = inputs['input_ids'],
                attention_mask = inputs['attention_mask'],
                max_new_tokens=min(max_tokens, 80),
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                top_k=50,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=stop_tokens,
                repetition_penalty=1.2,  # Penaliza repeticiones
                no_repeat_ngram_size=3,  # Evita n-gramas repetidos
                early_stopping=True 
            )
        
        # Decodificar SOLO los tokens nuevos (no el prompt completo)
        generated_tokens = outputs[0][prompt_length:]
        response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        logger.info(f"📝 Respuesta bruta del modelo: {response}")
        
        # Limpiar la respuesta
        response = self._clean_response(response)

        if not response or len(response.strip()) < 5:
            logger.info("⚠️ Respuesta vacía o muy corta, usando respuesta por defecto")
            # Generar respuesta contextual basada en el último mensaje
            return "No tengo esta información registrada. ¿En qué más puedo ayudarte?"
        
        return response
    
    def _clean_response(self, response: str) -> str:
        """
        Limpia la respuesta del modelo.
        
        MEJORAS:
        1. Trunca después de 2 oraciones
        2. Remueve conversaciones ficticias
        3. Valida que sea una respuesta única
        """
        if not response:
            return ""
        
        # 1. Remover prefijos incorrectos
        prefixes = ["<ASSISTANT>:", "Asistente:", "Assistant:", ":"]
        for prefix in prefixes:
            if response.startswith(prefix):
                response = response[len(prefix):].strip()
        
        # 2. ✅ TRUNCAR en marcadores de conversación ficticia
        stop_markers = [
            "\n\n",           # Doble salto de línea
            "\n:",            # Nuevo diálogo
            "\n<USER>:",      # Nuevo usuario
            "\n<ASSISTANT>:", # Nuevo asistente
            "Paciente:",      # Diálogo del paciente
            "Usuario:",       # Diálogo del usuario
        ]
        
        for marker in stop_markers:
            if marker in response:
                response = response.split(marker)[0]
                logger.debug(f"🔪 Truncado en marcador: {marker}")
        
        # 3. ✅ LIMITAR A 2 ORACIONES
        sentences = self._split_sentences(response)
        
        if len(sentences) > 2:
            logger.warning(f"⚠️ Respuesta tenía {len(sentences)} oraciones, truncando a 2")
            response = ". ".join(sentences[:2]) + "."
        
        # 4. Limpiar espacios múltiples
        response = " ".join(response.split())
        
        # 5. Asegurar que termina con puntuación
        if response and response[-1] not in '.!?':
            response += "."
        
        return response.strip()

    def _split_sentences(self, text: str) -> list[str]:
        """
        Divide texto en oraciones.

        Detecta fin de oracion por:
        - Punto seguido de espacio y mayuscula
        - Signos de interrogacion o exclamacion
        """ 

        import re
        # Patrón: Punto/Interrogación/Exclamación + Espacio + Mayúscula
        pattern = r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ])'
        
        sentences = re.split(pattern, text)
        
        # Limpiar oraciones vacías
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
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
