# 📚 Índice de Recursos - Integración Hugging Face con GPU

## 🎯 ¿Por dónde empezar?

### Si eres principiante:
1. **[INICIO_RAPIDO.md](INICIO_RAPIDO.md)** - Comienza aquí (10 pasos rápidos)
2. **[TUTORIAL_GPU_COMPLETO.md](TUTORIAL_GPU_COMPLETO.md)** - Tutorial detallado paso a paso

### Si ya sabes lo que haces:
1. **[verificar_gpu.py](#scripts-de-verificación)** - Detecta GPU y CUDA
2. **[instalar_con_gpu.ps1](#scripts-de-instalación)** - Instala todo automáticamente
3. **[.env.example](#configuración)** - Configura variables de entorno

---

## 📁 Scripts de Verificación

### `verificar_gpu.py`
**Propósito:** Detecta tu GPU, versión de CUDA, y recomienda instalación de PyTorch

**Cuándo usar:**
- Antes de instalar dependencias
- Para verificar que PyTorch detecte tu GPU
- Para diagnosticar problemas de CUDA

**Uso:**
```powershell
python verificar_gpu.py
```

**Salida:**
```
✅ GPU NVIDIA detectada: NVIDIA GeForce RTX 3060
✅ Versión de CUDA: 12.1
📦 Comando recomendado: pip install torch --index-url ...
```

---

### `verificar_sistema.py`
**Propósito:** Verificación completa del sistema antes de iniciar

**Qué verifica:**
- ✅ Versión de Python
- ✅ GPU y CUDA
- ✅ Dependencias instaladas
- ✅ Redis funcionando
- ✅ Archivo .env configurado
- ✅ Estructura del proyecto

**Cuándo usar:**
- Después de instalar todo
- Antes de iniciar la aplicación
- Para diagnosticar problemas

**Uso:**
```powershell
python verificar_sistema.py
```

**Salida:**
```
✅ Python: 3.11.5
✅ CUDA disponible: Sí
✅ Dependencias: Todas instaladas
✅ Redis: Conectado
✅ Configuración: .env correcto
✅ SISTEMA LISTO PARA INICIAR
```

---

### `probar_modelo.py`
**Propósito:** Probar modelos de Hugging Face antes de integrarlos

**Qué hace:**
- Descarga y carga el modelo
- Muestra uso de VRAM
- Genera una respuesta de prueba
- Mide velocidad de inferencia

**Cuándo usar:**
- Para elegir el modelo correcto
- Para verificar que cabe en tu GPU
- Para ver la calidad de respuestas

**Uso:**
```powershell
python probar_modelo.py
```

**Flujo interactivo:**
```
1. DialoGPT Small (350MB)
2. DialoGPT Medium (800MB) ⭐
3. DialoGPT Large (1.5GB)
Selecciona: 2

✅ Modelo cargado en cuda
📊 Memoria GPU usada: 1.62 GB
💬 Respuesta generada exitosamente
```

---

## 🔧 Scripts de Instalación

### `instalar_con_gpu.ps1`
**Propósito:** Instalación automática con detección de CUDA

**Qué hace:**
1. Detecta versión de CUDA automáticamente
2. Instala PyTorch con la versión correcta
3. Instala todas las dependencias
4. Verifica que todo funcione

**Cuándo usar:**
- Primera instalación del proyecto
- Después de cambiar de GPU
- Para reinstalar todo

**Uso:**
```powershell
.\instalar_con_gpu.ps1
```

**Proceso:**
```
Detectando CUDA... ✅ CUDA 12.1
Instalando PyTorch... ✅
Instalando dependencias... ✅
Verificando instalación... ✅
¡Listo para usar!
```

---

## 📖 Documentación

### `INICIO_RAPIDO.md`
**Para:** Principiantes que quieren arrancar rápido

**Contiene:**
- 9 pasos numerados
- Comandos copy-paste
- Soluciones rápidas a problemas comunes
- Enlaces a documentación detallada

**Tiempo estimado:** 15-30 minutos

---

### `TUTORIAL_GPU_COMPLETO.md`
**Para:** Usuarios que quieren entender cada paso

**Contiene:**
- Explicaciones detalladas
- Por qué hacer cada paso
- Qué esperar en cada paso
- Troubleshooting exhaustivo
- Ejemplos de salida

**Secciones:**
1. Verificación del Sistema
2. Instalación de Dependencias
3. Prueba de Modelos
4. Configuración del Proyecto
5. Actualización del Model Loader
6. Inicio de la Aplicación
7. Solución de Problemas

**Tiempo estimado:** 1-2 horas (primera vez)

---

### `MODELOS_RECOMENDADOS.md`
**Para:** Elegir el modelo correcto para tu caso de uso

**Contiene:**
- Tabla comparativa de modelos
- Requisitos de VRAM
- Pros y contras de cada modelo
- Recomendaciones por GPU
- Ejemplos de configuración

**Modelos cubiertos:**
- DialoGPT (Small, Medium, Large)
- BlenderBot
- FLAN-T5
- GPT-2

**Recomendación principal:** `microsoft/DialoGPT-medium`

---

### `GUIA_REDIS_COMPLETA.md`
**Para:** Entender cómo funciona Redis en el proyecto

**Contiene:**
- Arquitectura de Redis
- Implementación del cliente
- Repository pattern
- TTL y expiración
- Rate limiting
- Endpoints de debugging

---

## ⚙️ Configuración

### `.env.example`
**Propósito:** Plantilla de configuración

**Variables principales:**

**Modelo IA:**
```env
MODEL_NAME=microsoft/DialoGPT-medium
DEVICE=cuda
MAX_LENGTH=150
TEMPERATURE=0.7
TOP_P=0.9
TOP_K=50
```

**Redis:**
```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
CONVERSATION_TTL=3600
```

**Aplicación:**
```env
APP_NAME="WhatsApp AI Assistant"
ENVIRONMENT=development
LOG_LEVEL=INFO
PORT=8000
```

**Uso:**
```powershell
Copy-Item .env.example .env
notepad .env
```

---

### `requirements.txt`
**Propósito:** Lista de dependencias Python

**Dependencias principales:**
- `torch==2.6.0` - PyTorch (instalar con CUDA primero)
- `transformers==4.47.1` - Hugging Face
- `fastapi==0.115.4` - Framework web
- `redis==5.2.1` - Cliente Redis
- `pydantic-settings==2.6.1` - Configuración

**Uso:**
```powershell
pip install -r requirements.txt
```

**Nota:** Instala PyTorch con CUDA primero usando `instalar_con_gpu.ps1`

---

## 🎓 Flujo de Trabajo Recomendado

### Primera vez (Setup completo):

```
1. verificar_gpu.py          → Verificar hardware
2. instalar_con_gpu.ps1      → Instalar todo
3. Copy .env.example a .env  → Configurar
4. probar_modelo.py          → Elegir modelo
5. docker-compose up redis   → Iniciar Redis
6. verificar_sistema.py      → Verificar todo
7. uvicorn app.main:app      → Iniciar app
```

**Tiempo total:** 30-60 minutos

---

### Cambiar de modelo:

```
1. probar_modelo.py          → Probar nuevo modelo
2. Editar .env               → MODEL_NAME=nuevo_modelo
3. Reiniciar aplicación      → Ctrl+C y volver a iniciar
```

**Tiempo:** 5-10 minutos

---

### Debugging:

```
1. verificar_sistema.py      → Ver qué falla
2. Consultar TUTORIAL        → Sección "Solución de Problemas"
3. Verificar logs            → Ver errores específicos
4. Re-ejecutar instalación   → instalar_con_gpu.ps1 si es necesario
```

---

## 📊 Comparación de Modelos (Resumen)

| Modelo | Tamaño | VRAM | Velocidad | Calidad | Recomendado para |
|--------|--------|------|-----------|---------|------------------|
| **DialoGPT-small** | 350MB | 2GB+ | ⚡⚡⚡ | ⭐⭐ | GPUs limitadas, pruebas |
| **DialoGPT-medium** | 800MB | 4GB+ | ⚡⚡ | ⭐⭐⭐⭐ | **Producción general** ⭐ |
| **DialoGPT-large** | 1.5GB | 8GB+ | ⚡ | ⭐⭐⭐⭐⭐ | GPUs potentes, mejor calidad |
| BlenderBot | 1.6GB | 6GB+ | ⚡ | ⭐⭐⭐⭐⭐ | Conversaciones naturales |

---

## 🆘 Problemas Comunes

### GPU no detectada
```powershell
# Verificar drivers
nvidia-smi

# Reinstalar PyTorch
.\instalar_con_gpu.ps1
```

### Out of memory
```env
# En .env, cambiar a modelo más pequeño
MODEL_NAME=microsoft/DialoGPT-small
MAX_LENGTH=100
```

### Redis no conecta
```powershell
docker-compose up -d redis
```

### Imports no funcionan
```powershell
# Verificar entorno virtual activo
.\venv\Scripts\Activate.ps1

# Reinstalar dependencias
.\instalar_con_gpu.ps1
```

---

## 📞 Recursos Externos

- **Hugging Face Hub:** https://huggingface.co/models
- **PyTorch CUDA:** https://pytorch.org/get-started/locally/
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **Redis Docs:** https://redis.io/docs/

---

## ✅ Checklist de Producción

Antes de deploy:

- [ ] `verificar_sistema.py` pasa todas las verificaciones
- [ ] Modelo probado con datos reales
- [ ] Variables de entorno de producción configuradas
- [ ] Redis configurado con password
- [ ] PostgreSQL configurado (persistencia)
- [ ] Logs configurados
- [ ] Monitoreo de GPU activo
- [ ] Backup strategy definida
- [ ] Rate limiting configurado
- [ ] SSL/TLS habilitado

---

**Última actualización:** Enero 2024  
**Versión del proyecto:** 1.0.0  
**Mantenedor:** Tu equipo
