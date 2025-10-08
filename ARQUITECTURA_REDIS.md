# 🏗️ Arquitectura del Sistema con Redis

## 📊 Diagrama de Arquitectura Completo

```
┌─────────────────────────────────────────────────────────────────┐
│                         USUARIO                                 │
│                      (WhatsApp)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ Mensaje
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                         N8N                                      │
│                  (Workflow Automation)                           │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  WhatsApp    │ → │   Process    │ → │   HTTP       │     │
│  │  Trigger     │    │   Message    │    │   Request    │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ POST /chat
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FASTAPI BACKEND                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  API LAYER                                │  │
│  │                                                           │  │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │  │
│  │  │  /chat  │  │ /health │  │  /redis │  │ /model  │   │  │
│  │  │         │  │         │  │  /test  │  │  /info  │   │  │
│  │  └────┬────┘  └─────────┘  └─────────┘  └─────────┘   │  │
│  └───────┼──────────────────────────────────────────────────┘  │
│          │                                                      │
│          │ Dependency Injection                                │
│          ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               SERVICES LAYER                             │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────┐    │  │
│  │  │      ConversationService                         │    │  │
│  │  │  ┌────────────────────────────────────────┐     │    │  │
│  │  │  │ • process_user_message()               │     │    │  │
│  │  │  │ • get_or_create_conversation()         │     │    │  │
│  │  │  │ • add_message()                        │     │    │  │
│  │  │  │ • get_conversation_history()           │     │    │  │
│  │  │  └────────────────┬───────────────────────┘     │    │  │
│  │  └─────────────────────┼───────────────────────────┘    │  │
│  │                        │                                 │  │
│  │  ┌─────────────────────┼───────────────────────────┐    │  │
│  │  │      AIService      │                           │    │  │
│  │  │  ┌──────────────────▼─────────────────────┐    │    │  │
│  │  │  │ • generate_response()                  │    │    │  │
│  │  │  │ • detect_action()                      │    │    │  │
│  │  │  └────────────────────────────────────────┘    │    │  │
│  │  └───────────────────────────────────────────────┘    │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │                                    │
│                         │                                    │
│  ┌──────────────────────┼────────────────────────────────┐  │
│  │        INFRASTRUCTURE LAYER                           │  │
│  │                      │                                 │  │
│  │  ┌───────────────────┼──────────────────────────┐     │  │
│  │  │   Redis Infrastructure                       │     │  │
│  │  │                   │                          │     │  │
│  │  │  ┌────────────────▼──────────────────┐      │     │  │
│  │  │  │  ConversationRepository           │      │     │  │
│  │  │  │  ┌──────────────────────────┐     │      │     │  │
│  │  │  │  │ • save(conversation)     │     │      │     │  │
│  │  │  │  │ • get(user_id)          │     │      │     │  │
│  │  │  │  │ • delete(user_id)       │     │      │     │  │
│  │  │  │  │ • extend_ttl(user_id)   │     │      │     │  │
│  │  │  │  │ • get_all_user_ids()    │     │      │     │  │
│  │  │  │  └──────────┬───────────────┘     │      │     │  │
│  │  │  └─────────────┼─────────────────────┘      │     │  │
│  │  │                │                             │     │  │
│  │  │  ┌─────────────▼─────────────────────┐      │     │  │
│  │  │  │  RedisClient                      │      │     │  │
│  │  │  │  ┌──────────────────────────┐     │      │     │  │
│  │  │  │  │ • set(key, value, ttl)  │     │      │     │  │
│  │  │  │  │ • get(key)              │     │      │     │  │
│  │  │  │  │ • delete(key)           │     │      │     │  │
│  │  │  │  │ • increment(key)        │     │      │     │  │
│  │  │  │  │ • expire(key, seconds)  │     │      │     │  │
│  │  │  │  └──────────┬───────────────┘     │      │     │  │
│  │  │  └─────────────┼─────────────────────┘      │     │  │
│  │  └────────────────┼──────────────────────────┘     │  │
│  │                   │                                 │  │
│  │  ┌────────────────┼──────────────────────────┐     │  │
│  │  │   AI Infrastructure                       │     │  │
│  │  │  ┌─────────────▼─────────────────────┐    │     │  │
│  │  │  │  ModelLoader                      │    │     │  │
│  │  │  │  • load_model()                   │    │     │  │
│  │  │  │  • get_model_info()               │    │     │  │
│  │  │  └───────────────────────────────────┘    │     │  │
│  │  └───────────────────────────────────────────┘     │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│                      EXTERNAL SERVICES                          │
│                                                                  │
│  ┌──────────────────────┐         ┌──────────────────────┐     │
│  │   REDIS SERVER       │         │   AI MODEL           │     │
│  │                      │         │   (HuggingFace)      │     │
│  │  ┌────────────────┐  │         │                      │     │
│  │  │ Key-Value Store│  │         │  DialoGPT-medium     │     │
│  │  │                │  │         │                      │     │
│  │  │ conversation:  │  │         └──────────────────────┘     │
│  │  │ +59112345678   │  │                                      │
│  │  │                │  │                                      │
│  │  │ TTL: 3600s     │  │                                      │
│  │  └────────────────┘  │                                      │
│  └──────────────────────┘                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🔄 Flujo de Datos Detallado

### 1. Usuario envía mensaje

```
Usuario (WhatsApp) → n8n Webhook → FastAPI (/chat)
```

### 2. Procesamiento en FastAPI

```
/chat endpoint
    ↓
