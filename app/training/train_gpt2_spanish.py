"""
Fine-Tuning Script para GPT-2 Español
======================================

Script optimizado para entrenar DeepESP/gpt2-spanish con conversaciones médicas.

Diferencias con DialoGPT:
- GPT-2 usa formato de prompt diferente
- Tokenización específica para español
- Mejores hiperparámetros para español
"""

import os
import sys
import json
import torch
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling
)
from datasets import Dataset

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuración de entrenamiento."""
    model_name: str = "DeepESP/gpt2-spanish"
    # Usar dataset final (fusionado) si existe, sino usar v2
    dataset_path: str = "app/training/datasets/tuberculosis_conversations_final.json"
    output_dir: str = "app/training/models/gpt2-spanish-tuberculosis"
    num_epochs: int = 10
    batch_size: int = 4
    learning_rate: float = 3e-5
    warmup_steps: int = 100
    max_length: int = 512
    save_steps: int = 50


class MedicalGPT2Trainer:
    """
    Entrenador especializado para GPT-2 español con conversaciones médicas.
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.train_dataset = None
        self.eval_dataset = None
        
        logger.info("=" * 80)
        logger.info("🤖 FINE-TUNING GPT-2 ESPAÑOL - CONVERSACIONES MÉDICAS")
        logger.info("=" * 80)
        logger.info(f"🖥️  Dispositivo: {self.device}")
        
        if self.device == "cuda":
            logger.info(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    def load_dataset(self) -> None:
        """
        Carga y preprocesa el dataset de conversaciones médicas.
        """
        logger.info("")
        
        # Verificar si existe el dataset final, sino usar v2
        dataset_path = self.config.dataset_path
        if not os.path.exists(dataset_path):
            logger.warning(f"⚠️ Dataset final no encontrado: {dataset_path}")
            dataset_path = "app/training/datasets/tuberculosis_conversations_v2.json"
            logger.info(f"📂 Usando dataset alternativo: {dataset_path}")
            
            if not os.path.exists(dataset_path):
                raise FileNotFoundError(f"❌ No se encontró ningún dataset válido")
        else:
            logger.info(f"📂 Cargando dataset desde: {dataset_path}")
        
        # Cargar JSON
        with open(dataset_path, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
        
        logger.info(f"✅ Cargadas {len(conversations)} conversaciones")
        
        # Convertir a formato de texto para GPT-2
        # NUEVO FORMATO: prompt + completion (con contexto de sistema embebido)
        texts = []
        for i, conv in enumerate(conversations):
            # Validar formato
            if "prompt" not in conv or "completion" not in conv:
                logger.warning(f"⚠️ Conversación {i} sin formato correcto, saltando...")
                continue
            
            # Combinar prompt (incluye sistema + contexto) + completion + fin
            # El modelo aprenderá a predecir completion dado el prompt completo
            text = f"{conv['prompt']}{conv['completion']}<|endoftext|>"
            texts.append({"text": text})
        
        # Crear dataset
        dataset = Dataset.from_list(texts)
        
        # Split 90% train, 10% eval
        split = dataset.train_test_split(test_size=0.1, seed=42)
        self.train_dataset = split['train']
        self.eval_dataset = split['test']
        
        logger.info(f"✅ Dataset procesado: {len(dataset)} ejemplos")
        logger.info(f"📊 Train: {len(self.train_dataset)} | Eval: {len(self.eval_dataset)}")
    
    def load_model_and_tokenizer(self) -> None:
        """
        Carga el modelo GPT-2 español y su tokenizer.
        """
        logger.info(f"🤖 Cargando modelo base: {self.config.model_name}")
        
        # Cargar tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.config.model_name)
        
        # GPT-2 español necesita configuración especial de tokens
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            self.tokenizer.pad_token_id = self.tokenizer.eos_token_id
        
        # Importante para generación
        self.tokenizer.padding_side = "left"
        
        logger.info("✅ Tokenizer cargado")
        
        # Cargar modelo
        self.model = GPT2LMHeadModel.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float32  # FP32 para estabilidad
        )
        
        # Configurar pad_token_id en el modelo
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        
        # Mover a GPU
        self.model.to(self.device)
        
        logger.info(f"✅ Modelo cargado en {self.device}")
        logger.info(f"📊 Parámetros: {self.model.num_parameters():,}")
    
    def tokenize_dataset(self) -> None:
        """
        Tokeniza el dataset completo.
        """
        logger.info("🔤 Tokenizando dataset...")
        
        def tokenize_function(examples):
            # Tokenizar
            model_inputs = self.tokenizer(
                examples["text"],
                truncation=True,
                max_length=self.config.max_length,
                padding="max_length",
                return_attention_mask=True
            )
            
            # Para language modeling, labels = input_ids
            # Pero enmascaramos padding (-100 para que no contribuya a la loss)
            model_inputs["labels"] = [
                [
                    token_id if token_id != self.tokenizer.pad_token_id else -100
                    for token_id in input_ids
                ]
                for input_ids in model_inputs["input_ids"]
            ]
            
            return model_inputs
        
        # Aplicar tokenización
        self.train_dataset = self.train_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"]
        )
        
        self.eval_dataset = self.eval_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"]
        )
        
        # Configurar formato PyTorch
        self.train_dataset.set_format("torch")
        self.eval_dataset.set_format("torch")
        
        logger.info("✅ Dataset tokenizado")
    
    def train(self) -> None:
        """
        Entrena el modelo con los parámetros configurados.
        """
        logger.info("=" * 80)
        logger.info("🚀 INICIANDO FINE-TUNING")
        logger.info("=" * 80)
        logger.info(f"📊 Configuración:")
        logger.info(f"   - Modelo: {self.config.model_name}")
        logger.info(f"   - Épocas: {self.config.num_epochs}")
        logger.info(f"   - Batch Size: {self.config.batch_size}")
        logger.info(f"   - Learning Rate: {self.config.learning_rate}")
        logger.info(f"   - Max Length: {self.config.max_length}")
        logger.info(f"   - Ejemplos de entrenamiento: {len(self.train_dataset)}")
        logger.info(f"   - Ejemplos de evaluación: {len(self.eval_dataset)}")
        logger.info("=" * 80)
        
        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Argumentos de entrenamiento optimizados para GPT-2 español
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            warmup_steps=self.config.warmup_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=0.01,
            max_grad_norm=1.0,
            fp16=False,  # FP32 para estabilidad
            logging_dir=f"{self.config.output_dir}/logs",
            logging_steps=10,
            save_steps=self.config.save_steps,
            eval_steps=self.config.save_steps,
            eval_strategy="steps",
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="none",
            remove_unused_columns=False,
            # Optimizaciones específicas
            gradient_accumulation_steps=2,  # Simula batch_size mayor
            lr_scheduler_type="cosine",  # Mejor scheduler
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # Causal LM, no masked LM
        )
        
        # Crear Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=self.train_dataset,
            eval_dataset=self.eval_dataset,
            data_collator=data_collator
        )
        
        # Entrenar
        logger.info("🏋️  Iniciando entrenamiento...")
        logger.info("⏰ Tiempo estimado: 1-3 horas")
        logger.info("💡 Puedes monitorear la GPU con: nvidia-smi -l 1")
        logger.info("")
        
        try:
            train_result = trainer.train()
            
            logger.info("")
            logger.info("=" * 80)
            logger.info("✅ ENTRENAMIENTO COMPLETADO")
            logger.info("=" * 80)
            logger.info(f"📊 Métricas finales:")
            logger.info(f"   - Loss de entrenamiento: {train_result.training_loss:.4f}")
            logger.info(f"   - Tiempo total: {train_result.metrics['train_runtime']:.2f} segundos")
            logger.info("=" * 80)
            
            # Guardar modelo
            logger.info(f"💾 Guardando modelo entrenado en: {self.config.output_dir}")
            self.model.save_pretrained(self.config.output_dir)
            self.tokenizer.save_pretrained(self.config.output_dir)
            logger.info("✅ Modelo guardado exitosamente")
            
            # Evaluar
            logger.info("🔍 Evaluando modelo...")
            eval_results = trainer.evaluate()
            
            logger.info("=" * 80)
            logger.info("📊 RESULTADOS DE EVALUACIÓN")
            logger.info("=" * 80)
            logger.info(f"   - Loss de evaluación: {eval_results['eval_loss']:.4f}")
            
            # Calcular perplexity
            import math
            perplexity = math.exp(eval_results['eval_loss'])
            logger.info(f"   - Perplexity: {perplexity:.2f}")
            logger.info("=" * 80)
            
            # Guardar métricas
            metrics_file = os.path.join(self.config.output_dir, "metrics.json")
            with open(metrics_file, 'w') as f:
                json.dump({
                    "train_loss": train_result.training_loss,
                    "eval_loss": eval_results['eval_loss'],
                    "perplexity": perplexity,
                    "train_runtime": train_result.metrics['train_runtime']
                }, f, indent=2)
            
            logger.info(f"💾 Métricas guardadas en: {metrics_file}")
            
        except Exception as e:
            logger.error(f"❌ Error durante el entrenamiento: {e}")
            raise
    
    def test_generation(self, test_prompts: Optional[List[str]] = None) -> None:
        """
        Prueba la generación de respuestas con el modelo entrenado.
        """
        if test_prompts is None:
            test_prompts = [
                "Hola, necesito una cita",
                "Quiero cancelar mi cita",
                "Para odontología",
                "Tengo mucho dolor de cabeza",
                "Qué especialidades tienen?",
                "Buenos días",
                "Mi nombre es Juan Pérez"
            ]
        
        logger.info("=" * 80)
        logger.info("🧪 PROBANDO GENERACIÓN DE RESPUESTAS")
        logger.info("=" * 80)
        
        self.model.eval()
        
        for prompt in test_prompts:
            logger.info(f"\n👤 Usuario: {prompt}")
            
            try:
                # Formatear como en el entrenamiento
                formatted_prompt = f"Usuario: {prompt}\nAsistente:"
                
                # Tokenizar
                inputs = self.tokenizer(
                    formatted_prompt,
                    return_tensors="pt",
                    padding=True,
                    return_attention_mask=True
                )
                
                input_ids = inputs["input_ids"].to(self.device)
                attention_mask = inputs["attention_mask"].to(self.device)
                
                # Generar
                with torch.no_grad():
                    outputs = self.model.generate(
                        input_ids,
                        attention_mask=attention_mask,
                        max_new_tokens=60,
                        temperature=0.8,
                        do_sample=True,
                        top_p=0.92,
                        top_k=50,
                        pad_token_id=self.tokenizer.pad_token_id,
                        eos_token_id=self.tokenizer.eos_token_id,
                        no_repeat_ngram_size=3,
                        repetition_penalty=1.3,
                        num_return_sequences=1
                    )
                
                # Decodificar solo los tokens nuevos
                response = self.tokenizer.decode(
                    outputs[0][input_ids.shape[1]:],
                    skip_special_tokens=True
                )
                
                # Limpiar respuesta
                response = response.split("\n")[0].strip()  # Solo primera línea
                
                logger.info(f"🤖 Asistente: {response}")
                
            except Exception as e:
                logger.error(f"❌ Error generando respuesta: {e}")
                logger.info(f"🤖 Asistente: [Error en generación]")
        
        logger.info("\n" + "=" * 80)


