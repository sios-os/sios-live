#!/usr/bin/env python3
"""Stage 2: Full fine-tune of Qwen 2.5 32B on 4x A100 80GB.

Uses DeepSpeed ZeRO-2 for multi-GPU sharding of optimizer states.
Performs a FULL fine-tune (not LoRA) on 20,000 training pairs.

Hardware: 4x A100 80GB = 320 GB total VRAM
Memory breakdown (8-bit optimizer):
  - Model weights (bf16):     64 GB  (sharded across 4 GPUs = 16 GB each)
  - Gradients (bf16):         64 GB  (sharded = 16 GB each)
  - Optimizer states (8-bit): 64 GB  (sharded = 16 GB each)
  - Activations (grad ckpt):  ~20 GB (per GPU, seq_len 2048, batch 2)
  - Total per GPU:            ~68 GB (fits in 80 GB with headroom)

Output: /workspace/training_output/anubis_v{gen}/ (full fine-tuned model)

Run on 4x A100: deepspeed 02_finetune.py [--gen 1] [--data <path>]
  or: torchrun --nproc_per_node=4 02_finetune.py [--gen 1] [--data <path>]
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
DATA_PATH = OUTPUT_DIR / "training_data_20k.jsonl"

# Training hyperparameters for 20K pairs, 4x A100 80GB
# Single generation with 4 epochs over 20K pairs = 80K total examples
GEN_CONFIGS = {
    1: {  # Generation 1 — broad learning on 20K pairs
        "learning_rate": 2e-5,       # Standard for full fine-tuning
        "epochs": 4,                  # 4 epochs over 20K = 80K examples
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,  # Effective batch = 2*8*4 = 64
        "warmup_ratio": 0.03,         # 3% warmup
        "max_seq_length": 2048,
        "use_8bit_optimizer": True,   # bitsandbytes 8-bit AdamW
        "use_deepspeed": True,
        "deepspeed_config": "training/b200_pipeline/deepspeed_zero2.json",
    },
    2: {  # Generation 2 — refined learning on 20K + self-distilled data
        "learning_rate": 1e-5,
        "epochs": 3,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "warmup_ratio": 0.03,
        "max_seq_length": 2048,
        "use_8bit_optimizer": True,
        "use_deepspeed": True,
        "deepspeed_config": "training/b200_pipeline/deepspeed_zero2.json",
    },
    3: {  # Generation 3 — final polish on further expanded data
        "learning_rate": 5e-6,
        "epochs": 3,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 8,
        "warmup_ratio": 0.02,
        "max_seq_length": 2048,
        "use_8bit_optimizer": True,
        "use_deepspeed": True,
        "deepspeed_config": "training/b200_pipeline/deepspeed_zero2.json",
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
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    log("data", f"Loaded {len(pairs)} training pairs from {path}")
    return pairs


def fine_tune_full(generation: int, data_path: Path):
    """Run full fine-tune using HuggingFace Trainer + DeepSpeed."""
    config = GEN_CONFIGS[generation]
    log("finetune", f"Starting generation {generation} (full fine-tune, 4x A100)", config=config)

    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
    )
    from datasets import Dataset

    output_path = OUTPUT_DIR / f"anubis_v{generation}"
    output_path.mkdir(parents=True, exist_ok=True)

    # Load tokenizer
    log("finetune", "Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model in bf16 — DeepSpeed handles sharding
    log("finetune", f"Loading {BASE_MODEL} in bf16 (DeepSpeed will shard)...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
        # Don't use device_map with DeepSpeed — it handles placement
    )

    # Enable gradient checkpointing to save VRAM
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    log("finetune", "Model loaded", params=sum(p.numel() for p in model.parameters()) / 1e9)

    # Load and prepare dataset
    pairs = load_dataset(data_path)
    max_seq = config["max_seq_length"]

    def format_and_tokenize(pair):
        messages = pair.get("messages", [])
        if len(messages) < 2:
            return None
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
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

    dataset = Dataset.from_list(formatted)

    # Data collator
    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
    )

    # Build training arguments
    training_args_kwargs = dict(
        output_dir=str(output_path),
        num_train_epochs=config["epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        logging_steps=20,
        save_strategy="epoch",
        save_total_limit=2,
        bf16=True,
        gradient_checkpointing=True,
        lr_scheduler_type="cosine",
        weight_decay=0.01,
        max_grad_norm=1.0,
        report_to="none",
        seed=42,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        save_safetensors=True,
    )

    # Use 8-bit optimizer if requested
    if config.get("use_8bit_optimizer"):
        training_args_kwargs["optim"] = "adamw_bnb_8bit"
        log("finetune", "Using 8-bit AdamW optimizer (bitsandbytes)")
    else:
        training_args_kwargs["optim"] = "adamw_torch"

    # Use DeepSpeed if configured
    ds_config_path = config.get("deepspeed_config", "")
    if config.get("use_deepspeed") and ds_config_path and Path(ds_config_path).exists():
        training_args_kwargs["deepspeed"] = ds_config_path
        log("finetune", f"Using DeepSpeed config: {ds_config_path}")

    training_args = TrainingArguments(**training_args_kwargs)

    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    # Train
    log("finetune", "Starting training...")
    start_time = time.time()
    train_result = trainer.train()
    duration = time.time() - start_time

    # Save model (each GPU saves its shard, then we merge)
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
        "duration_hours": duration / 3600,
        "train_loss": train_result.training_loss,
        "timestamp": datetime.utcnow().isoformat(),
        "artifact_hash": _hash_dir(output_path),
        "backend": "deepspeed_zero2",
        "gpu": "4x A100 80GB",
        "optimizer": "adamw_bnb_8bit" if config.get("use_8bit_optimizer") else "adamw_torch",
        "effective_batch_size": (
            config["per_device_train_batch_size"]
            * config["gradient_accumulation_steps"]
            * 4  # 4 GPUs
        ),
    }

    metadata_path = output_path / "generation_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    log("finetune", "Training complete", **metadata)
    _print_summary(generation, output_path, len(pairs), config, duration, train_result.training_loss, metadata["artifact_hash"])
    return output_path, metadata


def _hash_dir(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.read_bytes())
    return h.hexdigest()[:16]


def _print_summary(generation, output_path, num_pairs, config, duration, loss, artifact_hash):
    print(f"\n=== Generation {generation} Complete ===")
    print(f"Backend: DeepSpeed ZeRO-2 + 8-bit AdamW")
    print(f"Output: {output_path}")
    print(f"Training pairs: {num_pairs}")
    print(f"Epochs: {config['epochs']}")
    print(f"Duration: {duration/3600:.1f} hours ({duration/60:.0f} minutes)")
    print(f"Final loss: {loss:.4f}")
    print(f"Artifact hash: {artifact_hash}")
    print(f"GPU: 4x A100 80GB")


def fine_tune(generation: int, data_path: Path):
    """Run full fine-tune."""
    return fine_tune_full(generation, data_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, default=1, help="Generation number")
    parser.add_argument("--data", type=str, default="", help="Custom data path")
    args = parser.parse_args()

    data_path = Path(args.data) if args.data else DATA_PATH
    if not data_path.exists():
        log("error", f"Training data not found: {data_path}")
        sys.exit(1)

    output_path, metadata = fine_tune(args.gen, data_path)

    # Write generation record (the authoritative record lives in
    # anubis/mixed_model.py via 06_track_stage.py — this is a local artifact
    # summary for quick inspection alongside the model files)
    record = {
        "gen_id": f"anubis_v{args.gen}",
        "version": f"1.{args.gen}",
        "base_model": BASE_MODEL,
        "training_pairs_used": metadata["training_pairs"],
        "teachers_used": [BASE_MODEL, "template_generator"],
        "capabilities_tested": 0,
        "capabilities_passed": 0,
        "artifact_hash": metadata["artifact_hash"],
        "backend": metadata.get("backend", "unknown"),
        "notes": f"Full fine-tune generation {args.gen} on 4x A100 80GB",
    }

    record_path = OUTPUT_DIR / f"generation_{args.gen}_record.json"
    record_path.write_text(json.dumps(record, indent=2))
    log("finetune", "Generation record written", path=str(record_path))


if __name__ == "__main__":
    main()
