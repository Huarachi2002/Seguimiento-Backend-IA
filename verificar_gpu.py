"""
Script para verificar tu GPU y compatibilidad con CUDA.
Ejecuta: python verificar_gpu.py
"""

import sys
import subprocess


def verificar_gpu_nvidia():
    """Verifica si tienes una GPU NVIDIA y CUDA instalado."""
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE GPU Y CUDA")
    print("=" * 70)
    print()
    
    # 1. Verificar si existe nvidia-smi
    print("1️⃣ Verificando NVIDIA GPU...")
    try:
        result = subprocess.run(
            ["nvidia-smi"], 
            capture_output=True, 
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            print("✅ GPU NVIDIA detectada!")
            print()
            print(result.stdout)
            
            # Extraer información de CUDA
            if "CUDA Version:" in result.stdout:
                cuda_version = result.stdout.split("CUDA Version:")[1].split()[0]
                print(f"✅ CUDA Version detectada: {cuda_version}")
                return True, cuda_version
            else:
                print("⚠️ GPU detectada pero no se pudo determinar versión de CUDA")
                return True, "unknown"
        else:
            print("❌ No se detectó GPU NVIDIA o nvidia-smi no está disponible")
            return False, None
            
    except FileNotFoundError:
        print("❌ nvidia-smi no encontrado")
        print("   Esto significa que:")
        print("   - No tienes una GPU NVIDIA, O")
        print("   - Los drivers de NVIDIA no están instalados")
        return False, None
    except Exception as e:
        print(f"❌ Error al verificar GPU: {e}")
        return False, None


def recomendar_instalacion(tiene_gpu, cuda_version):
    """Recomienda qué versión de PyTorch instalar."""
    print()
    print("=" * 70)
    print("📦 RECOMENDACIÓN DE INSTALACIÓN DE PYTORCH")
    print("=" * 70)
    print()
    
    if not tiene_gpu:
        print("💡 Tu sistema no tiene GPU NVIDIA o CUDA no está instalado.")
        print()
        print("Opción 1: Instalar PyTorch para CPU (más lento pero funciona)")
        print("   pip install torch torchvision torchaudio")
        print()
        print("Opción 2: Instalar drivers NVIDIA y CUDA primero")
        print("   1. Descargar de: https://www.nvidia.com/Download/index.aspx")
        print("   2. Instalar CUDA Toolkit: https://developer.nvidia.com/cuda-downloads")
        print("   3. Reiniciar y volver a ejecutar este script")
        print()
        return
    
    print(f"✅ GPU NVIDIA detectada con CUDA {cuda_version}")
    print()
    
    # Determinar versión de CUDA y recomendar PyTorch
    if cuda_version.startswith("12."):
        print("📥 Para CUDA 12.x, instala PyTorch con:")
        print()
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124")
        print()
    elif cuda_version.startswith("11."):
        print("📥 Para CUDA 11.x, instala PyTorch con:")
        print()
        print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
        print()
    else:
        print("📥 Versión de CUDA no reconocida. Instala PyTorch estándar:")
        print()
        print("   pip install torch torchvision torchaudio")
        print()
    
    print("🔗 Más info: https://pytorch.org/get-started/locally/")
    print()


def verificar_pytorch_instalado():
    """Verifica si PyTorch está instalado y si detecta la GPU."""
    print()
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE PYTORCH")
    print("=" * 70)
    print()
    
    try:
        import torch
        
        print(f"✅ PyTorch instalado: versión {torch.__version__}")
        print(f"✅ CUDA disponible en PyTorch: {torch.cuda.is_available()}")
        
        if torch.cuda.is_available():
            print(f"✅ GPU detectada por PyTorch: {torch.cuda.get_device_name(0)}")
            print(f"✅ Número de GPUs disponibles: {torch.cuda.device_count()}")
            print(f"✅ Memoria total de GPU: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            print()
            print("🎉 ¡TODO LISTO! Tu GPU está configurada correctamente.")
        else:
            print("⚠️ PyTorch instalado pero no detecta CUDA")
            print("   Necesitas reinstalar PyTorch con soporte CUDA")
        
    except ImportError:
        print("❌ PyTorch no está instalado")
        print("   Instálalo usando el comando recomendado arriba")
    except Exception as e:
        print(f"❌ Error verificando PyTorch: {e}")


def main():
    """Función principal."""
    print()
    print("🚀 Este script verificará si tu sistema está listo para usar GPU")
    print()
    
    # Verificar GPU
    tiene_gpu, cuda_version = verificar_gpu_nvidia()
    
    # Recomendar instalación
    recomendar_instalacion(tiene_gpu, cuda_version)
    
    # Verificar PyTorch si está instalado
    verificar_pytorch_instalado()
    
    print()
    print("=" * 70)
    print()


if __name__ == "__main__":
    main()
