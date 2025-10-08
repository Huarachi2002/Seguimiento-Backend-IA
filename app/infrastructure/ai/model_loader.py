"""
Model Loader Module
===================

Este módulo maneja la carga y gestión del modelo de IA.

Responsabilidades:
1. Cargar el modelo y tokenizer desde Hugging Face
2. Gestionar el dispositivo (CPU/GPU)
3. Cachear el modelo para mejorar performance
4. Manejar errores de carga
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import Tuple, Optional
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class ModelLoader:
    """
    Clase para cargar y gestionar el modelo de IA.
    
    Patrón Singleton: Solo debe existir una instancia del modelo
    en memoria (los modelos son grandes y costosos de cargar).
    """
    
    _instance: Optional['ModelLoader'] = None
    _model = None
    _tokenizer = None
    _device = None
    
    def __new__(cls):
        """
        Implementación del patrón Singleton.
        
        Asegura que solo exista una instancia de ModelLoader.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def load_model(cls) -> Tuple[any, any, str]:
        """
        Carga el modelo de lenguaje y tokenizer.
        
        Este método:
        1. Detecta el dispositivo disponible (GPU si existe, sino CPU)
        2. Descarga el modelo de Hugging Face (si no está cacheado)
        3. Carga el modelo en memoria
        4. Configura para inferencia
        
        Returns:
            Tupla (model, tokenizer, device)
        
        Raises:
            Exception: Si falla la carga del modelo
        """
        # Si ya está cargado, retornar
        if cls._model is not None and cls._tokenizer is not None:
            logger.info("✅ Modelo ya cargado, retornando instancia existente")
            return cls._model, cls._tokenizer, cls._device
        
        try:
            logger.info(f"🔄 Iniciando carga del modelo: {settings.model_name}")
            
            # 1. Detectar dispositivo
            cls._device = cls._detect_device()
            logger.info(f"🖥️ Dispositivo detectado: {cls._device}")
            
            # 2. Cargar tokenizer
            logger.info("📝 Cargando tokenizer...")
            cls._tokenizer = AutoTokenizer.from_pretrained(
                settings.model_name,
                cache_dir=settings.model_cache_dir if settings.model_cache_dir != "./models" else None
            )
            
            # Configurar pad_token si no existe
            if cls._tokenizer.pad_token is None:
                cls._tokenizer.pad_token = cls._tokenizer.eos_token
                logger.info("⚙️ pad_token configurado como eos_token")
            
            # 3. Cargar modelo
            logger.info("🤖 Cargando modelo (esto puede tardar unos minutos)...")
            cls._model = AutoModelForCausalLM.from_pretrained(
                settings.model_name,
                cache_dir=settings.model_cache_dir if settings.model_cache_dir != "./models" else None,
                torch_dtype=torch.float16 if cls._device == "cuda" else torch.float32,
                low_cpu_mem_usage=True  # Optimización de memoria
            )
            
            # 4. Mover modelo al dispositivo
            cls._model.to(cls._device)
            
            # 5. Configurar para inferencia (no entrenamiento)
            cls._model.eval()
            
            logger.info(f"✅ Modelo cargado exitosamente")
            logger.info(f"📊 Parámetros del modelo: {cls._count_parameters(cls._model):,}")
            
            return cls._model, cls._tokenizer, str(cls._device)
            
        except Exception as e:
            logger.error(f"❌ Error cargando el modelo: {e}")
            logger.error("💡 Sugerencias:")
            logger.error("   1. Verifica que MODEL_NAME sea correcto")
            logger.error("   2. Verifica tu conexión a internet")
            logger.error("   3. Verifica que tengas suficiente espacio en disco")
            raise e
    
    @classmethod
    def _detect_device(cls) -> str:
        """
        Detecta el mejor dispositivo disponible.
        
        Orden de preferencia:
        1. CUDA (NVIDIA GPU) - Más rápido
        2. MPS (Apple Silicon M1/M2) - Rápido en Mac
        3. CPU - Más lento pero siempre disponible
        
        Returns:
            String del dispositivo: "cuda", "mps", o "cpu"
        """
        # Si está configurado manualmente, respetarlo
        if settings.device.lower() != "auto":
            device_name = settings.device.lower()
            if device_name == "cuda" and not torch.cuda.is_available():
                logger.warning("⚠️ CUDA solicitado pero no disponible, usando CPU")
                return "cpu"
            return device_name
        
        # Auto-detectar
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            logger.info(f"🎮 GPU CUDA detectada: {gpu_name}")
            return "cuda"
        elif torch.backends.mps.is_available():
            logger.info("🍎 Apple Silicon (MPS) detectado")
            return "mps"
        else:
            logger.info("💻 Usando CPU (puede ser más lento)")
            return "cpu"
    
    @classmethod
    def _count_parameters(cls, model) -> int:
        """
        Cuenta el número de parámetros del modelo.
        
        Útil para debugging y logging.
        
        Args:
            model: Modelo de PyTorch
        
        Returns:
            Número total de parámetros
        """
        return sum(p.numel() for p in model.parameters())
    
    @classmethod
    def unload_model(cls) -> None:
        """
        Descarga el modelo de memoria.
        
        Útil para liberar memoria cuando no se necesita el modelo.
        En producción, raramente se usaría esto.
        """
        if cls._model is not None:
            del cls._model
            del cls._tokenizer
            cls._model = None
            cls._tokenizer = None
            
            # Limpiar caché de GPU si es CUDA
            if cls._device == "cuda":
                torch.cuda.empty_cache()
            
            logger.info("🗑️ Modelo descargado de memoria")
    
    @classmethod
    def get_model_info(cls) -> dict:
        """
        Obtiene información sobre el modelo cargado.
        
        Returns:
            Dict con información del modelo
        """
        return {
            "model_name": settings.model_name,
            "device": str(cls._device),
            "is_loaded": cls._model is not None,
            "parameters": cls._count_parameters(cls._model) if cls._model else 0,
            "cuda_available": torch.cuda.is_available(),
            "mps_available": torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
        }
