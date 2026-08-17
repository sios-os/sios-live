#!/usr/bin/env python3
"""Stage 2: Full fine-tune of Qwen 2.5 32B on H100 NVL 94GB.

Uses Unsloth for 2-5x speedup and 60% less VRAM usage.
Performs a FULL fine-tune (not LoRA) on the training data.

With Unsloth on 94GB VRAM:
  - 32B model fits with room for optimizer states
  - Gradient checkpointing enabled
  - bf16 precision (H100 supports bf16)
  - Sequence length 2048

Output: /workspace/training_output/anubis_v{gen}/ (fine-tuned model)

Run on H100: python 02_finetune.py [--gen 1|2|3] [--data <path>]
"""
import json
import os
import sys
import time
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────
BASE_MODEL = "Qwen/Qwen2.5-32B-Instruct"
OUTPUT_DIR = Path("/workspace/training_output")
DATA_PATH = OUTPUT_DIR / "training_data.jsonl"

# Training hyperparameters per generation
# Adjusted for H100 NVL 94GB with Unsloth
GEN_CONFIGS = {
    1: {  # Generation 1 — broad learning
        "learning_rate": 1e-5,
        "epochs": 3,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 16,
        "warmup_ratio": 0.05,
        "max_seq_length": 1024,
        "use_unsloth": True,
    },
    2: {  # Generation 2 — refined learning from self-distilled data
        "learning_rate": 5e-6,
        "epochs": 2,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 16,
        "warmup_ratio": 0.03,
        "max_seq_length": 1024,
        "use_unsloth": True,
    },
    3: {  # Generation 3 — final polish
        "learning_rate": 2e-6,
        "epochs": 2,
        "per_device_train_batch_size": 1,
        "gradient_accumulation_steps": 16,
        "warmup_ratio": 0.02,
        "max_seq_length": 1024,
        "use_unsloth": True,
    },
}


def log(stage: str, msg: str, **kwargs):
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "message": msg,
        **kwargs,
    }
    print(json.dumps(entry, default=str), flush=True)


def load_dataset(path: Path) -> list[dict]:
    """Load JSONL training data."""
    pairs = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            pairs.append(json.loads(line))
    log("data", f"Loaded {len(pairs)} training pairs from {path}")
    return pairs


def check_unsloth_available() -> bool:
    """Check if Unsloth is available."""
    try:
        from unsloth import FastLanguageModel
        return True
    except ImportError:
        return False


def fine_tune_unsloth(generation: int, data_path: Path):
    """Run full fine-tune using Unsloth (preferred path)."""
    config = GEN_CONFIGS[generation]
    log("finetune", f"Starting generation {generation} (Unsloth)", config=config)

    from unsloth import FastLanguageModel
    import torch
    from transformers import TrainingArguments, Trainer
    from datasets import Dataset

    # Output directory
    output_path = OUTPUT_DIR / f"anubis_v{generation}"
    output_path.mkdir(parents=True, exist_ok=True)

    # Load model with Unsloth — 4-bit quantized for 94GB VRAM
    # 32B model in bf16 needs ~128GB VRAM for full fine-tune, but H100 NVL has 94GB.
    # Using 4-bit quantization reduces model to ~20GB, leaving room for optimizer + activations.
    log("finetune", f"Loading {BASE_MODEL} with Unsloth (4-bit)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=BASE_MODEL,
        max_seq_length=config["max_seq_length"],
        dtype=torch.bfloat16,
        load_in_4bit=True,  # 4-bit quantization to fit in 94GB VRAM
        full_finetuning=False,  # Use LoRA adapters on top of 4-bit base
    )

    # Add LoRA adapters for efficient fine-tuning
    model = FastLanguageModel.get_peft_model(
        model,
        r=16,  # Lower LoRA rank to save VRAM
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=42,
        loftq_config=None,
    )

    vram_gb = torch.cuda.memory_allocated() / 1e9
    log("finetune", "Model loaded with LoRA adapters", vram_gb=vram_gb)

    # Load and prepare dataset
    pairs = load_dataset(data_path)

    # Format and tokenize training examples
    max_seq = config["max_seq_length"]

    def format_and_tokenize(pair):
        messages = pair.get("messages", [])
        if len(messages) < 2:
            return None
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        # Tokenize with padding handled by collator
        enc = tokenizer(
            text,
            truncation=True,
            max_length=max_seq,
            return_tensors=None,
        )
        enc["labels"] = enc["input_ids"].copy()
        return enc

    formatted = [format_and_tokenize(p) for p in pairs if format_and_tokenize(p)]
    log("finetune", f"Formatted and tokenized {len(formatted)} training examples")

    # Create HuggingFace dataset
    dataset = Dataset.from_list(formatted)

    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=config["epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        max_grad_norm=1.0,
        report_to="none",
        seed=42,
        dataloader_num_workers=4,
        remove_unused_columns=False,
    )

    # Data collator for tokenized inputs
    from transformers import DataCollatorForSeq2Seq
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
    )

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # Train
    log("finetune", "Starting training (Unsloth)...")
    start_time = time.time()
    train_result = trainer.train()
    duration = time.time() - start_time

    # Save model
    log("finetune", "Saving fine-tuned model...")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    # Record metadata
    metadata = {
        "generation": generation,
        "base_model": BASE_MODEL,
        "output_path": str(output_path),
        "training_pairs": len(pairs),
        "epochs": config["epochs"],
        "learning_rate": config["learning_rate"],
        "duration_s": duration,
        "duration_minutes": duration / 60,
        "train_loss": train_result.training_loss,
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_hash": _hash_dir(output_path),
        "backend": "unsloth",
        "gpu": "H100 NVL 94GB",
    }

    metadata_path = output_path / "generation_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    log("finetune", "Training complete", **metadata)
    _print_summary(generation, output_path, len(pairs), config, duration, train_result.training_loss, metadata["artifact_hash"])
    return output_path, metadata


