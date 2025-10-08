# 🎯 GUÍA COMPLETA: Implementación de Redis en FastAPI

## 📌 Resumen Ejecutivo

Redis ha sido **completamente implementado** en tu proyecto FastAPI para gestionar el **contexto conversacional temporal** de tu asistente de WhatsApp.

### ¿Por qué Redis?
- ⚡ **Ultra rápido** - Todo se almacena en memoria RAM
- ⏰ **TTL Automático** - Las conversaciones expiran solas después de 1 hora
- 🔄 **Perfecto para sesiones** - Ideal para contexto conversacional temporal
- 📊 **Rate Limiting** - Controla el número de mensajes por usuario

---

## 📂 ¿Qué archivos se crearon/modificaron?

### ✨ Archivos NUEVOS:

1. **`app/infrastructure/redis/redis_client.py`**
   - Cliente Redis con métodos de alto nivel
   - Operaciones: set, get, delete, increment, TTL, etc.

2. **`app/infrastructure/redis/conversation_repository.py`**
   - Repositorio para guardar/recuperar conversaciones
   - Métodos: save, get, delete, extend_ttl, etc.

3. **`app/infrastructure/redis/__init__.py`**
   - Exportaciones del módulo Redis

4. **`REDIS_CONFIG.md`**
   - Guía completa de configuración de Redis
   - Instalación, configuración, troubleshooting

5. **`REDIS_IMPLEMENTATION.md`**
   - Documentación técnica de la implementación
   - Flujos, estructuras de datos, testing

6. **`test-redis.ps1`**
   - Script PowerShell para verificar configuración
   - Ejecutar: `.\test-redis.ps1`

### 🔧 Archivos MODIFICADOS:

1. **`app/services/conversation_service.py`**
   - ❌ ANTES: Guardaba conversaciones en memoria (diccionario)
   - ✅ AHORA: Usa Redis con TTL automático

2. **`app/core/dependencies.py`**
   - Agregadas funciones de inyección de dependencias
   - `get_redis()`, `get_conversation_service()`, etc.
   - Rate limiting ahora usa Redis

3. **`app/main.py`**
   - Inicializa Redis al arrancar
   - Cierra conexión al apagar

4. **`app/api/routes/chat.py`**
   - Usa inyección de dependencias
   - Conversaciones se guardan automáticamente en Redis

5. **`app/api/routes/health.py`**
   - Nuevos endpoints de debug:
     - `GET /redis/test`
     - `GET /redis/stats`
     - `DELETE /redis/clear`

6. **`.env.example`**
   - Actualizado con configuración de Redis

---

## 🔐 Configuraciones Necesarias

### 1️⃣ Variables de Entorno

Crea/edita tu archivo **`.env`**:

```bash
# ===== REDIS =====
# Para desarrollo local:
REDIS_URL=redis://localhost:6379/0

# Para Docker Compose:
# REDIS_URL=redis://redis:6379/0

# Para producción (Redis Cloud):
# REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345

# Password (opcional)
REDIS_PASSWORD=

# Tiempo de expiración (1 hora = 3600 segundos)
SESSION_EXPIRE_TIME=3600
```

### 2️⃣ Instalación de Redis

Elige UNA de estas opciones:

#### **Opción A: Docker (Recomendado - Más fácil)**

```powershell
# Ejecutar Redis en Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Verificar
docker exec -it redis redis-cli ping
# Debe responder: PONG
```

#### **Opción B: Docker Compose (Si usas todo con Docker)**

```powershell
# Ya está configurado en tu docker-compose.yml
docker-compose up -d

# Verificar
docker exec -it whatsapp-ai-redis redis-cli ping
```

#### **Opción C: WSL2 (Windows con Linux)**

```bash
# Dentro de WSL2
sudo apt update
sudo apt install redis-server
sudo service redis-server start

# Verificar
redis-cli ping
```

### 3️⃣ Verificar Instalación

```powershell
# Ejecutar script de verificación
.\test-redis.ps1

# O manualmente:
redis-cli ping
# Debe responder: PONG
```

---

## 🚀 Cómo Funciona

### Flujo Completo:

