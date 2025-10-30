# ========================================
# Multi-stage Dockerfile para FastAPI Backend con AI
# ========================================
# Optimizado para Python 3.10 + Transformers + Redis
# Ventajas del multi-stage:
# 1. Imagen final más pequeña (~500MB vs 2GB+)
# 2. Mayor seguridad (solo runtime en prod)
# 3. Build más eficiente con caching de layers

# ===== Stage 1: Builder =====
# Esta etapa compila y prepara las dependencias
FROM python:3.10-slim as builder

# Instalar dependencias del sistema necesarias para compilar
# - build-essential: Para compilar paquetes de Python con extensiones C
# - curl: Para health checks
# - git: Necesario para algunos paquetes de PyPI
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo requirements primero (mejor caching de Docker)
# Si requirements.txt no cambia, Docker usa la capa cacheada
COPY requirements.txt .

# Instalar dependencias en un directorio temporal
# --user: Instala en ~/.local (fácil de copiar a stage 2)
# --no-cache-dir: No guarda cache de pip (reduce tamaño)
# --upgrade: Asegura versiones más recientes
RUN pip install --no-cache-dir --user --upgrade pip setuptools wheel && \
    pip install --no-cache-dir --user -r requirements.txt


# ===== Stage 2: Runtime =====
# Esta etapa contiene solo lo necesario para ejecutar
FROM python:3.10-slim

# Metadatos de la imagen (útil para registro y debugging)
LABEL maintainer="whatsapp-ai-assistant@uagrm.com"
LABEL description="WhatsApp AI Assistant Backend con Redis y Transformers"
LABEL version="1.0.0"
LABEL python-version="3.10"

# Variables de entorno importantes
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH \
    # Configuración de Hugging Face
    HF_HOME=/app/models \
    TRANSFORMERS_CACHE=/app/models \
    # Desactivar telemetría de Hugging Face (opcional)
    HF_HUB_DISABLE_TELEMETRY=1 \
    # Optimizaciones de PyTorch
    OMP_NUM_THREADS=4 \
    MKL_NUM_THREADS=4

# Instalar solo las dependencias de runtime necesarias
# - curl: Para health checks
# - libgomp1: Para OpenMP (usado por PyTorch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root por seguridad
# NUNCA ejecutes aplicaciones como root en producción
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/models && \
    chown -R appuser:appuser /app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar dependencias compiladas del builder
# Cambiar de /root/.local a /home/appuser/.local
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

COPY app/training/models/gpt2-spanish-tb-structured /app/training/models/gpt2-spanish-tb-structured

# Copiar código de la aplicación
# --chown asegura que appuser sea dueño de los archivos
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root ANTES de ejecutar la app
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
# Docker usará esto para verificar si el contenedor está saludable
# - interval: Cada cuánto verificar
# - timeout: Tiempo máximo de espera
# - start-period: Tiempo de gracia al inicio (para descargar modelo)
# - retries: Intentos antes de marcar como unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
# Usar exec form para mejor manejo de signals (SIGTERM, etc.)
# El modelo se descargará automáticamente en el primer request
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
