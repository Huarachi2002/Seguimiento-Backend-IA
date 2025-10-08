"""
Main Application Module
========================

Este es el punto de entrada de la aplicación FastAPI.

Aquí se:
1. Crea la aplicación FastAPI
2. Configura middleware (CORS, logging, etc.)
3. Registra las rutas
4. Inicializa servicios
5. Gestiona el ciclo de vida de la aplicación

**Arquitectura de la aplicación:**

┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (main.py - este archivo)              │
└──────────────┬──────────────────────────┘
               │
        ┌──────┴───────┐
        │              │
    ┌───▼───┐    ┌────▼────┐
    │  API  │    │ Middleware│
    │Routes │    │  (CORS)   │
    └───┬───┘    └─────────┘
        │
    ┌───▼──────────────────────┐
    │     Services Layer       │
    │  (Business Logic)        │
    │  - AIService             │
    │  - ConversationService   │
    └───┬──────────────────────┘
        │
    ┌───▼──────────────────────┐
    │  Infrastructure Layer    │
    │  (External adapters)     │
    │  - ModelLoader           │
    │  - Database              │
    │  - N8N Client            │
    └──────────────────────────┘
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Importaciones de configuración y logging
from app.core.config import settings
from app.core.logging import setup_logging, get_logger

# Importaciones de infraestructura
from app.infrastructure.ai.model_loader import ModelLoader
from app.infrastructure.redis import get_redis_client, close_redis_client

# Importaciones de servicios
from app.services.ai_service import AIService
from app.services.conversation_service import ConversationService

# Importaciones de routes
from app.api.routes import health, chat

# Configurar logging ANTES de cualquier otra cosa
setup_logging()
logger = get_logger(__name__)

# Variables globales para servicios (se inicializan en startup)
ai_service: AIService = None
conversation_service: ConversationService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestor del ciclo de vida de la aplicación.
    
    Este es un concepto importante en FastAPI. El ciclo de vida tiene dos fases:
    
    1. **Startup** (antes de yield): Se ejecuta UNA VEZ cuando la app inicia
       - Cargar modelos de IA
       - Conectar a base de datos
       - Inicializar servicios
       - Configurar recursos
    
    2. **Shutdown** (después de yield): Se ejecuta UNA VEZ cuando la app termina
       - Cerrar conexiones de DB
       - Liberar recursos
       - Guardar estados si es necesario
    
    Ventajas sobre @app.on_event("startup"):
    - Más moderno (recomendado por FastAPI)
    - Permite usar async/await
    - Mejor para testing
    """
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info(f"🚀 Iniciando {settings.app_name} v{settings.app_version}")
    logger.info(f"🌍 Entorno: {settings.environment}")
    logger.info(f"🏥 Centro Médico: {settings.medical_center_name}")
    logger.info("=" * 60)
    
    try:
        # 1. Conectar a Redis
        logger.info("🔌 Conectando a Redis...")
        redis_client = get_redis_client()
        if redis_client.is_connected():
            logger.info(f"✅ Redis conectado: {settings.redis_url}")
        else:
            logger.warning("⚠️ Redis no disponible - continuando sin cache")
        
        # 2. Cargar el modelo de IA
        logger.info("📦 Cargando modelo de IA...")
        model, tokenizer, device = ModelLoader.load_model()
        logger.info(f"✅ Modelo cargado en: {device}")
        
        # 3. Inicializar servicios
        global ai_service, conversation_service
        
        logger.info("⚙️ Inicializando servicios...")
        ai_service = AIService(model=model, tokenizer=tokenizer, device=device)
        
        # ConversationService ahora se inyecta vía dependencies
        # pero podemos pre-calentar el servicio si queremos
        logger.info("✅ Servicios inicializados")
        
        # 4. TODO: Conectar a base de datos
        # db_engine = create_database_connection()
        
        logger.info("=" * 60)
        logger.info("✅ Aplicación lista para recibir requests")
        logger.info(f"📡 Escuchando en puerto: {settings.port}")
        logger.info(f"⏰ TTL de sesiones: {settings.session_expire_time}s")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error durante startup: {e}")
        raise e
    
    # yield marca el punto donde la aplicación está corriendo
    yield
    
    # ===== SHUTDOWN =====
    logger.info("🔄 Apagando aplicación...")
    
    # 1. Cerrar conexión de Redis
    try:
        close_redis_client()
        logger.info("✅ Redis desconectado")
    except Exception as e:
        logger.error(f"❌ Error cerrando Redis: {e}")
    
    # 2. Cerrar conexiones de DB
    # db_engine.dispose()
    
    # 3. Liberar memoria del modelo si es necesario
    # ModelLoader.unload_model()  # Solo si necesitas liberar memoria
    
    logger.info("👋 Aplicación apagada correctamente")