```
1. Usuario envía mensaje WhatsApp
   ↓
2. n8n recibe mensaje
   ↓
3. n8n hace POST a /chat
   ↓
4. FastAPI recibe mensaje
   ↓
5. ConversationService procesa
   ↓
6. Se guarda en Redis:
   - Clave: conversation:+59112345678
   - Valor: JSON con historial completo
   - TTL: 3600 segundos (1 hora)
   ↓
7. Modelo IA genera respuesta
   ↓
8. Se actualiza conversación en Redis
   ↓
9. Respuesta enviada a n8n
   ↓
10. n8n envía a WhatsApp
```

### Estructura en Redis:

```json
// Clave: conversation:+59112345678
{
  "conversation_id": "conv_+59112345678_1728123456",
  "user_id": "+59112345678",
  "status": "active",
  "messages": [
    {
      "role": "user",
      "content": "Hola, necesito una cita",
      "timestamp": "2025-10-05T10:30:00"
    },
    {
      "role": "assistant",
      "content": "¡Hola! Con gusto te ayudo...",
      "timestamp": "2025-10-05T10:30:05"
    }
  ]
}
```

---

## 🧪 Cómo Probar

### 1. Verificar que Redis funciona:

```powershell
# Ejecutar script de verificación
.\test-redis.ps1
```

### 2. Iniciar la aplicación:

```powershell
uvicorn app.main:app --reload
```

### 3. Probar endpoint de Redis:

```powershell
# En navegador o Postman:
http://localhost:8000/redis/test
```

**Respuesta esperada:**
```json
{
  "status": "success",
  "redis": {
    "connected": true,
    "url": "localhost:6379/0",
    "test_operation": "ok"
  },
  "conversations": {
    "total_active": 0,
    "session_expire_time": 3600
  }
}
```

### 4. Enviar un mensaje de prueba:

```powershell
# Con curl o Postman
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{
    "user_id": "+59112345678",
    "messages": [
      {
        "role": "user",
        "content": "Hola, necesito una cita"
      }
    ]
  }'
```

### 5. Verificar que se guardó en Redis:

```powershell
# Ver conversaciones activas
http://localhost:8000/redis/test

# O desde Redis CLI:
redis-cli KEYS "conversation:*"
redis-cli GET "conversation:+59112345678"
```

---

## 📊 Endpoints Disponibles

### Endpoints de Producción:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/chat` | Enviar mensaje (usa Redis automáticamente) |
| GET | `/chat/history/{user_id}` | Obtener historial de conversación |
| GET | `/health` | Health check general |

### Endpoints de Debug (Desarrollo):

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/redis/test` | Verificar conexión y operaciones |
| GET | `/redis/stats` | Estadísticas de uso |
| DELETE | `/redis/clear?confirm=true` | Limpiar todas las conversaciones |

---

## 🔧 Comandos Útiles

### Redis CLI:

```bash
# Conectar a Redis
redis-cli

# Ver todas las claves
KEYS *

# Ver conversaciones
KEYS conversation:*

# Ver una conversación específica
GET conversation:+59112345678

# Ver tiempo de vida restante (TTL)
TTL conversation:+59112345678
# Ejemplo: 2850 (47.5 minutos restantes)

# Eliminar una conversación
DEL conversation:+59112345678

# Limpiar TODO (CUIDADO)
FLUSHDB

# Ver estadísticas
INFO stats

# Salir
EXIT
```

### Docker:

```powershell
# Ver logs de Redis
docker-compose logs -f redis

# Conectar a Redis CLI en Docker
docker exec -it whatsapp-ai-redis redis-cli

# Ver contenedores corriendo
docker ps | findstr redis
```

---

## ⚙️ Configuración Avanzada

### Cambiar tiempo de expiración:

```bash
# En .env
SESSION_EXPIRE_TIME=7200  # 2 horas
SESSION_EXPIRE_TIME=1800  # 30 minutos
SESSION_EXPIRE_TIME=86400 # 24 horas
```

### Redis con autenticación:

```bash
# Opción 1: En la URL
REDIS_URL=redis://:mi_password_seguro@localhost:6379/0

# Opción 2: Variable separada (recomendado)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=mi_password_seguro
```

### Producción con Redis Cloud:

1. Crea cuenta en https://redis.com/try-free/
2. Crea una base de datos
3. Copia la connection string
4. Pega en .env:

```bash
REDIS_URL=redis://default:tu_password@redis-12345.cloud.redislabs.com:12345
```

---

## 🚨 Solución de Problemas

### ❌ Error: "Connection refused"

**Problema:** Redis no está corriendo

**Solución:**
```powershell
# Verificar si Redis está corriendo
redis-cli ping

