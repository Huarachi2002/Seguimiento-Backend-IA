# 📤 Guía Rápida: Subir Modelo a Hugging Face Hub

Esta guía te ayudará a subir tu modelo fine-tuned de 4GB a Hugging Face Hub de forma **GRATUITA**.

---

## 🎯 ¿Por Qué Hugging Face Hub?

- ✅ **100% GRATIS** hasta 100GB de almacenamiento
- ✅ **CDN Global** - Descarga rápida desde cualquier región
- ✅ **Versionado** - Control de versiones como Git
- ✅ **Colaboración** - Comparte con tu equipo
- ✅ **Descarga automática** - FastAPI lo descarga solo

---

## 📋 Requisitos Previos

1. Cuenta en Hugging Face: https://huggingface.co/join
2. Modelo entrenado localmente en: `app/training/models/gpt2-spanish-tb-structured/`
3. Python instalado con pip

---

## 🚀 Paso a Paso (10 minutos)

### 1. Instalar Hugging Face CLI

```bash
# En tu terminal local (Windows PowerShell)
pip install huggingface_hub
```

### 2. Obtener Token de Autenticación

1. Ve a: https://huggingface.co/settings/tokens
2. Click en **"New token"**
3. Nombre: `whatsapp-ai-model-upload`
4. Tipo: **Write** (para poder subir)
5. **Copiar el token** (lo necesitarás en el siguiente paso)

### 3. Autenticarse

```bash
# Login con Hugging Face
huggingface-cli login

# Pegar el token cuando te lo pida
# Token: hf_xxxxxxxxxxxxxxxxxxxxx
```

### 4. Navegar al Directorio del Modelo

```powershell
# En PowerShell
cd C:\Users\PC\Desktop\UAGRM\SW2-2025\Grupal\whatsapp-ai-assistant\fastapi-backend
cd app\training\models\gpt2-spanish-tb-structured
```

### 5. Verificar Contenido del Modelo

```powershell
# Listar archivos (deberías ver estos archivos)
ls

# Archivos esperados:
# - config.json
# - pytorch_model.bin (o model.safetensors)
# - tokenizer_config.json
# - vocab.json
# - merges.txt
# - special_tokens_map.json
```

### 6. Subir el Modelo

```bash
# Reemplaza "tu-usuario" con tu nombre de usuario de Hugging Face
# Ejemplo: Huarachi2002/gpt2-spanish-tb-structured

huggingface-cli upload tu-usuario/gpt2-spanish-tb-structured . --repo-type model

# Esto creará el repositorio automáticamente y subirá todos los archivos
```

**⏱️ Tiempo estimado**: 15-30 minutos (depende de tu velocidad de internet)

**📊 Progreso**: Verás barras de progreso para cada archivo:
```
Uploading pytorch_model.bin: 100%|████████| 4.2GB/4.2GB [15:30<00:00, 4.5MB/s]
Uploading config.json: 100%|████████| 1.2kB/1.2kB [00:01<00:00, 900B/s]
...
```

### 7. Verificar en el Navegador

1. Ve a: `https://huggingface.co/tu-usuario/gpt2-spanish-tb-structured`
2. Deberías ver tu modelo con todos los archivos
3. Por defecto es **público** (cualquiera puede descargarlo)

---

## ⚙️ Configurar FastAPI para Usar el Modelo

### 1. Actualizar Variables de Entorno

Edita tu archivo `.env`:

```env
# Antes (modelo local)
# MODEL_NAME=/app/training/models/gpt2-spanish-tb-structured

# Después (modelo en Hugging Face)
MODEL_NAME=tu-usuario/gpt2-spanish-tb-structured

# Ejemplo real:
# MODEL_NAME=Huarachi2002/gpt2-spanish-tb-structured

# Cache local (para no re-descargar en cada inicio)
MODEL_CACHE_DIR=/app/models
```

### 2. NO Necesitas Cambiar el Código

