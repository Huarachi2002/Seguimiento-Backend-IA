"""
Logging Configuration Module
=============================

Este módulo configura el sistema de logging de la aplicación.

Por qué es importante un buen sistema de logging:
1. Debugging: Ayuda a encontrar errores en producción
2. Auditoría: Registro de acciones importantes
3. Monitoreo: Detectar problemas antes que los usuarios
4. Análisis: Entender patrones de uso

Niveles de log:
- DEBUG: Información detallada para diagnóstico
- INFO: Confirmación de que las cosas funcionan como se espera
- WARNING: Algo inesperado ocurrió, pero la app sigue funcionando
- ERROR: Error serio, alguna funcionalidad no funcionó
- CRITICAL: Error muy grave, la aplicación podría detenerse
"""

import logging
import sys
from pathlib import Path
from typing import Any
from logging.handlers import RotatingFileHandler
from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """
    Formatter personalizado que añade colores a los logs en consola.
    Esto hace que sea más fácil identificar errores rápidamente.
    """
    
    # Códigos ANSI para colores
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea el log con colores"""
        log_color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging() -> None:
    """
    Configura el sistema de logging de la aplicación.
    
    Esta función:
    1. Crea un logger raíz
    2. Configura handlers para consola y archivo
    3. Aplica el formato y nivel de log apropiado
    
    Los logs se guardan en:
    - Consola: Para desarrollo (con colores)
    - Archivo: Para producción (con rotación)
    """
    
    # Crear directorio de logs si no existe
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Obtener el logger raíz
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Limpiar handlers existentes (evita duplicados)
    logger.handlers.clear()
    
    # ===== Handler para CONSOLA =====
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.is_development else logging.INFO)
    
    # Formato para desarrollo (más detallado)
    if settings.is_development:
        console_format = ColoredFormatter(
            fmt='%(levelname)s | %(asctime)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        # Formato para producción (más compacto)
        console_format = logging.Formatter(
            fmt='%(levelname)s | %(asctime)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # ===== Handler para ARCHIVO =====
    # RotatingFileHandler: Crea nuevos archivos cuando el actual llega al límite
    # Esto evita que los logs crezcan indefinidamente
    file_handler = RotatingFileHandler(
        filename=log_dir / f"{settings.app_name.lower().replace(' ', '_')}.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,  # Mantiene 5 archivos históricos
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Formato para archivo (incluye más detalles)
    file_format = logging.Formatter(
        fmt='%(levelname)s | %(asctime)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)
    
    # Reducir verbosidad de librerías externas
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    
    logger.info(f"✅ Logging configurado - Nivel: {settings.log_level} - Entorno: {settings.environment}")


def get_logger(name: str) -> logging.Logger:
    """
    Obtiene un logger con el nombre especificado.
    
    Buena práctica: Usa __name__ del módulo para identificar de dónde vienen los logs.
    Ejemplo: logger = get_logger(__name__)
    
    Args:
        name: Nombre del logger (usualmente __name__ del módulo)
    
    Returns:
        Logger configurado
    """
    return logging.getLogger(name)
