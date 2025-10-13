# ====================================================================
# SCRIPT DE INSTALACIÓN PARA GPU
# ====================================================================
# Ejecuta: .\instalar_con_gpu.ps1

Write-Host "`n" -NoNewline
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "🚀 INSTALACIÓN DE DEPENDENCIAS CON SOPORTE GPU" -ForegroundColor Cyan
Write-Host "=" -ForegroundColor Cyan -NoNewline; Write-Host ("=" * 69) -ForegroundColor Cyan
Write-Host "`n"

# Verificar que el entorno virtual está activado
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️  Entorno virtual no activado" -ForegroundColor Yellow
    Write-Host "   Activando entorno virtual..." -ForegroundColor Yellow
    .\venv\Scripts\Activate
}

Write-Host "✅ Entorno virtual activado" -ForegroundColor Green
Write-Host "`n"

# Paso 1: Actualizar pip
Write-Host "1️⃣  Actualizando pip, setuptools y wheel..." -ForegroundColor Yellow
python -m pip install --upgrade pip setuptools wheel
Write-Host "✅ Herramientas actualizadas" -ForegroundColor Green
Write-Host "`n"

# Paso 2: Limpiar caché
Write-Host "2️⃣  Limpiando caché de pip..." -ForegroundColor Yellow
pip cache purge
Write-Host "✅ Caché limpiado" -ForegroundColor Green
Write-Host "`n"

# Paso 3: Detectar versión de CUDA
Write-Host "3️⃣  Detectando versión de CUDA..." -ForegroundColor Yellow

try {
    $nvidiaOutput = nvidia-smi 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ GPU NVIDIA detectada" -ForegroundColor Green
        
        # Extraer versión de CUDA
        if ($nvidiaOutput -match "CUDA Version: (\d+\.\d+)") {
            $cudaVersion = $matches[1]
            Write-Host "✅ CUDA Version: $cudaVersion" -ForegroundColor Green
            
            # Determinar URL de PyTorch según versión CUDA
            if ($cudaVersion -match "^12\.") {
                $torchUrl = "https://download.pytorch.org/whl/cu124"
                $cudaShort = "cu124"
                Write-Host "📦 Usando PyTorch para CUDA 12.x" -ForegroundColor Cyan
            }
            elseif ($cudaVersion -match "^11\.") {
                $torchUrl = "https://download.pytorch.org/whl/cu118"
                $cudaShort = "cu118"
                Write-Host "📦 Usando PyTorch para CUDA 11.x" -ForegroundColor Cyan
            }
            else {
                $torchUrl = "https://download.pytorch.org/whl/cpu"
                $cudaShort = "cpu"
                Write-Host "⚠️  Versión CUDA no reconocida, usando CPU" -ForegroundColor Yellow
            }
        }
        else {
            $torchUrl = "https://download.pytorch.org/whl/cpu"
            $cudaShort = "cpu"
            Write-Host "⚠️  No se pudo detectar versión CUDA, usando CPU" -ForegroundColor Yellow
        }
    }
    else {
        $torchUrl = "https://download.pytorch.org/whl/cpu"
        $cudaShort = "cpu"
        Write-Host "⚠️  GPU no detectada, usando CPU" -ForegroundColor Yellow
    }
}
catch {
    $torchUrl = "https://download.pytorch.org/whl/cpu"
    $cudaShort = "cpu"
    Write-Host "⚠️  Error detectando GPU, usando CPU" -ForegroundColor Yellow
}

Write-Host "`n"

# Paso 4: Instalar PyTorch
Write-Host "4️⃣  Instalando PyTorch ($cudaShort)..." -ForegroundColor Yellow
Write-Host "   Esto puede tomar varios minutos..." -ForegroundColor Gray

if ($cudaShort -eq "cpu") {
    pip install torch torchvision torchaudio
}
else {
    pip install torch torchvision torchaudio --index-url $torchUrl
}

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ PyTorch instalado correctamente" -ForegroundColor Green
}
else {
    Write-Host "❌ Error instalando PyTorch" -ForegroundColor Red
    exit 1
}
Write-Host "`n"

# Paso 5: Instalar dependencias principales
Write-Host "5️⃣  Instalando dependencias principales..." -ForegroundColor Yellow

$dependencias = @(
    "fastapi==0.115.4",
    "uvicorn[standard]==0.32.1",
    "pydantic==2.10.3",
    "pydantic-settings==2.6.1",
    "transformers==4.47.1",
    "accelerate",
    "sqlalchemy==2.0.36",
    "alembic==1.14.0",
    "psycopg2-binary==2.9.10",
    "redis==5.2.1",
    "httpx==0.28.1",
    "aiohttp==3.11.10",
    "python-dotenv==1.0.1",
    "python-multipart==0.0.20",
    "python-jose[cryptography]==3.3.0",
    "passlib[bcrypt]==1.7.4",
    "pytest==8.3.4",
    "pytest-asyncio==0.24.0",
    "black==24.10.0"
)

foreach ($dep in $dependencias) {
    Write-Host "   Instalando $dep..." -ForegroundColor Gray
    pip install $dep --quiet
}

Write-Host "✅ Dependencias principales instaladas" -ForegroundColor Green
Write-Host "`n"

# Paso 6: Verificar instalación
Write-Host "6️⃣  Verificando instalación..." -ForegroundColor Yellow

python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"No detectada\"}')"

Write-Host "`n"
Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host ("=" * 69) -ForegroundColor Green
Write-Host "✅ INSTALACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "=" -ForegroundColor Green -NoNewline; Write-Host ("=" * 69) -ForegroundColor Green
Write-Host "`n"

Write-Host "📝 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Ejecuta: python verificar_gpu.py" -ForegroundColor White
Write-Host "   2. Configura tu .env con el modelo que quieras usar" -ForegroundColor White
Write-Host "   3. Ejecuta: python -m app.main" -ForegroundColor White
Write-Host "`n"
