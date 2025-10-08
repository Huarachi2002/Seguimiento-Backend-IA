"""
Integration Tests for Chat Endpoint
====================================

Tests de integración que prueban el flujo completo del endpoint.
"""

import pytest
from fastapi import status


class TestChatEndpoint:
    """Tests para el endpoint de chat"""
    
    def test_health_check(self, client):
        """Health check debe retornar 200"""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data
        assert "model_loaded" in data
    
    def test_root_endpoint(self, client):
        """Root debe retornar información de la API"""
        response = client.get("/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "name" in data
        assert "version" in data
    
    @pytest.mark.skip(reason="Requiere modelo cargado")
    def test_chat_endpoint_valid_request(self, client, sample_chat_request):
        """Chat con request válido debe retornar respuesta"""
        response = client.post("/chat/", json=sample_chat_request)
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "response" in data
        assert "user_id" in data
        assert "conversation_id" in data
    
    def test_chat_endpoint_invalid_request(self, client):
        """Chat con request inválido debe retornar 422"""
        invalid_request = {
            "messages": [],  # Vacío - inválido
            "user_id": "123"
        }
        response = client.post("/chat/", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# Para ejecutar: pytest tests/integration/test_chat_api.py -v