# Si no responde, iniciarlo:
# Docker:
docker start redis

# WSL:
sudo service redis-server start

# Docker Compose:
docker-compose up -d redis
```

### ❌ Error: "Module 'redis' not found"

**Problema:** Dependencias no instaladas

**Solución:**
```powershell
pip install -r requirements.txt
```

### ❌ Conversaciones no se guardan

**Verificar:**
```powershell
# 1. Redis está conectado
http://localhost:8000/redis/test

# 2. Ver logs de la aplicación
# Busca: "✅ Redis conectado"

# 3. Verificar .env
# REDIS_URL debe estar correctamente configurado
```

### ❌ Conversaciones no expiran

**Verificar TTL:**
```bash
redis-cli TTL conversation:+59112345678
# Debe mostrar segundos restantes, no -1
```

---

## 📚 Dónde Está Cada Cosa

### Credenciales y Configuración:

📄 **Archivo:** `.env` (en la raíz del proyecto)

```bash
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=
SESSION_EXPIRE_TIME=3600
```

### Código de Redis:

📂 **Carpeta:** `app/infrastructure/redis/`

- `redis_client.py` - Cliente de bajo nivel
- `conversation_repository.py` - Lógica de conversaciones
- `__init__.py` - Exportaciones

### Servicio de Conversaciones:

📄 **Archivo:** `app/services/conversation_service.py`

Usa Redis automáticamente para todas las operaciones.

### Dependencias:

📄 **Archivo:** `app/core/dependencies.py`

Funciones de inyección:
- `get_redis()` - Cliente Redis
- `get_conversation_service()` - Servicio con Redis

---

## ✅ Checklist Final

Antes de ir a producción, verifica:

- [ ] Redis instalado y corriendo
- [ ] `.env` configurado con `REDIS_URL`
- [ ] Script `test-redis.ps1` ejecutado exitosamente
- [ ] Endpoint `/redis/test` responde OK
- [ ] Conversaciones se guardan correctamente
- [ ] Conversaciones expiran después de 1 hora
- [ ] Rate limiting funciona (máx 20 req/min)
- [ ] Redis Cloud configurado (para producción)
- [ ] Logs muestran: "✅ Redis conectado"

---

## 🎓 Conceptos Importantes

### ¿Qué es TTL?
**Time To Live** - Tiempo de vida de un dato en Redis.
- Después de este tiempo, Redis elimina automáticamente el dato
- En nuestro caso: 3600 segundos (1 hora)

### ¿Por qué usar Redis para conversaciones?
1. **Temporal** - No necesitamos guardar conversaciones para siempre
2. **Rápido** - Todo en memoria RAM
3. **Automático** - TTL elimina conversaciones antiguas solo
4. **Escalable** - Puede manejar millones de conversaciones

### ¿Qué pasa si Redis falla?
- La aplicación puede seguir funcionando
- Las conversaciones nuevas no tendrán contexto
- El rate limiting podría no funcionar
- Considera configurar Redis en modo de alta disponibilidad para producción

---

## 📞 Siguiente Paso: Integración

Ahora que Redis está configurado, puedes:

1. ✅ Probar la API con Postman
2. ✅ Integrar con n8n
3. ✅ Conectar con WhatsApp
4. ✅ Monitorear conversaciones en tiempo real

---

## 📖 Documentación Adicional

- **REDIS_CONFIG.md** - Guía detallada de configuración
- **REDIS_IMPLEMENTATION.md** - Documentación técnica
- **.env.example** - Ejemplo de configuración

---

## 🎯 Resumen en 3 Pasos

### 1. Instalar Redis
```powershell
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

### 2. Configurar .env
```bash
REDIS_URL=redis://localhost:6379/0
SESSION_EXPIRE_TIME=3600
```

### 3. Verificar
```powershell
.\test-redis.ps1
uvicorn app.main:app --reload
# Ir a: http://localhost:8000/redis/test
```

---

**¡Listo! Redis está completamente integrado en tu proyecto.** 🎉

¿Preguntas? Revisa `REDIS_CONFIG.md` para más detalles.
