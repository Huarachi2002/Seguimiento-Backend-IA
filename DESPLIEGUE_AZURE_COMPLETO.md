# 🚀 Guía Definitiva: Despliegue en Azure (Opción B - Recomendada)

## ⚡ Estrategia Seleccionada

**Azure Cache for Redis + Azure Container Instance**

✅ **Ventajas**:
- Más simple de configurar
- Redis completamente manejado por Azure (sin mantenimiento)
- Más económico que Container Apps
- Alta disponibilidad automática
- Backups automáticos

📦 **Arquitectura**:
```
┌─────────────────────────────────────────┐
│   Azure Cache for Redis (Manejado)     │
│   - Puerto: 6380 (SSL)                  │
│   - Password seguro automático          │
└──────────────────┬──────────────────────┘
                   │
                   │ Conexión segura
                   │
┌──────────────────▼──────────────────────┐
│   Azure Container Instance              │
│   - FastAPI App                          │
│   - Puerto: 8000                         │
│   - Modelo: Hiachi20/gpt2-spanish-tb... │
└─────────────────────────────────────────┘
```

---

## 📋 PARTE 1: Crear Azure Cache for Redis

### **Paso 1: Acceder al Portal de Azure**

1. Abre tu navegador
2. Ve a: **https://portal.azure.com**
3. Inicia sesión con tu cuenta Microsoft

### **Paso 2: Buscar el Servicio de Redis**

1. En la **barra de búsqueda superior** (donde dice "Search resources, services, and docs")
2. Escribe: **"Azure Cache for Redis"**
3. En los resultados, click en **"Azure Cache for Redis"** (tiene un ícono rojo)

### **Paso 3: Crear Nueva Instancia de Redis**

1. Click en el botón **"+ Create"** (esquina superior izquierda)
2. Se abrirá el formulario de creación

### **Paso 4: Configurar Basics (Pestaña 1 de 6)**

**Detalles del Proyecto:**

- **Subscription**: Selecciona tu suscripción activa
- **Resource group**: 
  - Si ya tienes uno: Selecciónalo (ej: `whatsapp-ai-rg`)
  - Si no: Click en **"Create new"** 
    - Nombre: `whatsapp-ai-rg`
    - Click **OK**

**Detalles de la Instancia:**

- **DNS name**: `whatsapp-ai-redis` 
  - ⚠️ Debe ser único globalmente
  - Si ya existe, prueba: `whatsapp-ai-redis-2024`
  - Esto creará: `whatsapp-ai-redis.redis.cache.windows.net`

- **Location**: Selecciona **"East US"** 
  - ⚠️ IMPORTANTE: Usa la misma región donde crearás el Container Instance

- **Cache type**: Selecciona **"Basic C0 (250 MB Cache)"**
  - 💰 Costo: ~$0.02/hora (~$16/mes)
  - Para producción real, considera C1 o superior

**Dejar TODO lo demás como está**

Click en **"Next: Networking >"**

### **Paso 5: Configurar Networking (Pestaña 2 de 6)**

**Connectivity method:**

- Selecciona **"Public endpoint"**
  - ✅ Más fácil de configurar
  - ⚠️ Para producción avanzada, considera Private endpoint

**Firewall:**

- **Minimum TLS version**: `1.2` (por defecto, está bien)
- **Allow access only from specific IP ranges**: 
  - **NO marcar** esta opción por ahora
  - (La dejaremos abierta, pero Redis requiere password igual)

Click en **"Next: Advanced >"**

### **Paso 6: Configurar Advanced (Pestaña 3 de 6)**

**Redis version:**
- Selecciona **"6"** (la más reciente disponible)

**Non-SSL port (6379):**
- **NO marcar** esta opción
- ✅ Dejar solo SSL habilitado (puerto 6380) por seguridad

**Redis cluster (Sharding):**
- Dejar **desmarcado** (no necesario para Basic tier)

**Redis data persistence:**
- **No disponible** en Basic tier (está bien para desarrollo)

**Todo lo demás dejarlo por defecto**

Click en **"Next: Tags >"**

### **Paso 7: Configurar Tags (Pestaña 4 de 6)**

(Opcional, pero recomendado para organizar)

