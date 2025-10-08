# 🏗️ ARQUITECTURA DETALLADA - WhatsApp AI Assistant

## 📚 Índice

1. [Visión General](#visión-general)
2. [Principios de Diseño](#principios-de-diseño)
3. [Arquitectura por Capas](#arquitectura-por-capas)
4. [Patrones Implementados](#patrones-implementados)
5. [Flujo de Datos](#flujo-de-datos)
6. [Decisiones de Diseño](#decisiones-de-diseño)
7. [Escalabilidad](#escalabilidad)

---

## 🎯 Visión General

Este proyecto implementa una **arquitectura hexagonal (ports and adapters)**, también conocida como **clean architecture**. El objetivo es crear un sistema:

- ✅ **Mantenible**: Fácil de entender y modificar
- ✅ **Testeable**: Componentes aislados y testeables
- ✅ **Escalable**: Puede crecer sin reescritura completa
- ✅ **Flexible**: Fácil cambiar tecnologías (DB, IA, etc.)

### ¿Por qué Arquitectura Hexagonal?

```
┌─────────────────────────────────────────────┐
│              Mundo Exterior                  │
│  (WhatsApp, n8n, Bases de Datos, etc.)     │
└────────────────┬────────────────────────────┘
                 │
        ┌────────▼────────┐
        │   Adaptadores   │ ← Capa que traduce entre exterior e interior
        │  (API, DB, IA)  │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │    Servicios    │ ← Lógica de aplicación (casos de uso)
        │ (Orquestación)  │
        └────────┬────────┘
                 │
        ┌────────▼────────┐
        │     Dominio     │ ← Lógica de negocio pura
        │  (Reglas core)  │
        └─────────────────┘
```

**Beneficios:**
1. **Independencia de Frameworks**: No estás atado a FastAPI, puedes cambiar a Flask sin tocar la lógica
2. **Independencia de DB**: Cambiar de PostgreSQL a MongoDB solo afecta adaptadores
3. **Independencia de UI**: Mismo backend puede servir REST API, GraphQL, WebSockets
4. **Testeable**: Puedes probar lógica de negocio sin DB, sin API, sin nada externo

---

## 🎨 Principios de Diseño

### 1. Separation of Concerns (SoC)
Cada componente tiene **una sola responsabilidad**:

- **Domain**: Reglas de negocio
- **Services**: Casos de uso
- **API**: Presentación
- **Infrastructure**: Detalles técnicos

### 2. Dependency Inversion
Las dependencias apuntan hacia adentro:

```
API ──► Services ──► Domain
         ▲
         │
    Infrastructure
```

✅ Correcto: Infrastructure depende de Domain  
❌ Incorrecto: Domain depende de Infrastructure

### 3. Don't Repeat Yourself (DRY)
Código compartido en módulos reutilizables:
- `utils/`: Funciones utilitarias
- `core/`: Configuración compartida
- `domain/exceptions.py`: Excepciones centralizadas

### 4. SOLID Principles

#### S - Single Responsibility
Cada clase/función hace una cosa:
```python
# ✅ Correcto
class AIService:
    def generate_response(self): ...

class ConversationService:
    def save_conversation(self): ...

# ❌ Incorrecto
class MegaService:
    def generate_response(self): ...
    def save_conversation(self): ...
    def send_email(self): ...
```

#### O - Open/Closed
Abierto a extensión, cerrado a modificación:
```python
# Puedes añadir nuevos tipos de mensajes sin modificar Message
class Message:
    role: MessageRole
    content: str

class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    # Fácil añadir: SYSTEM = "system"
```

#### L - Liskov Substitution
Subclases pueden reemplazar a la clase base:
```python
class DomainException(Exception): ...
class ModelNotLoadedException(DomainException): ...

# Ambas pueden usarse intercambiablemente
except DomainException as e:  # Captura todas
```

#### I - Interface Segregation
Interfaces pequeñas y específicas (vía duck typing en Python)

#### D - Dependency Inversion
Ya explicado arriba ✅

---

## 🏛️ Arquitectura por Capas

### Capa 1: Domain (Núcleo)

**Ubicación**: `app/domain/`

**Responsabilidad**: Lógica de negocio pura, independiente de tecnología

**Archivos**:
- `models.py`: Entidades del dominio (Message, Conversation, Appointment)
- `schemas.py`: Contratos de datos (Pydantic models)
- `exceptions.py`: Errores del dominio

**Reglas**:
- ❌ NO puede importar nada de infrastructure, api, services
- ✅ SOLO imports de Python stdlib y librerías de utilidad (pydantic, datetime)

**Ejemplo**:
```python
@dataclass
class Conversation:
    """Entidad pura - no sabe de DB, API, nada"""
    conversation_id: str
    messages: List[Message]
    
    def add_message(self, role, content):
        """Lógica de negocio pura"""
        self.messages.append(Message(role, content))
```

### Capa 2: Services (Casos de Uso)

**Ubicación**: `app/services/`

**Responsabilidad**: Orquestar la lógica de negocio, implementar casos de uso

**Archivos**:
- `ai_service.py`: Generar respuestas con IA
- `conversation_service.py`: Gestionar conversaciones

**Reglas**:
- ✅ Puede usar Domain
- ✅ Puede usar Infrastructure (inyección de dependencias)
- ❌ NO puede importar de API

**Ejemplo**:
```python
class ConversationService:
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service  # Inyección de dependencia
    
    def process_user_message(self, user_id, message):
        # Orquestar: obtener conversación, generar respuesta, guardar
        conv = self.get_conversation(user_id)
        response = self.ai_service.generate_response(conv)
        conv.add_message("assistant", response)
        return response
```

### Capa 3: Infrastructure (Adaptadores)

**Ubicación**: `app/infrastructure/`

**Responsabilidad**: Implementar detalles técnicos (DB, APIs externas, IA)

**Archivos**:
- `ai/model_loader.py`: Cargar modelo de Hugging Face
- `database/` (TODO): Conexión y repos de DB
- `n8n/` (TODO): Cliente para n8n

**Reglas**:
- ✅ Puede usar Domain y Services
- ✅ Implementa interfaces definidas en Domain
- ❌ NO debe ser usado directamente por API

**Ejemplo**:
```python
class ModelLoader:
    """Adaptador para Hugging Face"""
    @classmethod
    def load_model(cls):
        # Detalles técnicos de carga
        tokenizer = AutoTokenizer.from_pretrained(...)
        model = AutoModelForCausalLM.from_pretrained(...)
        return model, tokenizer
```

### Capa 4: API (Presentación)

**Ubicación**: `app/api/`

**Responsabilidad**: Exponer funcionalidad vía HTTP REST

**Archivos**:
- `routes/chat.py`: Endpoints de chat
- `routes/health.py`: Health checks
- `middleware/` (TODO): CORS, autenticación, etc.

**Reglas**:
- ✅ Puede usar Services
- ✅ Usa Domain schemas para validación
- ❌ NO debe contener lógica de negocio

**Ejemplo**:
```python
@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # Solo orquestar: validar, llamar servicio, retornar
    response = conversation_service.process_user_message(
        request.user_id,
        request.messages[-1].content
    )
    return ChatResponse(response=response, ...)
```

### Capa 5: Core (Configuración)

**Ubicación**: `app/core/`

**Responsabilidad**: Configuración transversal

**Archivos**:
- `config.py`: Variables de entorno
- `logging.py`: Sistema de logs
- `dependencies.py`: Inyección de dependencias

---

## 🔧 Patrones Implementados

### 1. Singleton Pattern
**Dónde**: `ModelLoader`, `Settings`

**Por qué**: Solo debe haber una instancia del modelo en memoria

```python
class ModelLoader:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. Factory Pattern
**Dónde**: Creación de conversaciones

**Por qué**: Lógica compleja de creación centralizada

```python
def get_or_create_conversation(user_id):
    if user_id not in conversations:
        conversation = Conversation(...)  # Factory
    return conversation
```

### 3. Strategy Pattern
**Dónde**: Detección de intenciones

**Por qué**: Múltiples algoritmos intercambiables

```python
def detect_action(message):
    # Estrategia basada en keywords
    if "agendar" in message:
        return ActionIntent("schedule")
    # Podría cambiarse por ML sin afectar el resto
```

### 4. Dependency Injection
**Dónde**: Servicios, endpoints

**Por qué**: Facilita testing y desacoplamiento

```python
class ConversationService:
    def __init__(self, ai_service: AIService):  # Inyección
        self.ai_service = ai_service

# En tests:
mock_ai = MockAIService()
service = ConversationService(mock_ai)  # Inyectar mock
```

### 5. Repository Pattern
**Dónde**: (TODO) Acceso a datos

**Por qué**: Abstrae la fuente de datos

```python
# TODO:
class ConversationRepository:
    def save(self, conversation): ...
    def get(self, conversation_id): ...

# Puedes tener:
class InMemoryConversationRepo: ...
class PostgresConversationRepo: ...
```

---

## 🔄 Flujo de Datos

### Flujo Completo de un Mensaje

```
1. Usuario envía WhatsApp
   ↓
2. n8n recibe webhook de WhatsApp
   ↓
3. n8n hace POST /chat a FastAPI
   ↓
4. FastAPI - Capa API
   - Recibe request
   - Valida con Pydantic (ChatRequest schema)
   - Logging del request
   ↓
5. FastAPI - Capa Services
   - ConversationService.process_user_message()
   - Recupera/crea conversación
   - Añade mensaje del usuario
   ↓
6. FastAPI - AIService
   - Construye prompt con contexto
   - Llama al modelo (Infrastructure)
   - Detecta intenciones
   ↓
7. FastAPI - Infrastructure
   - ModelLoader provee el modelo
   - Genera texto con Transformers
   ↓
8. FastAPI - Capa Services
   - Guarda respuesta en conversación
   - Retorna respuesta + metadata
   ↓
9. FastAPI - Capa API
   - Serializa con ChatResponse schema
   - Retorna JSON
   ↓
10. n8n recibe respuesta
   ↓
11. n8n envía a WhatsApp
   ↓
12. Usuario recibe mensaje
```

---

## 💡 Decisiones de Diseño

### ¿Por qué FastAPI?
- ✅ Asíncrono (mejor concurrencia)
- ✅ Validación automática (Pydantic)
- ✅ Documentación automática (Swagger)
- ✅ Type hints nativos
- ✅ Alta performance

### ¿Por qué Pydantic?
- ✅ Validación de datos robusta
- ✅ Serialización/deserialización automática
- ✅ Type safety
- ✅ Documentación en schemas

### ¿Por qué SQLAlchemy? (TODO)
- ✅ ORM completo
- ✅ Soporta múltiples DBs
- ✅ Migraciones con Alembic
- ✅ Querys type-safe

### ¿Por qué Redis? (TODO)
- ✅ Cache ultrarrápido
- ✅ Rate limiting distribuido
- ✅ Sessions compartidas (multi-instancia)
- ✅ Pub/Sub para eventos

---

## 📈 Escalabilidad

### Escala Vertical (Mejor Hardware)

```
┌─────────────────┐
│   1 Servidor    │
│   CPU: 4 cores  │  →  CPU: 16 cores
│   RAM: 8GB      │  →  RAM: 64GB
│   GPU: No       │  →  GPU: NVIDIA A100
└─────────────────┘
```

**Cuándo**: Primeras etapas, < 1000 usuarios concurrentes

### Escala Horizontal (Más Servidores)

```
             ┌──────────────┐
             │ Load Balancer │
             └──────┬───────┘
        ┌───────────┼───────────┐
        │           │           │
    ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
    │ API 1 │   │ API 2 │   │ API 3 │
    └───┬───┘   └───┬───┘   └───┬───┘
        └───────────┼───────────┘
                    │
        ┌───────────▼───────────┐
        │  Shared Redis/DB      │
        └───────────────────────┘
```

**Requisitos**:
- ✅ Stateless (sin estado en servidor)
- ✅ Sesiones en Redis
- ✅ DB compartida

**Cuándo**: > 1000 usuarios concurrentes

### Microservicios (Futuro)

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ Chat Service│    │ AI Service  │    │Appointments │
└──────┬──────┘    └──────┬──────┘    └──────┬──────┘
       │                  │                    │
       └──────────────────┼────────────────────┘
                          │
                    ┌─────▼─────┐
                    │ Event Bus │
                    └───────────┘
```

**Cuándo**: Sistema muy grande, equipos independientes

---

## 🔐 Seguridad por Capa

### API Layer
- ✅ CORS configurado
- ✅ Rate limiting
- ✅ Input validation (Pydantic)
- 🔜 JWT authentication
- 🔜 API key para n8n

### Service Layer
- ✅ Validación de contexto
- ✅ Sanitización de inputs
- 🔜 Business rules enforcement

### Infrastructure Layer
- 🔜 DB connection pooling
- 🔜 Prepared statements (SQL injection prevention)
- 🔜 Secrets management (no hardcoded)

---

## 📝 Conclusión

Esta arquitectura está diseñada para:

1. **Crecer**: De prototipo a producción sin reescritura
2. **Mantenerse**: Código claro, documentado, separado
3. **Testearse**: Componentes aislados y mockeable
4. **Cambiar**: Tecnologías intercambiables sin afectar el core

**Próximos pasos recomendados**:
1. Implementar capa de base de datos
2. Añadir tests completos
3. Integración con n8n
4. CI/CD pipeline
5. Monitoreo y observabilidad