# ===== CREAR APLICACIÓN FASTAPI =====
app = FastAPI(
    title=settings.app_name,
    description="""
    ## API para Asistente de WhatsApp con IA
    
    Esta API procesa mensajes de WhatsApp a través de n8n y proporciona
    respuestas inteligentes usando un modelo de lenguaje.
    
    ### Características principales:
    
    - 🤖 **IA Conversacional**: Modelo de lenguaje para respuestas naturales
    - 📅 **Gestión de Citas**: Agendar, cancelar, reprogramar citas médicas
    - 🔒 **Seguridad**: Validación de identidad y rate limiting
    - 📊 **Detección de Intenciones**: Identifica automáticamente qué quiere el usuario
    - 💬 **Historial**: Mantiene contexto de conversaciones
    
    ### Flujo de integración:
    
    ```
    Usuario (WhatsApp) 
        ↓
    n8n Webhook
        ↓
    POST /chat (esta API)
        ↓
    Modelo de IA
        ↓
    Respuesta
        ↓
    n8n → WhatsApp
    ```
    
    ### Enlaces útiles:
    
    - [Documentación completa](#)
    - [Repositorio GitHub](#)
    - [Configurar n8n](#)
    """,
    version=settings.app_version,
    lifespan=lifespan,  # Usar el gestor de ciclo de vida
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc (documentación alternativa)
)


# ===== MIDDLEWARE =====

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],  # GET, POST, PUT, DELETE, etc.
    allow_headers=["*"],  # Todos los headers
)


# Middleware personalizado para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    """
    Middleware que registra todas las peticiones HTTP.
    
    Útil para:
    - Debugging
    - Auditoría
    - Monitoreo de performance
    - Análisis de uso
    """
    import time
    
    # Antes de procesar el request
    start_time = time.time()
    method = request.method
    url = request.url.path
    
    logger.info(f"→ {method} {url}")
    
    # Procesar el request
    response = await call_next(request)
    
    # Después de procesar el request
    duration = time.time() - start_time
    status_code = response.status_code
    
    # Log con color según status code
    if status_code < 400:
        logger.info(f"← {method} {url} - {status_code} ({duration:.2f}s)")
    else:
        logger.warning(f"← {method} {url} - {status_code} ({duration:.2f}s)")
    
    return response


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Handler global para excepciones no capturadas.
    
    Esto asegura que:
    - Nunca se muestren stack traces al usuario
    - Todos los errores se loggean
    - Se retorna una respuesta consistente
    """
    logger.error(f"❌ Excepción no capturada: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "Ocurrió un error inesperado. Por favor, contacta al soporte.",
            "detail": str(exc) if settings.is_development else None
        }
    )


# ===== REGISTRAR RUTAS =====

# Rutas de health check (sin prefijo)
app.include_router(health.router)

# Rutas de chat
app.include_router(chat.router)

# TODO: Añadir más rutas según necesidades
# app.include_router(appointments.router)
# app.include_router(patients.router)


# ===== PUNTO DE ENTRADA PARA DESARROLLO =====

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 Iniciando servidor de desarrollo...")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.is_development,  # Hot reload solo en desarrollo
        log_level=settings.log_level.lower(),
        access_log=True
    )
