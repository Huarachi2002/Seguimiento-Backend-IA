"""
Script de Comparación: GPT-2 Base vs Fine-Tuned
================================================

Compara respuestas del modelo base GPT-2 español vs el modelo fine-tuned
con conversaciones médicas.
"""

import torch
import logging
from transformers import GPT2LMHeadModel, GPT2Tokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelComparator:
    """Comparador de modelos GPT-2."""
    
    def __init__(self, base_model_name: str, finetuned_model_path: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"🖥️  Dispositivo: {self.device}")
        
        # Cargar modelo base
        logger.info(f"📦 Cargando modelo BASE: {base_model_name}")
        self.base_tokenizer = GPT2Tokenizer.from_pretrained(base_model_name)
        self.base_model = GPT2LMHeadModel.from_pretrained(base_model_name)
        
        # Configurar pad_token
        if self.base_tokenizer.pad_token is None:
            self.base_tokenizer.pad_token = self.base_tokenizer.eos_token
            self.base_tokenizer.pad_token_id = self.base_tokenizer.eos_token_id
        
        self.base_model.to(self.device)
        self.base_model.eval()
        logger.info("✅ Modelo BASE cargado")
        
        # Cargar modelo fine-tuned
        logger.info(f"📦 Cargando modelo FINE-TUNED: {finetuned_model_path}")
        self.ft_tokenizer = GPT2Tokenizer.from_pretrained(finetuned_model_path)
        self.ft_model = GPT2LMHeadModel.from_pretrained(finetuned_model_path)
        
        # Configurar pad_token
        if self.ft_tokenizer.pad_token is None:
            self.ft_tokenizer.pad_token = self.ft_tokenizer.eos_token
            self.ft_tokenizer.pad_token_id = self.ft_tokenizer.eos_token_id
        
        self.ft_model.to(self.device)
        self.ft_model.eval()
        logger.info("✅ Modelo FINE-TUNED cargado")
    
    def generate_response(self, model, tokenizer, prompt: str, max_tokens: int = 80) -> str:
        """
        Genera respuesta con el modelo dado.
        
        IMPORTANTE: Usa el mismo formato que el entrenamiento.
        El prompt debe incluir el contexto de sistema completo.
        """
        
        # Formatear prompt con contexto de sistema (igual que en entrenamiento)
        formatted_prompt = (
            "Eres un asistente virtual EXCLUSIVO del servicio de Tuberculosis del centro de salud CAÑADA DEL CARMEN.\n\n"
            "REGLAS IMPORTANTES:\n"
            "1. SOLO atiendes consultas sobre TUBERCULOSIS\n"
            "2. Máximo 2 oraciones por respuesta\n"
            "3. Usa el nombre del paciente si lo conoces\n"
            "4. Sé profesional y empático\n"
            "5. Si preguntan por otro servicio, redirige amablemente\n\n"
            f"Paciente: {prompt}\n"
            "Asistente:"
        )
        
        # Tokenizar
        inputs = tokenizer(
            formatted_prompt,
            return_tensors="pt",
            padding=True,
            return_attention_mask=True
        )
        
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)
        
        # Generar
        with torch.no_grad():
            outputs = model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_tokens,
                temperature=0.8,
                do_sample=True,
                top_p=0.92,
                top_k=50,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
                no_repeat_ngram_size=3,
                repetition_penalty=1.3,
                num_return_sequences=1
            )
        
        # Decodificar solo tokens nuevos
        response = tokenizer.decode(
            outputs[0][input_ids.shape[1]:],
            skip_special_tokens=True
        )
        
        # Limpiar (solo hasta primer salto de línea o punto final doble)
        response = response.split("\n")[0].strip()
        
        return response
    
    def compare(self, test_prompts: list):
        """Compara ambos modelos con los prompts de prueba."""
        
        logger.info("")
        logger.info("=" * 80)
        logger.info("🔍 COMPARACIÓN DE MODELOS")
        logger.info("=" * 80)
        
        for idx, prompt in enumerate(test_prompts, 1):
            print("\n" + "=" * 80)
            print(f"Prueba {idx}/{len(test_prompts)}")
            print("=" * 80)
            print(f"\n👤 USUARIO: {prompt}\n")
            
            # Respuesta del modelo base
            base_response = self.generate_response(self.base_model, self.base_tokenizer, prompt)
            print(f"🤖 MODELO BASE:")
            print(f"   {base_response}\n")
            
            # Respuesta del modelo fine-tuned
            ft_response = self.generate_response(self.ft_model, self.ft_tokenizer, prompt)
            print(f"✨ MODELO FINE-TUNED:")
            print(f"   {ft_response}\n")
            
            # Comparar longitud
            if len(ft_response) > len(base_response):
                print("📊 El modelo fine-tuned generó una respuesta más completa")
            elif len(ft_response) < len(base_response):
                print("📊 El modelo base generó una respuesta más completa")
            else:
                print("📊 Ambas respuestas tienen longitud similar")
            
            input("\n⏸️  Presiona ENTER para continuar...")
        
        print("\n" + "=" * 80)
        print("✅ Comparación completada")
        print("=" * 80)


def main():
    """Función principal."""
    
    # Configuración
    BASE_MODEL = "DeepESP/gpt2-spanish"
    FINETUNED_MODEL = "app/training/models/gpt2-spanish-medical"
    
    # Prompts de prueba
    TEST_PROMPTS = [
        "Hola, necesito una cita",
        "Quiero cancelar mi cita",
        "Para odontología",
        "Tengo mucho dolor de cabeza",
        "Qué especialidades tienen?",
        "Cuánto cuesta la consulta?",
        "Buenos días",
        "Mi teléfono es 78901234"
    ]
    
    # Crear comparador
    comparator = ModelComparator(BASE_MODEL, FINETUNED_MODEL)
    
    # Comparar
    comparator.compare(TEST_PROMPTS)


if __name__ == "__main__":
    main()