Click en **"+ Add"** y agrega:

| Name | Value |
|------|-------|
| `Environment` | `Production` |
| `Project` | `WhatsApp-AI` |
| `Component` | `Cache` |

Click en **"Next: Review + create >"**

### **Paso 8: Revisar y Crear (Pestaña 5 de 6)**

1. **Revisa toda la configuración**:
   - ✅ Resource group: `whatsapp-ai-rg`
   - ✅ DNS name: `whatsapp-ai-redis`
   - ✅ Location: `East US`
   - ✅ Cache type: `Basic C0`
   - ✅ TLS: `1.2`
   - ✅ Redis version: `6`

2. **Verifica el costo estimado** (abajo a la derecha):
   - Debe mostrar algo como: `~$0.02/hour`

3. Click en el botón azul **"Create"**

### **Paso 9: Esperar el Despliegue**

1. Verás una pantalla que dice **"Deployment in progress"**
2. Esto tomará **5-10 minutos** ⏱️
3. Puedes ver el progreso en tiempo real
4. Cuando esté listo, verás **"Your deployment is complete"**
5. Click en **"Go to resource"**

### **Paso 10: Obtener las Credenciales de Redis**

🔑 **MUY IMPORTANTE - Copiar y Guardar en un Bloc de Notas:**

1. En tu instancia de Redis recién creada
2. En el menú lateral izquierdo, busca **"Settings"**
3. Click en **"Access keys"** (bajo Settings)
4. Verás dos opciones: **Primary** y **Secondary**

**COPIA Y GUARDA** (click en el ícono de copiar):

```
✅ Host name: whatsapp-ai-redis.redis.cache.windows.net
✅ SSL port: 6380
✅ Primary access key: [Una cadena larga tipo: abc123XYZ789...]
```

**NO cierres esta página todavía, la necesitarás en el siguiente paso**

---

## 📦 PARTE 2: Preparar y Subir tu Imagen Docker

Ahora que tienes Redis, necesitas preparar tu aplicación.

### **Paso 11: Actualizar Configuración Local**

Abre **PowerShell** o **CMD** en tu computadora:

```powershell
# Navega a tu proyecto
cd c:\Users\PC\Desktop\UAGRM\SW2-2025\Grupal\whatsapp-ai-assistant\fastapi-backend
```

### **Paso 12: Verificar Dockerfile**

Tu Dockerfile ya está listo (lo ajustaste), solo verifica que tenga:

```dockerfile
FROM python:3.11-slim
...
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

✅ Está correcto

### **Paso 13: Construir la Imagen Docker**

En PowerShell:

```powershell
# Construir la imagen
docker build -t whatsapp-ai-assistant:latest .
```

⏱️ Esto tomará **3-5 minutos** la primera vez.

Deberías ver al final:
```
Successfully built [ID]
Successfully tagged whatsapp-ai-assistant:latest
```

### **Paso 14: Crear Azure Container Registry (ACR)**

Vuelve al **Portal de Azure**:

1. En la barra de búsqueda, escribe: **"Container registries"**
2. Click en **"Container registries"**
3. Click en **"+ Create"**

**Formulario de creación:**

**Pestaña "Basics":**

- **Subscription**: Tu suscripción
- **Resource group**: Selecciona **`whatsapp-ai-rg`** (el mismo de Redis)
- **Registry name**: `whatsappairegistry`
  - ⚠️ Solo letras minúsculas y números, sin guiones
  - ⚠️ Debe ser único globalmente
  - Si ya existe, prueba: `whatsappai2024`
- **Location**: **East US** (la misma que Redis)
- **Pricing plan**: **Basic** (más económico)
- **Zone redundancy**: Dejar deshabilitada

Click en **"Review + create"**

Click en **"Create"**

⏱️ Espera 1-2 minutos

Cuando termine, click en **"Go to resource"**

### **Paso 15: Habilitar Admin User en ACR**

1. Estás en tu **Container Registry** recién creado
2. En el menú lateral izquierdo, busca **"Settings"**
3. Click en **"Access keys"**
4. Activa el toggle **"Admin user"**
5. **COPIA Y GUARDA** en tu bloc de notas:

```
✅ Login server: whatsappairegistry.azurecr.io
✅ Username: whatsappairegistry
✅ password: [Una contraseña larga]
```

### **Paso 16: Subir la Imagen al ACR**

Vuelve a **PowerShell**:

```powershell
# 1. Etiquetar la imagen para ACR
# Reemplaza 'whatsappairegistry' si usaste otro nombre
docker tag whatsapp-ai-assistant:latest whatsappairegistry.azurecr.io/whatsapp-ai-assistant:latest