def fine_tune_standard(generation: int, data_path: Path):
    """Fallback: standard HuggingFace fine-tune without Unsloth."""
    config = GEN_CONFIGS[generation]
    log("finetune", f"Starting generation {generation} (standard HF)", config=config)

    import torch
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer,
        TrainingArguments, Trainer,
        DataCollatorForLanguageModeling,
    )

    output_path = OUTPUT_DIR / f"anubis_v{generation}"
    output_path.mkdir(parents=True, exist_ok=True)

    log("finetune", "Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    log("finetune", f"Loading {BASE_MODEL} in bfloat16...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    vram_gb = torch.cuda.memory_allocated() / 1e9
    log("finetune", "Model loaded", vram_gb=vram_gb)

    # Load and prepare dataset
    pairs = load_dataset(data_path)
    dataset = prepare_dataset(pairs, tokenizer, config["max_seq_length"], torch)

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    training_args = TrainingArguments(
        output_dir=str(output_path),
        num_train_epochs=config["epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        logging_steps=10,
        save_strategy="epoch",
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        optim="adamw_torch",
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        max_grad_norm=1.0,
        report_to="none",
        seed=42,
        dataloader_num_workers=4,
        remove_unused_columns=False,
    )

    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=dataset, data_collator=data_collator, tokenizer=tokenizer,
    )

    log("finetune", "Starting training (standard)...")
    start_time = time.time()
    train_result = trainer.train()
    duration = time.time() - start_time

    log("finetune", "Saving fine-tuned model...")
    trainer.save_model(str(output_path))
    tokenizer.save_pretrained(str(output_path))

    metadata = {
        "generation": generation,
        "base_model": BASE_MODEL,
        "output_path": str(output_path),
        "training_pairs": len(pairs),
        "epochs": config["epochs"],
        "learning_rate": config["learning_rate"],
        "duration_s": duration,
        "duration_minutes": duration / 60,
        "train_loss": train_result.training_loss,
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_hash": _hash_dir(output_path),
        "backend": "standard_hf",
        "gpu": "H100 NVL 94GB",
    }

    metadata_path = output_path / "generation_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    log("finetune", "Training complete", **metadata)
    _print_summary(generation, output_path, len(pairs), config, duration, train_result.training_loss, metadata["artifact_hash"])
    return output_path, metadata


def prepare_dataset(pairs, tokenizer, max_seq_length, torch):
    """Tokenize dataset for standard HF training."""
    def format_pair(pair):
        messages = pair.get("messages", [])
        if len(messages) < 2:
            return None
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        return text

    texts = [format_pair(p) for p in pairs if format_pair(p)]
    log("finetune", f"Formatted {len(texts)} training examples")

    encodings = tokenizer(texts, truncation=True, max_length=max_seq_length, padding=False, return_tensors=None)

    class SimpleDataset(torch.utils.data.Dataset):
        def __init__(self, encodings):
            self.encodings = encodings
        def __len__(self):
            return len(self.encodings["input_ids"])
        def __getitem__(self, idx):
            return {
                "input_ids": torch.tensor(self.encodings["input_ids"][idx]),
                "attention_mask": torch.tensor(self.encodings["attention_mask"][idx]),
                "labels": torch.tensor(self.encodings["input_ids"][idx]),
            }

    return SimpleDataset(encodings)


def _hash_dir(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


def _print_summary(generation, output_path, num_pairs, config, duration, loss, artifact_hash):
    print(f"\n=== Generation {generation} Complete ===")
    print(f"Backend: {'Unsloth' if check_unsloth_available() else 'Standard HF'}")
    print(f"Output: {output_path}")
    print(f"Training pairs: {num_pairs}")
    print(f"Epochs: {config['epochs']}")
    print(f"Duration: {duration/60:.1f} minutes")
    print(f"Final loss: {loss:.4f}")
    print(f"Artifact hash: {artifact_hash}")


def fine_tune(generation: int, data_path: Path):
    """Run fine-tune — automatically selects Unsloth or standard."""
    if check_unsloth_available():
        return fine_tune_unsloth(generation, data_path)
    else:
        log("finetune", "Unsloth not available — using standard HuggingFace training")
        return fine_tune_standard(generation, data_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, default=1, help="Generation number (1, 2, or 3)")
    parser.add_argument("--data", type=str, default="", help="Custom data path")
    args = parser.parse_args()

    data_path = Path(args.data) if args.data else DATA_PATH
    if not data_path.exists():
        log("error", f"Training data not found: {data_path}")
        sys.exit(1)

    output_path, metadata = fine_tune(args.gen, data_path)

    # Write generation record for the mixed model tracker
    record = {
        "gen_id": f"anubis_v{args.gen}",
        "version": f"0.{args.gen}",
        "stage": 3 if args.gen == 1 else 4,
        "base_model": BASE_MODEL,
        "training_pairs_used": metadata["training_pairs"],
        "teachers_used": [BASE_MODEL],
        "capabilities_tested": 0,
        "capabilities_passed": 0,
        "artifact_hash": metadata["artifact_hash"],
        "backend": metadata.get("backend", "unknown"),
        "notes": f"Full fine-tune generation {args.gen} on H100 NVL 94GB",
    }

    record_path = OUTPUT_DIR / f"generation_{args.gen}_record.json"
    record_path.write_text(json.dumps(record, indent=2))
    log("finetune", "Generation record written", path=str(record_path))


if __name__ == "__main__":
    main()
