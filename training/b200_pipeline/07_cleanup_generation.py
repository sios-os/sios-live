#!/usr/bin/env python3
"""Cleanup: free disk space from a completed generation's raw model files.

Full fine-tuning saves a complete ~64GB HuggingFace model per generation.
Once a generation's self-distillation step has read that model to produce
data for the *next* generation, the raw model directory is no longer
needed (the next generation trains fresh from the base model + accumulated
data, not by continuing from this checkpoint) — except for the FINAL
generation, whose model feeds directly into GGUF conversion.

This keeps disk usage bounded across a 3-generation pipeline instead of
accumulating ~64GB+ per generation indefinitely.

Run: python 07_cleanup_generation.py --gen 1
"""
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/workspace/training_output")


def log(stage, msg, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "stage": stage, "message": msg, **kwargs}
    print(json.dumps(entry, default=str), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, required=True, help="Generation number to clean up")
    args = parser.parse_args()

    model_dir = OUTPUT_DIR / f"anubis_v{args.gen}"
    if not model_dir.exists():
        log("cleanup", f"Nothing to clean — {model_dir} does not exist")
        return

    # Preserve the small metadata file before deleting large model weights
    meta_path = model_dir / "generation_metadata.json"
    if meta_path.exists():
        backup_path = OUTPUT_DIR / f"generation_{args.gen}_metadata_backup.json"
        shutil.copy(meta_path, backup_path)
        log("cleanup", f"Backed up metadata to {backup_path}")

    total_freed = 0
    large_extensions = {".safetensors", ".bin", ".pt", ".pth"}
    for f in model_dir.rglob("*"):
        if f.is_file() and f.suffix in large_extensions:
            total_freed += f.stat().st_size
            f.unlink()

    # Remove any leftover checkpoint-* subdirectories entirely (should not
    # exist given save_strategy="no", but clean up defensively)
    for d in model_dir.glob("checkpoint-*"):
        if d.is_dir():
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            total_freed += size
            shutil.rmtree(d, ignore_errors=True)

    log("cleanup", f"Freed {total_freed / 1e9:.1f} GB from generation {args.gen}", path=str(model_dir))


if __name__ == "__main__":
    main()
