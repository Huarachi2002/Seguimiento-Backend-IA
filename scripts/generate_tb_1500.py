# -*- coding: utf-8 -*-
"""
Genera exactamente 1500 ejemplos (prompt/completion) para el asistente
EXCLUSIVO del servicio de Tuberculosis del centro de salud CAÑADA DEL CARMEN.

Distribución por categoría (suma = 1500):
- saludos_no_registrado:            150
- saludos_registrado_sin_cita:      150
- saludos_registrado_con_cita:      150
- recordatorios_asistente:          200
- respuesta_recordatorio_si:        100
- respuesta_recordatorio_no:        100
- cancelaciones:                    150
- reprogramaciones:                 150
- consultas_cita_paciente:          150
- estado_salud_leve:                120
- emergencias:                       60
- fuera_contexto:                   120
- seguimiento_inasistencia:         100
- verificacion_identidad:           100
Total:                              1500
"""
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

CENTER = "CAÑADA DEL CARMEN"
HEADER = f"Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis del centro de salud {CENTER}."
IMPORTANT = "IMPORTANTE: Solo atiendes casos de TUBERCULOSIS."
LINE_BREAK = "\n"

random.seed(42)

NOMBRES = [
    "Juan Pérez", "María González", "Carlos López", "Ana Martínez", "Pedro Rodríguez",
    "Laura Fernández", "Diego Silva", "Sofía Ramírez", "Roberto Torres", "Carmen Vargas",
    "Luis Morales", "Patricia Castro", "Fernando Ruiz", "Isabel Ortiz", "Miguel Herrera",
    "Rosa Jiménez", "Javier Romero", "Valeria Mendoza", "Andrés Navarro", "Carolina Aguilar",
    "Héctor Salazar", "Paola Rojas", "Matías Fuentes", "Camila Soto", "Brenda Paredes",
    "Oscar Cabrera", "Elena Villalba", "Ricardo Guzmán", "Natalia Domínguez", "Sergio Espinoza"
]

SALUDOS = [
    "Hola", "Buenos días", "Buenas tardes", "Hola, buenas", "Buen día", "Qué tal",
    "Saludos", "Hola, quisiera información", "Buenas noches", "Hola, necesito ayuda"
]

HORAS = ["08:00", "09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"]
TURNOS = ["mañana", "tarde"]
DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado"]
PREGUNTAS_FUERA = [
    "¿Atienden odontología?", "Necesito pediatra", "¿Tienen medicina general?",
    "Quiero ver al cardiólogo", "¿Hacen análisis de sangre?", "¿Dónde está el banco?",
    "¿Cuál es el clima?", "¿Tienen ginecología?", "Necesito traumatólogo", "¿Atienden dermatología?"
]
MOTIVOS_CANCEL = [
    "Tengo trabajo", "Me salió un viaje", "Problemas familiares", "No me siento bien",
    "Olvidé la cita", "Tengo otra cita médica", "Compromiso laboral",
    "No tengo transporte", "Emergencia familiar", "Me confundí de fecha"
]
SINTOMAS_LEVES = [
    "Tengo un poco de tos", "Me siento cansado", "Tengo tos seca",
    "Poca fiebre", "Me duele un poco el pecho", "Sudoración nocturna",
    "Tengo apetito reducido", "Bajé de peso levemente"
]
SINTOMAS_GRAVES = [
    "Toso sangre", "Mucho dolor en el pecho", "No puedo respirar bien",
    "Fiebre muy alta", "Sangre al toser", "Dificultad severa para respirar"
]

COUNTS = {
    "saludos_no_registrado": 150,
    "saludos_registrado_sin_cita": 150,
    "saludos_registrado_con_cita": 150,
    "recordatorios_asistente": 200,
    "respuesta_recordatorio_si": 100,
    "respuesta_recordatorio_no": 100,
    "cancelaciones": 150,
    "reprogramaciones": 150,
    "consultas_cita_paciente": 150,
    "estado_salud_leve": 120,
    "emergencias": 60,
    "fuera_contexto": 120,
    "seguimiento_inasistencia": 100,
    "verificacion_identidad": 100,
}

def fecha_relativa_o_formato():
    r = random.random()
    if r < 0.3:
        return "mañana"
    elif r < 0.45:
        return "pasado mañana"
    else:
        d = datetime.now() + timedelta(days=random.randint(2, 20))
        return d.strftime("%d/%m/%Y")

