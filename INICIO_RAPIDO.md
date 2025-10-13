# 🚀 Inicio Rápido - WhatsApp AI Assistant con GPU

## ⚡ Comienza aquí

Si eres nuevo en el proyecto y quieres ponerlo en marcha rápidamente:

### 1️⃣ Clonar y entrar al proyecto

```powershell
cd c:\Users\PC\Desktop\UAGRM\SW2-2025\Grupal\whatsapp-ai-assistant\fastapi-backend
```

### 2️⃣ Crear y activar entorno virtual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3️⃣ Verificar GPU (opcional pero recomendado)

```powershell
python verificar_gpu.py
```

Esto te dirá:
- ✅ Si tienes GPU NVIDIA
- ✅ Qué versión de CUDA tienes
- ✅ Qué comando usar para instalar PyTorch

### 4️⃣ Instalar dependencias con GPU

**Opción A: Automático (Recomendado)**
```powershell
.\instalar_con_gpu.ps1
```

**Opción B: Manual**
```powershell
# Para CUDA 12.x
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# Para CUDA 11.x
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Sin GPU (CPU)
pip install torch torchvision torchaudio

# Instalar resto de dependencias
pip install -r requirements.txt
```

### 5️⃣ Probar modelos

```powershell
python probar_modelo.py
```

Esto te permitirá:
- Probar diferentes modelos antes de elegir
- Ver cuánta VRAM usa cada modelo
- Verificar que la GPU funciona correctamente

### 6️⃣ Configurar variables de entorno

```powershell
# Copiar el archivo de ejemplo
Copy-Item .env.example .env

# Editar .env con tu editor favorito
notepad .env
```

**Configuración mínima necesaria:**
```env
# Modelo (usa el que probaste en el paso 5)
MODEL_NAME=microsoft/DialoGPT-medium
DEVICE=cuda

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CONVERSATION_TTL=3600
```

### 7️⃣ Iniciar Redis

```powershell
docker-compose up -d redis
```

### 8️⃣ Iniciar la aplicación

```powershell
python -m uvicorn app.main:app --reload
```

**Deberías ver:**
```
INFO:     Started server process
INFO:app.infrastructure.ai.model_loader:🤖 Cargando modelo...
INFO:app.infrastructure.ai.model_loader:✅ Modelo cargado en cuda
INFO:app.infrastructure.redis.redis_client:✅ Conectado a Redis
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 9️⃣ Probar el API

**En otra terminal:**
```powershell
curl -X POST "http://localhost:8000/api/chat" `
  -H "Content-Type: application/json" `
  -d '{\"user_id\": \"test\", \"message\": \"Hola\"}'
```

**Respuesta esperada:**
```json
{
  "response": "¡Hola! ¿En qué puedo ayudarte hoy?",
  "user_id": "test",
  "timestamp": "2024-01-15T10:30:00"
}
```

---

## 📚 Documentación Completa

### Para principiantes
- **[TUTORIAL_GPU_COMPLETO.md](TUTORIAL_GPU_COMPLETO.md)** - Tutorial paso a paso con explicaciones detalladas

### Para configuración
- **[MODELOS_RECOMENDADOS.md](MODELOS_RECOMENDADOS.md)** - Comparativa de modelos y recomendaciones
- **[GUIA_REDIS_COMPLETA.md](GUIA_REDIS_COMPLETA.md)** - Todo sobre Redis en el proyecto

### Para arquitectura
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Arquitectura del sistema
- **[RESUMEN_PROYECTO.md](RESUMEN_PROYECTO.md)** - Resumen ejecutivo

---

## 🆘 Solución Rápida de Problemas

| Problema | Solución Rápida |
|----------|-----------------|
| GPU no detectada | `nvidia-smi` → Instalar drivers NVIDIA |
| CUDA out of memory | Cambiar a modelo más pequeño en `.env` |
| Redis connection refused | `docker-compose up -d redis` |
| Import errors | `.\instalar_con_gpu.ps1` |
| Modelo muy lento | Cambiar `DEVICE=cpu` a `DEVICE=cuda` en `.env` |

---

## 📊 Requisitos del Sistema

### Mínimo (CPU)
- Python 3.9+
- 8GB RAM
- 5GB espacio en disco
- Redis

### Recomendado (GPU)
- Python 3.9-3.12 (evitar 3.13)
- 16GB RAM
- GPU NVIDIA con 4GB+ VRAM
- CUDA 11.8 o 12.x
- 10GB espacio en disco
- Redis

---

## 🎯 Próximos Pasos

1. ✅ **Básico funcionando** → Lee [TUTORIAL_GPU_COMPLETO.md](TUTORIAL_GPU_COMPLETO.md)
2. ✅ **Optimizar modelo** → Lee [MODELOS_RECOMENDADOS.md](MODELOS_RECOMENDADOS.md)
3. ✅ **Integrar WhatsApp** → Configura N8N o WhatsApp Business API
4. ✅ **Producción** → Configura PostgreSQL y deploy

---

## 🔗 Enlaces Útiles

- **Hugging Face**: https://huggingface.co/models
- **PyTorch + CUDA**: https://pytorch.org/get-started/locally/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Redis**: https://redis.io/docs/

---

## 💡 Consejos

1. **Primera vez cargando modelo**: Tarda 5-10 minutos (se descarga)
2. **Siguientes veces**: Instantáneo (ya está cacheado)
3. **Monitorear GPU**: Usa `nvidia-smi -l 1` en otra terminal
4. **Cambiar modelo**: Solo edita `.env` y reinicia

---

¿Problemas? Revisa [TUTORIAL_GPU_COMPLETO.md](TUTORIAL_GPU_COMPLETO.md) → Sección "Solución de Problemas"