# 2. Login al ACR
# Reemplaza con TU username y password del paso anterior
docker login whatsappairegistry.azurecr.io -u whatsappairegistry -p [TU-PASSWORD]
```

Deberías ver:
```
Login Succeeded
```

```powershell
# 3. Subir la imagen
docker push whatsappairegistry.azurecr.io/whatsapp-ai-assistant:latest
```

⏱️ Esto tomará **5-15 minutos** dependiendo de tu internet.

Verás progreso:
```
Pushing [===>                ] 123MB/456MB
```

Al final:
```
latest: digest: sha256:abc123... size: 1234
```

### **Paso 17: Verificar que la Imagen se Subió**

En el **Portal de Azure**:

1. Ve a tu **Container Registry** (`whatsappairegistry`)
2. En el menú lateral, click en **"Services"**
3. Click en **"Repositories"**
4. Deberías ver: **`whatsapp-ai-assistant`**
5. Click en él
6. Deberías ver el tag: **`latest`** con fecha de hoy

✅ ¡Imagen lista en Azure!

---

## 🎯 PARTE 3: Crear Azure Container Instance con Todo Conectado

### **Paso 18: Crear Container Instance**

1. En el Portal de Azure, barra de búsqueda: **"Container instances"**
2. Click en **"Container instances"**
3. Click en **"+ Create"**

### **Paso 19: Configurar Basics (Pestaña 1 de 4)**

**Detalles del Proyecto:**

- **Subscription**: Tu suscripción
- **Resource group**: **`whatsapp-ai-rg`** (el mismo de Redis y ACR)

**Detalles del Contenedor:**

- **Container name**: `whatsapp-ai-container`
- **Region**: **East US** (misma que Redis y ACR)
- **Availability zones**: Dejar vacío
- **SKU**: Standard
- **Image source**: Selecciona **"Azure Container Registry"**

**Configuración de Imagen:**

- **Registry**: Selecciona **`whatsappairegistry`** (tu ACR)
- **Image**: Selecciona **`whatsapp-ai-assistant`**
- **Image tag**: Selecciona **`latest`**
- **OS type**: Linux (por defecto)

**Tamaño:**

- **Number of CPU cores**: `2`
- **Memory (GB)**: `4`

Click en **"Next: Networking >"**

### **Paso 20: Configurar Networking (Pestaña 2 de 4)**

**Networking type:**
- Selecciona **"Public"**

**DNS name label:**
- Escribe: `whatsapp-ai-hiachi`
  - ⚠️ Debe ser único en la región
  - Si ya existe, prueba: `whatsapp-ai-hiachi-2024`
  - Esto creará: `whatsapp-ai-hiachi.eastus.azurecontainer.io`

**Ports:**

Ya viene un puerto por defecto, déjalo y agrega:

| Port | Protocol |
|------|----------|
| 8000 | TCP |

Si hay un puerto 80 por defecto, puedes eliminarlo o dejarlo.

Click en **"Next: Advanced >"**

### **Paso 21: Configurar Advanced - Variables de Entorno (⚠️ CRÍTICO)**

Esta es la parte MÁS IMPORTANTE. Aquí conectaremos todo.

**Restart policy:**
- Selecciona **"On failure"** (o "Always" si prefieres)

**Environment variables:**

Click en **"+ Add"** para CADA una de estas variables:

**📝 COPIA EXACTAMENTE ESTAS VARIABLES:**

| Name | Value | Secure |
|------|-------|--------|
| `MODEL_NAME` | `Hiachi20/gpt2-spanish-tb-structured` | No |
| `ENVIRONMENT` | `production` | No |
| `LOG_LEVEL` | `INFO` | No |
| `DEVICE` | `cpu` | No |
| `MODEL_CACHE_DIR` | `/app/models` | No |
| `MAX_TOKENS` | `150` | No |
| `TEMPERATURE` | `0.7` | No |
| `MEDICAL_CENTER_NAME` | `CAÑADA DEL CARMEN` | No |
| `SEGUIMIENTO_SERVICE_URL` | `http://44.220.135.146:3001` | No |
| `SEGUIMIENTO_TIMEOUT` | `10` | No |

