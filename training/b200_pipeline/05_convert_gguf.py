#!/usr/bin/env python3
"""Stage 5: Convert fine-tuned model to GGUF for deployment on RTX 5060 Ti.

Converts the HuggingFace model to GGUF format using llama.cpp's
convert script, then quantizes to fit the 5060 Ti's 16GB VRAM.

Quantization options:
  - Q3_K_M (~13GB) — fits 16GB with room for context
  - Q4_K_M (~16GB) — tight fit, better quality
  - Q5_K_M (~19GB) — too large for 16GB, use Q4 instead
  - Q8_0 (~32GB)   — too large for 16GB

Recommended: Q3_K_M for 32B, Q8_0 for 7B/14B

Run on B200: python 05_convert_gguf.py --gen 3 --quant Q3_K_M
"""
import json
import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/workspace/training_output")


def log(stage, msg, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "stage": stage, "message": msg, **kwargs}
    print(json.dumps(entry, default=str))


def convert_to_gguf(model_path: Path, output_dir: Path):
    """Convert HuggingFace model to GGUF format."""
    log("convert", f"Converting {model_path} to GGUF...")

    # Check if this is a LoRA adapter (no config.json) and merge if needed
    config_path = model_path / "config.json"
    adapter_config = model_path / "adapter_config.json"

    if not config_path.exists() and adapter_config.exists():
        log("convert", "Found LoRA adapter — merging with base model...")

        # Read adapter config to get base model
        import json as _json
        adapter_cfg = _json.loads(adapter_config.read_text())
        base_model_name = adapter_cfg.get("base_model_name_or_path", "Qwen/Qwen2.5-32B-Instruct")

        # Override 4-bit quantized base with original full-precision model
        if "bnb-4bit" in base_model_name or "4bit" in base_model_name:
            base_model_name = "Qwen/Qwen2.5-32B-Instruct"
            log("convert", f"Overriding 4-bit base with full-precision: {base_model_name}")
        else:
            log("convert", f"Base model: {base_model_name}")

        # Merge LoRA into base model — must load in full bf16, not 4-bit
        merged_path = output_dir / "anubis_v3_merged"
        merge_script = f"""
import torch
from unsloth import FastLanguageModel
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

print("Loading base model in full bf16: {base_model_name}")
base_model = AutoModelForCausalLM.from_pretrained(
    "{base_model_name}",
    torch_dtype=torch.bfloat16,
    device_map="cpu",
    low_cpu_mem_usage=True,
)
tokenizer = AutoTokenizer.from_pretrained("{base_model_name}")

print("Loading LoRA adapter: {model_path}")
model = PeftModel.from_pretrained(base_model, "{model_path}")

print("Merging adapter into base model...")
model = model.merge_and_unload()

# Remove any quantization config so llama.cpp can convert it
if hasattr(model.config, "quantization_config"):
    del model.config.quantization_config

print("Saving merged model to: {merged_path}")
model.save_pretrained("{merged_path}", safe_serialization=True)
tokenizer.save_pretrained("{merged_path}")
print("Merge complete!")
"""
        subprocess.run(
            [sys.executable, "-c", merge_script],
            check=True,
            env={**os.environ, "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"},
        )
        model_path = merged_path
        log("convert", f"Merged model saved to {model_path}")

    # Clone llama.cpp if not present
    llama_cpp_dir = Path("/workspace/llama.cpp")
    if not llama_cpp_dir.exists():
        log("convert", "Cloning llama.cpp...")
        subprocess.run(
            ["git", "clone", "https://github.com/ggerganov/llama.cpp.git", str(llama_cpp_dir)],
            check=True,
        )

    # Build llama.cpp
    log("convert", "Building llama.cpp...")
    build_dir = llama_cpp_dir / "build"
    build_dir.mkdir(exist_ok=True)

    # Find nvcc for CUDA support
    nvcc_path = None
    for candidate in ["/usr/local/cuda/bin/nvcc", "/opt/cuda/bin/nvcc"]:
        if Path(candidate).exists():
            nvcc_path = candidate
            break

    env = os.environ.copy()
    if nvcc_path:
        env["CUDACXX"] = nvcc_path
        cmake_args = ["cmake", "..", "-DGGML_CUDA=ON"]
    else:
        # No CUDA compiler — build CPU-only (fine for conversion, slower for inference test)
        log("convert", "No nvcc found — building CPU-only llama.cpp")
        cmake_args = ["cmake", "..", "-DGGML_CUDA=OFF"]

    subprocess.run(cmake_args, cwd=str(build_dir), check=True, env=env)
    subprocess.run(["make", "-j", "16"], cwd=str(build_dir), check=True, env=env)

    # Convert to GGUF
    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    gguf_path = output_dir / f"{model_path.name}.gguf"

    log("convert", f"Running conversion: {convert_script}")
    subprocess.run([
        sys.executable, str(convert_script),
        str(model_path),
        "--outfile", str(gguf_path),
        "--outtype", "f16",  # Convert to f16 first, quantize in next step
    ], check=True)

    log("convert", f"GGUF created: {gguf_path}", size_gb=gguf_path.stat().st_size / 1e9)
    return gguf_path


