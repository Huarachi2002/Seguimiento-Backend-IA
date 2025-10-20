"""
Configuration Module
====================

Este módulo maneja toda la configuración de la aplicación usando Pydantic Settings.
Las configuraciones se cargan desde variables de entorno (.env file).

Ventajas de usar Pydantic Settings:
- Validación automática de tipos
- Valores por defecto
- Documentación clara
- Fácil testing (puedes sobrescribir valores)
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List


class Settings(BaseSettings):
    """
    Clase de configuración principal.
    
    Pydantic automáticamente:
    1. Lee las variables de entorno
    2. Valida los tipos
    3. Aplica valores por defecto si no existen
    
    El decorador @lru_cache en get_settings() asegura que solo se cree
    una instancia (patrón Singleton).
    """
    
    # ===== Configuración de la Aplicación =====
    app_name: str = "WhatsApp AI Assistant"
    app_version: str = "1.0.0"
    environment: str = "development"  # development, staging, production
    log_level: str = "INFO"
    port: int = 8000
    
    # ===== Configuración del Modelo de IA =====
    model_name: str = "microsoft/DialoGPT-medium"
    device: str = "cpu"  # cpu, cuda, mps
    model_cache_dir: str = "./models"
    
    # ===== Configuración de Base de Datos =====
    database_url: str = "postgresql://postgres:hiachi20@localhost:5432/seguimiento_db"
    
    # ===== Configuración de Redis =====
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None
    session_expire_time: int = 3600  # 1 hora
    
    # ===== Configuración de Seguimiento Backend =====
    seguimiento_service_url: str = "http://localhost:3001"
    seguimiento_timeout: int = 10  # segundos
    
    # ===== Configuración de N8N =====
    n8n_webhook_url: str = "http://localhost:5678/webhook/whatsapp-response"
    n8n_api_key: str | None = None
    
    # ===== Configuración de CORS =====
    cors_origins: str = "http://localhost:3000,http://localhost:5678"
    cors_allow_credentials: bool = True
    
    # ===== Configuración de Seguridad =====
    secret_key: str = "change-this-secret-key-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # ===== Configuración del Centro Médico =====
    medical_center_name: str = "CAÑADA DEL CARMEN"
    medical_center_phone: str = "+591-xxx-xxxx"
    medical_center_email: str = "contacto@canadadelcarmen.com"
    
    # ===== Límites y Cuotas =====
    max_tokens: int = 150
    temperature: float = 0.7
    max_conversation_history: int = 10
    rate_limit_per_minute: int = 20
    
    # Configuración del modelo de Pydantic Settings
    model_config = SettingsConfigDict(
        # Archivo .env a cargar
        env_file=".env",
        # Codificación del archivo
        env_file_encoding="utf-8",
        # Permite caracteres extra en el .env que no estén definidos aquí
        extra="ignore",
        # Case sensitive para las variables de entorno
        case_sensitive=False
    )
    
    @property
    def cors_origins_list(self) -> List[str]:
        """
        Convierte el string de orígenes CORS en una lista.
        
        Returns:
            Lista de URLs permitidas para CORS
        """
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    @property
    def is_development(self) -> bool:
        """Verifica si estamos en modo desarrollo"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Verifica si estamos en modo producción"""
        return self.environment.lower() == "production"
    
    def get_system_context(self) -> str:
        """
        Retorna el contexto del sistema con los valores reales del centro médico.
        Esto reemplaza los placeholders con la configuración real.
        """
        return f"""
Eres un asistente virtual del servicio de TUBERCULOSIS del centro de salud {self.medical_center_name}.

IMPORTANTE: Solo atiendes casos de TUBERCULOSIS. No hay otros servicios disponibles.

TUS FUNCIONES:
1. Verificar identidad del paciente (por número telefónico o nombre completo)
2. Consultar estado de salud actual del paciente
3. Agendar citas para control de tuberculosis
4. Recordar citas próximas
5. Consultar motivos de inasistencia

FLUJO DE CONVERSACIÓN:

A) Si el PACIENTE inicia la conversación:
   1. Saludar y verificar identidad (nombre completo o número)
   2. Preguntar: "¿Cómo te sientes hoy?" o "¿Cómo ha estado tu salud?"
   3. Si menciona síntomas, preguntar detalles específicos
   4. Preguntar: "¿Deseas agendar una cita para control?"
   5. Si dice sí, preguntar: "¿Qué día y horario prefieres?"
   6. Confirmar la cita con fecha y hora

B) Si TÚ inicias la conversación (RECORDATORIO):
   1. Saludar: "Hola [nombre], te recordamos tu cita de tuberculosis"
   2. Indicar: "Tienes cita el [fecha] a las [hora]"
   3. Preguntar: "¿Podrás asistir?"
   4. Si dice NO: "¿Cuál es el motivo por el que no podrás asistir?"
   5. Esperar respuesta y registrar motivo

C) Si el paciente NO RESPONDIÓ al recordatorio:
   1. Mensaje directo: "Hola [nombre], notamos que no asististe a tu cita del [fecha]"
   2. Preguntar: "¿Cuál fue el motivo de tu inasistencia?"
   3. Esperar respuesta del paciente

REGLAS ESTRICTAS:
- SOLO habla de tuberculosis y control de salud
- Si preguntan por otros servicios, responde: "Solo atiendo el servicio de tuberculosis. Para otros servicios, contacta al {self.medical_center_phone}"
- Respuestas de MÁXIMO 2 oraciones
- Tono amigable pero profesional
- NO inventes información
- Si no sabes algo, deriva: "Déjame verificar con el personal médico"

EJEMPLOS:

Usuario: "Hola"
Tú: "¡Hola! Soy el asistente del servicio de tuberculosis de {self.medical_center_name}. ¿Cuál es tu nombre?"

Usuario: "Juan Pérez"
Tú: "Gracias, Juan. ¿Cómo te has sentido últimamente?"

Usuario: "Tengo tos"
Tú: "¿Hace cuánto tiempo tienes tos? ¿Has tenido fiebre?"

Usuario: "2 días, sin fiebre"
Tú: "Entiendo. ¿Deseas agendar una cita para control?"

Usuario: "Sí"
Tú: "Perfecto. ¿Qué día y horario prefieres para tu cita?"

Usuario: "Quiero cancelar mi cita"
Tú: "Entiendo que necesitas cancelar. ¿Cuál es el motivo?"

Usuario: "No puedo ir mañana"
Tú: "Comprendo. ¿Deseas reprogramar para otra fecha?"

EMERGENCIAS:
Si mencionan: sangre al toser, dificultad para respirar, fiebre alta (>38.5°C):
"Esto requiere atención urgente. Por favor contacta al {self.medical_center_phone} o acude al centro de inmediato."

Contacto: {self.medical_center_phone}
Email: {self.medical_center_email}
"""


@lru_cache()
def get_settings() -> Settings:
    """
    Función para obtener la configuración de la aplicación.
    
    El decorador @lru_cache() asegura que solo se cree una instancia
    de Settings (patrón Singleton). Esto es importante porque:
    - Mejora el rendimiento (no se lee el .env múltiples veces)
    - Asegura consistencia (todos usan la misma configuración)
    - Facilita el testing (puedes limpiar el caché y crear nuevas instancias)
    
    Returns:
        Instancia única de Settings
    """
    return Settings()


# Instancia global de configuración para importar fácilmente
settings = get_settings()
