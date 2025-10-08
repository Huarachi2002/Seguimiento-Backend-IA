"""
WhatsApp AI Assistant - FastAPI Backend
========================================

Este paquete contiene toda la lógica del backend para el asistente de IA
que atiende mensajes de WhatsApp a través de n8n.

Arquitectura:
- core/: Configuración central y dependencias
- api/: Capa de presentación (endpoints REST)
- domain/: Modelos de dominio y lógica de negocio
- services/: Casos de uso y servicios de aplicación
- infrastructure/: Adaptadores externos (DB, IA, n8n)
- utils/: Utilidades compartidas
"""

__version__ = "1.0.0"
