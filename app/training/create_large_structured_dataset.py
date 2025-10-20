"""
Script para Crear Dataset ESTRUCTURADO MASIVO
==============================================

Genera entre 2000-5000 ejemplos estructurados para entrenar
el modelo con suficiente diversidad.

Autor: Sistema de IA
Fecha: 19 de Octubre, 2025
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path


class LargeStructuredDatasetGenerator:
    """
    Generador MASIVO de datasets estructurados (2000-5000 ejemplos)
    """
    
    def __init__(self, num_ejemplos: int = 3000):
        self.num_ejemplos = num_ejemplos
        self.system_prompt = """Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud CAÑADA DEL CARMEN.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta.
Si preguntan algo fuera de Tuberculosis, responde: "Lo siento, solo atiendo consultas sobre Tuberculosis"."""
        
        # 50 nombres variados
        self.nombres = [
            "Taison Perez", "María González", "Carlos Rodríguez", "Ana López", "Luis Martinez",
            "Sofia Fernández", "Miguel Sánchez", "Laura Torres", "Pedro Ramírez", "Elena Castro",
            "Jorge Morales", "Daniela Vargas", "Roberto Salazar", "Valentina Rojas", "Fernando Ortiz",
            "Camila Mendoza", "Andrés Gutiérrez", "Isabella Ríos", "Gabriel Cruz", "Lucía Herrera",
            "Diego Flores", "Natalia Reyes", "Sebastián Jiménez", "Paula Vega", "Mateo Romero",
            "Victoria Silva", "Nicolás Medina", "Martina Díaz", "Santiago Paredes", "Catalina Campos",
            "Alejandro Núñez", "Carmen Soto", "Raúl Peña", "Adriana Luna", "Javier Cordero",
            "Gabriela Robles", "Emilio Aguilar", "Verónica Arias", "Ricardo Maldonado", "Teresa Ibarra",
            "Marcos Vázquez", "Claudia Guerrero", "Fabián Delgado", "Patricia Montes", "Óscar Navarro",
            "Silvia Escobar", "Ignacio Ramos", "Beatriz Cabrera", "Leonardo Fuentes", "Rosa Molina"
        ]
        
        # 30 variaciones de saludos del usuario
        self.saludos_user = [
            "Hola", "Buenos días", "Buenas tardes", "Buenas noches", "Hola doctor",
            "Hola doctora", "Saludos", "Qué tal", "Hola, ¿cómo estás?", "Buenas",
            "Hola!", "Hi", "Hey", "Hola, necesito ayuda", "Hola, tengo una consulta",
            "Buenos días doctor", "Buenas tardes doctora", "Hola, ¿cómo está?",
            "Qué onda", "Hola, ¿me ayudas?", "Hola, tengo dudas", "Buen día",
            "Buena tarde", "Buena noche", "Hola, ¿estás ahí?", "Hola asistente",
            "Hola bot", "Necesito información", "Quiero consultar", "Ayuda por favor"
        ]
        
        # 15 variaciones de respuestas de saludo del asistente
        self.saludos_assistant_templates = [
            "¡Hola {nombre}! ¿En qué puedo ayudarte hoy?",
            "¡Buenos días {nombre}! ¿Cómo te sientes?",
            "¡Hola {nombre}! ¿Tienes alguna consulta sobre tu tratamiento?",
            "¡Buenas tardes {nombre}! ¿Necesitas información sobre tu cita?",
            "¡Hola {nombre}! Estoy aquí para ayudarte con tu seguimiento.",
            "¡Saludos {nombre}! ¿En qué puedo asistirte?",
            "¡Hola {nombre}! ¿Cómo va tu tratamiento?",
            "¡Buenos días {nombre}! ¿Qué necesitas hoy?",
            "¡Hola {nombre}! ¿Todo bien con tu medicación?",
            "¡Buenas {nombre}! Cuéntame, ¿cómo te sientes?",
            "¡Hola {nombre}! ¿Necesitas recordatorio de tu cita?",
            "¡Saludos {nombre}! ¿Alguna duda sobre tu tratamiento?",
            "¡Hola {nombre}! Aquí para cualquier consulta sobre TB.",
            "¡Buenos días {nombre}! ¿Cómo está tu tos?",
            "¡Hola {nombre}! ¿Qué consulta tienes hoy?"
        ]
        
        # 25 variaciones de preguntas sobre citas
        self.preguntas_citas = [
            "¿Cuándo es mi cita?", "¿Cuándo es mi próxima cita?", "¿Tengo cita?",
            "¿Tengo alguna cita programada?", "¿Cuál es mi próxima cita?",
            "Cuándo debo ir al centro?", "¿Cuándo me toca ir?", "¿Para cuándo es mi cita?",
            "Dime mi próxima cita", "¿Qué día tengo cita?", "¿A qué hora es mi cita?",
            "¿Dónde es mi cita?", "Necesito saber mi cita", "Información sobre mi cita",
            "¿Cuándo es mi control?", "¿Cuándo tengo control?", "Fecha de mi cita",
            "Hora de mi cita", "¿Tengo control próximamente?", "¿Cuándo debo volver?",
            "¿Cuándo es mi siguiente consulta?", "¿Tengo cita agendada?",
            "¿Me puedes decir cuándo es mi cita?", "Quiero saber mi próxima cita",
            "¿Qué día me toca?"
        ]
        
        # 10 variaciones de respuestas con cita
        self.respuestas_con_cita_templates = [
            "Tu próxima cita es el {fecha} a las {hora}.",
            "Tienes cita programada para el {fecha} a las {hora}.",
            "Tu cita está agendada el {fecha} a las {hora}.",
            "Debes venir el {fecha} a las {hora} para tu control.",
            "Tu control es el {fecha} a las {hora}.",
            "Está programada para el {fecha} a las {hora}. No olvides asistir.",
            "El {fecha} a las {hora} tienes tu control de TB.",
            "Tu próximo control es el {fecha} a las {hora}.",
            "Tienes agendado el {fecha} a las {hora}.",
            "Tu cita de seguimiento es el {fecha} a las {hora}."
        ]
        
        # 8 variaciones de respuestas sin cita
        self.respuestas_sin_cita = [
            "No tienes citas programadas actualmente. ¿Necesitas agendar una?",
            "No encuentro ninguna cita registrada para ti. Comunícate con el centro.",
            "Actualmente no tienes citas agendadas.",
            "No hay citas programadas. ¿Deseas solicitar una?",
            "No veo citas pendientes en tu registro.",
            "No tienes controles agendados por el momento.",
            "No hay citas en tu historial. Contacta al centro para agendar.",
            "No encuentro citas programadas para ti."
        ]
        
        # 20 preguntas sobre síntomas de TB
        self.preguntas_sintomas = [
            "¿Qué síntomas tiene la tuberculosis?",
            "¿Cuáles son los síntomas de TB?",
            "¿Cómo sé si tengo tuberculosis?",
            "Síntomas de la tuberculosis",
            "¿Qué siento si tengo TB?",
            "¿Cuáles son las señales de TB?",
            "Tengo tos, ¿puede ser tuberculosis?",
            "¿Cómo detectar TB?",
            "¿Qué señales da la TB?",
            "¿Cuáles son los síntomas principales?",
            "¿Cómo se manifiesta la tuberculosis?",
            "¿Qué siente una persona con TB?",
            "Síntomas de TB pulmonar",
            "¿Cuáles son los signos de alerta?",
            "¿Qué es normal sentir con TB?",
            "Tengo fiebre y tos, ¿es TB?",
            "¿La TB da fiebre?",
            "¿Qué molestias causa la tuberculosis?",
            "¿Cuándo sospechar de TB?",
            "Indicios de tuberculosis"
        ]
        
        # 10 respuestas sobre síntomas
        self.respuestas_sintomas = [
            "Los síntomas principales son: tos persistente por más de 2 semanas, fiebre, sudores nocturnos y pérdida de peso.",
            "Tos con sangre, fiebre vespertina, cansancio extremo y pérdida de apetito son señales de TB.",
            "Si tienes tos por más de 15 días, fiebre y pérdida de peso, consulta inmediatamente.",
            "Tos persistente, sudoración nocturna, fiebre y debilidad son síntomas clave de TB.",
            "Los signos incluyen: tos crónica, expectoración con sangre, fiebre y pérdida de peso.",
            "Tos que dura más de 2 semanas, fiebre, escalofríos y fatiga son alertas de TB.",
            "Síntomas: tos persistente, dolor en el pecho, fiebre y sudores nocturnos.",
            "Si presentas tos, fiebre vespertina y pérdida de peso rápida, acude al centro.",
            "La TB causa tos prolongada, fiebre intermitente, sudoración nocturna y debilidad.",
            "Tos con flema por más de 2 semanas, fiebre y pérdida de apetito indican TB."
        ]
        
        # 18 preguntas sobre tratamiento
        self.preguntas_tratamiento = [
            "¿Cuánto dura el tratamiento?",
            "¿Cuánto tiempo debo tomar las pastillas?",
            "¿Cuál es la duración del tratamiento de TB?",
            "¿Por cuánto tiempo es el tratamiento?",
            "¿Cuándo termina mi tratamiento?",
            "¿Cuántos meses dura el tratamiento?",
            "¿Cuánto tiempo tomo la medicación?",
            "Duración del tratamiento de tuberculosis",
            "¿Cuándo dejo de tomar las pastillas?",
            "¿Cuánto falta para terminar mi tratamiento?",
            "¿Cuándo acaba el tratamiento?",
            "¿Son muchos meses de tratamiento?",
            "¿Cuánto dura la medicación?",
            "Tiempo de tratamiento de TB",
            "¿Cuánto tardo en curarme?",
            "¿Cuántos meses son de tratamiento?",
            "¿Hasta cuándo debo tomar pastillas?",
            "¿Cuánto dura la terapia de TB?"
        ]
        
        # 8 respuestas sobre tratamiento
        self.respuestas_tratamiento = [
            "El tratamiento de TB dura 6 meses. Es importante completarlo sin interrupciones.",
            "Son 6 meses de medicación diaria. No debes suspenderlo aunque te sientas mejor.",
            "El tratamiento completo es de 6 meses con pastillas diarias.",
            "Debes tomar medicación por 6 meses para curar completamente la TB.",
            "Son 6 meses de tratamiento. Suspenderlo antes puede generar resistencia.",
            "La duración estándar es 6 meses. Es crucial no abandonar el tratamiento.",
            "6 meses de pastillas diarias. Completar el tratamiento garantiza la cura.",
            "El tratamiento dura aproximadamente 6 meses sin interrupciones."
        ]
        
        # 20 preguntas sobre medicación
        self.preguntas_medicacion = [
            "¿Cómo debo tomar las pastillas?",
            "¿A qué hora tomo la medicación?",
            "¿Cuántas pastillas debo tomar?",
            "¿Puedo tomar las pastillas con comida?",
            "¿Qué pasa si olvido una dosis?",
            "¿Puedo partir las pastillas?",
            "¿Debo tomar las pastillas con agua?",
            "¿Cuántas veces al día tomo la medicación?",
            "¿Las pastillas tienen efectos secundarios?",
            "¿Qué hago si vomito las pastillas?",
            "¿Puedo tomar alcohol durante el tratamiento?",
            "¿Las pastillas me darán náuseas?",
            "¿Debo tomar todas las pastillas juntas?",
            "¿Qué pasa si salto un día?",
            "¿Puedo tomar las pastillas en la noche?",
            "¿Necesito tomar las pastillas en ayunas?",
            "¿Qué hago si me siento mal con las pastillas?",
            "¿Las pastillas interactúan con otros medicamentos?",
            "¿Puedo dejar de tomar si me siento bien?",
            "¿Qué pasa si tomo doble dosis?"
        ]
        
        # 10 respuestas sobre medicación
        self.respuestas_medicacion = [
            "Debes tomar las pastillas en ayunas, preferiblemente por la mañana con agua.",
            "Toma toda la medicación junta en una sola dosis matutina en ayunas.",
            "Si olvidas una dosis, tómala apenas lo recuerdes el mismo día.",
            "No suspendas el tratamiento aunque te sientas mejor. Completa los 6 meses.",
            "Evita el alcohol durante el tratamiento, puede dañar tu hígado.",
            "Si vomitas dentro de 1 hora, consulta si debes repetir la dosis.",
            "Las náuseas son normales al inicio. Toma las pastillas con un poco de comida.",
            "No partas las pastillas. Tómalas enteras con abundante agua.",
            "Contacta al centro si tienes efectos secundarios severos.",
            "Nunca tomes doble dosis. Si saltaste un día, continúa normalmente."
        ]
        
        # 30 preguntas fuera de contexto (off-topic)
        self.preguntas_off_topic = [
            "¿Qué es la hipotenusa?",
            "¿Cómo está el clima?",
            "¿Qué hora es?",
            "¿Cuál es la capital de Francia?",
            "¿Qué es el COVID-19?",
            "¿Qué es la diabetes?",
            "¿Cómo se cura el cáncer?",
            "¿Qué es la gripe?",
            "¿Qué deportes te gustan?",
            "Cuéntame un chiste",
            "¿Quién es el presidente?",
            "¿Qué día es hoy?",
            "¿Puedes ayudarme con matemáticas?",
            "¿Qué es la hipertensión?",
            "¿Cómo se prepara un pastel?",
            "¿Qué es la fotosíntesis?",
            "¿Cómo funciona un motor?",
            "¿Qué es el amor?",
            "¿Cuánto es 2 + 2?",
            "¿Qué opinas de la política?",
            "¿Cómo se hace una empanada?",
            "¿Qué es la inteligencia artificial?",
            "¿Cuál es el mejor teléfono?",
            "¿Qué películas recomiendas?",
            "¿Cómo se juega al fútbol?",
            "¿Qué es la energía solar?",
            "¿Cómo se toca guitarra?",
            "¿Qué es el universo?",
            "¿Cuál es tu color favorito?",
            "¿Qué significa la vida?"
        ]
        
        # 5 variaciones de rechazo a preguntas off-topic
        self.respuestas_off_topic = [
            "Lo siento, solo atiendo consultas sobre Tuberculosis.",
            "Mi especialidad es solo Tuberculosis. ¿Tienes preguntas sobre TB?",
            "No puedo ayudarte con eso. Solo respondo sobre Tuberculosis.",
            "Esa pregunta está fuera de mi área. Solo atiendo temas de TB.",
            "Solo proporciono información sobre Tuberculosis."
        ]
        
        # Estados de citas
        self.estados_cita = ["Programado", "Confirmado", "Pendiente"]
        
        # Horarios de citas (24 horarios diferentes)
        self.horarios = [
            "08:00", "08:30", "09:00", "09:30", "10:00", "10:30",
            "11:00", "11:30", "12:00", "14:00", "14:30", "15:00",
            "15:30", "16:00", "16:30", "17:00", "17:30", "18:00",
            "07:00", "07:30", "13:00", "13:30", "18:30", "19:00"
        ]
        
        self.dataset = []
    
    def _format_data_block(
        self,
        paciente_registrado: bool,
        nombre: str = None,
        citas: List[Dict] = None,
        ultima_visita: str = None
    ) -> str:
        """Formatea el bloque <DATA>"""
        data_lines = []
        data_lines.append("Paciente_registrado = " + ("True" if paciente_registrado else "False"))
        data_lines.append("Nombre = " + (f'"{nombre}"' if nombre else "None"))
        
        if citas:
            citas_str = "["
            for i, cita in enumerate(citas):
                citas_str += f'{{fecha: "{cita["fecha"]}", hora: "{cita["hora"]}", estado: "{cita["estado"]}"}}'
                if i < len(citas) - 1:
                    citas_str += ", "
            citas_str += "]"
            data_lines.append(f"Citas = {citas_str}")
        else:
            data_lines.append("Citas = []")
        
        data_lines.append("Ultima_visita = " + (f'"{ultima_visita}"' if ultima_visita else "None"))
        
        return "\n".join(data_lines)
    
    def _create_prompt(self, data_block: str, user_message: str) -> str:
        """Crea el prompt completo"""
        prompt = f"<SYS>\n{self.system_prompt}\n</SYS>\n\n"
        prompt += f"<DATA>\n{data_block}\n</DATA>\n\n"
        prompt += f"<USER>: {user_message}\n<ASSISTANT>:"
        return prompt
    
    def _generate_random_date(self, days_ahead: int = 30) -> str:
        """Genera fecha aleatoria futura"""
        fecha = datetime.now() + timedelta(days=random.randint(1, days_ahead))
        return fecha.strftime("%Y-%m-%d")
    
    def _generate_random_past_date(self, days_ago: int = 90) -> str:
        """Genera fecha aleatoria pasada"""
        fecha = datetime.now() - timedelta(days=random.randint(1, days_ago))
        return fecha.strftime("%Y-%m-%d")
    
    def _add_example(self, prompt: str, completion: str):
        """Agrega ejemplo al dataset"""
        self.dataset.append({
            "prompt": prompt,
            "completion": f" {completion}"
        })

    def _clean_completion(self, text: str) -> str:
        """
        Limpia y trunca el completion a maximo 2 oraciones.

        Asegura que:
        - Sea corto (max 2 oraciones).
        - Termine con puntuacion
        - No tenga saltos de linea dobles
        - No contenga marcadores de conversacion

        Args:
            text: Completion original

        Returns:
            Completion limpio y corto
        """

        import re

        # 1. Remover saltos de línea dobles
        text = text.replace('\n\n', '. ')
        text = text.replace('\n', ' ')
        
        # 2. Dividir en oraciones (por punto + espacio + mayúscula)
        # Patrón: . seguido de espacio y letra mayúscula
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])', text)
        
        # Limpiar oraciones vacías
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # 3. Tomar solo las primeras 2 oraciones
        if len(sentences) > 2:
            text = '. '.join(sentences[:2])
            # Asegurar que termina con punto
            if not text.endswith('.'):
                text += '.'
        elif len(sentences) > 0:
            text = ' '.join(sentences)
        
        # 4. Asegurar que termina con puntuación
        if text and text[-1] not in '.!?':
            text += '.'
        
        # 5. Limpiar espacios múltiples
        text = ' '.join(text.split())
        
        # 6. Limitar longitud máxima (200 caracteres)
        if len(text) > 200:
            # Cortar en el último punto antes de 200 chars
            truncated = text[:200]
            last_period = truncated.rfind('.')
            if last_period > 50:  # Si hay un punto razonable
                text = truncated[:last_period + 1]
            else:
                text = truncated + '.'
        
        return text.strip()
    
    def generate_saludos_con_cita(self, num: int):
        """Genera ejemplos de saludos con cita programada"""
        print(f"🔄 Generando {num} ejemplos: Saludos con cita...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            saludo_user = random.choice(self.saludos_user)
            
            # Cita aleatoria
            fecha_cita = self._generate_random_date(30)
            hora_cita = random.choice(self.horarios)
            estado_cita = random.choice(self.estados_cita)
            
            citas = [{
                "fecha": fecha_cita,
                "hora": hora_cita,
                "estado": estado_cita
            }]
            
            ultima_visita = self._generate_random_past_date(60) if random.random() > 0.3 else None
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=citas,
                ultima_visita=ultima_visita
            )
            
            prompt = self._create_prompt(data_block, saludo_user)
            
            # Respuesta con recordatorio de cita
            completion = random.choice(self.saludos_assistant_templates).format(nombre=nombre.split()[0])
            completion += f" Te recuerdo que tienes cita el {fecha_cita} a las {hora_cita}."
            
            # LIMPIAR COMPLETION ANTES DE AGREGAR
            completion = self._clean_completion(completion)
            
            self._add_example(prompt, completion)
    
    def generate_saludos_sin_cita(self, num: int):
        """Genera ejemplos de saludos sin cita"""
        print(f"🔄 Generando {num} ejemplos: Saludos sin cita...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            saludo_user = random.choice(self.saludos_user)
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=self._generate_random_past_date(90) if random.random() > 0.5 else None
            )
            
            prompt = self._create_prompt(data_block, saludo_user)
            completion = random.choice(self.saludos_assistant_templates).format(nombre=nombre.split()[0])
            
            # LIMPIAR COMPLETION
            completion = self._clean_completion(completion)
            
            self._add_example(prompt, completion)
    
    def generate_consultas_cita_con_datos(self, num: int):
        """Genera consultas sobre citas cuando SÍ hay cita"""
        print(f"🔄 Generando {num} ejemplos: Consultas de cita CON datos...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            pregunta = random.choice(self.preguntas_citas)
            
            fecha_cita = self._generate_random_date(45)
            hora_cita = random.choice(self.horarios)
            
            citas = [{
                "fecha": fecha_cita,
                "hora": hora_cita,
                "estado": random.choice(self.estados_cita)
            }]
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=citas,
                ultima_visita=self._generate_random_past_date()
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_con_cita_templates).format(
                fecha=fecha_cita,
                hora=hora_cita
            )

            # LIMPIAR COMPLETION
            completion = self._clean_completion(completion)

            self._add_example(prompt, completion)
    
    def generate_consultas_cita_sin_datos(self, num: int):
        """Genera consultas sobre citas cuando NO hay cita"""
        print(f"🔄 Generando {num} ejemplos: Consultas de cita SIN datos...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            pregunta = random.choice(self.preguntas_citas)
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=self._generate_random_past_date() if random.random() > 0.3 else None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_sin_cita)

            # ✅ LIMPIAR COMPLETION
            completion = self._clean_completion(completion)

            self._add_example(prompt, completion)
    
    def generate_paciente_no_registrado(self, num: int):
        """Genera ejemplos de pacientes NO registrados"""
        print(f"🔄 Generando {num} ejemplos: Pacientes NO registrados...")
        for _ in range(num):
            pregunta = random.choice(self.preguntas_citas + self.saludos_user)
            
            data_block = self._format_data_block(
                paciente_registrado=False,
                nombre=None,
                citas=None,
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = "No encuentro tu información en el sistema. Por favor comunícate con el centro de salud."
            
            completion = self._clean_completion(completion)

            self._add_example(prompt, completion)
    
    def generate_preguntas_sintomas(self, num: int):
        """Genera preguntas sobre síntomas de TB"""
        print(f"🔄 Generando {num} ejemplos: Preguntas sobre síntomas...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            pregunta = random.choice(self.preguntas_sintomas)
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_sintomas)
            
            completion = self._clean_completion(completion)

            self._add_example(prompt, completion)
    
    def generate_preguntas_tratamiento(self, num: int):
        """Genera preguntas sobre tratamiento"""
        print(f"🔄 Generando {num} ejemplos: Preguntas sobre tratamiento...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            pregunta = random.choice(self.preguntas_tratamiento)
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=self._generate_random_past_date()
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_tratamiento)

            completion = self._clean_completion(completion)
            
            self._add_example(prompt, completion)
    
    def generate_preguntas_medicacion(self, num: int):
        """Genera preguntas sobre medicación"""
        print(f"🔄 Generando {num} ejemplos: Preguntas sobre medicación...")
        for _ in range(num):
            nombre = random.choice(self.nombres)
            pregunta = random.choice(self.preguntas_medicacion)
            
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=self._generate_random_past_date()
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_medicacion)

            completion = self._clean_completion(completion)
            
            self._add_example(prompt, completion)
    
    def generate_preguntas_off_topic(self, num: int):
        """Genera preguntas fuera de contexto"""
        print(f"🔄 Generando {num} ejemplos: Preguntas OFF-TOPIC...")
        for _ in range(num):
            nombre = random.choice(self.nombres) if random.random() > 0.3 else None
            pregunta = random.choice(self.preguntas_off_topic)
            
            paciente_registrado = nombre is not None
            
            data_block = self._format_data_block(
                paciente_registrado=paciente_registrado,
                nombre=nombre,
                citas=[],
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = random.choice(self.respuestas_off_topic)

            # LIMPIAR COMPLETION
            completion = self._clean_completion(completion)

            self._add_example(prompt, completion)
    
    def generate_all(self):
        """Genera TODOS los ejemplos balanceados"""
        print(f"\n{'='*70}")
        print(f"🚀 GENERANDO {self.num_ejemplos} EJEMPLOS ESTRUCTURADOS")
        print(f"{'='*70}\n")
        
        # Distribución balanceada de ejemplos
        distribucion = {
            "saludos_con_cita": int(self.num_ejemplos * 0.12),      # 12%
            "saludos_sin_cita": int(self.num_ejemplos * 0.10),      # 10%
            "consultas_cita_con_datos": int(self.num_ejemplos * 0.18),  # 18%
            "consultas_cita_sin_datos": int(self.num_ejemplos * 0.15),  # 15%
            "paciente_no_registrado": int(self.num_ejemplos * 0.10),    # 10%
            "preguntas_sintomas": int(self.num_ejemplos * 0.15),        # 15%
            "preguntas_tratamiento": int(self.num_ejemplos * 0.10),     # 10%
            "preguntas_medicacion": int(self.num_ejemplos * 0.07),      # 7%
            "preguntas_off_topic": int(self.num_ejemplos * 0.03)        # 3%
        }
        
        # Generar cada tipo
        self.generate_saludos_con_cita(distribucion["saludos_con_cita"])
        self.generate_saludos_sin_cita(distribucion["saludos_sin_cita"])
        self.generate_consultas_cita_con_datos(distribucion["consultas_cita_con_datos"])
        self.generate_consultas_cita_sin_datos(distribucion["consultas_cita_sin_datos"])
        self.generate_paciente_no_registrado(distribucion["paciente_no_registrado"])
        self.generate_preguntas_sintomas(distribucion["preguntas_sintomas"])
        self.generate_preguntas_tratamiento(distribucion["preguntas_tratamiento"])
        self.generate_preguntas_medicacion(distribucion["preguntas_medicacion"])
        self.generate_preguntas_off_topic(distribucion["preguntas_off_topic"])
        
        # Mezclar dataset
        random.shuffle(self.dataset)
        
        print(f"\n{'='*70}")
        print(f"✅ TOTAL GENERADO: {len(self.dataset)} ejemplos")
        print(f"{'='*70}\n")
    
    def save(self, filename: str = "tuberculosis_structured_large.json"):
        """Guarda el dataset en archivo JSON"""
        output_path = Path(__file__).parent / "datasets" / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dataset guardado en: {output_path}")
        print(f"📊 Total de ejemplos: {len(self.dataset)}")
        
        # Estadísticas
        print(f"\n📈 ESTADÍSTICAS:")
        print(f"   - Tamaño del archivo: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
        print(f"   - Promedio longitud prompt: {sum(len(e['prompt']) for e in self.dataset) / len(self.dataset):.0f} chars")
        print(f"   - Promedio longitud completion: {sum(len(e['completion']) for e in self.dataset) / len(self.dataset):.0f} chars")


def main():
    """
    Función principal
    
    Uso:
        python app/training/create_large_structured_dataset.py
        python app/training/create_large_structured_dataset.py 5000  # Para 5000 ejemplos
    """
    import sys
    
    # Determinar número de ejemplos
    num_ejemplos = 3000  # Default
    if len(sys.argv) > 1:
        try:
            num_ejemplos = int(sys.argv[1])
            if num_ejemplos < 100 or num_ejemplos > 10000:
                print("⚠️ El número de ejemplos debe estar entre 100 y 10000")
                return
        except ValueError:
            print("❌ Argumento inválido. Uso: python create_large_structured_dataset.py [num_ejemplos]")
            return
    
    print(f"\n🎯 Configurado para generar: {num_ejemplos} ejemplos\n")
    
    # Generar dataset
    generator = LargeStructuredDatasetGenerator(num_ejemplos=num_ejemplos)
    generator.generate_all()
    generator.save(filename=f"tuberculosis_structured_{num_ejemplos}.json")
    
    print(f"\n✅ ¡LISTO! Dataset masivo generado exitosamente")
    print(f"\n📝 SIGUIENTE PASO:")
    print(f"   python app/training/train_gpt2_structured.py --dataset datasets/tuberculosis_structured_{num_ejemplos}.json --epochs 15\n")


if __name__ == "__main__":
    main()
