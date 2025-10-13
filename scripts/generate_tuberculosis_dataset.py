import json
import random
from datetime import datetime, timedelta

class TuberculosisDatasetGenerator:
    """Generador de datasets específicos para Tuberculosis"""
    
    def __init__(self):
        self.dataset = []
        
        # Nombres de pacientes
        self.nombres = [
            "Juan Pérez", "María González", "Carlos López", "Ana Martínez",
            "Pedro Rodríguez", "Laura Fernández", "Diego Silva", "Sofía Ramírez",
            "Roberto Torres", "Carmen Vargas", "Luis Morales", "Patricia Castro",
            "Fernando Ruiz", "Isabel Ortiz", "Miguel Herrera", "Rosa Jiménez"
        ]
        
        # Motivos de cancelación
        self.motivos_cancelacion = [
            "Tengo trabajo", "Me salió un viaje", "Problemas familiares",
            "No me siento bien", "Olvid é la cita", "Tengo otra cita médica",
            "Compromiso laboral", "No tengo transporte", "Emergencia familiar"
        ]
        
        # Síntomas
        self.sintomas_leves = [
            "Tengo un poco de tos", "Me siento cansado", "Tengo tos seca",
            "Poca fiebre", "Me duele un poco el pecho", "Sudoración nocturna"
        ]
        
        self.sintomas_graves = [
            "Toso sangre", "Mucho dolor en el pecho", "No puedo respirar bien",
            "Fiebre muy alta", "Sangre al toser", "Dificultad para respirar"
        ]
    
    def generate_all(self):
        """Generar todos los datasets"""
        
        # 1. Saludos iniciales (100)
        self.generate_greetings(100)
        
        # 2. Recordatorios de cita (150)
        self.generate_reminders(150)
        
        # 3. Cancelaciones (150)
        self.generate_cancellations(150)
        
        # 4. Agendamiento (150)
        self.generate_scheduling(150)
        
        # 5. Seguimiento inasistencia (100)
        self.generate_followup(100)
        
        # 6. Consulta estado de salud (100)
        self.generate_health_check(100)
        
        # 7. Emergencias (50)
        self.generate_emergencies(50)
        
        # 8. Fuera de contexto (100)
        self.generate_out_of_context(100)
        
        # 9. Consulta de citas (100)
        self.generate_appointment_queries(100)
        
        return self.dataset
    
    def generate_greetings(self, count):
        """Generar saludos iniciales"""
        saludos = [
            "Hola", "Buenos días", "Buenas tardes", "Hola, buenas",
            "Buen día", "Qué tal", "Saludos", "Hola, quisiera información"
        ]
        
        for _ in range(count):
            nombre = random.choice(self.nombres)
            saludo = random.choice(saludos)
            
            # Caso 1: Paciente registrado CON cita
            if random.random() < 0.4:
                fecha_cita = (datetime.now() + timedelta(days=random.randint(1, 15))).strftime("%d/%m/%Y")
                hora_cita = random.choice(["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
                
                self.dataset.append({
                    "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}
- Estado: REGISTRADO
- Próxima Cita: {fecha_cita} a las {hora_cita}

Paciente: {saludo}
Asistente:""",
                    "completion": f" ¡Hola {nombre.split()[0]}! ¿Cómo te sientes hoy? Te recuerdo que tienes cita el {fecha_cita} a las {hora_cita} para tu control de tuberculosis. ¿Necesitas algo?"
                })
            
            # Caso 2: Paciente registrado SIN cita
            elif random.random() < 0.7:
                self.dataset.append({
                    "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}
- Estado: REGISTRADO
- Próxima Cita: NO TIENE CITAS PROGRAMADAS

Paciente: {saludo}
Asistente:""",
                    "completion": f" ¡Hola {nombre.split()[0]}! ¿Cómo te sientes hoy? Veo que no tienes citas programadas. ¿Necesitas agendar una consulta?"
                })
            
            # Caso 3: Paciente NO registrado
            else:
                self.dataset.append({
                    "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: NO REGISTRADO

Paciente: {saludo}
Asistente:""",
                    "completion": " ¡Hola! Bienvenido al servicio de Tuberculosis. Para poder asistirte, ¿podrías darme tu nombre completo?"
                })
    
    def generate_reminders(self, count):
        """Generar recordatorios de cita"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            fecha = "mañana" if random.random() < 0.5 else (datetime.now() + timedelta(days=2)).strftime("%d de %B")
            hora = random.choice(["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
            
            # Recordatorio
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}
- Próxima Cita: {fecha} a las {hora}
- ACCIÓN: Enviar recordatorio

Asistente inicia conversación.
Asistente:""",
                "completion": f" Hola {nombre.split()[0]}, te recordamos que tienes cita para tuberculosis el {fecha} a las {hora}. ¿Podrás asistir?"
            })
            
            # Respuesta positiva
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: Hola {nombre.split()[0]}, te recordamos que tienes cita el {fecha} a las {hora}. ¿Podrás asistir?
Paciente: Sí, ahí estaré
Asistente:""",
                "completion": f" ¡Perfecto {nombre.split()[0]}! Te esperamos el {fecha} a las {hora}. Recuerda traer tu documento de identidad y tarjeta de control. ¡Cuídate!"
            })
            
            # Respuesta negativa
            if random.random() < 0.5:
                self.dataset.append({
                    "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: Hola {nombre.split()[0]}, te recordamos que tienes cita el {fecha} a las {hora}. ¿Podrás asistir?
Paciente: No podré ir
Asistente:""",
                    "completion": f" Entiendo {nombre.split()[0]}. ¿Cuál es el motivo por el que no podrás asistir?"
                })
    
    def generate_cancellations(self, count):
        """Generar cancelaciones"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            motivo = random.choice(self.motivos_cancelacion)
            
            # Solicitud de cancelación
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}

Paciente: Quiero cancelar mi cita
Asistente:""",
                "completion": f" Entiendo {nombre.split()[0]}. Para registrar la cancelación, ¿podrías decirme cuál es el motivo?"
            })
            
            # Registro de motivo
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: ¿Cuál es el motivo?
Paciente: {motivo}
Asistente:""",
                "completion": f" He registrado el motivo: {motivo.lower()}. ¿Deseas que reprogramemos tu cita para otra fecha?"
            })
    
    def generate_scheduling(self, count):
        """Generar agendamiento"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            dia = random.choice(["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"])
            turno = random.choice(["mañana", "tarde"])
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}

Paciente: Quiero agendar una cita
Asistente:""",
                "completion": f" Perfecto {nombre.split()[0]}. ¿Para qué día prefieres tu cita de control de tuberculosis?"
            })
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: ¿Para qué día prefieres tu cita?
Paciente: El {dia}
Asistente:""",
                "completion": f" Perfecto, el {dia}. ¿En qué horario te viene mejor: mañana (9:00-12:00) o tarde (14:00-17:00)?"
            })
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: ¿En qué horario: mañana o tarde?
Paciente: En la {turno}
Asistente:""",
                "completion": f" Excelente {nombre.split()[0]}. He agendado tu cita para el {dia} en la {turno}. Recibirás un recordatorio. ¿Algo más?"
            })
    
    def generate_followup(self, count):
        """Generar seguimiento de inasistencia"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            fecha_pasada = (datetime.now() - timedelta(days=random.randint(1, 5))).strftime("%d/%m/%Y")
            motivo = random.choice(self.motivos_cancelacion)
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}
- Cita pasada: {fecha_pasada} - NO ASISTIÓ
- ACCIÓN: Preguntar motivo de inasistencia

Asistente inicia conversación.
Asistente:""",
                "completion": f" Hola {nombre.split()[0]}, notamos que no asististe a tu cita del {fecha_pasada}. ¿Cuál fue el motivo?"
            })
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Asistente: ¿Cuál fue el motivo de tu inasistencia?
Paciente: {motivo}
Asistente:""",
                "completion": f" Entiendo {nombre.split()[0]}, he registrado: {motivo.lower()}. ¿Deseas reprogramar tu cita?"
            })
    
    def generate_health_check(self, count):
        """Generar consultas de estado de salud"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            sintoma = random.choice(self.sintomas_leves)
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}

