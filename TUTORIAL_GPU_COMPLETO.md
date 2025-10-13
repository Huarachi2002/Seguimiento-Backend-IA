# 🚀 Tutorial Completo: Integrar Hugging Face con GPU en FastAPI

## 📋 Índice
1. [Verificación del Sistema](#paso-1-verificación-del-sistema)
2. [Instalación de Dependencias](#paso-2-instalación-de-dependencias)
3. [Prueba de Modelos](#paso-3-prueba-de-modelos)
4. [Configuración del Proyecto](#paso-4-configuración-del-proyecto)
5. [Actualizar el Model Loader](#paso-5-actualizar-el-model-loader)
6. [Probar la Aplicación](#paso-6-probar-la-aplicación)
7. [Solución de Problemas](#solución-de-problemas)

---

## PASO 1: Verificación del Sistema

### ¿Qué vamos a hacer?
Verificar que tu GPU está correctamente configurada y detectar la versión de CUDA.

### Comandos a ejecutar:

```powershell
# Activar el entorno virtual
.\venv\Scripts\Activate.ps1

# Ejecutar el script de verificación
python verificar_gpu.py
```

### ¿Qué debería ver?

**Si tienes GPU:**
```
============================================================
VERIFICACIÓN DE GPU Y CUDA
============================================================

GPU NVIDIA detectada:
NVIDIA GeForce RTX 3060
Versión de CUDA: 12.1

RECOMENDACIÓN DE INSTALACIÓN:
Para instalar PyTorch con CUDA 12.1, ejecuta:
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Si NO tienes GPU:**
```
No se detectó GPU NVIDIA o nvidia-smi no está disponible.
Se usará CPU para el modelo.
```

### ⚠️ Importante:
- **Anota la versión de CUDA** que detectó (ejemplo: 12.1)
- Si no detecta GPU pero tienes una NVIDIA, necesitas instalar los drivers:
  - Descarga desde: https://www.nvidia.com/Download/index.aspx

---

## PASO 2: Instalación de Dependencias

### Opción A: Instalación Automática (Recomendado)

```powershell
# Ejecutar el script de instalación automática
.\instalar_con_gpu.ps1
```

**Este script hace:**
1. ✅ Detecta tu versión de CUDA automáticamente
2. ✅ Instala PyTorch con soporte GPU correcto
3. ✅ Instala todas las dependencias del proyecto
4. ✅ Verifica que todo funcione

**Tiempo estimado:** 5-10 minutos (dependiendo de tu internet)

### Opción B: Instalación Manual

Si prefieres hacerlo paso a paso:

#### 1. Instalar PyTorch con GPU

**Para CUDA 12.x:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```

**Para CUDA 11.x:**
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Para CPU (sin GPU):**
```powershell
pip install torch torchvision torchaudio
```

#### 2. Instalar Transformers y otras dependencias

```powershell
pip install transformers==4.47.1
pip install accelerate==1.2.1
pip install redis==5.2.1
pip install fastapi==0.115.4
pip install uvicorn==0.34.0
pip install pydantic==2.10.3
pip install pydantic-settings==2.6.1
pip install python-dotenv==1.0.1
```

#### 3. Verificar instalación

```powershell
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}')"
```

**Debería mostrar:**
```
PyTorch: 2.6.0+cu124
CUDA disponible: True
```

---

## PASO 3: Prueba de Modelos

### ¿Qué vamos a hacer?
Probar diferentes modelos antes de elegir uno para tu aplicación.

### Ejecutar el probador de modelos:

```powershell
python probar_modelo.py
```

### Flujo del probador:

```
🤖 PROBADOR DE MODELOS DE HUGGING FACE
============================================================

🔍 VERIFICACIÓN DE SISTEMA
✅ CUDA disponible: Sí
✅ GPU detectada: NVIDIA GeForce RTX 3060
✅ VRAM total: 12.00 GB
✅ VRAM disponible: 11.50 GB

Modelos disponibles:

1. DialoGPT Small (350MB) - Rápido
   microsoft/DialoGPT-small

2. DialoGPT Medium (800MB) - Recomendado
   microsoft/DialoGPT-medium

3. DialoGPT Large (1.5GB) - Mejor calidad
   microsoft/DialoGPT-large

4. BlenderBot (1.6GB) - Mejor conversacional
   facebook/blenderbot-400M-distill

5. FLAN-T5 Base (900MB) - Tareas específicas
   google/flan-t5-base

0. Ingresar otro modelo manualmente

Selecciona un modelo (1-5 o 0):
```

### 💡 Recomendaciones según tu GPU:

| VRAM | Modelo Recomendado | Opción |
|------|-------------------|--------|
| 4GB | DialoGPT Small | Opción 1 |
| 6-8GB | **DialoGPT Medium** | **Opción 2** ⭐ |
| 12GB+ | DialoGPT Large o BlenderBot | Opción 3 o 4 |

### Ejemplo de ejecución:

```
Selecciona un modelo (1-5 o 0): 2

¿Usar prompt de prueba por defecto? (s/n): s

🤖 PROBANDO MODELO: microsoft/DialoGPT-medium
============================================================

1️⃣  Cargando tokenizer...
✅ Tokenizer cargado

2️⃣  Cargando modelo...
   Esto puede tomar varios minutos la primera vez...
   El modelo se descargará a: ~/.cache/huggingface/

✅ Modelo cargado en: cuda
📊 Memoria GPU usada por el modelo: 1.62 GB

3️⃣  Generando respuesta de prueba...

💬 Pregunta: Hola, necesito agendar una cita médica

🤖 Respuesta: Claro, estaré encantado de ayudarte. ¿Para qué especialidad necesitas la cita?

============================================================
✅ PRUEBA COMPLETADA EXITOSAMENTE
============================================================
```

### ⚠️ Notas importantes:

- **Primera ejecución**: El modelo se descarga (puede tardar 5-10 min)
- **Ubicación**: Se guarda en `C:\Users\PC\.cache\huggingface\`
- **Siguientes ejecuciones**: Serán instantáneas (ya está descargado)

---

## PASO 4: Configuración del Proyecto

### 1. Editar el archivo `.env`

Abre tu archivo `.env` y agrega/modifica estas líneas:

```env
# Configuración del Modelo de IA
MODEL_NAME=microsoft/DialoGPT-medium
DEVICE=cuda
MAX_LENGTH=150
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=50

# Redis (ya configurado previamente)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_DECODE_RESPONSES=true
CONVERSATION_TTL=3600

# PostgreSQL (para futuro)
DATABASE_URL=postgresql://user:password@localhost:5432/whatsapp_db
```

### 2. Valores según tu GPU:

**Para GPU con 4GB VRAM (DialoGPT Small):**
```env
MODEL_NAME=microsoft/DialoGPT-small
DEVICE=cuda
MAX_LENGTH=100
```

**Para GPU con 6-8GB VRAM (DialoGPT Medium):**
```env
MODEL_NAME=microsoft/DialoGPT-medium
DEVICE=cuda
MAX_LENGTH=150
```

**Para GPU con 12GB+ VRAM (DialoGPT Large):**
```env
MODEL_NAME=microsoft/DialoGPT-large
DEVICE=cuda
MAX_LENGTH=200
```

**Para CPU (sin GPU):**
```env
MODEL_NAME=microsoft/DialoGPT-small
DEVICE=cpu
MAX_LENGTH=100
```

### 3. Verificar archivo `app/core/config.py`

Ya debería estar configurado con Pydantic Settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Modelo IA
    model_name: str = "microsoft/DialoGPT-medium"
    device: str = "cuda"
    max_length: int = 150
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    # ... resto de configuración

    class Config:
        env_file = ".env"
        case_sensitive = False
```

✅ **Los valores del `.env` tendrán prioridad sobre los valores por defecto**

---

## PASO 5: Actualizar el Model Loader

### Verificar archivo `app/infrastructure/ai/model_loader.py`

Asegúrate de que esté actualizado para usar GPU:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class ModelLoader:
    _instance = None
    _model = None
    _tokenizer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load_model(self):
        """Carga el modelo y tokenizer con soporte GPU."""
        if self._model is None or self._tokenizer is None:
            logger.info(f"Cargando modelo: {settings.model_name}")
            logger.info(f"Dispositivo: {settings.device}")
            
            # Cargar tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(settings.model_name)
            
            # Determinar dtype según dispositivo
            dtype = torch.float16 if settings.device == "cuda" else torch.float32
            
            # Cargar modelo
            self._model = AutoModelForCausalLM.from_pretrained(
                settings.model_name,
                torch_dtype=dtype
            )
            
            # Mover a GPU si está disponible
            self._model = self._model.to(settings.device)
            
            logger.info(f"Modelo cargado exitosamente en {settings.device}")
            
            if settings.device == "cuda":
                memoria_usada = torch.cuda.memory_allocated(0) / 1e9
                logger.info(f"Memoria GPU usada: {memoria_usada:.2f} GB")
        
        return self._model, self._tokenizer
    
    @property
    def model(self):
        if self._model is None:
            self.load_model()
        return self._model
    
    @property
    def tokenizer(self):
        if self._tokenizer is None:
            self.load_model()
        return self._tokenizer

# Singleton global
model_loader = ModelLoader()
```

---

## PASO 6: Probar la Aplicación

### 1. Iniciar Redis (si no está corriendo)

```powershell
docker-compose up -d redis
```

### 2. Iniciar la aplicación FastAPI

```powershell
python -m uvicorn app.main:app --reload
```

### Qué deberías ver en la consola:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:app.infrastructure.ai.model_loader:Cargando modelo: microsoft/DialoGPT-medium
INFO:app.infrastructure.ai.model_loader:Dispositivo: cuda
INFO:app.infrastructure.ai.model_loader:Modelo cargado exitosamente en cuda
INFO:app.infrastructure.ai.model_loader:Memoria GPU usada: 1.62 GB
INFO:app.infrastructure.redis.redis_client:Conectado a Redis en localhost:6379
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

✅ **Si ves esto, todo está funcionando correctamente**

### 3. Probar el endpoint de chat

Abre otra terminal PowerShell y ejecuta:

```powershell
curl -X POST "http://localhost:8000/api/chat" `
  -H "Content-Type: application/json" `
  -d '{\"user_id\": \"test_user\", \"message\": \"Hola, necesito agendar una cita\"}'
```

**Respuesta esperada:**
```json
{
  "response": "Claro, estaré encantado de ayudarte. ¿Para qué especialidad necesitas la cita?",
  "user_id": "test_user",
  "timestamp": "2024-01-15T10:30:00"
}
```

### 4. Verificar uso de GPU en tiempo real

Abre una tercera terminal y ejecuta:

```powershell
nvidia-smi -l 1
```

Esto mostrará el uso de GPU cada segundo. Deberías ver tu aplicación Python usando VRAM.

---

## Solución de Problemas

### ❌ Error: "CUDA out of memory"

**Problema:** Tu GPU no tiene suficiente VRAM para el modelo.

**Solución:**
1. Usa un modelo más pequeño en `.env`:
   ```env
   MODEL_NAME=microsoft/DialoGPT-small
   MAX_LENGTH=100
   ```
2. O usa CPU:
   ```env
   DEVICE=cpu
   ```

### ❌ Error: "torch.cuda.is_available() returns False"

**Problema:** PyTorch no detecta la GPU.

**Soluciones:**
1. Verifica que instalaste PyTorch con CUDA:
   ```powershell
   pip uninstall torch
   pip install torch --index-url https://download.pytorch.org/whl/cu124
   ```
2. Verifica drivers NVIDIA:
   ```powershell
   nvidia-smi
   ```

### ❌ Error: "Model loading is slow"

**Problema:** Primera carga descarga el modelo (normal).

**Solución:**
- Espera pacientemente (5-10 minutos la primera vez)
- Las siguientes veces será instantáneo
- Verifica tu conexión a internet

### ❌ Error: "Redis connection refused"

**Problema:** Redis no está corriendo.

**Solución:**
```powershell
docker-compose up -d redis
```

### ❌ Error: Import errors en Python

**Problema:** Dependencias no instaladas.

**Solución:**
```powershell
.\instalar_con_gpu.ps1
```

---

## 📊 Checklist Final

Antes de poner en producción, verifica:

- [ ] GPU detectada correctamente (`nvidia-smi` funciona)
- [ ] PyTorch con CUDA instalado (`torch.cuda.is_available() = True`)
- [ ] Modelo probado con `probar_modelo.py`
- [ ] `.env` configurado con el modelo correcto
- [ ] Redis corriendo (`docker-compose ps`)
- [ ] FastAPI inicia sin errores
- [ ] Endpoint `/api/chat` responde correctamente
- [ ] Memoria GPU monitoreada y estable

---

## 🎉 ¡Felicidades!

Si llegaste hasta aquí y todos los pasos funcionaron, ahora tienes:

✅ Un asistente de IA funcionando con GPU  
✅ Respuestas más rápidas (GPU vs CPU)  
✅ Contexto conversacional con Redis  
✅ API REST lista para WhatsApp  

### 📚 Próximos Pasos

1. **Integrar con WhatsApp**: Conectar con WhatsApp Business API
2. **Mejorar prompts**: Personalizar para tu caso de uso médico
3. **Agregar PostgreSQL**: Guardar conversaciones permanentemente
4. **Monitoreo**: Configurar logs y métricas
5. **Optimización**: Fine-tuning del modelo para tu dominio

---

## 📞 Recursos Adicionales

- **Hugging Face Docs**: https://huggingface.co/docs
- **PyTorch CUDA Setup**: https://pytorch.org/get-started/locally/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Redis Docs**: https://redis.io/docs/

**Documentos del proyecto:**
- `MODELOS_RECOMENDADOS.md` - Comparativa de modelos
- `GUIA_REDIS_COMPLETA.md` - Redis en detalle
- `ARCHITECTURE.md` - Arquitectura del proyecto
