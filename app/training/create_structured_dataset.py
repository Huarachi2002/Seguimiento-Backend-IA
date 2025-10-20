"""
Script para Crear Dataset ESTRUCTURADO
========================================

Este script genera un dataset con formato estructurado que entrena al modelo
a leer datos externos (backend) en vez de inventar información.

FORMATO NUEVO:
--------------
<SYS>
Eres un asistente virtual especializado SOLO en Tuberculosis.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
</SYS>

<DATA>
Paciente_registrado = True/False
Nombre = "Nombre Real" o None
Citas = [{fecha: "2025-10-20", hora: "10:00", estado: "Programado"}] o []
Ultima_visita = "2025-10-10" o None
</DATA>

<USER>: mensaje del usuario
<ASSISTANT>: respuesta basada SOLO en <DATA>
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path


class StructuredDatasetGenerator:
    """
    Generador de datasets estructurados para entrenar el modelo
    a leer datos externos del backend.
    """
    
    def __init__(self):
        self.system_prompt = """Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud CAÑADA DEL CARMEN.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta."""
        
        # Nombres reales para ejemplos
        self.nombres = [
            "Juan Pérez", "María García", "Carlos López", "Ana Martínez",
            "Pedro Rodríguez", "Laura Fernández", "Diego González", "Sofía Torres",
            "Taison Perez", "Roberto Silva", "Valentina Cruz", "Jorge Morales"
        ]
        
        self.dataset = []
    
    def _format_data_block(
        self,
        paciente_registrado: bool,
        nombre: str = None,
        citas: List[Dict] = None,
        ultima_visita: str = None
    ) -> str:
        """
        Formatea el bloque <DATA> con información estructurada.
        
        Args:
            paciente_registrado: Si el paciente está en la BD
            nombre: Nombre del paciente o None
            citas: Lista de citas [{fecha, hora, estado}] o None/[]
            ultima_visita: Fecha de última visita o None
        
        Returns:
            String formateado para <DATA>
        """
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
        """
        Crea el prompt completo con sistema, datos y mensaje.
        
        Args:
            data_block: Bloque <DATA> formateado
            user_message: Mensaje del usuario
        
        Returns:
            Prompt completo
        """
        return f"""<SYS>
{self.system_prompt}
</SYS>

<DATA>
{data_block}
</DATA>

