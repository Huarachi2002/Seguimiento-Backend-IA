# ========================================
# Multi-stage Dockerfile para FastAPI Backend
# ========================================
# Ventajas del multi-stage:
# 1. Imagen final más pequeña
# 2. Mayor seguridad (solo runtime en prod)
# 3. Build más eficiente

# ===== Stage 1: Builder =====
# Esta etapa compila y prepara las dependencias
FROM python:3.10-slim as builder

# Instalar dependencias del sistema necesarias para compilar
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar solo requirements primero (mejor caching de Docker)
COPY requirements.txt .

# Instalar dependencias en un directorio temporal
# Esto permite copiarlas a la imagen final sin build-essential
RUN pip install --no-cache-dir --user -r requirements.txt


# ===== Stage 2: Runtime =====
# Esta etapa contiene solo lo necesario para ejecutar
FROM python:3.10-slim

# Metadatos de la imagen
LABEL maintainer="tu-email@example.com"
LABEL description="WhatsApp AI Assistant Backend"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/root/.local/bin:$PATH

# Crear usuario no-root por seguridad
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app /app/logs /app/models && \
    chown -R appuser:appuser /app

# Establecer directorio de trabajo
WORKDIR /app

# Copiar dependencias compiladas del builder
COPY --from=builder /root/.local /root/.local

# Copiar código de la aplicación
COPY --chown=appuser:appuser . .

# Cambiar a usuario no-root
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
# Docker usará esto para verificar si el contenedor está saludable
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Comando de inicio
# Usar exec form para mejor manejo de signals (SIGTERM, etc.)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