Dependency Injection:
    → ConversationService
    → RedisClient
    → AIService
    ↓
ConversationService.process_user_message()
    ↓
┌─────────────────────────────────┐
│ 1. Obtener/Crear Conversación  │
│    ├─ Buscar en Redis           │
│    ├─ Si existe: Extender TTL   │
│    └─ Si no: Crear nueva        │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 2. Añadir mensaje del usuario  │
│    ├─ Agregar a conversación    │
│    └─ Guardar en Redis          │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 3. Generar respuesta con IA     │
│    ├─ AIService.generate()      │
│    └─ Usar historial de Redis   │
└─────────────────────────────────┘
    ↓
┌─────────────────────────────────┐
│ 4. Guardar respuesta            │
│    ├─ Añadir a conversación     │
│    └─ Actualizar en Redis       │
└─────────────────────────────────┘
    ↓
Retornar respuesta → n8n → WhatsApp
```

## 💾 Estructura de Datos en Redis

### Conversación Completa:

```json
// Clave: conversation:+59112345678
// TTL: 3600 segundos
{
  "conversation_id": "conv_+59112345678_1728123456",
  "user_id": "+59112345678",
  "status": "active",
  "created_at": "2025-10-05T10:00:00",
  "updated_at": "2025-10-05T10:05:00",
  "messages": [
    {
      "message_id": "msg_001",
      "role": "user",
      "content": "Hola, necesito una cita",
      "timestamp": "2025-10-05T10:00:00",
      "metadata": {}
    },
    {
      "message_id": "msg_002",
      "role": "assistant",
      "content": "¡Hola! Con gusto te ayudo a agendar una cita. ¿Para qué especialidad?",
      "timestamp": "2025-10-05T10:00:05",
      "metadata": {}
    },
    {
      "message_id": "msg_003",
      "role": "user",
      "content": "Cardiología",
      "timestamp": "2025-10-05T10:05:00",
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

### Metadata:

```json
// Clave: conversation_meta:+59112345678
// TTL: 3600 segundos
{
  "last_activity": "2025-10-05T10:05:00",
  "message_count": 3
}
```

### Rate Limiting:

```
// Clave: rate_limit:+59112345678
// TTL: 60 segundos
// Valor: contador numérico
15  // requests en el último minuto
```

## 🔌 Inyección de Dependencias

```python
# app/core/dependencies.py

def get_redis() -> RedisClient:
    """Singleton del cliente Redis"""
    return get_redis_client()

def get_conv_repository() -> ConversationRepository:
    """Repositorio con Redis inyectado"""
    redis = get_redis()
    return ConversationRepository(redis)

def get_ai_service() -> AIService:
    """Servicio de IA"""
    model_loader = get_model_loader()
    return AIService(model_loader)

def get_conversation_service(
    ai_service: AIService = Depends(get_ai_service),
    repo: ConversationRepository = Depends(get_conv_repository)
) -> ConversationService:
    """Servicio completo con todas las dependencias"""
    return ConversationService(ai_service, repo)
```

## 🌐 Endpoints de la API

### Producción:

| Endpoint | Método | Descripción | Usa Redis |
|----------|--------|-------------|-----------|
| `/chat` | POST | Procesar mensaje | ✅ Sí |
| `/chat/history/{user_id}` | GET | Obtener historial | ✅ Sí |
| `/health` | GET | Health check | ✅ Verifica |

### Debug/Desarrollo:

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/redis/test` | GET | Test de Redis |
| `/redis/stats` | GET | Estadísticas |
| `/redis/clear` | DELETE | Limpiar todo |

## ⚙️ Configuración por Ambiente

### Desarrollo Local:

```bash
# .env
ENVIRONMENT=development
REDIS_URL=redis://localhost:6379/0
SESSION_EXPIRE_TIME=3600
```

### Docker Compose:

```bash
# .env
ENVIRONMENT=development
REDIS_URL=redis://redis:6379/0
SESSION_EXPIRE_TIME=3600
```

### Producción:

```bash
# .env
ENVIRONMENT=production
REDIS_URL=redis://default:password@redis-cloud.com:12345
SESSION_EXPIRE_TIME=7200  # 2 horas
RATE_LIMIT_PER_MINUTE=50
```

## 🔒 Seguridad

### Rate Limiting:

```python
# Límite: 20 requests por minuto
# Implementado en: app/core/dependencies.py

async def verify_rate_limit(user_id: str, redis: RedisClient):
    key = f"rate_limit:{user_id}"
    count = redis.increment(key)
    
    if count == 1:
        redis.expire(key, 60)  # 60 segundos
    
    if count > 20:
        raise HTTPException(429, "Demasiadas solicitudes")
```

### TTL Automático:

```python
# Conversaciones expiran después de 1 hora
# Si usuario está activo, se extiende automáticamente

repo.save(conversation, ttl=3600)  # 1 hora
repo.extend_ttl(user_id)           # Extender si activo
```

## 📊 Monitoreo

### Logs Importantes:

```
# Startup
✅ Conectado a Redis: redis://localhost:6379/0
✅ ConversationService inicializado con Redis

# Durante operación
📝 Nueva conversación creada en Redis: conv_xxx
💾 Conversación guardada: +59112345678 (5 mensajes, TTL=3600s)
📖 Conversación recuperada de Redis: conv_xxx
⏰ TTL extendido: +59112345678 -> 3600s

# Rate Limiting
✅ Rate limit OK para +59112345678: 5/20
⚠️ Rate limit excedido para +59112345678: 21 requests/min

# Shutdown
✅ Redis desconectado
```

## 🎯 Ventajas de esta Arquitectura

1. **Separación de Responsabilidades**
   - API Layer: Maneja HTTP
   - Services: Lógica de negocio
   - Infrastructure: Detalles técnicos

2. **Inyección de Dependencias**
   - Fácil testing (inyectar mocks)
   - Bajo acoplamiento
   - Configuración centralizada

3. **Persistencia con Redis**
   - Ultra rápido (in-memory)
   - TTL automático
   - Perfecto para sesiones

4. **Escalabilidad**
   - Cada capa es independiente
   - Fácil agregar más servicios
   - Redis puede escalar horizontalmente

5. **Mantenibilidad**
   - Código organizado
   - Fácil de entender
   - Documentado

## 🚀 Próximos Pasos Sugeridos

1. **Implementar PostgreSQL**
   - Para datos permanentes (usuarios, citas, etc.)
   - Redis para sesiones, PostgreSQL para datos

2. **Agregar Métricas**
   - Prometheus para monitoreo
   - Grafana para visualización

3. **Implementar Caché Adicional**
   - Caché de respuestas frecuentes en Redis
   - Reducir llamadas al modelo de IA

4. **Alta Disponibilidad**
   - Redis Sentinel o Cluster
   - Múltiples instancias de FastAPI

5. **CI/CD**
   - Tests automáticos
   - Deploy automático con Docker

---

**Esta arquitectura es escalable, mantenible y lista para producción.** 🎉
