# 📝 Resumen de Implementación de Redis

## ✅ ¿Qué se ha implementado?

### 1. **Infraestructura Redis** 

#### Archivos Creados:
- `app/infrastructure/redis/redis_client.py` - Cliente Redis con métodos de alto nivel
- `app/infrastructure/redis/conversation_repository.py` - Repositorio para gestionar conversaciones
- `app/infrastructure/redis/__init__.py` - Exportaciones del módulo

#### Funcionalidades:
- ✅ Conexión a Redis con manejo de errores
- ✅ Operaciones CRUD (Create, Read, Update, Delete)
- ✅ TTL automático (Time To Live)
- ✅ Serialización/deserialización JSON
- ✅ Rate limiting
- ✅ Patrón Singleton para conexión única

---

### 2. **Servicio de Conversaciones Actualizado**

#### Archivo Modificado:
- `app/services/conversation_service.py`

#### Cambios:
- ❌ ANTES: Almacenaba conversaciones en memoria (diccionario)
- ✅ AHORA: Usa Redis para persistencia temporal

#### Nuevas Funcionalidades:
- Conversaciones se guardan automáticamente en Redis
- TTL automático: expiran después de 1 hora de inactividad
- Extender TTL cuando usuario está activo
- Métodos para estadísticas y limpieza

---

### 3. **Configuración y Dependencias**

#### Archivos Modificados:
- `app/core/config.py` - Ya tenía configuración de Redis, sin cambios
- `app/core/dependencies.py` - Agregadas funciones de inyección de dependencias:
  - `get_redis()` - Cliente Redis
  - `get_conv_repository()` - Repositorio de conversaciones
  - `verify_rate_limit()` - Ahora usa Redis para rate limiting
  - `get_ai_service()` - Servicio de IA
  - `get_conversation_service()` - Servicio de conversaciones con Redis

---

### 4. **Inicialización de la Aplicación**

#### Archivo Modificado:
- `app/main.py`

#### Cambios en el ciclo de vida:
```python
# STARTUP:
1. Conectar a Redis
2. Cargar modelo de IA
3. Inicializar servicios

# SHUTDOWN:
1. Cerrar conexión Redis
2. Cerrar DB (cuando se implemente)
3. Liberar recursos
```

---

### 5. **Endpoints Actualizados**

#### Archivo Modificado:
- `app/api/routes/chat.py`

#### Cambios:
- Usa inyección de dependencias para `ConversationService`
- Rate limiting integrado con Redis
- Las conversaciones se guardan automáticamente en Redis

#### Archivo Modificado:
- `app/api/routes/health.py`

#### Nuevos Endpoints:
- `GET /redis/test` - Verifica conexión y operaciones de Redis
- `GET /redis/stats` - Estadísticas de uso de Redis
- `DELETE /redis/clear` - Limpia todas las conversaciones (solo desarrollo)

---

### 6. **Documentación y Configuración**

#### Archivos Creados/Actualizados:
- `REDIS_CONFIG.md` - Guía completa de configuración de Redis
- `.env.example` - Actualizado con variables de Redis

---

## 🔧 Configuraciones Necesarias

### Variables de Entorno (.env)

```bash
# ===== CONFIGURACIÓN DE REDIS =====
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
SESSION_EXPIRE_TIME=3600  # 1 hora en segundos
```

### Opciones según Entorno:

#### Desarrollo Local:
```bash
REDIS_URL=redis://localhost:6379/0
```

#### Docker Compose:
```bash
REDIS_URL=redis://redis:6379/0
```

#### Producción (Redis Cloud):
```bash
REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345
```

---

## 🚀 Cómo Usar

### 1. Instalar Redis

**Opción A: Docker (Recomendado)**
```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**Opción B: WSL2 (Windows)**
```bash
sudo apt install redis-server
sudo service redis-server start
```

**Opción C: Docker Compose**
```powershell
docker-compose up -d
```

### 2. Configurar Variables de Entorno

```powershell
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y configurar Redis
# REDIS_URL=redis://localhost:6379/0
```

### 3. Iniciar la Aplicación

```powershell
# Con uvicorn
uvicorn app.main:app --reload

# O con Docker
docker-compose up
```

### 4. Verificar Redis

```powershell
# Desde terminal
redis-cli ping
# Respuesta: PONG

# Desde la API
curl http://localhost:8000/redis/test
```

---

## 📊 Flujo de Datos

```
Usuario envía mensaje de WhatsApp
    ↓
n8n Webhook
    ↓
POST /chat (FastAPI)
    ↓
ConversationService.process_user_message()
    ↓
ConversationRepository.save()
    ↓
Redis.set("conversation:{user_id}", data, TTL=3600)
    ↓
Conversación almacenada en Redis
    ↓
Después de 1 hora → Redis elimina automáticamente (TTL)
```

---

## 🔑 Estructura de Datos en Redis

### Claves:

```
conversation:{user_id}          → JSON con toda la conversación
conversation_meta:{user_id}     → Metadata (última actividad, etc.)
rate_limit:{user_id}            → Contador para rate limiting
```

### Ejemplo de Conversación en Redis:

```json
{
  "conversation_id": "conv_+59112345678_1728123456",
  "user_id": "+59112345678",
  "status": "active",
  "created_at": "2025-10-05T10:30:00",
  "updated_at": "2025-10-05T10:35:00",
  "messages": [
    {
      "message_id": "msg_123",
      "role": "user",
      "content": "Hola, necesito una cita",
      "timestamp": "2025-10-05T10:30:00",
      "metadata": {}
    },
    {
      "message_id": "msg_124",
      "role": "assistant",
      "content": "¡Hola! Con gusto te ayudo a agendar una cita...",
      "timestamp": "2025-10-05T10:30:05",
      "metadata": {}
    }
  ],
  "metadata": {}
}
```

---

## 🧪 Testing

### 1. Test de Conectividad

```bash
# Endpoint de test
curl http://localhost:8000/redis/test

