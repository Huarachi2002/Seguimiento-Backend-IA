# WhatsApp AI Assistant - FastAPI Backend

Sistema de asistente virtual con IA para atención de pacientes vía WhatsApp, integrado con n8n.

## 🏗️ Arquitectura del Proyecto

Este proyecto sigue una **arquitectura hexagonal (clean architecture)** para máxima escalabilidad y mantenibilidad:

```
app/
├── core/              # Configuración central
│   ├── config.py      # Variables de entorno
│   ├── logging.py     # Sistema de logging
│   └── dependencies.py # Inyección de dependencias
│
├── domain/            # Lógica de negocio pura
│   ├── models.py      # Entidades del dominio
│   ├── schemas.py     # Validación de datos (Pydantic)
│   └── exceptions.py  # Excepciones personalizadas
│
├── services/          # Casos de uso
│   ├── ai_service.py           # Servicio de IA
│   └── conversation_service.py # Gestión de conversaciones
│
├── infrastructure/    # Adaptadores externos
│   ├── ai/
│   │   └── model_loader.py    # Carga del modelo
│   ├── database/              # TODO: Conexión a DB
│   └── n8n/                   # TODO: Cliente n8n
│
└── api/               # Capa de presentación
    ├── routes/
    │   ├── chat.py    # Endpoints de chat
    │   └── health.py  # Health checks
    └── middleware/    # TODO: Middleware personalizado
```

## 📋 Características Principales

- ✅ **IA Conversacional**: Modelo de lenguaje para respuestas naturales
- ✅ **Detección de Intenciones**: Identifica automáticamente acciones (agendar, cancelar, etc.)
- ✅ **Gestión de Conversaciones**: Mantiene contexto e historial
- ✅ **Health Checks**: Endpoints para monitoreo (Kubernetes-ready)
- ✅ **Logging Estructurado**: Sistema completo de logs con rotación
- ✅ **Configuración por Entorno**: Variables de entorno con validación
- ✅ **CORS Configurado**: Listo para integrarse con n8n
- ✅ **Documentación Automática**: Swagger UI y ReDoc

## 🚀 Inicio Rápido

### Opción 1: Docker (RECOMENDADO) 🐳

```powershell
# 1. Build
.\docker-deploy.ps1 -Action build

# 2. Start
.\docker-deploy.ps1 -Action start

# 3. Verificar
.\docker-deploy.ps1 -Action status
```

✅ **Ventajas Docker**:
- Sin instalación de Python
- Aislamiento completo
- Redis incluido
- Listo para producción
- Reproducible en cualquier máquina

📚 **Documentación completa**: Ver [DOCKER_README.md](DOCKER_README.md) y [DOCKER_GUIA.md](DOCKER_GUIA.md)

---

### Opción 2: Instalación Local

### 1. Prerrequisitos

- Python 3.10 (verificar: `python --version`)
- Redis instalado y corriendo
- (Opcional) GPU con CUDA para mejor performance

### 2. Instalación

```bash
# Clonar el repositorio
cd fastapi-backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configuración

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus configuraciones
notepad .env
```

**Variables importantes:**

```env
MODEL_NAME=microsoft/DialoGPT-medium  # Modelo de Hugging Face
DEVICE=cpu  # o 'cuda' si tienes GPU
DATABASE_URL=sqlite:///./whatsapp_ai.db
N8N_WEBHOOK_URL=http://localhost:5678/webhook/whatsapp-response
MEDICAL_CENTER_NAME=CAÑADA DEL CARMEN
```

### 4. Ejecutar

```bash
# Desarrollo (con hot reload)
python -m app.main

# O con uvicorn directamente
uvicorn app.main:app --reload --port 8000

# O de la siguiente manera
python -m app.main:app --reload
```

### 5. Verificar

Abre tu navegador en:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Modelo Info**: http://localhost:8000/model/info

## 📡 Integración con n8n

### Flujo de Datos

