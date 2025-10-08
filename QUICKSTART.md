# 🚀 GUÍA DE INICIO RÁPIDO

Esta guía te llevará paso a paso desde cero hasta tener tu asistente funcionando.

## 📋 Prerequisitos

Antes de empezar, necesitas:

- ✅ Python 3.10 o superior instalado
- ✅ Git (para clonar el repositorio)
- ✅ Editor de código (VS Code recomendado)
- ✅ (Opcional) Cuenta en Hugging Face para modelos

## 🎯 Paso 1: Configuración del Entorno

### Windows (PowerShell)

```powershell
# 1. Navegar al directorio del proyecto
cd "c:\Users\PC\Desktop\UAGRM\SW2\Proyecto Grupal SW2 Taller\whatsapp-ai-assistant\fastapi-backend"

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar entorno virtual
.\venv\Scripts\Activate

# 4. Actualizar pip
python -m pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt
```

### Linux/Mac (Bash)

```bash
# 1. Navegar al directorio
cd ~/whatsapp-ai-assistant/fastapi-backend

# 2. Crear entorno virtual
python3 -m venv venv

# 3. Activar entorno virtual
source venv/bin/activate

# 4. Actualizar pip
pip install --upgrade pip

# 5. Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Paso 2: Configuración de Variables de Entorno

```powershell
# 1. Copiar archivo de ejemplo
copy .env.example .env

# 2. Editar con tu editor favorito
notepad .env
# O usar VS Code:
code .env
```

### Configuración Básica Recomendada

```env
# Aplicación
APP_NAME="WhatsApp AI Assistant"
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000

# Modelo de IA
MODEL_NAME=microsoft/DialoGPT-medium
DEVICE=cpu

# Base de Datos (SQLite para desarrollo)
DATABASE_URL=sqlite:///./whatsapp_ai.db

# Centro Médico
MEDICAL_CENTER_NAME=CAÑADA DEL CARMEN
MEDICAL_CENTER_PHONE=+591-xxx-xxxx
MEDICAL_CENTER_EMAIL=contacto@canadadelcarmen.com
```

### 🔥 Modelos de IA Recomendados

| Modelo | Tamaño | Requisitos | Uso |
|--------|--------|------------|-----|
| `microsoft/DialoGPT-small` | ~350MB | 2GB RAM | Pruebas rápidas |
| `microsoft/DialoGPT-medium` | ~800MB | 4GB RAM | **Recomendado** |
| `microsoft/DialoGPT-large` | ~1.5GB | 8GB RAM | Mejor calidad |
| `facebook/blenderbot-400M-distill` | ~1.6GB | 8GB RAM | Conversacional |

## 🚀 Paso 3: Ejecutar la Aplicación

### Opción A: Modo Desarrollo (con auto-reload)

```powershell
# Desde el directorio fastapi-backend
python -m app.main
```

O con uvicorn directamente:

```powershell
uvicorn app.main:app --reload --port 8000
```

### Opción B: Modo Producción

```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## ✅ Paso 4: Verificar que Funciona

### 1. Health Check

Abre tu navegador en: http://localhost:8000/health

Deberías ver:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu",
  "timestamp": "2025-10-04T10:30:00",
  "version": "1.0.0"
}
```

### 2. Documentación Interactiva

Abre: http://localhost:8000/docs

Aquí puedes probar todos los endpoints directamente desde el navegador.

### 3. Probar el Chat

En Swagger (http://localhost:8000/docs):

1. Expandir `POST /chat/`
2. Click en "Try it out"
3. Usar este JSON de ejemplo:

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hola, quiero agendar una cita"
    }
  ],
  "user_id": "+59170123456",
  "max_tokens": 150,
  "temperature": 0.7
}
```

4. Click en "Execute"

## 🔧 Paso 5: Solución de Problemas Comunes

### Problema 1: "Import could not be resolved"

**Solución**: Asegúrate de que el entorno virtual está activado y las dependencias instaladas.

```powershell
# Verificar que el entorno está activado (debe mostrar (venv))
# Si no:
.\venv\Scripts\Activate

# Reinstalar dependencias
pip install -r requirements.txt
```

### Problema 2: "Model loading failed"

**Solución**: El modelo se descarga la primera vez. Puede tardar varios minutos.

```powershell
# Verificar conexión a internet
# El modelo se descarga de Hugging Face
# Espera pacientemente la primera vez
```

### Problema 3: "Out of memory"

**Solución**: Usa un modelo más pequeño o aumenta RAM.

```env
# En .env, cambiar a:
MODEL_NAME=microsoft/DialoGPT-small
```

### Problema 4: Puerto 8000 ocupado

**Solución**: Cambiar puerto o cerrar aplicación que lo usa.

```env
# En .env:
PORT=8001
```

O al ejecutar:
```powershell
uvicorn app.main:app --port 8001
```

## 🧪 Paso 6: Ejecutar Tests