# Respuesta esperada:
{
  "status": "success",
  "redis": {
    "connected": true,
    "url": "localhost:6379/0",
    "test_operation": "ok"
  },
  "conversations": {
    "total_active": 0,
    "session_expire_time": 3600,
    "details": []
  }
}
```

### 2. Test de Conversación

```bash
# Enviar un mensaje
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "+59112345678",
    "messages": [
      {
        "role": "user",
        "content": "Hola, necesito una cita"
      }
    ]
  }'

# Verificar que se guardó en Redis
curl http://localhost:8000/redis/test
# Verás: "total_active": 1
```

### 3. Test de TTL

```bash
# Ver TTL de una conversación
redis-cli TTL "conversation:+59112345678"
# Respuesta: número de segundos restantes (ej: 3540)

# Después de 1 hora, verifica que expiró:
redis-cli EXISTS "conversation:+59112345678"
# Respuesta: 0 (no existe)
```

### 4. Test de Rate Limiting

```bash
# Hacer muchos requests rápidos
for i in {1..25}; do
  curl -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"user_id": "+59112345678", "messages": [{"role": "user", "content": "test"}]}'
done

# Después del request 20, debería recibir:
{
  "detail": "Demasiadas solicitudes. Por favor, espera un momento."
}
```

---

## 🛠️ Comandos Útiles

### Redis CLI

```bash
# Conectar
redis-cli

# Ver todas las claves
KEYS *

# Ver conversaciones
KEYS conversation:*

# Ver una conversación
GET conversation:+59112345678

# Ver TTL
TTL conversation:+59112345678

# Eliminar
DEL conversation:+59112345678

# Limpiar todo (CUIDADO)
FLUSHDB
```

### Docker

```powershell
# Ver logs de Redis
docker-compose logs -f redis

# Conectar a Redis CLI
docker exec -it whatsapp-ai-redis redis-cli

# Ver stats
docker exec -it whatsapp-ai-redis redis-cli INFO
```

### API Endpoints de Debug

```bash
# Test Redis
GET http://localhost:8000/redis/test

# Estadísticas
GET http://localhost:8000/redis/stats

# Limpiar (solo desarrollo)
DELETE http://localhost:8000/redis/clear?confirm=true

# Health check
GET http://localhost:8000/health
```

---

## ⚙️ Configuración Avanzada

### Cambiar Tiempo de Expiración

```bash
# En .env
SESSION_EXPIRE_TIME=7200  # 2 horas
```

### Redis con Password

```bash
# Opción 1: En URL
REDIS_URL=redis://:mi_password@localhost:6379/0

# Opción 2: Variable separada
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=mi_password
```

### Múltiples Bases de Datos

Redis soporta 16 bases de datos (0-15):

```bash
# Base de datos 0 (default)
REDIS_URL=redis://localhost:6379/0

# Base de datos 1
REDIS_URL=redis://localhost:6379/1
```

---

## 📈 Monitoreo

### Ver Conversaciones Activas

```python
from app.infrastructure.redis import get_conversation_repository

repo = get_conversation_repository()
users = repo.get_all_user_ids()
print(f"Conversaciones activas: {len(users)}")

for user_id in users:
    ttl = repo.get_ttl(user_id)
    print(f"{user_id}: {ttl}s restantes")
```

### Estadísticas desde la API

```bash
GET /redis/stats

# Respuesta:
{
  "status": "success",
  "keys": {
    "conversations": 5,
    "metadata": 5,
    "rate_limits": 3,
    "total": 13
  },
  "config": {
    "session_expire_time": "3600s (1h)",
    "rate_limit_per_minute": 20
  }
}
```

---

## 🚨 Solución de Problemas

### Redis no se conecta

1. Verificar que Redis está corriendo:
   ```bash
   redis-cli ping
   ```

2. Verificar URL en .env:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

3. Ver logs de la aplicación:
   ```
   ✅ Redis conectado: redis://localhost:6379/0
   ```

### Conversaciones no expiran

1. Verificar TTL configurado:
   ```bash
   redis-cli TTL conversation:+59112345678
   ```

2. Verificar configuración:
   ```bash
   # En .env
   SESSION_EXPIRE_TIME=3600
   ```

### Rate limiting no funciona

1. Verificar claves en Redis:
   ```bash
   redis-cli KEYS rate_limit:*
   ```

2. Verificar contador:
   ```bash
   redis-cli GET rate_limit:+59112345678
   ```

---

## ✅ Checklist de Implementación

- [x] Cliente Redis implementado
- [x] Repositorio de conversaciones creado
- [x] ConversationService actualizado para usar Redis
- [x] Dependencies actualizadas con inyección
- [x] Main.py actualizado con inicialización Redis
- [x] Endpoints de chat actualizados
- [x] Endpoints de debug agregados
- [x] Rate limiting con Redis implementado
- [x] Documentación completa creada
- [x] .env.example actualizado

---

## 📚 Próximos Pasos

1. ✅ Redis configurado
2. ⏭️ Probar endpoints con Postman/curl
3. ⏭️ Integrar con n8n y WhatsApp
4. ⏭️ Configurar Redis Cloud para producción
5. ⏭️ Implementar métricas y monitoreo
6. ⏭️ Agregar tests unitarios para Redis

---

**¡Redis está completamente integrado en tu proyecto!** 🎉