def main():
    """
    Función principal del script de entrenamiento.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Fine-tuning de GPT-2 español para conversaciones médicas")
    parser.add_argument("--epochs", type=int, default=5, help="Número de épocas")
    parser.add_argument("--batch_size", type=int, default=4, help="Tamaño del batch")
    parser.add_argument("--learning_rate", type=float, default=3e-5, help="Tasa de aprendizaje")
    parser.add_argument("--max_length", type=int, default=256, help="Longitud máxima de secuencia")
    parser.add_argument("--model_name", type=str, default="DeepESP/gpt2-spanish", help="Modelo base")
    parser.add_argument("--output_dir", type=str, default="app/training/models/gpt2-spanish-medical", help="Directorio de salida")
    
    args = parser.parse_args()
    
    # Configuración
    config = TrainingConfig(
        model_name=args.model_name,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_length=args.max_length
    )
    
    # Crear trainer
    trainer = MedicalGPT2Trainer(config)
    
    # Pipeline completo
    logger.info("🏁 Iniciando pipeline de Fine-Tuning")
    logger.info("")
    
    # 1. Cargar dataset
    trainer.load_dataset()
    
    # 2. Cargar modelo
    trainer.load_model_and_tokenizer()
    
    # 3. Tokenizar
    trainer.tokenize_dataset()
    
    # 4. Entrenar
    trainer.train()
    
    # 5. Probar generación
    trainer.test_generation()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("🎉 PROCESO COMPLETADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info(f"📁 Modelo guardado en: {config.output_dir}")
    logger.info("")
    logger.info("📝 Próximos pasos:")
    logger.info(f"   1. Actualiza MODEL_NAME en .env a: {config.output_dir}")
    logger.info("   2. Reinicia la aplicación FastAPI")
    logger.info("   3. Prueba el endpoint /chat")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
