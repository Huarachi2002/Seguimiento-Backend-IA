"""
Patient Service Module
======================

Servicio para manejar la lógica de pacientes.

Este servicio actúa como intermediario entre el AI Service
y el backend Seguimiento, enriqueciendo las respuestas con información
de la base de datos.
"""

from typing import Optional, Dict, Any
from app.infrastructure.http import SeguimientoClient
from app.core.logging import get_logger

logger = get_logger(__name__)


class PatientService:
    """
    Servicio para gestionar información de pacientes.
    
    Este servicio consulta el backend Seguimiento para obtener
    información real de pacientes desde PostgreSQL.
    """
    
    def __init__(self, seguimiento_client: SeguimientoClient):
        """
        Inicializa el servicio de pacientes.
        
        Args:
            seguimiento_client: Cliente para comunicarse con Seguimiento
        """
        self.seguimiento_client = seguimiento_client
        logger.info("✅ PatientService inicializado")
    
    async def get_patient_info(
        self,
        phone_number: Optional[str] = None,
        carnet_identidad: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene información completa de un paciente.
        
        Args:
            phone_number: Número de teléfono del paciente
            carnet_identidad: Carnet de identidad del paciente
        
        Returns:
            Información del paciente o None si no existe
        """
        if phone_number:
            return await self.seguimiento_client.get_patient_by_phone(phone_number)
        
        if carnet_identidad:
            return await self.seguimiento_client.get_patient_by_carnet(carnet_identidad)

        return None
    
    async def verify_patient(
        self,
        phone_number: Optional[str] = None,
        carnet_identidad: Optional[str] = None
    ) -> tuple[bool, Optional[Dict[str, Any]]]:
        """
        Verifica si un paciente existe en la base de datos.
        
        Args:
            phone_number: Número de teléfono
            carnet_identidad: Carnet de identidad
        
        Returns:
            Tupla (existe, datos_paciente)
        """
        logger.info(f"🔍 Verificando paciente: phone={phone_number}, carnet={carnet_identidad}")
        
        patient_data = await self.get_patient_info(
            phone_number=phone_number,
            carnet_identidad=carnet_identidad
        )
        
        if patient_data:
            logger.info(f"✅ Paciente verificado: {patient_data.get('nombre')}")
            return True, patient_data
        
        logger.info("ℹ️ Paciente no encontrado en base de datos")
        return False, None
    
    async def get_patient_appointments(self, patient_id: str) -> Optional[list]:
        """
        Obtiene las citas de un paciente.
        
        Args:
            patient_id: ID del paciente
        
        Returns:
            Lista de citas o None
        """
        return await self.seguimiento_client.get_patient_appointments(patient_id)
    
    async def get_next_appointment(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene la próxima cita de un paciente.
        
        Args:
            patient_id: ID del paciente
        
        Returns:
            Datos de la próxima cita o None
        """
        return await self.seguimiento_client.get_next_appointment(patient_id)
    
    def format_patient_context(self, patient_data: Dict[str, Any]) -> str:
        """
        Formatea la información del paciente para el contexto del modelo.
        
        Args:
            patient_data: Datos del paciente desde la BD
        
        Returns:
            Contexto formateado para el prompt
        """
        nombre = patient_data.get('nombre', 'N/A')
        proxima_cita = patient_data.get('proxima_cita')
        
        context = f"Paciente REGISTRADO: {nombre}\n"
        
        if proxima_cita:
            fecha = proxima_cita.get('fecha', 'N/A')
            estado = proxima_cita.get('estado', 'N/A')
            context += f"Próxima cita: {fecha} - Estado: {estado}\n"
        else:
            context += "Sin citas programadas\n"
        
        return context


# Instancia global
_patient_service: Optional[PatientService] = None


def get_patient_service() -> PatientService:
    """
    Obtiene la instancia global del servicio de pacientes.
    
    Returns:
        PatientService singleton
    """
    global _patient_service
    
    if _patient_service is None:
        from app.infrastructure.http import get_seguimiento_client

        seguimiento_client = get_seguimiento_client()
        _patient_service = PatientService(seguimiento_client)

    return _patient_service