```
Usuario (WhatsApp) 
    ↓
n8n Webhook (recibe mensaje)
    ↓
POST http://localhost:8000/chat
    ↓
FastAPI procesa con IA
    ↓
Retorna respuesta
    ↓
n8n envía a WhatsApp
```

### Configurar n8n

1. **Webhook de Entrada** (recibe de WhatsApp):
   - Método: POST
   - URL: `webhook/whatsapp-incoming`

2. **HTTP Request** (envía a FastAPI):
   - Método: POST
   - URL: `http://localhost:8000/chat`
   - Body:
   ```json
   {
     "messages": [
       {"role": "user", "content": "{{ $json.message }}"}
     ],
     "user_id": "{{ $json.from }}"
   }
   ```

3. **Webhook de Salida** (envía a WhatsApp):
   - Usa la respuesta de FastAPI

## 🐳 Docker

### Construcción

```bash
docker build -t whatsapp-ai-backend .
```

### Ejecución

```bash
docker run -p 8000:8000 \
  -e MODEL_NAME=microsoft/DialoGPT-medium \
  -e DEVICE=cpu \
  whatsapp-ai-backend
```

### Docker Compose

```bash
docker-compose up -d
```

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest

# Con cobertura
pytest --cov=app --cov-report=html

# Solo tests unitarios
pytest tests/unit

# Solo tests de integración
pytest tests/integration
```

## 📊 Endpoints Principales

### POST /chat
Procesa un mensaje del usuario y retorna respuesta.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Hola, quiero agendar una cita"}
  ],
  "user_id": "+59170123456",
  "max_tokens": 150,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "Claro, con gusto te ayudo...",
  "user_id": "+59170123456",
  "conversation_id": "conv_59170123456_1234567890",
  "action": "schedule_appointment",
  "params": {"status": "collecting_info"},
  "timestamp": "2025-10-04T10:30:00"
}
```

### GET /health
Health check del sistema.

### GET /chat/history/{user_id}
Obtiene historial de conversación.

## 🔧 Desarrollo

### Estructura de un Servicio

Los servicios encapsulan la lógica de negocio:

```python
from app.services.ai_service import AIService

# Inyectar en el servicio
ai_service = AIService(model, tokenizer, device)

# Usar
response = ai_service.generate_response(conversation)
```

### Añadir un Nuevo Endpoint

1. Crear ruta en `app/api/routes/`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("/")
async def create_appointment(data: AppointmentCreate):
    # Lógica
    pass
```

2. Registrar en `app/main.py`:
```python
from app.api.routes import appointments

app.include_router(appointments.router)
```

### Añadir una Excepción

1. Definir en `app/domain/exceptions.py`:
```python
class CustomException(DomainException):
    def __init__(self, detail: str):
        super().__init__(message="Error custom", details={"detail": detail})
