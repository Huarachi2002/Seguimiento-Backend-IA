"""
Fine-Tuning Script para GPT-2 Español - FORMATO ESTRUCTURADO
==============================================================

Script optimizado para entrenar GPT-2 con datos estructurados externos.

DIFERENCIAS CON EL SCRIPT ANTERIOR:
- Dataset usa formato <SYS>, <DATA>, <USER>, <ASSISTANT>
- Entrena al modelo a leer datos externos (backend) en vez de inventar
- Incluye ejemplos de negación ("No tengo esa información")
- Formato alineado con arquitectura FastAPI + NestJS + Redis
"""

import os
import torch
import logging
import argparse
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass

from transformers import (
    GPT2LMHeadModel,
    GPT2Tokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    EarlyStoppingCallback
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
    """Configuración de entrenamiento para modelo estructurado."""
    model_name: str = "DeepESP/gpt2-spanish"
    dataset_path: str = "app/training/datasets/tuberculosis_structured.json"
    output_dir: str = "app/training/models/gpt2-spanish-tb-structured"
    num_epochs: int = 15  # Más épocas para dataset estructurado
    batch_size: int = 4
    learning_rate: float = 2e-5  # LR más bajo para mejor convergencia
    warmup_steps: int = 200
    max_length: int = 512
    save_steps: int = 50
    eval_steps: int = 50


class StructuredMedicalGPT2Trainer:
    """
    Entrenador especializado para GPT-2 con datos estructurados.
    """
    
    def __init__(self, config: TrainingConfig):
        self.config = config
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.tokenizer = None
        self.train_dataset = None
        self.eval_dataset = None
        
        logger.info("=" * 80)
        logger.info("🤖 FINE-TUNING GPT-2 ESPAÑOL - FORMATO ESTRUCTURADO")
        logger.info("=" * 80)
        logger.info(f"🖥️  Dispositivo: {self.device}")
        
        if self.device == "cuda":
            logger.info(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
            logger.info(f"💾 VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    
    def load_dataset(self) -> None:
        """
        Carga el dataset estructurado.
        """
        logger.info("📂 Cargando dataset estructurado...")
        
        dataset_path = self.config.dataset_path
        
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(
                f"❌ Dataset no encontrado: {dataset_path}\n"
                f"   Ejecuta primero: python app/training/create_structured_dataset.py"
            )
        
        logger.info(f"📁 Archivo: {dataset_path}")
        
        # Cargar JSON
        import json
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"✅ Cargados {len(data)} ejemplos estructurados")
        
        # Validar formato
        for i, example in enumerate(data[:5]):
            if 'prompt' not in example or 'completion' not in example:
                raise ValueError(f"❌ Ejemplo {i} no tiene formato correcto (prompt/completion)")
            
            # Verificar que tenga los tags estructurados
            if '<SYS>' not in example['prompt'] or '<DATA>' not in example['prompt']:
                logger.warning(f"⚠️ Ejemplo {i} no tiene formato estructurado completo")
        
        # Convertir a formato de texto para entrenamiento
        texts = []
        for example in data:
            # Formato: prompt + completion (el modelo aprenderá a generar completion dado el prompt)
            text = example['prompt'] + example['completion']
            texts.append({"text": text})
        
        # Crear dataset
        dataset = Dataset.from_list(texts)
        
        # Split 90% train, 10% eval
        split = dataset.train_test_split(test_size=0.1, seed=42)
        self.train_dataset = split['train']
        self.eval_dataset = split['test']
        
        logger.info(f"📊 Dataset procesado:")
        logger.info(f"   - Train: {len(self.train_dataset)} ejemplos")
        logger.info(f"   - Eval: {len(self.eval_dataset)} ejemplos")
        
        # Estadísticas
        avg_length = sum(len(t['text']) for t in texts) / len(texts)
        logger.info(f"   - Longitud promedio: {avg_length:.0f} caracteres")
    
    def load_model_and_tokenizer(self) -> None:
        """
        Carga el modelo GPT-2 español y configura el tokenizer.
        """
        logger.info(f"🤖 Cargando modelo base: {self.config.model_name}")
        
        # Cargar tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.config.model_name)
        
        # Configurar tokens especiales
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            logger.info("✅ pad_token configurado como eos_token")
        
        # Agregar tokens especiales para nuestro formato estructurado
        special_tokens = {
            'additional_special_tokens': ['<SYS>', '</SYS>', '<DATA>', '</DATA>', '<USER>', '<ASSISTANT>']
        }
        num_added = self.tokenizer.add_special_tokens(special_tokens)
        logger.info(f"✅ {num_added} tokens especiales agregados")
        
        # Padding a la izquierda para generación
        self.tokenizer.padding_side = "left"
        
        logger.info("✅ Tokenizer configurado")
        
        # Cargar modelo
        self.model = GPT2LMHeadModel.from_pretrained(
            self.config.model_name,
            torch_dtype=torch.float32
        )
        
        # Redimensionar embeddings para los nuevos tokens
        self.model.resize_token_embeddings(len(self.tokenizer))
        logger.info(f"✅ Embeddings redimensionados a {len(self.tokenizer)} tokens")
        
        # Configurar pad_token_id
        self.model.config.pad_token_id = self.tokenizer.pad_token_id
        
        # Mover a GPU
        self.model.to(self.device)
        
        logger.info(f"✅ Modelo cargado en {self.device}")
        logger.info(f"📊 Parámetros: {self.model.num_parameters():,}")
    
    def tokenize_dataset(self) -> None:
        """
        Tokeniza el dataset completo.
        """
        logger.info("🔤 Tokenizando dataset estructurado...")
        
        def tokenize_function(examples):
            """
            Tokeniza un batch de ejemplos.
            
            IMPORTANTE: No truncamos agresivamente porque los ejemplos
            estructurados son más largos (incluyen <SYS>, <DATA>, etc.)
            """
            # Tokenizar textos
            result = self.tokenizer(
                examples["text"],
                padding="max_length",
                truncation=True,
                max_length=self.config.max_length,
                return_tensors="pt"
            )
            
            # Configurar labels (para language modeling, labels = input_ids)
            result["labels"] = result["input_ids"].clone()
            
            return result
        
        # Aplicar tokenización
        self.train_dataset = self.train_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"],
            desc="Tokenizando train"
        )
        
        self.eval_dataset = self.eval_dataset.map(
            tokenize_function,
            batched=True,
            remove_columns=["text"],
            desc="Tokenizando eval"
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
        logger.info("🚀 INICIANDO FINE-TUNING ESTRUCTURADO")
        logger.info("=" * 80)
        logger.info(f"📊 Configuración:")
        logger.info(f"   - Modelo: {self.config.model_name}")
        logger.info(f"   - Épocas: {self.config.num_epochs}")
        logger.info(f"   - Batch Size: {self.config.batch_size}")
        logger.info(f"   - Learning Rate: {self.config.learning_rate}")
        logger.info(f"   - Max Length: {self.config.max_length}")
        logger.info(f"   - Train: {len(self.train_dataset)} ejemplos")
        logger.info(f"   - Eval: {len(self.eval_dataset)} ejemplos")
        logger.info("=" * 80)
        
        # Crear directorio de salida
        os.makedirs(self.config.output_dir, exist_ok=True)
        
        # Argumentos de entrenamiento
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            per_device_eval_batch_size=self.config.batch_size,
            warmup_steps=self.config.warmup_steps,
            learning_rate=self.config.learning_rate,
            weight_decay=0.01,
            max_grad_norm=1.0,
            fp16=False,
            logging_dir=f"{self.config.output_dir}/logs",
            logging_steps=10,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            eval_strategy="steps",
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            greater_is_better=False,
            report_to="none",
            remove_unused_columns=False,
            gradient_accumulation_steps=2,
            lr_scheduler_type="cosine",
            dataloader_num_workers=0,  # Evita problemas en Windows
        )
        
        # Data collator
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False  # GPT-2 usa causal LM, no masked LM
        )
        
        # Callback de early stopping
        early_stop = EarlyStoppingCallback(
            early_stopping_patience=3,
            early_stopping_threshold=0.01
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
        
        try:
            train_result = trainer.train()
            
            logger.info("=" * 80)
            logger.info("✅ ENTRENAMIENTO COMPLETADO")
            logger.info("=" * 80)
            logger.info(f"📊 Resultados finales:")
            logger.info(f"   - Train Loss: {train_result.training_loss:.4f}")
            logger.info(f"   - Eval Loss: {trainer.evaluate()['eval_loss']:.4f}")
            
            # Guardar modelo
            logger.info(f"💾 Guardando modelo en: {self.config.output_dir}")
            trainer.save_model()
            self.tokenizer.save_pretrained(self.config.output_dir)
            
            logger.info("✅ Modelo guardado exitosamente")
            
        except KeyboardInterrupt:
            logger.warning("⚠️ Entrenamiento interrumpido por el usuario")
            logger.info("💾 Guardando modelo parcial...")
            trainer.save_model()
            self.tokenizer.save_pretrained(self.config.output_dir)
            
        except Exception as e:
            logger.error(f"❌ Error durante entrenamiento: {e}")
            raise
    
    def test_generation(self):
        """
        Prueba el modelo con ejemplos estructurados.
        """
        logger.info("=" * 80)
        logger.info("🧪 PROBANDO GENERACIÓN CON DATOS ESTRUCTURADOS")
        logger.info("=" * 80)
        
        test_cases = [
            # Caso 1: Paciente registrado CON cita
            {
                "name": "Paciente con cita",
                "prompt": """<SYS>
Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud CAÑADA DEL CARMEN.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta.
</SYS>

<DATA>
Paciente_registrado = True
Nombre = "Taison Perez"
Citas = [{fecha: "2025-10-25", hora: "10:00", estado: "Programado"}]
Ultima_visita = "2025-10-10"
</DATA>

<USER>: Hola
<ASSISTANT>:"""
            },
            # Caso 2: Paciente registrado SIN citas
            {
                "name": "Paciente sin citas",
                "prompt": """<SYS>
Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud CAÑADA DEL CARMEN.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta.
</SYS>

<DATA>
Paciente_registrado = True
Nombre = "Taison Perez"
Citas = []
Ultima_visita = None
</DATA>

<USER>: ¿Tengo citas programadas?
<ASSISTANT>:"""
            },
            # Caso 3: Paciente NO registrado
            {
                "name": "Paciente no registrado",
                "prompt": """<SYS>
Eres un asistente virtual especializado SOLO en Tuberculosis del centro de salud CAÑADA DEL CARMEN.
Responde solo con información basada en los datos proporcionados en <DATA>.
SI NO hay datos explícitos, debes responder: "No tengo esa información registrada".
NUNCA inventes nombres, fechas o información que no esté en <DATA>.
Máximo 2 oraciones por respuesta.
</SYS>

<DATA>
Paciente_registrado = False
Nombre = None
Citas = []
Ultima_visita = None
</DATA>

<USER>: ¿Cuándo es mi cita?
<ASSISTANT>:"""
            }
        ]
        
        self.model.eval()
        
        for i, test in enumerate(test_cases, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"CASO {i}: {test['name']}")
            logger.info(f"{'='*80}")
            logger.info(f"PROMPT:\n{test['prompt'][-200:]}")
            
            # Tokenizar
            inputs = self.tokenizer(
                test['prompt'],
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=self.config.max_length
            ).to(self.device)
            
            # Generar
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=100,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    top_k=50,
                    pad_token_id=self.tokenizer.pad_token_id,
                    repetition_penalty=1.2,
                    no_repeat_ngram_size=3
                )
            
            # Decodificar solo la respuesta generada
            prompt_length = inputs['input_ids'].shape[1]
            generated_tokens = outputs[0][prompt_length:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            logger.info(f"\nRESPUESTA GENERADA:\n{response}")
            logger.info("=" * 80)
        
        logger.info("\n✅ Pruebas completadas")


def main():
    """
    Función principal del script de entrenamiento estructurado.
    """
    parser = argparse.ArgumentParser(description="Fine-tuning GPT-2 español con datos estructurados")
    parser.add_argument("--dataset", type=str, default="app/training/datasets/tuberculosis_structured.json", help="Path al archivo de dataset JSON")
    parser.add_argument("--epochs", type=int, default=15, help="Número de épocas")
    parser.add_argument("--batch_size", type=int, default=4, help="Tamaño del batch")
    parser.add_argument("--learning_rate", type=float, default=2e-5, help="Tasa de aprendizaje")
    parser.add_argument("--max_length", type=int, default=512, help="Longitud máxima de secuencia")
    parser.add_argument("--model_name", type=str, default="DeepESP/gpt2-spanish", help="Modelo base")
    parser.add_argument("--output_dir", type=str, default="app/training/models/gpt2-spanish-tb-structured", help="Directorio de salida")
    
    args = parser.parse_args()
    
    # Configuración
    config = TrainingConfig(
        model_name=args.model_name,
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        num_epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        max_length=args.max_length
    )
    
    # Crear trainer
    trainer = StructuredMedicalGPT2Trainer(config)
    
    # Pipeline completo
    logger.info("🏁 Iniciando pipeline de Fine-Tuning Estructurado")
    logger.info("")
    
    try:
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
        logger.info("📝 PRÓXIMOS PASOS:")
        logger.info(f"   1. Actualiza MODEL_NAME en .env a: {config.output_dir}")
        logger.info("   2. Actualiza ai_service.py para usar el nuevo formato de prompt")
        logger.info("   3. Reinicia la aplicación FastAPI")
        logger.info("   4. Prueba el endpoint /chat")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ Error en el pipeline: {e}")
        raise


if __name__ == "__main__":
    main()