def hora_aleatoria():
    return random.choice(HORAS)

def nombre_simple(nombre_completo: str) -> str:
    return nombre_completo.split()[0]

def ultimos_4():
    return f"{random.randint(0, 9999):04d}"

def header_base():
    return f"{HEADER}\n\n{IMPORTANT}\n\n"

def make_prompt_registrado(nombre: str, proxima_cita: str | None = None):
    base = header_base()
    base += f"Paciente REGISTRADO: {nombre}\n"
    if proxima_cita:
        base += f"Próxima cita: {proxima_cita}\n\n"
    else:
        base += "\n"
    return base

def make_prompt_no_reg():
    return f"{HEADER}\n\n{IMPORTANT}\n\nPaciente NO REGISTRADO\n\n"

def build_item(prompt: str, completion: str):
    # Asegurar espacio inicial en completion (según tu formato de ejemplo)
    comp = completion if completion.startswith(" ") else f" {completion}"
    return {"prompt": prompt, "completion": comp}

def gen_saludos_no_registrado(n):
    out = []
    for _ in range(n):
        saludo = random.choice(SALUDOS)
        p = make_prompt_no_reg() + f"Paciente: {saludo}\nAsistente:"
        c = f"¡{saludo if saludo.startswith('Hola') else 'Hola'}! Bienvenido al servicio de Tuberculosis de {CENTER}. Para poder asistirte, ¿podrías darme tu nombre completo?"
        out.append(build_item(p, c))
    return out