**🔑 VARIABLES DE REDIS (Usa las credenciales del Paso 10):**

| Name | Value | Secure |
|------|-------|--------|
| `REDIS_HOST` | `whatsapp-ai-redis.redis.cache.windows.net` | No |
| `REDIS_PORT` | `6380` | No |
| `REDIS_PASSWORD` | [TU PRIMARY ACCESS KEY] | **SÍ** ✅ |
| `REDIS_DB` | `0` | No |
| `SESSION_EXPIRE_TIME` | `3600` | No |

**⚠️ IMPORTANTE para REDIS_PASSWORD:**
- Click en el checkbox **"Secure"** para esta variable
- Esto la encriptará y no será visible en logs

**Command override:**
- Dejar **vacío** (usará el CMD del Dockerfile)

**Todo lo demás dejarlo por defecto**

Click en **"Next: Tags >"**

### **Paso 22: Configurar Tags (Pestaña 3 de 4)**

(Opcional)

| Name | Value |
|------|-------|
| `Environment` | `Production` |
| `Project` | `WhatsApp-AI` |
| `Component` | `API` |

Click en **"Next: Review + create >"**

### **Paso 23: Revisar y Crear (Pestaña 4 de 4)**

**📋 CHECKLIST - Verifica que TODO esté correcto:**

- ✅ Resource group: `whatsapp-ai-rg`
- ✅ Container name: `whatsapp-ai-container`
- ✅ Region: `East US`
- ✅ Image: `whatsappairegistry.azurecr.io/whatsapp-ai-assistant:latest`
- ✅ CPU: `2.0`
- ✅ Memory: `4.0 GB`
- ✅ DNS: `whatsapp-ai-hiachi`
- ✅ Port: `8000`
- ✅ Environment variables: 15 variables configuradas

**Costo estimado:**
- Debería mostrar: ~$2.50/día (~$75/mes)

Si TODO está bien, click en **"Create"**

### **Paso 24: Esperar el Despliegue**

1. Pantalla: **"Deployment in progress"**
2. ⏱️ Esto tomará **5-10 minutos**
   - Azure necesita:
     - Descargar la imagen del ACR
     - Iniciar el contenedor
     - Tu app descargará el modelo de Hugging Face
3. Cuando veas **"Your deployment is complete"**
4. Click en **"Go to resource"**

---

## ✅ PARTE 4: Verificar que TODO Funciona

### **Paso 25: Ver el Estado del Contenedor**

1. Estás en tu **Container Instance**
2. En la página de **Overview**, verás:
   - **Status**: Debe decir **"Running"**
   - **FQDN**: `whatsapp-ai-hiachi.eastus.azurecontainer.io`
   - **IP address**: Una IP pública

Si dice **"Waiting"** o **"Creating"**, espera 2-3 minutos más.

### **Paso 26: Ver los Logs (CRÍTICO)**

🔍 Aquí verás si hay errores:

1. En el menú lateral izquierdo, click en **"Containers"** (bajo Settings)
2. Click en tu contenedor (aparece el nombre)
3. Click en la pestaña **"Logs"**

**✅ Deberías ver algo como:**

