"""
Script de verificación completa del sistema antes de iniciar.
Verifica: GPU, PyTorch, Redis, dependencias, y configuración.

Ejecuta: python verificar_sistema.py
"""

import sys
import os
from pathlib import Path


def print_header(text):
    """Imprime un encabezado formateado."""
    print()
    print("=" * 70)
    print(text.center(70))
    print("=" * 70)
    print()


def print_check(passed, message):
    """Imprime un resultado de verificación."""
    icon = "✅" if passed else "❌"
    print(f"{icon} {message}")


def print_info(message):
    """Imprime información adicional."""
    print(f"   ℹ️  {message}")


def verificar_python():
    """Verifica la versión de Python."""
    print_header("1. VERIFICACIÓN DE PYTHON")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.minor}"
    
    print(f"Versión de Python: {sys.version}")
    print()
    
    # Verificar versión recomendada
    if version.major == 3 and 9 <= version.minor <= 12:
        print_check(True, f"Versión de Python recomendada ({version.major}.{version.minor})")
        return True
    elif version.major == 3 and version.minor == 13:
        print_check(False, "Python 3.13 puede tener problemas de compatibilidad")
        print_info("Recomendamos Python 3.11 o 3.12")
        return True  # Permitir continuar pero con advertencia
    else:
        print_check(False, "Versión de Python no recomendada")
        print_info("Necesitas Python 3.9-3.12")
        return False


def verificar_gpu():
    """Verifica CUDA y GPU."""
    print_header("2. VERIFICACIÓN DE GPU Y CUDA")
    
    try:
        import torch
    except ImportError:
        print_check(False, "PyTorch no está instalado")
        print_info("Ejecuta: .\\instalar_con_gpu.ps1")
        return False
    
    print(f"PyTorch versión: {torch.__version__}")
    print()
    
    # Verificar CUDA
    cuda_disponible = torch.cuda.is_available()
    
    if cuda_disponible:
        print_check(True, "CUDA disponible")
        print_info(f"GPU: {torch.cuda.get_device_name(0)}")
        
        vram_total = torch.cuda.get_device_properties(0).total_memory / 1e9
        print_info(f"VRAM Total: {vram_total:.2f} GB")
        
        cuda_version = torch.version.cuda
        print_info(f"CUDA Version: {cuda_version}")
        
        # Recomendaciones según VRAM
        print()
        if vram_total < 4:
            print("   ⚠️  VRAM baja (<4GB) - Usa DialoGPT-small")
        elif vram_total < 8:
            print("   ✅ VRAM adecuada (4-8GB) - Usa DialoGPT-medium")
        else:
            print("   ✅ VRAM excelente (8GB+) - Puedes usar DialoGPT-large")
        
        return True
    else:
        print_check(False, "CUDA no disponible")
        print_info("Usarás CPU (más lento)")
        print_info("Para usar GPU:")
        print_info("  1. Instala drivers NVIDIA")
        print_info("  2. Reinstala PyTorch con CUDA")
        print_info("  3. Ejecuta: .\\instalar_con_gpu.ps1")
        return True  # No es error crítico, puede usar CPU


def verificar_dependencias():
    """Verifica que las dependencias estén instaladas."""
    print_header("3. VERIFICACIÓN DE DEPENDENCIAS")
    
    dependencias = {
        "torch": "PyTorch",
        "transformers": "Transformers",
        "fastapi": "FastAPI",
        "uvicorn": "Uvicorn",
        "redis": "Redis",
        "pydantic": "Pydantic",
        "pydantic_settings": "Pydantic Settings",
    }
    
    todas_ok = True
    
    for modulo, nombre in dependencias.items():
        try:
            __import__(modulo)
            print_check(True, f"{nombre} instalado")
        except ImportError:
            print_check(False, f"{nombre} NO instalado")
            todas_ok = False
    
    print()
    
    if not todas_ok:
        print("💡 Instala las dependencias faltantes:")
        print("   .\\instalar_con_gpu.ps1")
        print("   o")
        print("   pip install -r requirements.txt")
    
    return todas_ok


def verificar_redis():
    """Verifica conexión a Redis."""
    print_header("4. VERIFICACIÓN DE REDIS")
    
    try:
        import redis
    except ImportError:
        print_check(False, "Biblioteca redis no instalada")
        return False
    
    try:
        # Intentar conexión a Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        r.ping()
        print_check(True, "Redis está corriendo y accesible")
        
        # Obtener info
        info = r.info()
        print_info(f"Versión: {info.get('redis_version', 'desconocida')}")
        print_info(f"Memoria usada: {info.get('used_memory_human', 'desconocida')}")
        
        r.close()
        return True
        
    except redis.ConnectionError:
        print_check(False, "No se puede conectar a Redis")
        print_info("Inicia Redis con: docker-compose up -d redis")
        return False
    except Exception as e:
        print_check(False, f"Error al verificar Redis: {e}")
        return False