```powershell
# Instalar pytest si no está
pip install pytest pytest-asyncio

# Ejecutar todos los tests
pytest

# Solo tests unitarios
pytest tests/unit -v

# Con cobertura
pytest --cov=app --cov-report=html
```

## 🐳 Paso 7: Docker (Opcional)

### Construir imagen

```powershell
docker build -t whatsapp-ai-backend .
```

### Ejecutar contenedor

```powershell
docker run -p 8000:8000 `
  -e MODEL_NAME=microsoft/DialoGPT-medium `
  -e DEVICE=cpu `
  whatsapp-ai-backend
```

### Usar Docker Compose

```powershell
# Iniciar todos los servicios (API + DB + Redis)
docker-compose up -d

# Ver logs
docker-compose logs -f api

# Detener
docker-compose down
```

## 🔗 Paso 8: Integración con n8n

### 1. Instalar n8n

```powershell
# Con npm
npm install -g n8n

# O con Docker
docker run -it --rm `
  --name n8n `
  -p 5678:5678 `
  -v n8n_data:/home/node/.n8n `
  n8nio/n8n
```

### 2. Crear Workflow en n8n

1. Abrir n8n: http://localhost:5678
2. Crear nuevo workflow
3. Añadir nodos:

**Nodo 1: Webhook (Trigger)**
- Webhook URL: `webhook/whatsapp-incoming`
- Método: POST
- Responder inmediatamente: No

**Nodo 2: HTTP Request**
- Método: POST
- URL: `http://host.docker.internal:8000/chat`
- Body JSON:
```json
{
  "messages": [
    {"role": "user", "content": "{{ $json.message }}"}
  ],
  "user_id": "{{ $json.from }}"
}
```

**Nodo 3: WhatsApp (o tu servicio de mensajería)**
- Mensaje: `{{ $json.response }}`
- Para: `{{ $node["Webhook"].json["from"] }}`

### 3. Probar Integración

```powershell
# Enviar mensaje de prueba con curl
curl -X POST http://localhost:5678/webhook/whatsapp-incoming `
  -H "Content-Type: application/json" `
  -d '{\"from\": \"+59170123456\", \"message\": \"Hola\"}'
```

## 📊 Paso 9: Monitoreo

### Ver Logs en Tiempo Real

```powershell
# Los logs se guardan en logs/
Get-Content logs\whatsapp_ai_assistant.log -Tail 50 -Wait
```

### Métricas

Visitar http://localhost:8000/model/info para ver:
- Modelo cargado
- Dispositivo utilizado
- Parámetros del modelo
- Configuración actual

## 🎓 Paso 10: Próximos Pasos

### Aprender Más

1. **Leer ARCHITECTURE.md**: Entender cómo está estructurado
2. **Leer README.md**: Documentación completa
3. **Explorar el código**: Todos los archivos están documentados

### Personalizar

1. **Modificar el prompt del sistema**: `app/core/config.py` → `get_system_context()`
2. **Añadir nuevos endpoints**: Crear archivo en `app/api/routes/`
3. **Cambiar modelo**: Modificar `MODEL_NAME` en `.env`

### Desplegar a Producción

1. **Configurar PostgreSQL**: Cambiar `DATABASE_URL` en `.env`
2. **Configurar Redis**: Para cache y sessions
3. **Usar HTTPS**: Detrás de nginx o similar
4. **CI/CD**: GitHub Actions, GitLab CI, etc.

## 🆘 Obtener Ayuda

### Recursos

- **Documentación FastAPI**: https://fastapi.tiangolo.com/
- **Hugging Face Models**: https://huggingface.co/models
- **n8n Documentation**: https://docs.n8n.io/

### Comandos Útiles

```powershell
# Ver estructura del proyecto
tree /F

# Contar líneas de código
Get-ChildItem -Recurse -Filter *.py | Get-Content | Measure-Object -Line

# Buscar en código
Select-String -Path "app\**\*.py" -Pattern "TODO"

# Formatear código (si tienes black instalado)
black app/

# Type checking (si tienes mypy instalado)
mypy app/
```

## ✅ Checklist de Verificación

Antes de considerar tu setup completo, verifica:

- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas sin errores
- [ ] Archivo `.env` configurado
- [ ] Aplicación inicia sin errores
- [ ] `/health` retorna status "healthy"
- [ ] `/docs` muestra la documentación
- [ ] Endpoint `/chat` responde correctamente
- [ ] Tests pasan exitosamente
- [ ] Logs se generan correctamente

## 🎉 ¡Listo!

Si llegaste hasta aquí, ¡felicitaciones! Tienes un sistema de asistente de IA completamente funcional.

**Próximos desafíos**:
1. Integrar con WhatsApp real
2. Añadir base de datos para persistencia
3. Implementar gestión de citas completa
4. Desplegar a producción

---

**¿Preguntas?** Revisa la documentación o abre un issue en el repositorio.
