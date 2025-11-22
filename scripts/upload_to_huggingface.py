import os
import time
from huggingface_hub import HfApi, create_repo, upload_folder
import argparse

def upload_model_to_hf(local_model_path, repo_name, token):
    """
    Sube un modelo local a Hugging Face Hub.
    """
    print(f"🚀 Iniciando subida del modelo desde: {local_model_path}")
    print(f"📦 Repositorio destino: {repo_name}")

    try:
        # 1. Autenticación y API
        api = HfApi(token=token)
        
        # 2. Crear el repositorio si no existe
        # El formato de repo_name debe ser "usuario/nombre-repo"
        try:
            repo_url = create_repo(repo_name, token=token, exist_ok=True)
            print(f"✅ Repositorio listo: {repo_url}")
        except Exception as e:
            print(f"⚠️ Nota sobre el repositorio: {e}")

        # 3. Subir la carpeta del modelo
        # IMPORTANTE: Ignoramos los checkpoints de entrenamiento para ahorrar espacio y tiempo.
        # Solo subimos el modelo final necesario para inferencia.
        ignore_patterns = ["checkpoint-*", "runs/*", "*.pt"]
        
        print("⬆️ Subiendo archivos del modelo final...")
        print("   (Omitiendo carpetas 'checkpoint-' y archivos de optimizador para acelerar la subida)")
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                upload_folder(
                    folder_path=local_model_path,
                    repo_id=repo_name,
                    repo_type="model",
                    token=token,
                    ignore_patterns=ignore_patterns
                )
                break # Éxito, salir del loop
            except Exception as e:
                print(f"⚠️ Intento {attempt + 1}/{max_retries} falló: {e}")
                if attempt < max_retries - 1:
                    print("⏳ Reintentando en 5 segundos...")
                    time.sleep(5)
                else:
                    raise e # Re-lanzar la excepción si fallan todos los intentos
        
        print("\n✨ ¡Subida completada exitosamente!")
        print(f"🔗 Tu modelo está disponible en: https://huggingface.co/{repo_name}")
        print("\n📝 Para usarlo en tu proyecto, actualiza tu archivo .env:")
        print(f"MODEL_NAME={repo_name}")

    except Exception as e:
        print(f"\n❌ Error durante la subida: {str(e)}")

if __name__ == "__main__":
    # Configuración por defecto basada en tu estructura de carpetas
    DEFAULT_MODEL_PATH = "app/training/models/gpt2-spanish-tb-structured"
    
    print("--- Asistente de Subida a Hugging Face ---")
    
    # Obtener token
    token = input("1. Ingresa tu Token de Hugging Face (Write access): ").strip()
    if not token:
        print("❌ El token es obligatorio.")
        exit(1)
        
    # Obtener nombre del repositorio
    username = api = HfApi(token=token).whoami()["name"]
    default_repo_name = f"{username}/gpt2-spanish-tb-structured"
    
    repo_name = input(f"2. Nombre del repositorio (Enter para '{default_repo_name}'): ").strip()
    if not repo_name:
        repo_name = default_repo_name
        
    # Obtener ruta local
    local_path = input(f"3. Ruta local del modelo (Enter para '{DEFAULT_MODEL_PATH}'): ").strip()
    if not local_path:
        local_path = DEFAULT_MODEL_PATH
        
    if not os.path.exists(local_path):
        print(f"❌ La ruta {local_path} no existe.")
        exit(1)

    upload_model_to_hf(local_path, repo_name, token)
