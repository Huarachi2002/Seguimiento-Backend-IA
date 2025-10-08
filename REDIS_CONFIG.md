# 🔴 Guía de Configuración de Redis

## 📋 Índice
1. [¿Qué es Redis y por qué lo usamos?](#qué-es-redis)
2. [Instalación de Redis](#instalación)
3. [Configuración en el proyecto](#configuración)
4. [Variables de entorno](#variables-de-entorno)
5. [Uso con Docker](#uso-con-docker)
6. [Producción con Redis Cloud](#producción)
7. [Testing y Debug](#testing)

---

## 🤔 ¿Qué es Redis y por qué lo usamos?

**Redis** es una base de datos en memoria (in-memory) ultra-rápida que usamos para:

1. **Contexto Conversacional Temporal**: Guardar el historial de chat de cada usuario
2. **TTL Automático**: Las conversaciones expiran automáticamente después de 1 hora de inactividad
3. **Rate Limiting**: Limitar el número de requests por usuario
4. **Cache**: Almacenar datos temporales de forma eficiente

### Ventajas
- ⚡ **Rapidísimo** - Todo en RAM
- ⏰ **TTL Automático** - Los datos expiran solos
- 🔄 **Persistencia Opcional** - Puede guardar a disco
- 📦 **Estructuras de Datos Ricas** - Hash, List, Set, etc.

---

## 💻 Instalación de Redis

### Opción 1: Windows (Recomendado - WSL2)

```powershell
# 1. Instalar WSL2 (si no lo tienes)
wsl --install

# 2. Dentro de WSL2, instalar Redis
sudo apt update
sudo apt install redis-server

# 3. Iniciar Redis
sudo service redis-server start

# 4. Verificar que funciona
redis-cli ping
# Debería responder: PONG
```

### Opción 2: Windows (Memurai - Alternativa nativa)

```powershell
# Descargar Memurai (compatible con Redis)
# https://www.memurai.com/get-memurai

# Instalar y ejecutar como servicio de Windows
```

### Opción 3: Docker (Más fácil)

```powershell
# Ejecutar Redis en Docker
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Verificar
docker exec -it redis redis-cli ping
# Debería responder: PONG
```

### Opción 4: Linux/Mac

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server

# Mac (con Homebrew)
brew install redis
brew services start redis

# Verificar
redis-cli ping
```

---

## ⚙️ Configuración en el Proyecto

### 1. Estructura de Archivos

Ya hemos creado los siguientes archivos:

```
app/
├── infrastructure/
│   └── redis/
│       ├── __init__.py
│       ├── redis_client.py           # Cliente Redis
│       └── conversation_repository.py # Repositorio de conversaciones
├── core/
│   ├── config.py          # Configuración (incluye Redis)
│   └── dependencies.py    # Inyección de dependencias
└── services/
    └── conversation_service.py  # Ahora usa Redis
```

### 2. Flujo de Datos

```
Usuario envía mensaje
    ↓
FastAPI Endpoint (/chat)
    ↓
ConversationService
    ↓
ConversationRepository (Redis)
    ↓
Redis almacena:
  - conversation:{user_id} → JSON con historial completo
  - TTL: 3600 segundos (1 hora)
```

---

## 🔐 Variables de Entorno

### Archivo `.env`

Crea un archivo `.env` en la raíz del proyecto (copia de `.env.example`):

```bash
# ===== CONFIGURACIÓN DE REDIS =====

# Desarrollo Local
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=  #NOI APLICA POR EL MOMENTO

# Docker Compose
# REDIS_URL=redis://redis:6379/0

# Con Password
# REDIS_URL=redis://:mi_password@localhost:6379/0

# Redis Cloud (producción)
# REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345

# Tiempo de expiración (segundos)
SESSION_EXPIRE_TIME=3600  # 1 hora
```

### Opciones de Configuración

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `REDIS_URL` | URL de conexión completa | `redis://localhost:6379/0` |
| `REDIS_PASSWORD` | Password (si aplica) | `mi_password_seguro` |
| `SESSION_EXPIRE_TIME` | TTL en segundos | `3600` (1 hora) |

### Formatos de URL

```bash
# Sin autenticación
redis://localhost:6379/0

# Con password (opción 1)
redis://:password@localhost:6379/0

# Con password (opción 2 - preferida)
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=password

# Con usuario y password
redis://usuario:password@localhost:6379/0

# SSL/TLS
rediss://localhost:6380/0
```

---

## 🐳 Uso con Docker

### docker-compose.yml

Ya está configurado en tu proyecto:

```yaml
services:
  # API FastAPI
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  # Redis
  redis:
    image: redis:7-alpine
    container_name: whatsapp-ai-redis
    command: redis-server --appendonly yes
    volumes:
      - redis-data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  redis-data:
```

### Comandos Docker

```powershell
# Iniciar todo (API + Redis + PostgreSQL)
docker-compose up -d

# Ver logs de Redis
docker-compose logs -f redis

# Conectar al CLI de Redis
docker exec -it whatsapp-ai-redis redis-cli

# Ver todas las claves
docker exec -it whatsapp-ai-redis redis-cli KEYS "*"

# Ver una conversación específica
docker exec -it whatsapp-ai-redis redis-cli GET "conversation:+59112345678"

# Detener todo
docker-compose down

# Limpiar datos (CUIDADO - borra todo)
docker-compose down -v
```

---

## ☁️ Producción con Redis Cloud

Para producción, recomendamos **Redis Cloud** (gratis hasta 30MB):

### 1. Crear Cuenta

1. Ir a https://redis.com/try-free/
2. Crear cuenta gratuita
3. Crear una base de datos

### 2. Obtener Credenciales

Copia la conexión string que te dan:

```
redis://default:password@redis-12345.c123.us-east-1-2.ec2.cloud.redislabs.com:12345
```

### 3. Configurar en .env

```bash
REDIS_URL=redis://default:tu_password@redis-12345.cloud.redislabs.com:12345
```

### Alternativas de Producción

| Servicio | Tier Gratuito | Precio |
|----------|---------------|--------|
| **Redis Cloud** | 30MB | Desde $5/mes |
| **AWS ElastiCache** | No | Desde $15/mes |
| **Azure Cache for Redis** | No | Desde $14/mes |
| **Google Cloud Memorystore** | No | Desde $12/mes |
| **Upstash** | 10,000 comandos/día | Pay-as-you-go |

---

## 🧪 Testing y Debug

### Verificar Conexión

```powershell
# En terminal de PowerShell
python -c "import redis; r = redis.from_url('redis://localhost:6379/0'); print(r.ping())"
# Debe imprimir: True
```

### Comandos Útiles de Redis

```bash
# Conectar al CLI
redis-cli

# Dentro del CLI:

# Hacer ping
PING  # Responde: PONG

# Ver todas las claves
KEYS *

# Ver claves de conversaciones
KEYS conversation:*

# Ver una conversación
GET conversation:+59112345678

# Ver TTL de una clave (segundos restantes)
TTL conversation:+59112345678

# Eliminar una clave
DEL conversation:+59112345678

# Vaciar toda la base (CUIDADO)
FLUSHDB

# Ver info del servidor
INFO

# Ver memoria usada
MEMORY USAGE conversation:+59112345678

# Salir
EXIT
```

### Endpoint de Debug

Agrega este endpoint temporal para testear Redis:

```python
# En app/api/routes/health.py

@router.get("/redis-test")
async def test_redis(redis: RedisClient = Depends(get_redis)):
    """Endpoint para testear Redis"""
    
    # Test básico
    redis.set("test_key", "Hello Redis!", expire=60)
    value = redis.get("test_key")
    
    # Ver conversaciones activas
    from app.infrastructure.redis import get_conversation_repository
    repo = get_conversation_repository()
    active_users = repo.get_all_user_ids()
    
    return {
        "redis_connected": redis.is_connected(),
        "test_value": value,
        "active_conversations": len(active_users),
        "users": active_users
    }
```

### Verificar Logs

```powershell
# Ver logs de la aplicación
# Busca líneas como:
# ✅ Redis conectado: redis://localhost:6379/0
# 💾 Conversación guardada: +59112345678 (5 mensajes, TTL=3600s)
```

---

## 🔧 Solución de Problemas

### Problema: "Connection refused"

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solución:**
1. Verificar que Redis está corriendo:
   ```powershell
   # Windows (WSL)
   sudo service redis-server status
   
   # Docker
   docker ps | grep redis
   ```

2. Verificar puerto 6379:
   ```powershell
   netstat -an | findstr 6379
   ```

3. Verificar URL en .env:
   ```bash
   REDIS_URL=redis://localhost:6379/0
   ```

### Problema: "Authentication required"

```
redis.exceptions.ResponseError: NOAUTH Authentication required
```

**Solución:**
```bash
# Opción 1: Agregar password a URL
REDIS_URL=redis://:tu_password@localhost:6379/0

# Opción 2: Usar variable separada
REDIS_PASSWORD=tu_password
```

### Problema: Conversaciones no se guardan

**Verificar:**
```python
# En Python:
from app.infrastructure.redis import get_redis_client
redis = get_redis_client()
print(redis.is_connected())  # Debe ser True

# Ver claves:
print(redis.get_keys_by_pattern("conversation:*"))
```

---

## 📊 Monitoreo

### Ver Estadísticas

```bash
# En redis-cli
INFO stats

# Comandos ejecutados
INFO commandstats

# Memoria
INFO memory
```

### Comandos de la App

```python
# Desde Python
from app.infrastructure.redis import get_conversation_repository

repo = get_conversation_repository()

# Ver conversaciones activas
users = repo.get_all_user_ids()
print(f"Conversaciones activas: {len(users)}")

# Ver TTL
ttl = repo.get_ttl("+59112345678")
print(f"TTL restante: {ttl} segundos")

# Número de mensajes
count = repo.get_message_count("+59112345678")
print(f"Mensajes: {count}")
```

---

## ✅ Checklist de Configuración

- [ ] Redis instalado y corriendo
- [ ] Archivo `.env` creado con `REDIS_URL`
- [ ] Conexión exitosa (endpoint `/health` o redis-cli ping)
- [ ] `SESSION_EXPIRE_TIME` configurado
- [ ] Docker Compose funcionando (si aplica)
- [ ] Tests de conversación exitosos
- [ ] Rate limiting funcionando

---

## 📚 Recursos Adicionales

- [Documentación oficial de Redis](https://redis.io/docs/)
- [Redis Python Client (redis-py)](https://redis-py.readthedocs.io/)
- [Redis Cloud](https://redis.com/cloud/)
- [Redis Commands Reference](https://redis.io/commands/)

---

## 🎯 Siguientes Pasos

1. ✅ Redis configurado
2. ⏭️ Probar el endpoint `/chat` con mensajes
3. ⏭️ Verificar que las conversaciones expiran correctamente
4. ⏭️ Implementar limpieza manual si es necesario
5. ⏭️ Configurar Redis Cloud para producción

---

**¿Necesitas ayuda?** Consulta los logs o usa el endpoint `/redis-test` para debug.