def verificar_configuracion():
    """Verifica que exista el archivo .env."""
    print_header("5. VERIFICACIÓN DE CONFIGURACIÓN")
    
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    if env_path.exists():
        print_check(True, "Archivo .env existe")
        
        # Leer y verificar configuración importante
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                contenido = f.read()
            
            # Verificar configuraciones clave
            configs = {
                "MODEL_NAME": "Nombre del modelo",
                "DEVICE": "Dispositivo (cuda/cpu)",
                "REDIS_HOST": "Host de Redis",
                "REDIS_PORT": "Puerto de Redis",
            }
            
            print()
            for key, desc in configs.items():
                if key in contenido:
                    # Extraer valor
                    for line in contenido.split('\n'):
                        if line.startswith(key):
                            valor = line.split('=', 1)[1].strip()
                            print_info(f"{desc}: {valor}")
                            break
                else:
                    print(f"   ⚠️  {desc} no configurado")
            
        except Exception as e:
            print(f"   ⚠️  Error al leer .env: {e}")
        
        return True
    else:
        print_check(False, "Archivo .env no existe")
        
        if env_example_path.exists():
            print_info("Copia .env.example a .env:")
            print_info("  Copy-Item .env.example .env")
        else:
            print_info("Archivo .env.example tampoco existe")
        
        return False


def verificar_estructura():
    """Verifica que la estructura del proyecto esté correcta."""
    print_header("6. VERIFICACIÓN DE ESTRUCTURA")
    
    directorios_requeridos = [
        "app",
        "app/api",
        "app/core",
        "app/domain",
        "app/infrastructure",
        "app/infrastructure/ai",
        "app/infrastructure/redis",
        "app/services",
    ]
    
    archivos_requeridos = [
        "app/main.py",
        "app/core/config.py",
        "app/infrastructure/ai/model_loader.py",
        "requirements.txt",
    ]
    
    todas_ok = True
    
    for directorio in directorios_requeridos:
        path = Path(directorio)
        if path.exists() and path.is_dir():
            print_check(True, f"Directorio: {directorio}")
        else:
            print_check(False, f"Directorio faltante: {directorio}")
            todas_ok = False
    
    print()
    
    for archivo in archivos_requeridos:
        path = Path(archivo)
        if path.exists() and path.is_file():
            print_check(True, f"Archivo: {archivo}")
        else:
            print_check(False, f"Archivo faltante: {archivo}")
            todas_ok = False
    
    return todas_ok


def generar_reporte():
    """Genera un reporte completo de verificación."""
    print()
    print("=" * 70)
    print("INICIANDO VERIFICACIÓN COMPLETA DEL SISTEMA".center(70))
    print("=" * 70)
    
    resultados = {
        "Python": verificar_python(),
        "GPU/CUDA": verificar_gpu(),
        "Dependencias": verificar_dependencias(),
        "Redis": verificar_redis(),
        "Configuración": verificar_configuracion(),
        "Estructura": verificar_estructura(),
    }
    
    # Resumen final
    print_header("RESUMEN DE VERIFICACIÓN")
    
    total = len(resultados)
    aprobados = sum(1 for ok in resultados.values() if ok)
    
    for componente, ok in resultados.items():
        print_check(ok, componente)
    
    print()
    print(f"Resultado: {aprobados}/{total} verificaciones pasadas")
    print()
    
    if aprobados == total:
        print("=" * 70)
        print("✅ SISTEMA LISTO PARA INICIAR".center(70))
        print("=" * 70)
        print()
        print("Siguiente paso:")
        print("   python -m uvicorn app.main:app --reload")
        print()
    else:
        print("=" * 70)
        print("⚠️  ALGUNAS VERIFICACIONES FALLARON".center(70))
        print("=" * 70)
        print()
        print("Revisa los errores arriba y corrígelos antes de continuar.")
        print()
        print("Ayuda:")
        print("   - Para instalar dependencias: .\\instalar_con_gpu.ps1")
        print("   - Para configurar .env: Copy-Item .env.example .env")
        print("   - Para iniciar Redis: docker-compose up -d redis")
        print("   - Tutorial completo: TUTORIAL_GPU_COMPLETO.md")
        print()
    
    return aprobados == total


if __name__ == "__main__":
    try:
        exito = generar_reporte()
        sys.exit(0 if exito else 1)
    except KeyboardInterrupt:
        print("\n\n👋 Verificación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
        sys.exit(1)
