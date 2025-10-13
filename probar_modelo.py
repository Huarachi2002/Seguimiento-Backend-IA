"""
Script para probar modelos de Hugging Face antes de integrarlos.
Ejecuta: python probar_modelo.py
"""

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import sys


def verificar_gpu():
    """Verifica si CUDA está disponible."""
    print("=" * 70)
    print("🔍 VERIFICACIÓN DE SISTEMA")
    print("=" * 70)
    print()
    
    cuda_disponible = torch.cuda.is_available()
    
    if cuda_disponible:
        print(f"✅ CUDA disponible: Sí")
        print(f"✅ GPU detectada: {torch.cuda.get_device_name(0)}")
        print(f"✅ VRAM total: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        print(f"✅ VRAM disponible: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1e9:.2f} GB")
        device = "cuda"
    else:
        print(f"⚠️  CUDA no disponible, usando CPU")
        device = "cpu"
    
    print()
    return device


def probar_modelo(model_name, device, prompt_test=None):
    """
    Prueba un modelo de Hugging Face.
    
    Args:
        model_name: Nombre del modelo en Hugging Face
        device: 'cuda' o 'cpu'
        prompt_test: Texto de prueba (opcional)
    """
    print("=" * 70)
    print(f"🤖 PROBANDO MODELO: {model_name}")
    print("=" * 70)
    print()
    
    try:
        # 1. Cargar tokenizer
        print("1️⃣  Cargando tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        print("✅ Tokenizer cargado")
        print()
        
        # 2. Cargar modelo
        print("2️⃣  Cargando modelo...")
        print(f"   Esto puede tomar varios minutos la primera vez...")
        print(f"   El modelo se descargará a: ~/.cache/huggingface/")
        print()
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        
        # Mover a GPU si está disponible
        model = model.to(device)
        print(f"✅ Modelo cargado en: {device}")
        print()
        
        # 3. Verificar memoria
        if device == "cuda":
            memoria_usada = torch.cuda.memory_allocated(0) / 1e9
            print(f"📊 Memoria GPU usada por el modelo: {memoria_usada:.2f} GB")
            print()
        
        # 4. Hacer prueba de inferencia
        print("3️⃣  Generando respuesta de prueba...")
        print()
        
        if prompt_test is None:
            prompt_test = "Hola, necesito agendar una cita médica"
        
        print(f"💬 Pregunta: {prompt_test}")
        print()
        
        # Tokenizar entrada
        inputs = tokenizer.encode(
            prompt_test + tokenizer.eos_token,
            return_tensors="pt"
        ).to(device)
        
        # Generar respuesta
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=150,
                pad_token_id=tokenizer.eos_token_id,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                top_k=50
            )
        
        # Decodificar respuesta
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extraer solo la respuesta (quitar el prompt)
        if prompt_test in response:
            response = response.replace(prompt_test, "").strip()
        
        print(f"🤖 Respuesta: {response}")
        print()
        
        # 5. Estadísticas
        print("=" * 70)
        print("📊 ESTADÍSTICAS DEL MODELO")
        print("=" * 70)
        print()
        
        # Contar parámetros
        num_parametros = sum(p.numel() for p in model.parameters())
        print(f"Número de parámetros: {num_parametros:,}")
        print(f"Tamaño aproximado: {num_parametros * 2 / 1e9:.2f} GB (FP16)")
        
        if device == "cuda":
            print(f"Memoria GPU usada: {torch.cuda.memory_allocated(0) / 1e9:.2f} GB")
            print(f"Memoria GPU disponible: {(torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated(0)) / 1e9:.2f} GB")
        
        print()
        print("=" * 70)
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
        print("=" * 70)
        print()
        
        return True
        
    except Exception as e:
        print()
        print("=" * 70)
        print("❌ ERROR AL PROBAR EL MODELO")
        print("=" * 70)
        print()
        print(f"Error: {str(e)}")
        print()
        print("Posibles soluciones:")
        print("1. Verifica que el nombre del modelo sea correcto")
        print("2. Verifica tu conexión a internet")
        print("3. Verifica que tengas suficiente espacio en disco")
        print("4. Verifica que tengas suficiente VRAM (para GPU)")
        print()
        return False


def menu_principal():
    """Menú interactivo para probar modelos."""
    print()
    print("=" * 70)
    print("🤖 PROBADOR DE MODELOS DE HUGGING FACE")
    print("=" * 70)
    print()
    
    # Verificar GPU
    device = verificar_gpu()
    
    # Modelos recomendados
    modelos = {
        "1": ("microsoft/DialoGPT-small", "DialoGPT Small (350MB) - Rápido"),
        "2": ("microsoft/DialoGPT-medium", "DialoGPT Medium (800MB) - Recomendado"),
        "3": ("microsoft/DialoGPT-large", "DialoGPT Large (1.5GB) - Mejor calidad"),
        "4": ("facebook/blenderbot-400M-distill", "BlenderBot (1.6GB) - Mejor conversacional"),
        "5": ("google/flan-t5-base", "FLAN-T5 Base (900MB) - Tareas específicas"),
    }
    
    print("Modelos disponibles:")
    print()
    for key, (nombre, desc) in modelos.items():
        print(f"{key}. {desc}")
        print(f"   {nombre}")
        print()
    
    print("0. Ingresar otro modelo manualmente")
    print()
    
    # Selección
    seleccion = input("Selecciona un modelo (1-5 o 0): ").strip()
    
    if seleccion == "0":
        model_name = input("\nIngresa el nombre del modelo de Hugging Face: ").strip()
    elif seleccion in modelos:
        model_name = modelos[seleccion][0]
    else:
        print("❌ Selección inválida")
        return
    
    # Prompt personalizado
    print()
    usar_prompt_default = input("¿Usar prompt de prueba por defecto? (s/n): ").lower().strip()
    
    if usar_prompt_default == "n":
        prompt = input("Ingresa tu prompt de prueba: ").strip()
    else:
        prompt = None
    
    print()
    
    # Probar modelo
    exito = probar_modelo(model_name, device, prompt)
    
    if exito:
        print()
        print("💡 Para usar este modelo en tu aplicación:")
        print()
        print(f"   1. Abre tu archivo .env")
        print(f"   2. Cambia: MODEL_NAME={model_name}")
        print(f"   3. Cambia: DEVICE={device}")
        print(f"   4. Ejecuta: python -m app.main")
        print()


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print("\n\n👋 Prueba cancelada por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
