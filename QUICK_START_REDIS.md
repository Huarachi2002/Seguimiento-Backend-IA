# ⚡ QUICK START - Redis en 5 Minutos

## 🎯 ¿Qué se implementó?

✅ **Redis** está completamente integrado en tu proyecto FastAPI para:
- Guardar conversaciones temporalmente (con expiración automática después de 1 hora)
- Implementar rate limiting (máximo 20 mensajes por minuto por usuario)
- Almacenar contexto conversacional entre mensajes

---

## 🚀 Inicio Rápido (3 pasos)

### Paso 1: Instalar Redis

**Elige UNA opción:**

```powershell
# Opción A: Docker (Recomendado - más fácil)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Opción B: Docker Compose (si usas docker-compose.yml)
docker-compose up -d redis

# Opción C: WSL2/Linux
sudo apt install redis-server
sudo service redis-server start
```

### Paso 2: Configurar .env

Crea/edita el archivo `.env`:

```bash
REDIS_URL=redis://localhost:6379/0
SESSION_EXPIRE_TIME=3600
```

### Paso 3: Iniciar y Probar

```powershell
# Iniciar la aplicación
uvicorn app.main:app --reload

# Abrir en navegador:
http://localhost:8000/redis/test

# Deberías ver: "status": "success"
```

---

## ✅ Verificación Rápida

```powershell
# Ejecutar script de verificación
.\test-redis.ps1

# O manualmente:
redis-cli ping
# Respuesta: PONG
```

---

## 📁 Archivos Importantes

### Configuración:
- **`.env`** - Configuración de Redis (REDIS_URL, SESSION_EXPIRE_TIME)
- **`.env.example`** - Plantilla con ejemplos

### Documentación:
- **`GUIA_REDIS_COMPLETA.md`** - Guía completa en español ⭐
- **`REDIS_CONFIG.md`** - Instalación y configuración
- **`REDIS_IMPLEMENTATION.md`** - Documentación técnica
- **`ARQUITECTURA_REDIS.md`** - Diagramas y flujos

### Código:
- **`app/infrastructure/redis/`** - Todo el código de Redis
  - `redis_client.py` - Cliente Redis
  - `conversation_repository.py` - Lógica de conversaciones
  - `__init__.py` - Exportaciones

---

## 🧪 Endpoints de Prueba

```bash
# Test de Redis
GET http://localhost:8000/redis/test

# Estadísticas
GET http://localhost:8000/redis/stats

# Enviar mensaje
POST http://localhost:8000/chat
Content-Type: application/json

{
  "user_id": "+59112345678",
  "messages": [
    {
      "role": "user",
      "content": "Hola, necesito una cita"
    }
  ]
}
```

---

## 🔧 Comandos Útiles

```bash
# Ver si Redis funciona
redis-cli ping

# Ver conversaciones activas
redis-cli KEYS "conversation:*"

# Ver una conversación
redis-cli GET "conversation:+59112345678"

# Limpiar todo (CUIDADO)
redis-cli FLUSHDB
```

---

## ⚙️ Configuración por Ambiente

### Desarrollo Local:
```bash
REDIS_URL=redis://localhost:6379/0
```

### Docker Compose:
```bash
REDIS_URL=redis://redis:6379/0
```

### Producción (Redis Cloud):
```bash
REDIS_URL=redis://default:password@redis-12345.cloud.redislabs.com:12345
```

---

## 🔍 ¿Cómo Funciona?

```
Usuario → WhatsApp → n8n → POST /chat
                              ↓
                    FastAPI + ConversationService
                              ↓
                    Redis guarda conversación
                    (TTL: 1 hora)
                              ↓
                    IA genera respuesta
                              ↓
                    Redis actualiza conversación
                              ↓
                    n8n → WhatsApp → Usuario
```

---

## 📊 Datos en Redis

```
Clave: conversation:+59112345678
TTL: 3600 segundos (1 hora)

Valor: {
  "conversation_id": "conv_xxx",
  "user_id": "+59112345678",
  "messages": [
    {"role": "user", "content": "Hola..."},
    {"role": "assistant", "content": "¡Hola!..."}
  ]
}
```

**Después de 1 hora sin actividad → Redis elimina automáticamente**

---

## 🚨 Problemas Comunes

### ❌ "Connection refused"
→ Redis no está corriendo
→ Solución: `docker start redis` o `sudo service redis-server start`

### ❌ "Module redis not found"
→ Dependencias no instaladas
→ Solución: `pip install -r requirements.txt`

### ❌ Conversaciones no se guardan
→ Verificar: `http://localhost:8000/redis/test`
→ Debe mostrar: `"connected": true`

---

## 📚 Más Información

Lee **`GUIA_REDIS_COMPLETA.md`** para:
- Guía detallada de instalación
- Configuración avanzada
- Solución de problemas
- Ejemplos de uso
- Comandos útiles

---

## ✅ Checklist

- [ ] Redis instalado y corriendo (`redis-cli ping` → PONG)
- [ ] Archivo `.env` creado con REDIS_URL
- [ ] Script `.\test-redis.ps1` ejecutado exitosamente
- [ ] Endpoint `/redis/test` responde OK
- [ ] Aplicación iniciada sin errores
- [ ] Logs muestran: "✅ Redis conectado"

---

## 🎉 ¡Ya está!

Redis está **completamente implementado y funcionando**.

**Próximo paso:** Integrar con n8n y WhatsApp

---

**¿Preguntas?** Lee `GUIA_REDIS_COMPLETA.md` 📖