def gen_saludos_registrado_sin_cita(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        saludo = random.choice(SALUDOS)
        p = make_prompt_registrado(nombre, proxima_cita=None) + f"Paciente: {saludo}\nAsistente:"
        c = f"¡Hola {nombre_simple(nombre)}! ¿Cómo te sientes hoy? Veo que no tienes citas programadas. ¿Deseas agendar una consulta para el control de tuberculosis?"
        out.append(build_item(p, c))
    return out

def gen_saludos_registrado_con_cita(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha = fecha_relativa_o_formato()
        hora = hora_aleatoria()
        saludo = random.choice(SALUDOS)
        proxima = f"{fecha} a las {hora}"
        p = make_prompt_registrado(nombre, proxima) + f"Paciente: {saludo}\nAsistente:"
        c = f"¡Hola {nombre_simple(nombre)}! ¿Cómo te sientes hoy? Te recuerdo que tienes cita el {fecha} a las {hora}."
        out.append(build_item(p, c))
    return out

def gen_recordatorios_asistente(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha = fecha_relativa_o_formato()
        hora = hora_aleatoria()
        base = make_prompt_registrado(nombre, f"{fecha} a las {hora}")
        p = base + "Asistente inicia recordatorio de cita.\nAsistente:"
        c = f"Hola {nombre_simple(nombre)}, te recordamos que tienes cita para control de tuberculosis el {fecha} a las {hora}. ¿Podrás asistir?"
        out.append(build_item(p, c))
    return out

def gen_respuesta_recordatorio_si(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha = fecha_relativa_o_formato()
        hora = hora_aleatoria()
        p = f"{HEADER}\n\n{IMPORTANT}\n\nAsistente: Hola {nombre_simple(nombre)}, te recordamos que tienes cita el {fecha} a las {hora}. ¿Podrás asistir?\nPaciente: Sí, ahí estaré\nAsistente:"
        c = f"¡Perfecto {nombre_simple(nombre)}! Te esperamos el {fecha} a las {hora}. Recuerda traer tu documento de identidad y tu tarjeta de control."
        out.append(build_item(p, c))
    return out

def gen_respuesta_recordatorio_no(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha = fecha_relativa_o_formato()
        hora = hora_aleatoria()
        p = f"{HEADER}\n\n{IMPORTANT}\n\nAsistente: Hola {nombre_simple(nombre)}, te recordamos que tienes cita el {fecha} a las {hora}. ¿Podrás asistir?\nPaciente: No podré ir\nAsistente:"
        c = f"Entiendo {nombre_simple(nombre)}. ¿Cuál es el motivo por el que no podrás asistir?"
        out.append(build_item(p, c))
    return out

def gen_cancelaciones(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        p = make_prompt_registrado(nombre) + "Paciente: Quiero cancelar mi cita\nAsistente:"
        c = f"Entiendo {nombre_simple(nombre)}. Para registrar la cancelación, ¿podrías decirme cuál es el motivo?"
        out.append(build_item(p, c))

        # Registrar motivo inmediatamente después (par vinculado)
        motivo = random.choice(MOTIVOS_CANCEL)
        p2 = f"{HEADER}\n\n{IMPORTANT}\n\nAsistente: ¿Cuál es el motivo?\nPaciente: {motivo}\nAsistente:"
        c2 = f"He registrado el motivo: {motivo.lower()}. ¿Deseas reprogramar tu cita para otra fecha?"
        out.append(build_item(p2, c2))
    # Ajustar si duplicamos entradas por pares (mantenemos n ejemplos, no pares) => recortar a n
    return out[:n]

def gen_reprogramaciones(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        p = make_prompt_registrado(nombre) + "Paciente: Quiero reprogramar mi cita\nAsistente:"
        c = "Con gusto. ¿Para qué día prefieres tu nueva cita? ¿Te viene mejor en la mañana (09:00-11:00) o en la tarde (14:00-17:00)?"
        out.append(build_item(p, c))

        dia = random.choice(DIAS_SEMANA)
        turno = random.choice(TURNOS)
        p2 = f"{HEADER}\n\n{IMPORTANT}\n\nAsistente: ¿Para qué día prefieres tu nueva cita?\nPaciente: El " + dia + f"\nAsistente:"
        c2 = f"Perfecto, el {dia}. ¿En qué horario te viene mejor: {('mañana (09:00-11:00)' if turno=='mañana' else 'tarde (14:00-17:00)')}?"
        out.append(build_item(p2, c2))

        p3 = f"{HEADER}\n\n{IMPORTANT}\n\nAsistente: ¿En qué horario te viene mejor?\nPaciente: En la {turno}\nAsistente:"
        c3 = f"Excelente. He reprogramado tu cita para el {dia} en la {turno}. Recibirás un recordatorio por WhatsApp."
        out.append(build_item(p3, c3))
    return out[:n]

def gen_consultas_cita_paciente(n):
    out = []
    variantes = [
        "¿Cuándo es mi próxima cita?", "¿Para cuándo tengo cita?", "¿Cuándo me toca?",
        "¿Qué día es mi cita?", "¿A qué hora tengo cita?", "Quiero ver mi cita",
        "Consultar mi cita", "Ver mi cita programada", "Detalles de mi cita"
    ]
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha = fecha_relativa_o_formato()
        hora = hora_aleatoria()
        pregunta = random.choice(variantes)
        # a veces con cita, a veces sin cita
        if random.random() < 0.65:
            p = make_prompt_registrado(nombre, f"{fecha} a las {hora}") + f"Paciente: {pregunta}\nAsistente:"
            c = f"Hola {nombre_simple(nombre)}, tu próxima cita para tuberculosis es el {fecha} a las {hora}. ¿Necesitas algo más?"
        else:
            p = make_prompt_registrado(nombre, None) + f"Paciente: {pregunta}\nAsistente:"
            c = f"Hola {nombre_simple(nombre)}, actualmente no tienes citas programadas para tuberculosis. ¿Deseas agendar una?"
        out.append(build_item(p, c))
    return out

def gen_estado_salud_leve(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        sint = random.choice(SINTOMAS_LEVES)
        p = make_prompt_registrado(nombre) + f"Paciente: {sint}\nAsistente:"
        c = f"Entiendo {nombre_simple(nombre)}. Es importante que el personal médico te evalúe. ¿Deseas agendar una cita para control de tuberculosis?"
        out.append(build_item(p, c))
    return out

def gen_emergencias(n):
    out = []
    for _ in range(n):
        sint = random.choice(SINTOMAS_GRAVES)
        p = f"{HEADER}\n\n{IMPORTANT}\n\nPaciente: {sint}\nAsistente:"
        c = "⚠️ Enseguida un personal autorizado se pondrá en contacto contigo, por favor sé paciente hasta que el personal se contacte contigo."
        out.append(build_item(p, c))
    return out

def gen_fuera_contexto(n):
    out = []
    for _ in range(n):
        pregunta = random.choice(PREGUNTAS_FUERA)
        p = f"{HEADER}\n\n{IMPORTANT}\n\nPaciente: {pregunta}\nAsistente:"
        c = f"Lo siento, solo atiendo el servicio de Tuberculosis de {CENTER}. Para otros servicios médicos, por favor contacta directamente al centro de salud."
        out.append(build_item(p, c))
    return out

def gen_seguimiento_inasistencia(n):
    out = []
    for _ in range(n):
        nombre = random.choice(NOMBRES)
        fecha_pasada = (datetime.now() - timedelta(days=random.randint(1, 7))).strftime("%d/%m/%Y")
        p = f"{HEADER}\n\n{IMPORTANT}\n\nPaciente REGISTRADO: {nombre}\nCita pasada: {fecha_pasada} - NO ASISTIÓ\n\nAsistente inicia seguimiento.\nAsistente:"
        c = f"Hola {nombre_simple(nombre)}, notamos que no asististe a tu cita del {fecha_pasada}. ¿Cuál fue el motivo?"
        out.append(build_item(p, c))
    return out

def gen_verificacion_identidad(n):
    out = []
    variantes = [
        ("Quiero ver mi cita", "Claro, con gusto te ayudo. Para verificar tu identidad, ¿podrías proporcionarme tu nombre completo?"),
        ("Necesito consultar mi cita", "Perfecto. Primero necesito verificar tu identidad. ¿Cuál es tu nombre completo?"),
        ("¿Puedo ver mis citas?", "Sí, claro. Para acceder a tu información, ¿me das tu nombre completo?"),
        ("No recuerdo mi cita", "No te preocupes, te ayudo a consultarla. Para verificar tu identidad, ¿podrías darme tu nombre completo?")
    ]
    for _ in range(n):
        user_txt, resp = random.choice(variantes)
        p = make_prompt_no_reg() + f"Paciente: {user_txt}\nAsistente:"
        c = resp
        out.append(build_item(p, c))
        # paso de últimos 4 dígitos
        nombre = random.choice(NOMBRES)
        p2 = f"{HEADER}\n\n{IMPORTANT}\n\nPaciente: {nombre}\nAsistente:"
        c2 = "Gracias. ¿Podrías confirmar los últimos 4 dígitos de tu documento de identidad?"
        out.append(build_item(p2, c2))
        p3 = f"{HEADER}\n\n{IMPORTANT}\n\nPaciente: " + ultimos_4() + "\nAsistente:"
        c3 = "Perfecto, identidad verificada. ¿Qué información necesitas sobre tu cita de tuberculosis?"
        out.append(build_item(p3, c3))
    return out[:n]

def main():
    data = []
    data += gen_saludos_no_registrado(COUNTS["saludos_no_registrado"])
    data += gen_saludos_registrado_sin_cita(COUNTS["saludos_registrado_sin_cita"])
    data += gen_saludos_registrado_con_cita(COUNTS["saludos_registrado_con_cita"])
    data += gen_recordatorios_asistente(COUNTS["recordatorios_asistente"])
    data += gen_respuesta_recordatorio_si(COUNTS["respuesta_recordatorio_si"])
    data += gen_respuesta_recordatorio_no(COUNTS["respuesta_recordatorio_no"])
    data += gen_cancelaciones(COUNTS["cancelaciones"])
    data += gen_reprogramaciones(COUNTS["reprogramaciones"])
    data += gen_consultas_cita_paciente(COUNTS["consultas_cita_paciente"])
    data += gen_estado_salud_leve(COUNTS["estado_salud_leve"])
    data += gen_emergencias(COUNTS["emergencias"])
    data += gen_fuera_contexto(COUNTS["fuera_contexto"])
    data += gen_seguimiento_inasistencia(COUNTS["seguimiento_inasistencia"])
    data += gen_verificacion_identidad(COUNTS["verificacion_identidad"])

    # Ajuste final: asegurar 1500 exactos
    if len(data) > 1500:
        data = data[:1500]
    elif len(data) < 1500:
        # Rellenar con saludos_no_registrado hasta completar 1500
        faltan = 1500 - len(data)
        data += gen_saludos_no_registrado(faltan)

    # out_path = Path(__file__).resolve().parents[1] / "datasets" / "tuberculosis_1500.json"
    # out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path = Path(__file__).resolve().parent / "app" / "training" / "datasets" / "tuberculosis_1500.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"✅ Dataset generado: {out_path} ({len(data)} ejemplos)")

if __name__ == "__main__":
    main()