```
🚀 Iniciando WhatsApp AI Assistant v1.0.0
🌍 Entorno: production
🏥 Centro Médico: CAÑADA DEL CARMEN
==========================================================
🔌 Conectando a Redis...
✅ Redis conectado: whatsapp-ai-redis.redis.cache.windows.net:6380
📦 Cargando modelo de IA: Hiachi20/gpt2-spanish-tb-structured
🖥️ Dispositivo detectado: cpu
📝 Cargando tokenizer...
🤖 Cargando modelo (esto puede tardar unos minutos)...
✅ Modelo cargado exitosamente
📊 Parámetros del modelo: 124,439,808
==========================================================
✅ Aplicación lista para recibir requests
📡 Escuchando en puerto: 8000
⏰ TTL de sesiones: 3600s
==========================================================
INFO:     Started server process [1]
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**❌ Si ves errores:**

**Error de Redis:**
```
❌ Redis no disponible - continuando sin cache
```
**Solución:** Verifica que `REDIS_PASSWORD` sea correcta del Paso 10

**Error de Modelo:**
```
❌ Error cargando el modelo: 401 Unauthorized
```
**Solución:** El modelo no existe o es privado. Verifica en Hugging Face.

**Out of Memory:**
```
Killed
```
**Solución:** Aumenta memoria a 8 GB al recrear el contenedor

### **Paso 27: Obtener la URL de tu API**

1. Ve al **Overview** de tu Container Instance
2. **COPIA** el **FQDN**: `whatsapp-ai-hiachi.eastus.azurecontainer.io`

Tu API estará en:
```
http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000
```

### **Paso 28: Probar el Health Check**

Abre tu navegador y ve a:

```
http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000/health
```

**✅ Deberías ver:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cpu",
  "version": "1.0.0"
}
```

**❌ Si no carga:**
- Espera 2 minutos más (el modelo puede estar descargándose)
- Verifica los logs del Paso 26
- Verifica que el puerto 8000 esté configurado en Networking

### **Paso 29: Probar la Documentación Interactiva**

En tu navegador:

```
http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000/docs
```

Deberías ver **Swagger UI** con todos tus endpoints.

### **Paso 30: Probar un Endpoint Real**

En Swagger UI o en el navegador:

```
http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000/chat/history/76351308
```

Si hay historial, lo verás. Si no, verás:
```json
{
  "user_id": "76351308",
  "message_count": 0,
  "messages": []
}
```

✅ ¡Funciona! Significa que Redis está conectado correctamente.

---

## 🔗 PARTE 5: Conectar tu Servicio NestJS

### **Paso 31: Actualizar Variables de Entorno en NestJS**

En tu servicio NestJS, actualiza el archivo `.env`:

```env
# Antes (desarrollo local)
# IA_SERVICE_URL=http://127.0.0.1:8000

# Ahora (producción Azure)
IA_SERVICE_URL=http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000
```

### **Paso 32: Probar desde NestJS**

Reinicia tu servicio NestJS y prueba hacer una request al historial.

**Deberías ver en los logs de NestJS:**
```
[IAService] URL: http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000/chat/history/76351308
[IAService] ✅ Historial recuperado: X mensajes
```

---

## 🎉 ¡DESPLIEGUE COMPLETADO!

### 📊 Resumen de Recursos Creados

| Recurso | Nombre | Propósito | Costo/mes |
|---------|--------|-----------|-----------|
| Resource Group | `whatsapp-ai-rg` | Contenedor de recursos | Gratis |
| Azure Cache for Redis | `whatsapp-ai-redis` | Cache y estado | ~$16 |
| Container Registry | `whatsappairegistry` | Almacén de imágenes | ~$5 |
| Container Instance | `whatsapp-ai-container` | API FastAPI | ~$75 |
| **TOTAL** | | | **~$96/mes** |

### 🌐 URLs de tu Aplicación

```
Base URL:
http://whatsapp-ai-hiachi.eastus.azurecontainer.io:8000

Endpoints:
✅ Health:    /health
✅ Docs:      /docs
✅ Chat:      /chat
✅ History:   /chat/history/{user_id}
✅ Reset:     /chat/{user_id}/reset
```

### 🔑 Credenciales para Guardar

Guarda esto en un lugar seguro:

```
Azure Cache for Redis:
- Host: whatsapp-ai-redis.redis.cache.windows.net
- Port: 6380 (SSL)
- Password: [TU PRIMARY ACCESS KEY]

Azure Container Registry:
- Server: whatsappairegistry.azurecr.io
- Username: whatsappairegistry
- Password: [TU PASSWORD DE ACR]

Container Instance:
- FQDN: whatsapp-ai-hiachi.eastus.azurecontainer.io
- IP: [IP PÚBLICA]
```

---

## 🔧 Comandos Útiles - Portal de Azure

### Ver Logs en Tiempo Real