def quantize_gguf(gguf_path: Path, quant_type: str, output_dir: Path):
    """Quantize GGUF model to the specified type."""
    log("quant", f"Quantizing to {quant_type}...")

    llama_cpp_dir = Path("/workspace/llama.cpp")
    quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"

    quantized_path = output_dir / f"{gguf_path.stem}.{quant_type}.gguf"

    subprocess.run([
        str(quantize_bin),
        str(gguf_path),
        str(quantized_path),
        quant_type,
    ], check=True)

    size_gb = quantized_path.stat().st_size / 1e9
    log("quant", f"Quantized model created", path=str(quantized_path), size_gb=size_gb)

    return quantized_path


def test_inference(gguf_path: Path):
    """Quick test that the GGUF model works with llama.cpp."""
    log("test", "Testing GGUF model with llama.cpp server...")

    llama_cpp_dir = Path("/workspace/llama.cpp")
    server_bin = llama_cpp_dir / "build" / "bin" / "llama-server"

    # Start server in background
    proc = subprocess.Popen(
        [str(server_bin), "-m", str(gguf_path), "--port", "8899", "--n-gpu-layers", "99"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    time.sleep(10)  # Wait for server to start

    try:
        import urllib.request
        data = json.dumps({
            "prompt": "Who are you?",
            "n_predict": 128,
            "temperature": 0.2,
        }).encode()
        req = urllib.request.Request(
            "http://127.0.0.1:8899/completion",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        response_text = result.get("content", "")

        log("test", "Inference test passed", response=response_text[:200])
        return True, response_text
    except Exception as e:
        log("test", "Inference test failed", error=str(e))
        return False, str(e)
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, required=True, help="Generation to convert")
    parser.add_argument("--quant", type=str, default="Q3_K_M",
                       choices=["Q3_K_M", "Q3_K_S", "Q4_K_M", "Q4_K_S", "Q5_K_M", "Q6_K", "Q8_0"],
                       help="Quantization type (default: Q3_K_M for 32B on 16GB VRAM)")
    parser.add_argument("--test", action="store_true", help="Test inference after conversion")
    args = parser.parse_args()

    model_path = OUTPUT_DIR / f"anubis_v{args.gen}"
    if not model_path.exists():
        log("error", f"Model not found: {model_path}")
        sys.exit(1)

    output_dir = OUTPUT_DIR / "gguf"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Convert to GGUF
    gguf_path = convert_to_gguf(model_path, output_dir)

    # Quantize
    quantized_path = quantize_gguf(gguf_path, args.quant, output_dir)

    # Test
    test_passed = False
    test_response = ""
    if args.test:
        test_passed, test_response = test_inference(quantized_path)

    # Write deployment manifest
    manifest = {
        "model_name": f"anubis-v{args.gen}",
        "generation": args.gen,
        "base_model": "Qwen/Qwen2.5-32B-Instruct",
        "gguf_path": str(quantized_path),
        "quantization": args.quant,
        "size_gb": quantized_path.stat().st_size / 1e9,
        "target_hardware": "RTX 5060 Ti 16GB",
        "test_passed": test_passed,
        "test_response": test_response[:500],
        "created_at": datetime.utcnow().isoformat(),
        "deployment_config": {
            "llama_server_args": [
                "-m", str(quantized_path),
                "--port", "8080",
                "--n-gpu-layers", "99",
                "--ctx-size", "4096",
                "--threads", "8",
            ],
            "environment": {
                "ANUBIS_INFERENCE_BACKEND": "llama_subprocess",
                "ANUBIS_MODEL_PATH": str(quantized_path),
            },
        },
    }

    manifest_path = output_dir / "deployment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))

    print(f"\n=== GGUF Conversion Complete ===")
    print(f"Model: {quantized_path}")
    print(f"Quantization: {args.quant}")
    print(f"Size: {manifest['size_gb']:.1f} GB")
    print(f"Test passed: {test_passed}")
    print(f"Manifest: {manifest_path}")
    print(f"\nDownload {quantized_path} to the deployment machine.")
    print(f"Target: RTX 5060 Ti 16GB VRAM")


if __name__ == "__main__":
    main()
