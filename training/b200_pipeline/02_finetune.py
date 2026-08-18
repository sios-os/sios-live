#!/usr/bin/env python3
"""Stage 2: LoRA fine-tune of Qwen 2.5 32B on 4x A100 80GB.

Uses DeepSpeed ZeRO-3 for multi-GPU sharding of model weights.
Performs LoRA fine-tuning (rank 256) on 20,000 training pairs.

LoRA is used instead of full fine-tuning because the 32B model's AdamW
optimizer state (~384GB) exceeds available host RAM (503GB) when combined
with model loading overhead across 4 processes. LoRA reduces the trainable
parameters to ~500M, making optimizer state ~6GB — trivially fits in RAM.

Hardware: 4x A100 80GB = 320 GB total VRAM
Memory breakdown (LoRA with ZeRO-3):
  - Model weights (bf16, frozen): 64 GB (sharded = 16 GB each)
  - LoRA adapters (trainable):    ~1 GB (rank 256, all linear layers)
  - Optimizer state (AdamW):      ~6 GB (for adapter params only)
  - Activations (grad ckpt):      ~20 GB (per GPU, seq_len 2048, batch 4)
  - Total per GPU:                ~43 GB (fits in 80 GB with headroom)

After training, LoRA adapters are merged back into the base model for
GGUF conversion. The merged model is functionally equivalent to a
full fine-tuned model for inference purposes.

Output: /workspace/training_output/anubis_v{gen}/ (merged full model)

Run on 4x A100: deepspeed 02_finetune.py [--gen 1] [--data <path>]
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
# DeepSpeed config resolved relative to THIS file, not the process cwd —
# 00_master.py runs subprocesses with cwd=training/b200_pipeline/, so a
# path like "training/b200_pipeline/deepspeed_zero3.json" would never
# resolve there. Using __file__ makes this robust regardless of cwd.
DEEPSPEED_CONFIG_PATH = str(Path(__file__).resolve().parent / "deepspeed_zero3_lora.json")

# LoRA configuration — high rank for near-full-fine-tuning quality
LORA_R = 256
LORA_ALPHA = 512  # Common practice: alpha = 2 * rank
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

GEN_CONFIGS = {
    1: {  # Generation 1 — broad learning on 20K pairs
        "learning_rate": 1e-4,       # Higher LR for LoRA (10x full FT)
        "epochs": 4,                  # 4 epochs over 20K = 80K examples
        "per_device_train_batch_size": 4,  # Larger batch — LoRA uses less GPU memory
        "gradient_accumulation_steps": 4,  # Effective batch = 4*4*4 = 64
        "warmup_ratio": 0.03,         # 3% warmup
        "max_seq_length": 2048,
        "use_deepspeed": True,
        "deepspeed_config": DEEPSPEED_CONFIG_PATH,
    },
    2: {  # Generation 2 — refined learning on 20K + self-distilled data
        "learning_rate": 5e-5,
        "epochs": 3,
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 4,
        "warmup_ratio": 0.03,
        "max_seq_length": 2048,
        "use_deepspeed": True,
        "deepspeed_config": DEEPSPEED_CONFIG_PATH,
    },
    3: {  # Generation 3 — final polish on further expanded data
        "learning_rate": 2e-5,
        "epochs": 3,
        "per_device_train_batch_size": 4,
        "gradient_accumulation_steps": 4,
        "warmup_ratio": 0.02,
        "max_seq_length": 2048,
        "use_deepspeed": True,
        "deepspeed_config": DEEPSPEED_CONFIG_PATH,
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
    """Run LoRA fine-tune using HuggingFace Trainer + DeepSpeed ZeRO-3.

    IMPORTANT: For ZeRO Stage 3, TrainingArguments(deepspeed=...) must be
    constructed BEFORE AutoModelForCausalLM.from_pretrained() is called.
    HF Transformers hooks into the DeepSpeed config at that point (via
    HfDeepSpeedConfig / zero.Init()) so that model weights are partitioned
    across GPUs *during* loading instead of being fully materialized on
    every rank first (which would OOM immediately for a 32B model).

    After training, LoRA adapters are merged back into the base model
    to produce a complete model suitable for GGUF conversion.
    """
    config = GEN_CONFIGS[generation]
    log("finetune", f"Starting generation {generation} (LoRA fine-tune, 4x A100)", config=config)

    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        TrainingArguments,
        Trainer,
        DataCollatorForSeq2Seq,
    )
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, TaskType

    output_path = OUTPUT_DIR / f"anubis_v{generation}"
    output_path.mkdir(parents=True, exist_ok=True)

    # Resolve and validate the DeepSpeed config BEFORE anything else
    ds_config_path = config.get("deepspeed_config", "")
    if config.get("use_deepspeed"):
        if not ds_config_path or not Path(ds_config_path).exists():
            log("error", f"DeepSpeed config not found: {ds_config_path}")
            raise FileNotFoundError(
                f"DeepSpeed config required but not found at {ds_config_path}. "
                "LoRA fine-tuning a 32B model without ZeRO-3 sharding will OOM."
            )
        log("finetune", f"Using DeepSpeed config: {ds_config_path}")

    # Build training arguments FIRST — this registers the DeepSpeed config
    # via transformers.integrations.deepspeed so that the subsequent
    # from_pretrained() call partitions weights across GPUs during load.
    training_args_kwargs = dict(
        output_dir=str(output_path),
        num_train_epochs=config["epochs"],
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        warmup_ratio=config["warmup_ratio"],
        logging_steps=20,
        save_strategy="no",
        bf16=True,
        gradient_checkpointing=True,
        weight_decay=0.01,
        max_grad_norm=1.0,
        report_to="none",
        seed=42,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        save_safetensors=True,
    )

    if config.get("use_deepspeed"):
        training_args_kwargs["deepspeed"] = ds_config_path
    else:
        training_args_kwargs["optim"] = "adamw_torch"
        training_args_kwargs["lr_scheduler_type"] = "cosine"

    training_args = TrainingArguments(**training_args_kwargs)

    # NOW load tokenizer and model — DeepSpeed ZeRO-3 context is active
    log("finetune", "Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    log("finetune", f"Loading {BASE_MODEL} in bf16 (DeepSpeed ZeRO-3 will shard across GPUs)...")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )

    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()

    log("finetune", "Model loaded", params=sum(p.numel() for p in model.parameters()) / 1e9)

    # Apply LoRA adapters
    lora_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=LORA_TARGET_MODULES,
        bias="none",
    )
    model = get_peft_model(model, lora_config)
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())
    log("finetune", "LoRA adapters applied",
        trainable_params=trainable_params / 1e6,
        total_params=total_params / 1e9,
        trainable_pct=100 * trainable_params / total_params)

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

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        padding=True,
        return_tensors="pt",
    )

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

    # Save LoRA adapter weights (small, ~1-2GB)
    adapter_path = output_path / "adapter"
    adapter_path.mkdir(parents=True, exist_ok=True)
    log("finetune", "Saving LoRA adapter weights...")
    trainer.save_model(str(adapter_path))
    tokenizer.save_pretrained(str(adapter_path))

    # Merge LoRA adapters back into the base model for a complete model
    # that can be converted to GGUF. Only rank 0 does the merge.
    import torch.distributed as dist
    is_main = not dist.is_initialized() or dist.get_rank() == 0

    if is_main:
        log("finetune", "Merging LoRA adapters into base model...")
        from peft import PeftModel
        base_model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        merged_model = PeftModel.from_pretrained(base_model, str(adapter_path))
        merged_model = merged_model.merge_and_unload()
        merged_model.save_pretrained(str(output_path), safe_serialization=True)
        tokenizer.save_pretrained(str(output_path))
        log("finetune", "Merged model saved", path=str(output_path))

    if dist.is_initialized():
        dist.barrier()

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
        "backend": "deepspeed_zero3_lora",
        "gpu": "4x A100 80GB",
        "optimizer": "adamw" if config.get("use_deepspeed") else "adamw_torch",
        "lora_r": LORA_R,
        "lora_alpha": LORA_ALPHA,
        "lora_target_modules": LORA_TARGET_MODULES,
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
    parser.add_argument("--base_model", type=str, default="", help="Override base model path")
    # DeepSpeed/torchrun pass --local_rank automatically; accept and ignore it
    # (the actual local_rank is obtained from the env var LOCAL_RANK by HF/DS)
    parser.add_argument("--local_rank", type=int, default=0, help="Local rank (set by DeepSpeed)")
    args = parser.parse_args()

    global BASE_MODEL
    if args.base_model:
        BASE_MODEL = args.base_model
        log("finetune", f"Using custom base model: {BASE_MODEL}")

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
