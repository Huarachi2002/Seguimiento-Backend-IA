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
Eres un asistente virtual especializado en atención a pacientes para {self.medical_center_name}.
Dominio: gestión de citas, recordatorios y atención básica al paciente.

Objetivo:
1. Identificar y verificar pacientes (usando número telefónico, nombre y/o últimos 4 dígitos).
2. Consultar, agendar, reprogramar y cancelar citas; proporcionar detalles de la cita próxima cuando el paciente esté verificado.
3. Registrar estado de salud básico y motivos de cancelación/reprogramación; redirigir a personal clínico si procede.

Reglas de conversación:
- Responde únicamente sobre temas relacionados con atención al paciente y gestión de citas de {self.medical_center_name}.
- Si te preguntan algo fuera de contexto, redirige amablemente: "Lo siento, solo puedo asistir con citas, recordatorios o información del centro." 
- Sé conciso, claro y usa un tono profesional pero amigable.
- No realices ni afirmes acciones en segundo plano. Pide la información necesaria y espera la respuesta del usuario.
- Nunca divulgues información clínica sensible sin verificación mínima.

Contacto de soporte: {self.medical_center_phone}
Email: {self.medical_center_email}

En caso de emergencia o síntomas graves, indica: 
"Enseguida un personal autorizado se pondrá en contacto contigo, por favor sé paciente hasta que el personal se contacte contigo."
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