El código en `app/infrastructure/ai/model_loader.py` ya está preparado:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

def load_model():
    model_name = os.getenv('MODEL_NAME')  # Lee de .env
    cache_dir = os.getenv('MODEL_CACHE_DIR', '/app/models')
    
    # Descarga automáticamente desde Hugging Face si no está en cache
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        low_cpu_mem_usage=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    
    return model, tokenizer
```

### 3. Actualizar docker-compose.yml (Opcional)

Si tienes el modelo montado como volumen, **eliminarlo**:

```yaml
# ELIMINAR ESTO (ya no necesitas el modelo local)
volumes:
  # - ./app/training/models:/app/training/models:ro  # ❌ Eliminar esta línea
  - model-cache:/app/models  # ✅ Mantener esto (para cache)
```

---

## 🧪 Probar Localmente

### Sin Docker (desarrollo local)

```bash
# Activar entorno virtual
.\venv\Scripts\activate

# Actualizar .env con MODEL_NAME=tu-usuario/gpt2-spanish-tb-structured

# Ejecutar
python -m uvicorn app.main:app --reload

# Primera ejecución: Descargará el modelo (5-10 min)
# Downloading: 100%|██████| 4.2GB/4.2GB [05:30<00:00, 12.7MB/s]

# Siguientes ejecuciones: Usará cache local (30 seg)
```

### Con Docker

```powershell
# Build y start
docker-compose up --build -d

# Ver logs (verás la descarga del modelo)
docker-compose logs -f api

# Verás algo como:
# api_1 | Downloading model from Hugging Face...
# api_1 | Downloading: 100%|██████| 4.2GB/4.2GB
# api_1 | Model loaded successfully
# api_1 | Uvicorn running on http://0.0.0.0:8000

# Verificar
curl http://localhost:8000/health
```

---

## 🔒 Hacer el Modelo Privado (Opcional)

Si NO quieres que tu modelo sea público:

### 1. Hacer Privado en Hugging Face

1. Ve a: `https://huggingface.co/tu-usuario/gpt2-spanish-tb-structured/settings`
2. Scroll hasta **"Visibility"**
3. Click en **"Make private"**

### 2. Configurar Token en Producción

```env
# .env
MODEL_NAME=tu-usuario/gpt2-spanish-tb-structured
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxx  # Tu token de Hugging Face
```

### 3. Actualizar model_loader.py

```python
def load_model():
    model_name = os.getenv('MODEL_NAME')
    cache_dir = os.getenv('MODEL_CACHE_DIR', '/app/models')
    token = os.getenv('HF_TOKEN')  # Leer token
    
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        cache_dir=cache_dir,
        use_auth_token=token,  # Usar token para modelos privados
        low_cpu_mem_usage=True
    )
    
    tokenizer = AutoTokenizer.from_pretrained(
        model_name, 
        cache_dir=cache_dir,
        use_auth_token=token
    )
    
    return model, tokenizer
```

**⚠️ Nota**: Modelos privados requieren **Hugging Face Pro** ($9/mes)

---

## 📝 Agregar README al Modelo

Es buena práctica documentar tu modelo. Crea un archivo `README.md`:

