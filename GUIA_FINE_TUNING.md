# 🎓 Guía Completa de Fine-Tuning para DialoGPT

## 📚 Índice
1. [¿Qué es Fine-Tuning?](#qué-es-fine-tuning)
2. [Preparación](#preparación)
3. [Proceso de Entrenamiento](#proceso-de-entrenamiento)
4. [Comparación y Pruebas](#comparación-y-pruebas)
5. [Integración en la Aplicación](#integración-en-la-aplicación)
6. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 ¿Qué es Fine-Tuning?

### Concepto Simple
Fine-Tuning es como darle un **curso especializado** a un estudiante que ya sabe hablar español. El modelo DialoGPT ya sabe conversar, pero con Fine-Tuning aprende específicamente sobre:

- ✅ Tu centro médico (CAÑADA DEL CARMEN)
- ✅ Cómo agendar citas
- ✅ El proceso de verificación de identidad
- ✅ Respuestas apropiadas a emergencias
- ✅ El tono y estilo profesional que necesitas

### Cómo Funciona

```
┌─────────────────────────────────────────────────────┐
│  MODELO BASE (DialoGPT-medium)                      │
│  - Sabe conversar en español                        │
│  - Conocimiento general                             │
│  - 354 millones de parámetros                       │
└─────────────────────────────────────────────────────┘
                    ↓
                    │ + Tu Dataset
                    │   (200 conversaciones médicas)
                    ↓
┌─────────────────────────────────────────────────────┐
│  FINE-TUNING (Entrenamiento)                        │
│  - Ajusta los pesos del modelo                      │
│  - Aprende patrones específicos                     │
│  - Duración: 2-4 horas                              │
└─────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────┐
│  MODELO PERSONALIZADO (DialoGPT-Medical)            │
│  - Especializado en conversaciones médicas          │
│  - Conoce tu flujo de citas                         │
│  - Tono consistente y profesional                   │
└─────────────────────────────────────────────────────┘
```

### Qué Cambia en el Modelo

| Aspecto | Antes (Base) | Después (Fine-Tuned) |
|---------|--------------|----------------------|
| **Respuestas** | Genéricas | Específicas de tu centro |
| **Tono** | Variable | Consistente y profesional |
| **Conocimiento** | General | Especializado en citas médicas |
| **Flujo** | Desconocido | Conoce proceso de verificación |
| **Emergencias** | Puede confundirse | Responde correctamente |

---

## 🛠️ Preparación

### PASO 1: Verificar Requisitos

```powershell
# Verificar que todo esté listo
python verificar_sistema.py
```

**Debes tener:**
- ✅ GPU NVIDIA (RTX 4060 Ti ✓)
- ✅ CUDA instalado (12.6 ✓)
- ✅ PyTorch con CUDA (✓)
- ✅ Dataset preparado (medical_conversations.json ✓)
- ✅ Espacio en disco: ~5GB libres

### PASO 2: Entender el Dataset

Tu archivo `medical_conversations.json` tiene **200 conversaciones** en formato:

```json
[
  {
    "user": "Hola, necesito una cita",
    "assistant": "¡Claro! Con gusto te ayudo..."
  }
]
```

**Calidad del Dataset:**
- ✅ **200 ejemplos** - Suficiente para fine-tuning básico
- ✅ **Variedad** - Saludos, citas, cancelaciones, emergencias
- ✅ **Tono consistente** - Profesional y amable
- ⚠️ **Ideal:** 500-1000 ejemplos (puedes agregar más después)

---

## 🚀 Proceso de Entrenamiento

### PASO 1: Ejecutar el Entrenamiento

Abre PowerShell en tu proyecto y ejecuta:

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

```

### ¿Qué significan los parámetros?

| Parámetro | Qué hace | Tu valor | Por qué |
|-----------|----------|----------|---------|
| `--epochs` | Cuántas veces recorre todo el dataset | `3` | Balance entre aprendizaje y overfitting |
| `--batch_size` | Cuántos ejemplos procesa a la vez | `4` | Ajustado a tu VRAM de 8GB |
| `--learning_rate` | Qué tan rápido aprende | `5e-5` | Estándar para fine-tuning |

### PASO 2: Monitorear el Proceso

El entrenamiento mostrará:

```
🖥️  Dispositivo: cuda
🎮 GPU: NVIDIA GeForce RTX 4060 Ti
💾 VRAM: 8.59 GB

📂 Cargando dataset desde: app/training/datasets/medical_conversations.json
✅ Cargadas 200 conversaciones
✅ Dataset procesado: 200 ejemplos
📊 Train: 180 | Eval: 20

🤖 Cargando modelo base: microsoft/DialoGPT-medium
✅ Tokenizer cargado
✅ Modelo cargado en cuda
📊 Parámetros: 354,823,168

🔤 Tokenizando dataset...
✅ Dataset tokenizado

======================================================================
🚀 INICIANDO FINE-TUNING
======================================================================
📊 Configuración:
   - Épocas: 3
   - Batch Size: 4
   - Learning Rate: 5e-05
   - Ejemplos de entrenamiento: 180
   - Ejemplos de evaluación: 20
======================================================================

🏋️  Iniciando entrenamiento...
⏰ Esto tomará aproximadamente 2-4 horas
💡 Puedes monitorear la GPU con: nvidia-smi -l 1
```

### PASO 3: Durante el Entrenamiento

En **otra terminal PowerShell**, monitorea la GPU:

```powershell
nvidia-smi -l 1
```

Verás algo como:

```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 560.94                 Driver Version: 560.94         CUDA Version: 12.6     |
|----------------------------------------------------------------------+----------------------+
| GPU  Name                  | Temperature | Power | Memory-Usage    | GPU-Util             |
|==========================================================================================|
|   0  NVIDIA GeForce RTX 4060 Ti |  65°C      | 120W  | 6500MiB/8188MiB | 95%              |
+-----------------------------------------------------------------------------------------+
```

**Indicadores saludables:**
- ✅ GPU-Util: 90-100% (está trabajando)
- ✅ Temperatura: 60-80°C (normal)
- ✅ Memory: 6-7GB usados (correcto)
- ⚠️ Si Temp > 85°C: Mejorar ventilación

### PASO 4: Logs del Entrenamiento

Cada 50 pasos verás:

```
{'loss': 2.543, 'learning_rate': 5e-05, 'epoch': 0.5}
{'loss': 2.234, 'learning_rate': 4.5e-05, 'epoch': 1.0}
{'loss': 1.987, 'learning_rate': 4e-05, 'epoch': 1.5}
{'loss': 1.756, 'learning_rate': 3.5e-05, 'epoch': 2.0}
```

**¿Qué significa?**
- **loss** (pérdida): Qué tan "perdido" está el modelo
  - ✅ Debe **bajar** con el tiempo
  - ✅ De ~3.0 a ~1.5-2.0 es excelente
  - ⚠️ Si sube, hay problema

- **epoch**: Cuántas veces ha visto todo el dataset
  - Va de 0.0 a 3.0

### PASO 5: Finalización

Al terminar verás:

```
======================================================================
✅ ENTRENAMIENTO COMPLETADO
======================================================================
📊 Métricas finales:
   - Loss de entrenamiento: 1.756
   - Tiempo total: 7234.56 segundos (2.01 horas)
======================================================================

🔍 Evaluando modelo...
======================================================================
📊 RESULTADOS DE EVALUACIÓN
======================================================================
   - Loss de evaluación: 1.834
   - Perplexity: 6.26
======================================================================

💾 Guardando modelo entrenado en: app/training/models/dialogpt-medical
✅ Modelo guardado exitosamente

======================================================================
🧪 PROBANDO GENERACIÓN DE RESPUESTAS
======================================================================

👤 Usuario: Hola, necesito una cita
🤖 Asistente: ¡Claro! Con gusto te ayudo a agendar una cita. ¿Para qué especialidad la necesitas?

👤 Usuario: Quiero cancelar mi cita
🤖 Asistente: Entiendo que necesitas cancelar tu cita. ¿Podrías decirme cuál es el motivo de la cancelación?

======================================================================
🎉 ¡PROCESO COMPLETO!
======================================================================
📁 Modelo guardado en: app/training/models/dialogpt-medical
💡 Para usarlo, actualiza tu .env:
   MODEL_NAME=app/training/models/dialogpt-medical
======================================================================
```

---

## 🔍 Comparación y Pruebas

### PASO 1: Comparar Modelos

Ejecuta el comparador:

```powershell
python app/training/train_gpt2_spanish.py
```

### PASO 2: Ver las Diferencias

El script mostrará comparaciones como:

```
================================================================================
Prueba 1/8
================================================================================

👤 USUARIO: Hola, necesito una cita

🤖 MODELO BASE:
   Hola. ¿En qué puedo ayudarte?

✨ MODELO FINE-TUNED:
   ¡Claro! Con gusto te ayudo a agendar una cita en CAÑADA DEL CARMEN. 
   ¿Para qué especialidad la necesitas?

📊 El modelo fine-tuned generó una respuesta más completa y específica
```

### PASO 3: Análisis de Mejoras

**Aspectos a observar:**

| Criterio | Modelo Base | Modelo Fine-Tuned |
|----------|-------------|-------------------|
| **Especificidad** | Genérico | Menciona el centro médico |
| **Flujo** | Sin estructura | Sigue proceso de agendamiento |
| **Tono** | Informal | Profesional y cálido |
| **Contexto** | Limitado | Entiende contexto médico |

---

## 🔄 Integración en la Aplicación

### PASO 1: Actualizar `.env`

Cambia esta línea en tu archivo `.env`:

```env
# ANTES (modelo base)
# MODEL_NAME=DeepESP/gpt2-spanish

# DESPUÉS (modelo fine-tuned)
MODEL_NAME=app/training/models/gpt2-spanish-medical
```

### PASO 2: Reiniciar la Aplicación

```powershell
# Detener el servidor (Ctrl+C)

# Reiniciar
python -m uvicorn app.main:app --reload
```

### PASO 3: Verificar que Carga el Modelo Correcto

En los logs verás:

```
🔄 Iniciando carga del modelo: app/training/models/dialogpt-medical
🖥️ Dispositivo detectado: cuda
✅ Modelo cargado exitosamente
```

### PASO 4: Probar en Postman

```http
POST http://localhost:8000/chat/
Content-Type: application/json

{
  "user_id": "+59170123456",
  "message": "Hola, necesito una cita"
}
```

**Ahora deberías ver respuestas mucho mejores:**

```json
{
  "response": "¡Claro! Con gusto te ayudo a agendar una cita en CAÑADA DEL CARMEN. ¿Para qué especialidad la necesitas?",
  "user_id": "+59170123456",
  "conversation_id": "conv_+59170123456_xxx",
  "action": "schedule_appointment",
  "params": {
    "status": "collecting_info"
  }
}
```

---

## 📊 Métricas de Éxito

### ¿Cómo saber si funcionó?

Compara estos aspectos:

#### 1. **Perplexity** (Perplejidad)
- **Qué es:** Qué tan "confundido" está el modelo
- **Antes:** ~15-20 (modelo base)
- **Después:** ~6-8 (fine-tuned)
- ✅ **Menor es mejor**

#### 2. **Calidad de Respuestas**
- ✅ Menciona el centro médico por nombre
- ✅ Usa el flujo correcto de agendamiento
- ✅ Tono consistente
- ✅ Respuestas relevantes al contexto

#### 3. **Velocidad**
- Debería mantener la misma velocidad (~0.1-0.2s por respuesta)

---

## ⚠️ Solución de Problemas

### Error: "CUDA out of memory"

**Causa:** Batch size muy grande para tu GPU

**Solución:**
```powershell
python app/training/train_model.py --epochs 3 --batch_size 2
```

### Error: "Loss no baja" o "Loss aumenta"

**Causa:** Learning rate muy alto

**Solución:**
```powershell
python app/training/train_model.py --epochs 3 --batch_size 4 --learning_rate 1e-5
```

### Error: "Modelo genera respuestas vacías"

**Causa:** Overfitting (demasiadas épocas)

**Solución:**
```powershell
python app/training/train_model.py --epochs 2 --batch_size 4
```

### Error: "RuntimeError: CUDA error"

**Solución:**
```powershell
# Limpiar caché de CUDA
python -c "import torch; torch.cuda.empty_cache()"

# Reiniciar y probar de nuevo
python app/training/train_model.py --epochs 3 --batch_size 4
```

---

## 🎓 Conceptos Técnicos Explicados

### ¿Qué son las "Épocas"?

Una **época** es una pasada completa por todo el dataset.

```
Época 1: Modelo ve las 200 conversaciones por primera vez
Época 2: Modelo ve las 200 conversaciones de nuevo (reforzando)
Época 3: Modelo ve las 200 conversaciones por tercera vez (consolidando)
```

**¿Por qué 3?**
- 1 época: Aprendizaje insuficiente
- 3 épocas: Balance perfecto
- 5+ épocas: Overfitting (memoriza en vez de aprender)

### ¿Qué es el "Batch Size"?

El **batch size** es cuántos ejemplos procesa a la vez.

```
Batch Size 4:
- Toma 4 conversaciones
- Procesa juntas
- Actualiza el modelo
- Repite con las siguientes 4
```

**Tu GPU (8GB VRAM):**
- Batch Size 2: Seguro pero más lento
- **Batch Size 4: Óptimo** ⭐
- Batch Size 8: Puede dar error de memoria

### ¿Qué es el "Learning Rate"?

El **learning rate** controla qué tan grandes son los cambios en cada paso.

```
Learning Rate Alto (1e-3):
  - Aprende rápido
  - Puede "pasarse" y no converger

Learning Rate Medio (5e-5): ⭐ RECOMENDADO
  - Aprende de forma estable
  - Balance perfecto

Learning Rate Bajo (1e-6):
  - Aprende muy lento
  - Necesita muchas épocas
```

---

## 📈 Mejoras Futuras

### 1. **Agregar más datos**

Si tienes conversaciones reales del centro:

```json
// Agregar al medical_conversations.json
{
  "user": "Conversación real de un paciente",
  "assistant": "Respuesta real que dio el personal"
}
```

Re-entrena con más datos cada 3-6 meses.

### 2. **Ajuste fino de hiperparámetros**

Experimenta con:

```powershell
# Más conservador (menos overfitting)
python app/training/train_model.py --epochs 2 --batch_size 4 --learning_rate 2e-5

# Más agresivo (aprendizaje más fuerte)
python app/training/train_model.py --epochs 4 --batch_size 4 --learning_rate 7e-5
```

### 3. **Validación con usuarios reales**

Después del fine-tuning, monitorea:
- ¿Los usuarios están satisfechos?
- ¿Las respuestas son apropiadas?
- ¿Hay casos que el modelo no maneja bien?

Agrega esos casos al dataset y re-entrena.

---

## ✅ Checklist Final

Antes de usar en producción:

- [ ] Entrenamiento completado sin errores
- [ ] Loss final < 2.0
- [ ] Perplexity < 10
- [ ] Comparación muestra mejoras claras
- [ ] Pruebas en Postman exitosas
- [ ] Respuestas apropiadas al contexto
- [ ] Modelo guardado correctamente
- [ ] `.env` actualizado
- [ ] Aplicación inicia sin errores
- [ ] Respuestas en tiempo real (< 0.5s)

---

## 🎉 ¡Éxito!

Si completaste todos los pasos, ahora tienes:

✅ Un modelo DialoGPT especializado en conversaciones médicas  
✅ Respuestas específicas de tu centro médico  
✅ Tono profesional y consistente  
✅ Mejor manejo del flujo de agendamiento  

**Próximo paso:** Integrar con WhatsApp vía n8n 🚀
