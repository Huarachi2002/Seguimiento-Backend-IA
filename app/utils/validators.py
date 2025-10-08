# ========================================
# Utilidades y Validadores
# ========================================
"""
Utils Module

Funciones de utilidad compartidas en toda la aplicación.
"""

import re
from typing import Optional
from datetime import datetime


def validate_phone_number(phone: str) -> bool:
    """
    Valida formato de número telefónico.
    
    Acepta formatos:
    - +59170123456
    - 59170123456
    - 70123456
    
    Args:
        phone: Número de teléfono
    
    Returns:
        True si es válido
    """
    # Remover espacios y caracteres especiales
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Debe tener entre 8 y 15 dígitos
    if len(cleaned) < 8 or len(cleaned) > 15:
        return False
    
    # Si empieza con +, debe tener al menos 10 dígitos totales
    if cleaned.startswith('+') and len(cleaned) < 10:
        return False
    
    return True


def format_phone_number(phone: str) -> str:
    """
    Normaliza un número telefónico al formato estándar.
    
    Args:
        phone: Número de teléfono
    
    Returns:
        Número normalizado (ej: +59170123456)
    """
    # Remover todo excepto dígitos y +
    cleaned = re.sub(r'[^\d+]', '', phone)
    
    # Si no tiene +, añadirlo (asumiendo Bolivia +591)
    if not cleaned.startswith('+'):
        # Si empieza con 591, solo añadir +
        if cleaned.startswith('591'):
            cleaned = '+' + cleaned
        # Si es número local, añadir código de país
        elif len(cleaned) == 8:
            cleaned = '+591' + cleaned
        else:
            cleaned = '+' + cleaned
    
    return cleaned


def extract_last_four_digits(phone: str) -> str:
    """
    Extrae los últimos 4 dígitos de un número telefónico.
    
    Útil para verificación de identidad.
    
    Args:
        phone: Número de teléfono
    
    Returns:
        Últimos 4 dígitos
    """
    digits = re.sub(r'\D', '', phone)  # Solo dígitos
    return digits[-4:] if len(digits) >= 4 else digits


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto a una longitud máxima.
    
    Args:
        text: Texto a truncar
        max_length: Longitud máxima
        suffix: Sufijo a añadir si se trunca
    
    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def parse_datetime_flexible(date_str: str) -> Optional[datetime]:
    """
    Intenta parsear una fecha de múltiples formatos.
    
    Soporta:
    - ISO: 2025-10-04T10:30:00
    - Simple: 2025-10-04 10:30
    - Solo fecha: 2025-10-04
    
    Args:
        date_str: String de fecha
    
    Returns:
        datetime object o None si falla
    """
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    
    return None


def sanitize_input(text: str) -> str:
    """
    Sanitiza input del usuario removiendo caracteres peligrosos.
    
    Args:
        text: Texto a sanitizar
    
    Returns:
        Texto limpio
    """
    # Remover null bytes
    text = text.replace('\x00', '')
    
    # Limitar longitud
    text = text[:2000]
    
    # Remover múltiples espacios
    text = ' '.join(text.split())
    
    return text.strip()


def calculate_confidence_score(keyword_matches: int, total_keywords: int) -> float:
    """
    Calcula un score de confianza basado en keywords encontradas.
    
    Args:
        keyword_matches: Número de keywords encontradas
        total_keywords: Total de keywords posibles
    
    Returns:
        Score de 0.0 a 1.0
    """
    if total_keywords == 0:
        return 0.0
    
    return min(keyword_matches / total_keywords, 1.0)


def format_datetime_spanish(dt: datetime) -> str:
    """
    Formatea datetime en español para mensajes amigables.
    
    Args:
        dt: datetime object
    
    Returns:
        String formateado (ej: "4 de octubre de 2025 a las 10:30")
    """
    months = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
    ]
    
    month_name = months[dt.month - 1]
    
    return f"{dt.day} de {month_name} de {dt.year} a las {dt.hour:02d}:{dt.minute:02d}"