```markdown
---
license: apache-2.0
language: es
tags:
- conversational
- gpt2
- medical
- tuberculosis
- spanish
- fine-tuned
library_name: transformers
---

# GPT-2 Spanish Fine-tuned para Tuberculosis

## Descripción

Modelo GPT-2 fine-tuned en español para conversaciones sobre tuberculosis, 
entrenado con 4000+ interacciones médico-paciente simuladas.

## Uso

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("tu-usuario/gpt2-spanish-tb-structured")
tokenizer = AutoTokenizer.from_pretrained("tu-usuario/gpt2-spanish-tb-structured")

# Generar respuesta
input_text = "¿Cuáles son los síntomas de la tuberculosis?"
inputs = tokenizer(input_text, return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

## Entrenamiento

- **Base model**: GPT-2 (Spanish)
- **Dataset**: 4000 conversaciones estructuradas sobre tuberculosis
- **Epochs**: 3
- **Batch size**: 4
- **Learning rate**: 5e-5

## Métricas

- **Perplexity**: 15.2
- **Training loss**: 1.8
- **Validation loss**: 2.1

## Casos de Uso

- Chatbot médico para información sobre tuberculosis
- Asistente virtual en centros de salud
- Sistema de triaje automatizado

## Limitaciones

- Entrenado específicamente para tuberculosis
- Respuestas basadas en datos de entrenamiento
- NO reemplaza consulta médica profesional

## Autores

- Equipo de Desarrollo - UAGRM
- Centro Médico CAÑADA DEL CARMEN

## Licencia

Apache 2.0
```

Luego súbelo:

```bash
# Crear README.md en el directorio del modelo
echo "contenido del README" > README.md

# Subir actualización
huggingface-cli upload tu-usuario/gpt2-spanish-tb-structured README.md --repo-type model
```

---

## 🔄 Actualizar el Modelo (Nueva Versión)

Cuando entrenes una versión mejorada:

```bash
# 1. Navegar al nuevo modelo
cd app/training/models/gpt2-spanish-tb-structured

# 2. Subir nueva versión
huggingface-cli upload tu-usuario/gpt2-spanish-tb-structured . \
  --repo-type model \
  --commit-message "v2.0: Improved with 5000 samples, better accuracy"

# 3. En producción, limpiar cache y reiniciar
docker-compose exec api rm -rf /app/models/*
docker-compose restart api
```

---

## 🆘 Solución de Problemas

### Error: "Repository not found"

```bash
# Crear el repositorio primero en la web
# https://huggingface.co/new

# O usar --create-pr para crear automáticamente
huggingface-cli upload tu-usuario/gpt2-spanish-tb-structured . --repo-type model --create-pr
```

### Error: "Authentication required"

```bash
# Re-autenticarse
huggingface-cli logout
huggingface-cli login
```

### Error: "Disk quota exceeded"

Tu cuenta gratuita tiene 100GB. Si excedes:
- Elimina modelos viejos que no uses
- O upgradea a Hugging Face Pro

### Descarga Lenta en Producción

```bash
# Verificar velocidad de descarga
docker-compose exec api curl -o /dev/null https://huggingface.co/speed-test

# Si es muy lento, considera usar un servidor en una región más cercana
# o comprimir el modelo con quantización
```

---

## 📊 Comandos Útiles

```bash
# Ver tus modelos
huggingface-cli list

# Ver info de un modelo
huggingface-cli info tu-usuario/gpt2-spanish-tb-structured

# Descargar modelo localmente
huggingface-cli download tu-usuario/gpt2-spanish-tb-structured

# Eliminar modelo
# (solo desde la web: https://huggingface.co/tu-usuario/gpt2-spanish-tb-structured/settings)
```

---

## ✅ Checklist Final

Antes de desplegar en producción:

- [ ] Modelo subido a Hugging Face
- [ ] README.md creado en el repositorio del modelo
- [ ] `.env` actualizado con `MODEL_NAME=tu-usuario/gpt2-spanish-tb-structured`
- [ ] `MODEL_CACHE_DIR=/app/models` configurado
- [ ] Probado localmente con `docker-compose up`
- [ ] Primera descarga completada (5-10 min)
- [ ] Cache funcionando (reinicios rápidos ~30 seg)
- [ ] Health check pasando: `curl http://localhost:8000/health`

---

## 🎓 Recursos Adicionales

- **Documentación Hugging Face Hub**: https://huggingface.co/docs/hub
- **Transformers Library**: https://huggingface.co/docs/transformers
- **Gestión de Modelos**: https://huggingface.co/docs/hub/models

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta la documentación oficial.

**Última actualización**: Octubre 2025
