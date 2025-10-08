# ====================================
# Script de Inicio Rápido con Redis
# ====================================
# Este script te ayuda a verificar que Redis está configurado correctamente

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "🔴 Redis - Verificación Rápida" -ForegroundColor Cyan
Write-Host "==================================`n" -ForegroundColor Cyan

# 1. Verificar si Redis está corriendo
Write-Host "1️⃣  Verificando Redis..." -ForegroundColor Yellow

try {
    # Intentar conectar a Redis
    $redisTest = redis-cli ping 2>&1
    
    if ($redisTest -match "PONG") {
        Write-Host "   ✅ Redis está corriendo en localhost:6379" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Redis no responde" -ForegroundColor Red
        Write-Host "   ℹ️  Para iniciar Redis:" -ForegroundColor Yellow
        Write-Host "      - Con Docker: docker run -d --name redis -p 6379:6379 redis:7-alpine" -ForegroundColor Gray
        Write-Host "      - Con WSL: sudo service redis-server start" -ForegroundColor Gray
        Write-Host "      - Con Docker Compose: docker-compose up -d redis`n" -ForegroundColor Gray
        exit 1
    }
} catch {
    Write-Host "   ❌ redis-cli no encontrado" -ForegroundColor Red
    Write-Host "   ℹ️  Redis puede estar corriendo pero redis-cli no está instalado" -ForegroundColor Yellow
    Write-Host "   ℹ️  Intenta con Docker: docker exec -it whatsapp-ai-redis redis-cli ping`n" -ForegroundColor Yellow
}

# 2. Verificar archivo .env
Write-Host "`n2️⃣  Verificando archivo .env..." -ForegroundColor Yellow

if (Test-Path ".env") {
    Write-Host "   ✅ Archivo .env encontrado" -ForegroundColor Green
    
    # Leer REDIS_URL
    $envContent = Get-Content ".env"
    $redisUrl = $envContent | Where-Object { $_ -match "^REDIS_URL=" }
    
    if ($redisUrl) {
        Write-Host "   ✅ REDIS_URL configurado: $($redisUrl -replace 'REDIS_URL=', '')" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  REDIS_URL no encontrado en .env" -ForegroundColor Yellow
        Write-Host "   ℹ️  Agrega: REDIS_URL=redis://localhost:6379/0" -ForegroundColor Gray
    }
} else {
    Write-Host "   ⚠️  Archivo .env no encontrado" -ForegroundColor Yellow
    Write-Host "   ℹ️  Copia .env.example a .env:" -ForegroundColor Gray
    Write-Host "      cp .env.example .env`n" -ForegroundColor Gray
}

# 3. Verificar dependencias de Python
Write-Host "`n3️⃣  Verificando dependencias de Python..." -ForegroundColor Yellow

try {
    $pythonTest = python -c "import redis; print('OK')" 2>&1
    
    if ($pythonTest -match "OK") {
        Write-Host "   ✅ Paquete redis-py instalado" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Paquete redis no encontrado" -ForegroundColor Red
        Write-Host "   ℹ️  Instalar con: pip install -r requirements.txt`n" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  No se pudo verificar (Python no encontrado)" -ForegroundColor Yellow
}

# 4. Test de conexión Python
Write-Host "`n4️⃣  Test de conexión Python a Redis..." -ForegroundColor Yellow

$pythonScript = @"
import redis
try:
    r = redis.from_url('redis://localhost:6379/0', decode_responses=True)
    r.ping()
    print('✅ Conexión exitosa')
    
    # Test básico
    r.set('test_key', 'hello_redis', ex=10)
    value = r.get('test_key')
    print(f'✅ Test SET/GET: {value}')
    
    r.delete('test_key')
    print('✅ Test DELETE: OK')
    
except redis.ConnectionError as e:
    print(f'❌ Error de conexión: {e}')
except Exception as e:
    print(f'❌ Error: {e}')
"@

try {
    python -c $pythonScript
} catch {
    Write-Host "   ⚠️  No se pudo ejecutar test de Python" -ForegroundColor Yellow
}

# 5. Información de configuración
Write-Host "`n5️⃣  Configuración recomendada para .env:" -ForegroundColor Yellow
Write-Host "   " -NoNewline
Write-Host "# Redis" -ForegroundColor Gray
Write-Host "   " -NoNewline
Write-Host "REDIS_URL=redis://localhost:6379/0" -ForegroundColor Cyan
Write-Host "   " -NoNewline
Write-Host "REDIS_PASSWORD=" -ForegroundColor Cyan
Write-Host "   " -NoNewline
Write-Host "SESSION_EXPIRE_TIME=3600  # 1 hora" -ForegroundColor Cyan

# 6. Siguientes pasos
Write-Host "`n6️⃣  Siguientes pasos:" -ForegroundColor Yellow
Write-Host "   1. Asegúrate de que Redis está corriendo" -ForegroundColor White
Write-Host "   2. Configura REDIS_URL en tu archivo .env" -ForegroundColor White
Write-Host "   3. Inicia la aplicación:" -ForegroundColor White
Write-Host "      uvicorn app.main:app --reload" -ForegroundColor Cyan
Write-Host "   4. Prueba el endpoint de Redis:" -ForegroundColor White
Write-Host "      http://localhost:8000/redis/test" -ForegroundColor Cyan

# 7. Comandos útiles
Write-Host "`n7️⃣  Comandos útiles:" -ForegroundColor Yellow
Write-Host "   # Conectar a Redis CLI:" -ForegroundColor Gray
Write-Host "   redis-cli" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # Ver todas las claves:" -ForegroundColor Gray
Write-Host "   redis-cli KEYS '*'" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # Ver conversaciones activas:" -ForegroundColor Gray
Write-Host "   redis-cli KEYS 'conversation:*'" -ForegroundColor Cyan
Write-Host ""
Write-Host "   # Limpiar Redis (CUIDADO):" -ForegroundColor Gray
Write-Host "   redis-cli FLUSHDB" -ForegroundColor Cyan

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "✅ Verificación Completada" -ForegroundColor Green
Write-Host "==================================`n" -ForegroundColor Cyan

# Preguntar si quiere iniciar la app
$response = Read-Host "¿Quieres iniciar la aplicación ahora? (s/n)"
if ($response -eq "s" -or $response -eq "S") {
    Write-Host "`n🚀 Iniciando aplicación...`n" -ForegroundColor Green
    uvicorn app.main:app --reload
}