Paciente: {sintoma}
Asistente:""",
                "completion": f" Entiendo {nombre.split()[0]}. Es importante que el personal médico te evalúe. ¿Deseas agendar una cita para control?"
            })
    
    def generate_emergencies(self, count):
        """Generar casos de emergencia"""
        for _ in range(count):
            sintoma_grave = random.choice(self.sintomas_graves)
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Paciente: {sintoma_grave}
Asistente:""",
                "completion": " ⚠️ Enseguida un personal autorizado se pondrá en contacto contigo, por favor sé paciente hasta que el personal se contacte contigo."
            })
    
    def generate_out_of_context(self, count):
        """Generar preguntas fuera de contexto"""
        preguntas_fuera = [
            "¿Atienden odontología?",
            "Necesito pediatra",
            "¿Tienen medicina general?",
            "Quiero ver al cardiólogo",
            "¿Hacen análisis de sangre?",
            "¿Dónde está el banco?",
            "¿Cuál es el clima?",
            "¿Tienen ginecología?",
            "Necesito traumatólogo",
            "¿Atienden dermatología?"
        ]
        
        for _ in range(count):
            pregunta = random.choice(preguntas_fuera)
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

Paciente: {pregunta}
Asistente:""",
                "completion": " Lo siento, solo atiendo el servicio de Tuberculosis. Para otros servicios médicos, por favor contacta directamente al centro de salud."
            })
    
    def generate_appointment_queries(self, count):
        """Generar consultas de citas"""
        for _ in range(count):
            nombre = random.choice(self.nombres)
            fecha = (datetime.now() + timedelta(days=random.randint(1, 15))).strftime("%d/%m/%Y")
            hora = random.choice(["09:00", "10:00", "11:00", "14:00", "15:00"])
            
            self.dataset.append({
                "prompt": f"""Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis.

CONTEXTO ACTUAL:
- Paciente: {nombre}
- Próxima Cita: {fecha} a las {hora}

Paciente: ¿Cuándo es mi cita?
Asistente:""",
                "completion": f" Hola {nombre.split()[0]}, tu próxima cita para tuberculosis es el {fecha} a las {hora}. ¿Necesitas algo más?"
            })
    
    def save(self, filename="tuberculosis_completo.json"):
        """Guardar dataset"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        print(f"✅ Dataset guardado: {len(self.dataset)} ejemplos en {filename}")

if __name__ == "__main__":
    generator = TuberculosisDatasetGenerator()
    dataset = generator.generate_all()
    generator.save("app/training/datasets/tuberculosis_completo.json")
    print(f"📊 Total ejemplos: {len(dataset)}")