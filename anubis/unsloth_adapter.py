"""Unsloth integration — optional training acceleration.

Unsloth is an open-source optimization library that accelerates LLM
fine-tuning on consumer GPUs by 2-5x while using 60% less VRAM.
It rewrites underlying mathematical kernels into handwritten Triton code.

This module is an OPTIONAL adapter. The constitutional kernel prefers
standard-library-only code, so Unsloth is treated as an optional
dependency. When Unsloth is not installed, the adapter falls back to
standard HuggingFace Transformers training (or returns a "not available"
status).

Features:
- Detect if Unsloth is installed
- Configure training with Unsloth optimizations
- Generate optimized training scripts
- Fallback to standard training when unavailable
- Estimate VRAM savings and speed improvements
- Log all training configurations to the evidence ledger

Usage:
    from anubis.unsloth_adapter import UnslothAdapter
    adapter = UnslothAdapter()
    if adapter.is_available():
        script = adapter.generate_training_script(config)
    else:
        script = adapter.generate_fallback_script(config)
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ledger import Ledger


@dataclass
class TrainingConfig:
    """Configuration for a fine-tuning run."""
    model_name: str = "qwen2.5-coder:7b"
    max_seq_length: int = 2048
    batch_size: int = 2
    gradient_accumulation_steps: int = 16
    learning_rate: float = 2e-4
    epochs: int = 3
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    use_4bit: bool = True
    use_gradient_checkpointing: bool = True
    target_modules: list[str] = field(default_factory=lambda: [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ])

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "max_seq_length": self.max_seq_length,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "use_4bit": self.use_4bit,
            "use_gradient_checkpointing": self.use_gradient_checkpointing,
            "target_modules": self.target_modules,
        }


@dataclass
class TrainingEstimate:
    """Estimated training performance with and without Unsloth."""
    unsloth_available: bool = False
    estimated_vram_mb: int = 0
    estimated_vram_with_unsloth_mb: int = 0
    vram_savings_pct: float = 0.0
    estimated_speedup: float = 1.0
    estimated_time_minutes: float = 0.0
    estimated_time_with_unsloth_minutes: float = 0.0


class UnslothAdapter:
    """Optional adapter for Unsloth-accelerated training.

    Detects if Unsloth is installed and provides methods to
    generate optimized training scripts. Falls back gracefully
    when Unsloth is not available.
    """

    def __init__(self, ledger: Ledger | None = None) -> None:
        self.ledger = ledger
        self._available: bool | None = None

    def is_available(self) -> bool:
        """Check if Unsloth is installed."""
        if self._available is not None:
            return self._available
        try:
            import unsloth  # type: ignore
            self._available = True
        except ImportError:
            self._available = False
        return self._available

    def estimate_performance(
        self, config: TrainingConfig, dataset_size: int = 1000
    ) -> TrainingEstimate:
        """Estimate training performance with and without Unsloth.

        These are rough estimates based on Unsloth's documented
        performance characteristics:
        - 2-5x speedup (we use 3x as a conservative estimate)
        - 60% VRAM reduction
        """
        # Base VRAM estimate (very rough, depends on model size)
        # 7B model at 4-bit ≈ 6GB base + training overhead
        base_vram = 6000  # MB
        if config.use_4bit:
            base_vram = int(base_vram * 0.6)
        training_overhead = config.max_seq_length * config.batch_size * 0.01
        estimated_vram = int(base_vram + training_overhead)

        # Unsloth saves ~60% VRAM
        unsloth_vram = int(estimated_vram * 0.4)

        # Time estimate (very rough)
        # Standard: ~1 minute per 100 samples per epoch
        base_time = (dataset_size / 100) * config.epochs
        unsloth_time = base_time / 3.0  # 3x speedup

        return TrainingEstimate(
            unsloth_available=self.is_available(),
            estimated_vram_mb=estimated_vram,
            estimated_vram_with_unsloth_mb=unsloth_vram,
            vram_savings_pct=round((1 - unsloth_vram / estimated_vram) * 100, 1),
            estimated_speedup=3.0,
            estimated_time_minutes=round(base_time, 1),
            estimated_time_with_unsloth_minutes=round(unsloth_time, 1),
        )

    def generate_training_script(
        self, config: TrainingConfig, dataset_path: str
    ) -> str:
        """Generate an Unsloth-optimized training script.

        Args:
            config: Training configuration
            dataset_path: Path to the training dataset (JSONL)

        Returns:
            Python script as a string
        """
        if not self.is_available():
            return self.generate_fallback_script(config, dataset_path)

        c = config
        targets = ", ".join(f'"{m}"' for m in c.target_modules)

        script = f'''# Auto-generated Unsloth training script
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}
# Model: {c.model_name}
# WARNING: This script requires Unsloth to be installed.
# Install with: pip install unsloth

from unsloth import FastLanguageModel
import torch
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments

# Load model with Unsloth optimizations
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name="{c.model_name}",
    max_seq_length={c.max_seq_length},
    dtype=None,
    load_in_4bit={c.use_4bit},
)

# Add LoRA adapters
model = FastLanguageModel.get_peft_model(
    model,
    r={c.lora_r},
    target_modules=[{targets}],
    lora_alpha={c.lora_alpha},
    lora_dropout={c.lora_dropout},
    bias="none",
    use_gradient_checkpointing="{c.use_gradient_checkpointing}",
    random_state=42,
)

# Load dataset
dataset = load_dataset("json", data_files="{dataset_path}", split="train")

# Training arguments
training_args = TrainingArguments(
    per_device_train_batch_size={c.batch_size},
    gradient_accumulation_steps={c.gradient_accumulation_steps},
    warmup_steps=50,
    max_steps={c.epochs * 100},
    learning_rate={c.learning_rate},
    fp16=not torch.cuda.is_bf16_supported(),
    bf16=torch.cuda.is_bf16_supported(),
    logging_steps=10,
    optim="adamw_8bit",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=42,
    output_dir="outputs",
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="instruction",
    max_seq_length={c.max_seq_length},
    args=training_args,
)

# Train
trainer_stats = trainer.train()

# Save model
model.save_pretrained_gguf("outputs/merged_model", tokenizer)
print(f"Training complete. Saved to outputs/merged_model")
print(f"Total steps: {{trainer_stats.global_step}}")
print(f"Training loss: {{trainer_stats.training_loss:.4f}}")
'''
        if self.ledger:
            self.ledger.append({
                "event": "unsloth_script_generated",
                "model": c.model_name,
                "dataset_path": dataset_path,
                "config": c.to_dict(),
            })

        return script

    def generate_fallback_script(
        self, config: TrainingConfig, dataset_path: str
    ) -> str:
        """Generate a standard HuggingFace training script (no Unsloth).

        Used when Unsloth is not installed. Uses standard Transformers
        and PEFT for LoRA training.
        """
        c = config
        targets = ", ".join(f'"{m}"' for m in c.target_modules)

        script = f'''# Auto-generated training script (standard, no Unsloth)
# Generated at {time.strftime("%Y-%m-%d %H:%M:%S")}
# Model: {c.model_name}
# NOTE: Install Unsloth for 2-5x speedup: pip install unsloth

from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import load_dataset
from trl import SFTTrainer
import torch

# Load model
model = AutoModelForCausalLM.from_pretrained(
    "{c.model_name}",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("{c.model_name}")

# Prepare for LoRA
model = prepare_model_for_kbit_training(model)

# LoRA config
lora_config = LoraConfig(
    r={c.lora_r},
    target_modules=[{targets}],
    lora_alpha={c.lora_alpha},
    lora_dropout={c.lora_dropout},
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)

# Load dataset
dataset = load_dataset("json", data_files="{dataset_path}", split="train")

# Training arguments
training_args = TrainingArguments(
    per_device_train_batch_size={c.batch_size},
    gradient_accumulation_steps={c.gradient_accumulation_steps},
    warmup_steps=50,
    max_steps={c.epochs * 100},
    learning_rate={c.learning_rate},
    fp16=True,
    logging_steps=10,
    optim="adamw_torch",
    weight_decay=0.01,
    lr_scheduler_type="linear",
    seed=42,
    output_dir="outputs",
    gradient_checkpointing={c.use_gradient_checkpointing},
)

# Create trainer
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset,
    dataset_text_field="instruction",
    max_seq_length={c.max_seq_length},
    args=training_args,
)

# Train
trainer_stats = trainer.train()

# Save
model.save_pretrained("outputs/lora_adapter")
print(f"Training complete. Saved to outputs/lora_adapter")
'''
        if self.ledger:
            self.ledger.append({
                "event": "fallback_script_generated",
                "model": c.model_name,
                "dataset_path": dataset_path,
            })

        return script

    def save_script(
        self, script: str, output_path: str | Path
    ) -> dict[str, Any]:
        """Save a training script to disk."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(script, encoding="utf-8")
        return {"saved": True, "path": str(path), "lines": script.count("\n") + 1}

    def status(self) -> dict[str, Any]:
        """Return Unsloth adapter status."""
        return {
            "available": self.is_available(),
            "description": (
                "Unsloth provides 2-5x training speedup with 60% less VRAM. "
                "Install with: pip install unsloth"
            ) if not self.is_available() else "Unsloth is installed and ready",
        }
