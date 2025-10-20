"""
HTTP Client Infrastructure
===========================

Módulo para clientes HTTP que consumen servicios externos.
"""

from app.infrastructure.http.seguimiento_client import SeguimientoClient, get_seguimiento_client

__all__ = [
    'SeguimientoClient',
    'get_seguimiento_client'
]
