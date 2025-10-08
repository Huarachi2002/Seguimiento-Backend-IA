"""
Test Configuration and Fixtures
================================

Este archivo contiene configuración compartida y fixtures para todos los tests.

Fixtures son funciones que pytest ejecuta antes de los tests para preparar
el entorno (ej: crear DB de prueba, cargar datos, etc.)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


@pytest.fixture
def client():
    """
    Fixture que proporciona un cliente de prueba para FastAPI.
    
    Uso:
    ```python
    def test_endpoint(client):
        response = client.get("/health")
        assert response.status_code == 200
    ```
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_user_id():
    """ID de usuario para tests"""
    return "+59170123456"


@pytest.fixture
def sample_chat_request():
    """Request de ejemplo para tests de chat"""
    return {
        "messages": [
            {"role": "user", "content": "Hola, quiero agendar una cita"}
        ],
        "user_id": "+59170123456",
        "max_tokens": 150,
        "temperature": 0.7
    }


@pytest.fixture
def sample_conversation():
    """Conversación de ejemplo para tests"""
    from app.domain.models import Conversation, MessageRole
    
    conv = Conversation(
        conversation_id="test_conv_123",
        user_id="+59170123456"
    )
    conv.add_message(MessageRole.USER, "Hola")
    conv.add_message(MessageRole.ASSISTANT, "Hola, ¿en qué puedo ayudarte?")
    
    return conv


# Configuración de pytest
def pytest_configure(config):
    """Configuración global de pytest"""
    # Forzar modo de prueba
    settings.environment = "testing"
    settings.log_level = "DEBUG"
