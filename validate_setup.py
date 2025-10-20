"""
Script de Validación: Dataset Estructurado
===========================================

Este script verifica que todo esté configurado correctamente
antes de entrenar el modelo con datos estructurados.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple


class ValidationChecker:
    """
    Validador de configuración para dataset estructurado.
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.successes: List[str] = []
        
        print("=" * 80)
        print("🔍 VALIDADOR DE CONFIGURACIÓN: DATASET ESTRUCTURADO")
        print("=" * 80)
        print()
    
    def check_dataset_exists(self) -> bool:
        """Verifica que el dataset estructurado exista."""
        print("📂 Verificando dataset estructurado...")
        
        dataset_path = Path("app/training/datasets/tuberculosis_structured.json")
        
        if not dataset_path.exists():
            self.errors.append(
                "❌ Dataset estructurado NO encontrado.\n"
                "   Ejecuta: python app/training/create_structured_dataset.py"
            )
            return False
        
        # Verificar contenido
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if len(data) < 10:
                self.warnings.append(
                    f"⚠️ Dataset tiene solo {len(data)} ejemplos (se recomiendan 50+)"
                )
            else:
                self.successes.append(
                    f"✅ Dataset encontrado: {len(data)} ejemplos"
                )
            
            # Verificar formato de un ejemplo
            if data:
                example = data[0]
                if 'prompt' not in example or 'completion' not in example:
                    self.errors.append(
                        "❌ Formato de dataset incorrecto (falta 'prompt' o 'completion')"
                    )
                    return False
                
                # Verificar tags estructurados
                prompt = example['prompt']
                if '<SYS>' not in prompt or '<DATA>' not in prompt:
                    self.errors.append(
                        "❌ Dataset no tiene formato estructurado (faltan tags <SYS> y <DATA>)"
                    )
                    return False
                
                self.successes.append("✅ Formato de dataset válido")
            
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Error leyendo dataset: {e}")
            return False
    
    def check_redis_connection(self) -> bool:
        """Verifica conexión a Redis."""
        print("🔌 Verificando conexión a Redis...")
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=2)
            r.ping()
            self.successes.append("✅ Redis conectado")
            return True
        except ImportError:
            self.errors.append(
                "❌ Librería 'redis' no instalada.\n"
                "   Ejecuta: pip install redis"
            )
            return False
        except Exception as e:
            self.errors.append(
                f"❌ Redis no está corriendo.\n"
                f"   Error: {e}\n"
                f"   Inicia Redis: redis-server"
            )
            return False
    
    def check_nestjs_backend(self) -> bool:
        """Verifica que NestJS backend esté corriendo."""
        print("🌐 Verificando NestJS backend...")
        
        try:
            import httpx
            
            url = "http://localhost:3001/health"
            with httpx.Client(timeout=5) as client:
                response = client.get(url)
                response.raise_for_status()
            
            self.successes.append("✅ NestJS backend conectado (puerto 3001)")
            return True
        except ImportError:
            self.errors.append(
                "❌ Librería 'httpx' no instalada.\n"
                "   Ejecuta: pip install httpx"
            )
            return False
        except Exception as e:
            self.warnings.append(
                f"⚠️ NestJS backend no responde.\n"
                f"   Esto es OK si solo vas a entrenar el modelo.\n"
                f"   Pero necesitas iniciarlo antes de probar FastAPI."
            )
            return False
    
    def check_gpu_availability(self) -> bool:
        """Verifica disponibilidad de GPU."""
        print("🎮 Verificando GPU...")
        
        try:
            import torch
            
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                vram = torch.cuda.get_device_properties(0).total_memory / 1e9
                self.successes.append(
                    f"✅ GPU disponible: {gpu_name} ({vram:.2f} GB VRAM)"
                )
                return True
            else:
                self.warnings.append(
                    "⚠️ GPU no disponible. El entrenamiento será MÁS LENTO en CPU.\n"
                    "   Tiempo estimado: 8-12 horas en CPU vs 2-4 horas en GPU."
                )
                return False
        except ImportError:
            self.errors.append(
                "❌ PyTorch no instalado.\n"
                "   Ejecuta: pip install torch"
            )
            return False
    
    def check_disk_space(self) -> bool:
        """Verifica espacio en disco."""
        print("💾 Verificando espacio en disco...")
        
        try:
            import shutil
            
            total, used, free = shutil.disk_usage(".")
            free_gb = free / (1024 ** 3)
            
            if free_gb < 5:
                self.warnings.append(
                    f"⚠️ Espacio en disco bajo: {free_gb:.2f} GB libres.\n"
                    f"   Se recomienda al menos 5 GB para el modelo entrenado."
                )
            else:
                self.successes.append(f"✅ Espacio en disco: {free_gb:.2f} GB libres")
            
            return free_gb >= 5
        except Exception as e:
            self.warnings.append(f"⚠️ No se pudo verificar espacio en disco: {e}")
            return True
    
    def check_env_file(self) -> bool:
        """Verifica archivo .env."""
        print("⚙️ Verificando archivo .env...")
        
        env_path = Path(".env")
        
        if not env_path.exists():
            self.errors.append(
                "❌ Archivo .env no encontrado.\n"
                "   Copia .env.example a .env"
            )
            return False
        
        # Leer .env
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        # Verificar MODEL_NAME
        if "MODEL_NAME" not in env_content:
            self.warnings.append(
                "⚠️ MODEL_NAME no definido en .env.\n"
                "   Después de entrenar, actualiza MODEL_NAME a:\n"
                "   MODEL_NAME=app/training/models/gpt2-spanish-tb-structured"
            )
        elif "gpt2-spanish-tb-structured" not in env_content:
            self.warnings.append(
                "⚠️ MODEL_NAME no apunta al modelo estructurado.\n"
                "   Después de entrenar, actualiza MODEL_NAME a:\n"
                "   MODEL_NAME=app/training/models/gpt2-spanish-tb-structured"
            )
        else:
            self.successes.append("✅ MODEL_NAME configurado correctamente")
        
        # Verificar NESTJS_SERVICE_URL
        if "NESTJS_SERVICE_URL" not in env_content:
            self.warnings.append(
                "⚠️ NESTJS_SERVICE_URL no definido en .env.\n"
                "   Agrega: NESTJS_SERVICE_URL=http://localhost:3001"
            )
        else:
            self.successes.append("✅ NESTJS_SERVICE_URL configurado")
        
        return True
    
    def check_python_version(self) -> bool:
        """Verifica versión de Python."""
        print("🐍 Verificando versión de Python...")
        
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            self.warnings.append(
                f"⚠️ Python {version.major}.{version.minor} detectado.\n"
                f"   Se recomienda Python 3.9+ para mejor compatibilidad."
            )
        else:
            self.successes.append(
                f"✅ Python {version.major}.{version.minor}.{version.micro}"
            )
        
        return True
    
    def check_dependencies(self) -> bool:
        """Verifica dependencias instaladas."""
        print("📦 Verificando dependencias...")
        
        required_packages = [
            ('transformers', 'pip install transformers'),
            ('torch', 'pip install torch'),
            ('datasets', 'pip install datasets'),
            ('redis', 'pip install redis'),
            ('httpx', 'pip install httpx'),
            ('fastapi', 'pip install fastapi'),
            ('uvicorn', 'pip install uvicorn')
        ]
        
        missing = []
        installed = []
        
        for package, install_cmd in required_packages:
            try:
                __import__(package)
                installed.append(package)
            except ImportError:
                missing.append((package, install_cmd))
        
        if missing:
            self.errors.append(
                "❌ Dependencias faltantes:\n" +
                "\n".join(f"   - {pkg}: {cmd}" for pkg, cmd in missing)
            )
            return False
        else:
            self.successes.append(f"✅ Todas las dependencias instaladas ({len(installed)})")
        
        return True
    
    def check_ai_service_format(self) -> bool:
        """Verifica que ai_service.py use formato estructurado."""
        print("🤖 Verificando ai_service.py...")
        
        ai_service_path = Path("app/services/ai_service.py")
        
        if not ai_service_path.exists():
            self.errors.append("❌ ai_service.py no encontrado")
            return False
        
        with open(ai_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar que tenga formato estructurado
        if '<SYS>' not in content or '<DATA>' not in content:
            self.warnings.append(
                "⚠️ ai_service.py no parece usar formato estructurado.\n"
                "   Verifica que _build_prompt() use tags <SYS> y <DATA>"
            )
            return False
        else:
            self.successes.append("✅ ai_service.py usa formato estructurado")
        
        return True
    
    def run_all_checks(self) -> bool:
        """Ejecuta todas las verificaciones."""
        checks = [
            self.check_python_version,
            self.check_dependencies,
            self.check_disk_space,
            self.check_dataset_exists,
            self.check_env_file,
            self.check_ai_service_format,
            self.check_redis_connection,
            self.check_nestjs_backend,
            self.check_gpu_availability
        ]
        
        for check in checks:
            check()
            print()
        
        return self.print_summary()
    
    def print_summary(self) -> bool:
        """Imprime resumen de validación."""
        print("=" * 80)
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 80)
        print()
        
        # Éxitos
        if self.successes:
            print("✅ ÉXITOS:")
            for success in self.successes:
                print(f"   {success}")
            print()
        
        # Advertencias
        if self.warnings:
            print("⚠️ ADVERTENCIAS:")
            for warning in self.warnings:
                print(f"   {warning}")
            print()
        
        # Errores
        if self.errors:
            print("❌ ERRORES CRÍTICOS:")
            for error in self.errors:
                print(f"   {error}")
            print()
            print("🛠️ Soluciona los errores antes de continuar.")
            return False
        
        # Sin errores
        if not self.warnings:
            print("🎉 ¡TODO CONFIGURADO CORRECTAMENTE!")
            print()
            print("📝 PRÓXIMOS PASOS:")
            print("   1. Generar dataset: python app/training/create_structured_dataset.py")
            print("   2. Limpiar Redis: redis-cli FLUSHDB")
            print("   3. Entrenar modelo: python app/training/train_gpt2_structured.py --epochs 15")
            print("   4. Actualizar .env: MODEL_NAME=app/training/models/gpt2-spanish-tb-structured")
            print("   5. Reiniciar FastAPI: python app/main.py")
        else:
            print("⚠️ CONFIGURACIÓN VÁLIDA CON ADVERTENCIAS")
            print()
            print("Puedes continuar, pero revisa las advertencias arriba.")
        
        print("=" * 80)
        
        return True


def main():
    """
    Ejecuta el validador.
    """
    checker = ValidationChecker()
    success = checker.run_all_checks()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