<USER>: {user_message}
<ASSISTANT>:"""
    
    def generate_greetings_with_patient_data(self):
        """
        Genera ejemplos de saludos con datos reales del paciente.
        Entrena al modelo a usar el nombre de <DATA>.
        """
        print("📝 Generando saludos con datos de pacientes...")
        
        for nombre in self.nombres[:8]:  # 8 ejemplos
            # Caso 1: Paciente registrado SIN citas
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, "Hola")
            completion = f" ¡Hola {nombre.split()[0]}! ¿Cómo te sientes hoy? Veo que no tienes citas programadas."
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
            
            # Caso 2: Paciente registrado CON cita
            fecha_futura = (datetime.now() + timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d")
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[{"fecha": fecha_futura, "hora": "10:00", "estado": "Programado"}],
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, "Buenos días")
            completion = f" ¡Buenos días {nombre.split()[0]}! Te recuerdo que tienes cita el {fecha_futura} a las 10:00."
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
        
        print(f"✅ {len(self.dataset)} ejemplos de saludos generados")
    
    def generate_appointment_queries_with_data(self):
        """
        Genera preguntas sobre citas CON datos estructurados.
        Entrena al modelo a leer de <DATA> en vez de inventar.
        """
        print("📝 Generando consultas de citas con datos...")
        
        for nombre in self.nombres[:6]:
            # Caso 1: Tiene cita - debe leer de <DATA>
            fecha_cita = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[{"fecha": fecha_cita, "hora": "14:00", "estado": "Programado"}],
                ultima_visita="2025-10-10"
            )
            
            prompt = self._create_prompt(data_block, "¿Cuándo es mi próxima cita?")
            completion = f" Tu próxima cita es el {fecha_cita} a las 14:00, {nombre.split()[0]}."
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
            
            # Caso 2: NO tiene citas - debe decir "No tengo..."
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita="2025-09-15"
            )
            
            prompt = self._create_prompt(data_block, "¿Tengo citas programadas?")
            completion = f" No tienes citas programadas actualmente, {nombre.split()[0]}. ¿Deseas agendar una?"
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
        
        print(f"✅ {len(self.dataset)} ejemplos totales")
    
    def generate_unregistered_patient_examples(self):
        """
        Genera ejemplos de pacientes NO REGISTRADOS.
        Entrena al modelo a NO inventar información cuando no hay datos.
        """
        print("📝 Generando ejemplos de pacientes no registrados...")
        
        preguntas = [
            "¿Cuándo es mi cita?",
            "¿Tengo citas programadas?",
            "Hola, ¿cómo están mis resultados?",
            "¿Cuál es mi tratamiento actual?",
            "¿Puedo ver mi historial?"
        ]
        
        for pregunta in preguntas:
            data_block = self._format_data_block(
                paciente_registrado=False,
                nombre=None,
                citas=None,
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = " No encuentro tu información en el sistema. ¿Podrías darme tu nombre completo o número de documento?"
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
        
        print(f"✅ {len(self.dataset)} ejemplos totales")
    
    def generate_out_of_context_examples(self):
        """
        Genera ejemplos de preguntas FUERA DE CONTEXTO.
        Entrena al modelo a rechazar temas no relacionados con tuberculosis.
        """
        print("📝 Generando ejemplos fuera de contexto...")
        
        preguntas_fuera = [
            "¿Qué es la hipotenusa?",
            "¿Cuánto cuesta una consulta de odontología?",
            "¿Atienden partos aquí?",
            "¿Tienen vacunas para niños?",
            "¿Dónde puedo sacar turno para traumatología?"
        ]
        
        for pregunta in preguntas_fuera:
            # Con paciente registrado
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre="Juan Pérez",
                citas=[],
                ultima_visita=None
            )
            
            prompt = self._create_prompt(data_block, pregunta)
            completion = " Lo siento, solo atiendo consultas sobre Tuberculosis. Para otros servicios, contacta al centro al +591-75561400."
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
        
        print(f"✅ {len(self.dataset)} ejemplos totales")
    
    def generate_appointment_scheduling_examples(self):
        """
        Genera ejemplos de agendamiento de citas.
        """
        print("📝 Generando ejemplos de agendamiento...")
        
        for nombre in self.nombres[:5]:
            data_block = self._format_data_block(
                paciente_registrado=True,
                nombre=nombre,
                citas=[],
                ultima_visita="2025-09-20"
            )
            
            prompt = self._create_prompt(data_block, "Quiero agendar una cita")
            completion = f" Perfecto {nombre.split()[0]}, para agendar tu cita necesito que el personal médico se contacte contigo. ¿Confirmas tu número de teléfono?"
            
            self.dataset.append({
                "prompt": prompt,
                "completion": completion
            })
        
        print(f"✅ {len(self.dataset)} ejemplos totales")
    
    def generate_symptoms_reporting_examples(self):
        """
        Genera ejemplos de reporte de síntomas.
        """
        print("📝 Generando ejemplos de síntomas...")
        
        sintomas = [
            ("Tengo tos con flema hace 3 semanas", "Es importante evaluarte pronto. ¿Deseas una cita urgente?"),
            ("Tengo fiebre y sudores nocturnos", "Estos síntomas requieren atención. Enseguida un profesional se contactará contigo."),
            ("He perdido peso sin razón", "La pérdida de peso debe evaluarse. ¿Deseas agendar una consulta?")
        ]
        
        for sintoma, respuesta in sintomas:
            for nombre in self.nombres[:3]:
                data_block = self._format_data_block(
                    paciente_registrado=True,
                    nombre=nombre,
                    citas=[],
                    ultima_visita="2025-10-01"
                )
                
                prompt = self._create_prompt(data_block, sintoma)
                completion = f" {respuesta}"
                
                self.dataset.append({
                    "prompt": prompt,
                    "completion": completion
                })
        
        print(f"✅ {len(self.dataset)} ejemplos totales")
    
    def generate_complete_dataset(self, output_path: str = None):
        """
        Genera el dataset completo estructurado.
        
        Args:
            output_path: Ruta donde guardar el dataset
        """
        print("=" * 80)
        print("🚀 GENERANDO DATASET ESTRUCTURADO")
        print("=" * 80)
        
        # Generar todos los tipos de ejemplos
        self.generate_greetings_with_patient_data()
        self.generate_appointment_queries_with_data()
        self.generate_unregistered_patient_examples()
        self.generate_out_of_context_examples()
        self.generate_appointment_scheduling_examples()
        self.generate_symptoms_reporting_examples()
        
        # Mezclar dataset
        random.shuffle(self.dataset)
        
        print("=" * 80)
        print(f"✅ DATASET GENERADO: {len(self.dataset)} ejemplos")
        print("=" * 80)
        
        # Guardar
        if output_path is None:
            output_path = "app/training/datasets/tuberculosis_structured.json"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Dataset guardado en: {output_file}")
        
        # Estadísticas
        print("\n📊 ESTADÍSTICAS DEL DATASET:")
        print(f"   - Total ejemplos: {len(self.dataset)}")
        print(f"   - Promedio de tokens por ejemplo: ~{sum(len(ex['prompt']) + len(ex['completion']) for ex in self.dataset) / len(self.dataset) / 4:.0f}")
        
        # Mostrar ejemplos
        print("\n📝 EJEMPLOS DEL DATASET:")
        print("=" * 80)
        for i, ejemplo in enumerate(self.dataset[:3]):
            print(f"\nEJEMPLO {i+1}:")
            print(f"PROMPT:\n{ejemplo['prompt'][:300]}...")
            print(f"\nCOMPLETION:\n{ejemplo['completion']}")
            print("-" * 80)
        
        return output_file


def main():
    """
    Genera el dataset estructurado.
    """
    generator = StructuredDatasetGenerator()
    output_path = generator.generate_complete_dataset()
    
    print("\n" + "=" * 80)
    print("🎉 DATASET ESTRUCTURADO CREADO EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📁 Archivo: {output_path}")
    print("\n📝 PRÓXIMOS PASOS:")
    print("   1. Revisa el dataset generado")
    print("   2. Ejecuta: python app/training/train_gpt2_structured.py")
    print("   3. Actualiza MODEL_NAME en .env al nuevo modelo entrenado")
    print("=" * 80)


if __name__ == "__main__":
    main()
