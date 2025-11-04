"""
Seguimiento Client Module
====================

Cliente HTTP para consumir el servicio Seguimiento (backend principal).

Este cliente se encarga de:
1. Consultar información de pacientes
2. Verificar citas
3. Obtener datos de la base de datos PostgreSQL

El servicio Seguimiento debe estar corriendo en http://localhost:3001
"""

import httpx
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class SeguimientoClient:
    """
    Cliente HTTP para consumir el servicio Seguimiento.
    
    Maneja toda la comunicación con el backend principal que
    tiene acceso directo a PostgreSQL.
    """
    
    def __init__(self, base_url: str = "http://localhost:3001"):
        """
        Inicializa el cliente Seguimiento.
        
        Args:
            base_url: URL base del servicio Seguimiento
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 10.0  # Timeout de 10 segundos
        
        logger.info(f"🌐 SeguimientoClient inicializado: {self.base_url}")
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Realiza una petición HTTP al servicio Seguimiento.
        
        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint a consumir
            **kwargs: Parámetros adicionales (json, params, headers)
        
        Returns:
            Respuesta JSON o None si hay error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                
                json_response = response.json()
                logger.info(f"📥 Respuesta raw del backend: {json_response}")

                if isinstance(json_response, dict):
                    status = json_response.get("statusCode")
                    data = json_response.get("data")

                    if status == 500:
                        logger.error(f"❌ Error 500 desde Seguimiento: {data}")
                        return None
                    
                    # ✅ FIX: Si tiene la estructura esperada, retornar data
                    if data is not None:
                        logger.info(f"✅ Retornando 'data' del response: {data}")
                        return data
                    
                    # ✅ Si no tiene 'data', pero tiene statusCode 200/201, retornar todo
                    if status in [200, 201]:
                        logger.info(f"✅ Retornando response completo (sin 'data'): {json_response}")
                        return json_response
                
                # Si no es dict o no tiene la estructura esperada, retornar tal cual
                logger.info(f"✅ Retornando response directo: {json_response}")
                return json_response
                
        except httpx.TimeoutException:
            logger.error(f"⏱️ Timeout al conectar con Seguimiento: {url}")
            return None
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Error HTTP {e.response.status_code}: {url}")
            return None
        
        except httpx.RequestError as e:
            logger.error(f"❌ Error de conexión con Seguimiento: {e}")
            return None
        
        except Exception as e:
            logger.error(f"❌ Error inesperado en Seguimiento client: {e}")
            return None
    
    # ===== Métodos de Pacientes =====
    
    async def get_patient_by_phone(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """
        Busca un paciente por número de teléfono.
        
        Args:
            phone_number: Número de teléfono del paciente
        
        Returns:
            Datos del paciente o None si no existe
            
        Estructura esperada:
        {
            "id": "uuid",
            "nombre": "Juan Pérez",
            "telefono": "+59175123456",
            "carnet_identidad": "12345678",
            "fecha_nacimiento": "1990-01-01",
            "tiene_cita": true,
            "proxima_cita": {
                "id": "uuid",
                "fecha": "2025-10-20T10:00:00",
                "estado": "Programado"
            }
        }
        """
        logger.info(f"🔍 Buscando paciente por teléfono: {phone_number}")
        
        # Limpiar número de teléfono
        # phone_clean = phone_number.strip().replace('+', '').replace(' ', '').replace('-', '')
        
        #remover 591
        # phone_clean = phone_clean[3:]
        
        response = await self._request(
            method="GET",
            endpoint=f"/api/paciente/telefono/{phone_number}"
        )
        
        if response:
            logger.info(f"✅ Paciente encontrado: {response.get('nombre', 'N/A')}")
            return response
        
        logger.info(f"ℹ️ Paciente no encontrado: {phone_number}")
        return None
    
    async def get_patient_by_carnet(self, carnet_identidad: str) -> Optional[Dict[str, Any]]:
        """
        Busca un paciente por carnet de identidad.
        
        Args:
            carnet_identidad: Carnet de identidad del paciente
        
        Returns:
            Datos del paciente o None si no existe
        """
        logger.info(f"🔍 Buscando paciente por carnet: {carnet_identidad}")
        
        # Limpiar carnet (remover espacios y guiones)
        carnet_clean = carnet_identidad.strip().replace(' ', '').replace('-', '')
        
        response = await self._request(
            method="GET",
            endpoint=f"/api/paciente/carnet/{carnet_clean}"
        )
        
        if response:
            logger.info(f"✅ Paciente encontrado: {response.get('nombre', 'N/A')}")
            return response
        
        logger.info(f"ℹ️ Paciente no encontrado: {carnet_identidad}")
        return None
    
    async def get_patient_by_id(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene información completa de un paciente por ID.
        
        Args:
            patient_id: ID del paciente (UUID)
        
        Returns:
            Datos completos del paciente o None
        """
        logger.info(f"🔍 Obteniendo paciente por ID: {patient_id}")
        
        response = await self._request(
            method="GET",
            endpoint=f"/api/paciente/{patient_id}"
        )
        
        return response
    
    # ===== Métodos de Citas =====

    async def update_appointment(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Reprogramar cita para un paciente.
        
        Args:
            payload: Datos de la cita a reprogramar
        
        Returns:
            Datos de la cita reprogramada o None si hay error
        """
        logger.info(f"📅 Reprogramando cita para paciente: {payload}")
        
        response = await self._request(
            method="PUT",
            endpoint="/api/cita/update-assistant",
            json=payload
        )
        
        logger.info(f"✅ Cita reprogramada: {response}")
        return response
    
    async def get_patient_appointments(
        self,
        patient_id: str,
        include_past: bool = False
    ) -> Optional[list[Dict[str, Any]]]:
        """
        Obtiene las citas de un paciente.
        
        Args:
            patient_id: ID del paciente
            include_past: Si incluir citas pasadas
        
        Returns:
            Lista de citas o None si hay error
        """
        logger.info(f"📅 Obteniendo citas del paciente: {patient_id}")
        
        params = {"include_past": include_past}
        
        response = await self._request(
            method="GET",
            endpoint=f"/api/paciente/{patient_id}/citas",
            params=params
        )
        
        return response
    
    async def get_next_appointment(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la próxima cita del paciente.
        
        Args:
            patient_id: ID del paciente
        
        Returns:
            Datos de la próxima cita o None
            
        Estructura esperada:
        {
            "id": "uuid",
            "fecha": "2025-10-20T10:00:00",
            "estado": "Programado",
            "tipo_consulta": "Control de Tuberculosis",
            "observaciones": "Traer resultados de laboratorio"
        }
        """
        logger.info(f"📅 Obteniendo próxima cita de: {patient_id}")
        
        response = await self._request(
            method="GET",
            endpoint=f"/api/paciente/{patient_id}/proxima-cita"
        )
        
        return response
    
    # ===== Métodos de Verificación =====
    
    async def verify_patient_identity(
        self,
        phone_number: Optional[str] = None,
        carnet_identidad: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Verifica la identidad de un paciente.
        
        Busca por teléfono O carnet de identidad.
        
        Args:
            phone_number: Número de teléfono
            carnet_identidad: Carnet de identidad
        
        Returns:
            Datos del paciente verificado o None
        """
        logger.info("🔐 Verificando identidad de paciente")
        
        # Priorizar búsqueda por teléfono
        if phone_number:
            return await self.get_patient_by_phone(phone_number)
        
        # Si no hay teléfono, buscar por carnet
        if carnet_identidad:
            return await self.get_patient_by_carnet(carnet_identidad)
        
        logger.warning("⚠️ No se proporcionó teléfono ni carnet para verificación")
        return None
    
    # ===== Métodos de Health Check =====
    
    async def health_check(self) -> bool:
        """
        Verifica si el servicio Seguimiento está disponible.
        
        Returns:
            True si el servicio responde, False si no
        """
        logger.debug("💓 Verificando salud del servicio Seguimiento")
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/api/health")
                return response.status_code == 200
        
        except Exception as e:
            logger.error(f"❌ Servicio Seguimiento no disponible: {e}")
            return False
    

# Instancia global (Singleton)
_seguimiento_client: Optional[SeguimientoClient] = None


def get_seguimiento_client() -> SeguimientoClient:
    """
    Obtiene la instancia global del cliente Seguimiento.
    
    Returns:
        SeguimientoClient singleton
    """
    global _seguimiento_client
    
    if _seguimiento_client is None:
        # Obtener URL del servicio Seguimiento desde settings
        seguimiento_url = getattr(settings, 'seguimiento_service_url', 'http://localhost:3001')
        _seguimiento_client = SeguimientoClient(base_url=seguimiento_url)

    return _seguimiento_client