1. Container Instance → **Containers** → Tu contenedor → **Logs**
2. Click en **"Refresh"** cada 10 segundos

### Reiniciar el Contenedor

1. Container Instance → Click en **"Restart"** (arriba)
2. Espera 1-2 minutos
3. Verifica los logs

### Ver Métricas

1. Container Instance → **Metrics** (bajo Monitoring)
2. Selecciona:
   - CPU Usage
   - Memory Usage
   - Network In/Out

### Ver Conexiones a Redis

1. Azure Cache for Redis → **Metrics**
2. Selecciona:
   - Connected Clients
   - Cache Hits
   - Cache Misses

---

## 🆘 Troubleshooting Común

| Problema | Causa | Solución |
|----------|-------|----------|
| Container status: "Terminated" | Error en el código o variables incorrectas | Ver logs, corregir, eliminar y recrear |
| "Redis connection failed" | Password incorrecta o firewall | Verificar REDIS_PASSWORD en Step 21 |
| "Out of memory" | Modelo muy grande para 4GB | Recrear con 8GB de memoria |
| Modelo no se descarga | Nombre incorrecto o privado | Verificar en Hugging Face que sea público |
| Puerto 8000 no responde | Puerto no configurado en Networking | Verificar Step 20 |
| "502 Bad Gateway" desde NestJS | Container no está corriendo | Verificar status y logs |

---

## 🔄 Actualizar tu Aplicación (Nuevas Versiones)

Cuando hagas cambios en tu código:

### Proceso Completo:

```powershell
# 1. Construir nueva versión
docker build -t whatsapp-ai-assistant:v2 .

# 2. Etiquetar
docker tag whatsapp-ai-assistant:v2 whatsappairegistry.azurecr.io/whatsapp-ai-assistant:v2

# 3. Login (si no estás logueado)
docker login whatsappairegistry.azurecr.io -u whatsappairegistry -p [PASSWORD]

# 4. Subir
docker push whatsappairegistry.azurecr.io/whatsapp-ai-assistant:v2
```

### En Azure Portal:

1. Container Instance → **Delete** (arriba)
2. Confirmar eliminación
3. Esperar 1 minuto
4. Crear nueva instancia siguiendo Pasos 18-23
5. En **Image tag**, seleccionar **"v2"** en lugar de "latest"

---

## 💰 Optimizar Costos

### Opciones para Reducir Gastos:

1. **Detener cuando no uses** (Development):
   - Container Instance → **Stop**
   - Solo pagas por almacenamiento (~$0.10/día)

2. **Usar tier inferior de Redis** (si no necesitas mucha cache):
   - Basic C0: $16/mes (actual)
   - Basic C1 con persistence: $55/mes

3. **Scheduled scaling** (avanzado):
   - Usar Azure Functions para iniciar/detener en horarios

4. **Usar Redis externo** (si ya tienes):
   - Puedes seguir usando `44.220.135.146`
   - Ahorra los $16/mes de Azure Redis

---

## 🎯 ¿TODO LISTO?

✅ **Checklist Final:**

- [ ] Redis creado y credenciales guardadas
- [ ] ACR creado y admin habilitado
- [ ] Imagen Docker construida localmente
- [ ] Imagen subida a ACR (verificado en Repositories)
- [ ] Container Instance creado
- [ ] 15 variables de entorno configuradas correctamente
- [ ] Status: "Running"
- [ ] Logs muestran "Aplicación lista para recibir requests"
- [ ] `/health` responde con `"status": "healthy"`
- [ ] `/docs` muestra Swagger UI
- [ ] NestJS configurado con nueva URL
- [ ] Prueba end-to-end exitosa

---

## 📞 Próximos Pasos

1. **Configurar HTTPS** (Producción):
   - Usar Azure Application Gateway
   - O configurar certificado SSL

2. **Configurar Monitoring**:
   - Azure Application Insights
   - Alertas de errores

3. **Configurar Backups**:
   - Snapshots de Redis
   - Backup de imágenes Docker

4. **Configurar CI/CD**:
   - GitHub Actions para auto-deploy
   - Azure DevOps Pipelines

---

¡Felicidades! 🎉 Tu aplicación FastAPI con IA está completamente desplegada en Azure con todos los servicios conectados.