```

2. Usar en servicios:
```python
raise CustomException("Algo salió mal")
```

## 🔒 Seguridad

- ✅ Rate limiting por usuario
- ✅ Validación de API keys para n8n
- ✅ CORS configurado
- ✅ Sanitización de inputs con Pydantic
- 🔜 Autenticación JWT
- 🔜 Encriptación de datos sensibles

## 📈 Monitoreo y Logs

Los logs se guardan en:
- **Consola**: Desarrollo (con colores)
- **Archivo**: `logs/whatsapp_ai_assistant.log` (rotación automática)

Niveles de log:
- **DEBUG**: Información detallada
- **INFO**: Operaciones normales
- **WARNING**: Situaciones inusuales
- **ERROR**: Errores que requieren atención
- **CRITICAL**: Errores críticos

## 🚀 Próximos Pasos (Roadmap)

- [ ] **Base de Datos**
  - Implementar PostgreSQL
  - Crear modelos SQLAlchemy
  - Añadir migraciones con Alembic

- [ ] **Redis**
  - Caché de conversaciones
  - Rate limiting distribuido
  - Sessions

- [ ] **Tests**
  - Tests unitarios completos
  - Tests de integración
  - Tests end-to-end

- [ ] **Gestión de Citas**
  - CRUD de citas
  - Integración con calendario
  - Recordatorios automáticos

- [ ] **Pacientes**
  - CRUD de pacientes
  - Verificación de identidad
  - Historial médico básico

- [ ] **N8N Integration**
  - Cliente para enviar mensajes
  - Webhooks bidireccionales
  - Manejo de estados

- [ ] **Deployment**
  - CI/CD con GitHub Actions
  - Kubernetes manifests
  - Monitoring con Prometheus

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Buenas Prácticas Implementadas

1. **Separación de Responsabilidades**: Cada capa tiene su propósito
2. **Dependency Injection**: Facilita testing y reutilización
3. **Configuration Management**: Todo configurable por entorno
4. **Error Handling**: Excepciones específicas y bien manejadas
5. **Logging**: Completo y estructurado
6. **Documentation**: Docstrings en todo el código
7. **Type Hints**: Para mejor IDE support y validación

## 📚 Recursos de Aprendizaje

- **FastAPI**: https://fastapi.tiangolo.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Transformers**: https://huggingface.co/docs/transformers
- **Clean Architecture**: https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html

## ❓ FAQ

**P: ¿Por qué usar arquitectura hexagonal?**  
R: Permite cambiar tecnologías sin afectar la lógica de negocio. Por ejemplo, puedes cambiar de PostgreSQL a MongoDB modificando solo la capa de infraestructura.

**P: ¿Puedo usar otro modelo de IA?**  
R: Sí, solo cambia `MODEL_NAME` en `.env` a cualquier modelo de Hugging Face compatible.

**P: ¿Funciona sin GPU?**  
R: Sí, pero será más lento. GPU mejora significativamente la velocidad.

**P: ¿Cómo escalar en producción?**  
R: Usa Kubernetes, Redis para sesiones compartidas, y PostgreSQL para persistencia.

## 📞 Soporte

Para preguntas o issues, abre un issue en GitHub o contacta al equipo de desarrollo.

---

**Desarrollado con ❤️ para CAÑADA DEL CARMEN**


**Para Pruebas de conversacion el flujo correcto podria ser:**
User:
{
  "user_id": "78956014",
  "messages": [
    {
      "role": "user",
      "content": "Hola tengo citas disponibles"
    }
  ]
}

Assist:
{
    "response": "📅 Tu próxima cita:\n\n• Fecha: 04 de November de 2025\n• Hora: 00:00\n• Tipo: Toma de medicamentos\n• Estado: Programado\n\nTe esperamos en CAÑADA DEL CARMEN. Si necesitas reprogramar, dímelo.",
    "user_id": "78956014",
    "conversation_id": "conv_78956014_1762198764",
    "action": "lookup_appointment",
    "params": null,
    "timestamp": "2025-11-03T21:21:18.149019"
}

User:
{
  "user_id": "78956014",
  "messages": [
    {
      "role": "user",
      "content": "Deseo reprogramar mi cita para el dia de mañana a las 10:00 am"
    }
  ]
}

Assist:
{
    "response": "Por favor responde 'sí' para confirmar o 'no' para cancelar.",
    "user_id": "78956014",
    "conversation_id": "conv_78956014_1762198764",
    "action": null,
    "params": null,
    "timestamp": "2025-11-03T21:24:12.080148"
}

User:
{
  "user_id": "78956014",
  "messages": [
    {
      "role": "user",
      "content": "sí"
    }
  ]
}

Assist:
{
    "response": "✅ ¡Cita reprogramada!\n\n📅 04 de November de 2025\n⏰ 10:00\n\nTe esperamos en CAÑADA DEL CARMEN.",
    "user_id": "78956014",
    "conversation_id": "conv_78956014_1762206455",
    "action": "reschedule_appointment",
    "params": null,
    "timestamp": "2025-11-03T22:32:02.099236"
}