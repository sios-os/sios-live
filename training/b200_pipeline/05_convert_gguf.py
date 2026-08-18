#!/usr/bin/env python3
"""Stage 5: Convert fine-tuned model to GGUF for deployment on RTX 5060 Ti.

Converts the full fine-tuned HuggingFace model to GGUF format using
llama.cpp's convert script, then quantizes to fit the 5060 Ti's 16GB VRAM.

Since we're doing FULL fine-tuning (not LoRA), the model is saved as a
complete HuggingFace model with config.json — no merge step needed.

Quantization options:
  - Q3_K_M (~13GB) — fits 16GB with room for context
  - Q4_K_M (~16GB) — tight fit, better quality
  - Q5_K_M (~19GB) — too large for 16GB, use Q4 instead

Recommended: Q3_K_M for 32B (room for 4096 context), Q4_K_M as alternative

Run on A100: python 05_convert_gguf.py --gen 1 --quant Q3_K_M --test
"""
import json
import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

BASE_MODEL = "Qwen/Qwen2.5-32B-Instruct"
OUTPUT_DIR = Path("/workspace/training_output")
GGUF_DIR = OUTPUT_DIR / "gguf"


def log(stage: str, msg: str, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "stage": stage, "message": msg, **kwargs}
    print(json.dumps(entry, default=str), flush=True)


def convert_to_gguf(model_path: Path, output_dir: Path):
    """Convert HuggingFace model to GGUF format.

    Since we do full fine-tuning, the model is already a complete HF model
    with config.json — no LoRA merge needed.
    """
    log("convert", f"Converting {model_path} to GGUF...")

    # Clone and build llama.cpp
    llama_cpp_dir = Path("/workspace/llama.cpp")
    if not llama_cpp_dir.exists():
        log("convert", "Cloning llama.cpp...")
        subprocess.run(
            ["git", "clone", "https://github.com/ggerganov/llama.cpp.git", str(llama_cpp_dir)],
            check=True,
        )

    # Build llama.cpp (skip if already built)
    quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"
    if not quantize_bin.exists():
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
            log("convert", "No nvcc found — building CPU-only llama.cpp")
            cmake_args = ["cmake", "..", "-DGGML_CUDA=OFF"]

        subprocess.run(cmake_args, cwd=str(build_dir), check=True, env=env)
        subprocess.run(["make", "-j", "16"], cwd=str(build_dir), check=True, env=env)
    else:
        env = os.environ.copy()
        log("convert", "llama.cpp already built, skipping")

    # Convert to GGUF (f16 first, then quantize)
    convert_script = llama_cpp_dir / "convert_hf_to_gguf.py"
    gguf_f16_path = output_dir / f"{model_path.name}.f16.gguf"

    if not gguf_f16_path.exists():
        log("convert", f"Running conversion: {convert_script}")
        subprocess.run([
            sys.executable, str(convert_script),
            str(model_path),
            "--outfile", str(gguf_f16_path),
            "--outtype", "f16",
        ], check=True, env=env)
        log("convert", f"GGUF f16 created", size_gb=gguf_f16_path.stat().st_size / 1e9)
    else:
        log("convert", f"f16 GGUF already exists: {gguf_f16_path}")

    return gguf_f16_path


def quantize_gguf(gguf_path: Path, quant_type: str, output_dir: Path):
    """Quantize GGUF model to the specified type."""
    log("quant", f"Quantizing to {quant_type}...")

    llama_cpp_dir = Path("/workspace/llama.cpp")
    quantize_bin = llama_cpp_dir / "build" / "bin" / "llama-quantize"

    quantized_path = output_dir / f"{gguf_path.stem.replace('.f16', '')}.{quant_type}.gguf"

    if quantized_path.exists():
        log("quant", f"Already exists: {quantized_path}")
        return quantized_path

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

    # Start server in background (CPU mode — we don't need GPU for a quick test)
    proc = subprocess.Popen(
        [str(server_bin), "-m", str(gguf_path), "--port", "8899", "--n-gpu-layers", "0"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    time.sleep(15)  # Wait for server to start

    try:
        import urllib.request
        data = json.dumps({
            "messages": [
                {"role": "system", "content": "You are ANUBIS, a sovereign synthetic intelligence."},
                {"role": "user", "content": "Hello, who are you?"},
            ],
            "max_tokens": 100,
        }).encode()

        req = urllib.request.Request(
            "http://localhost:8899/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())

        response = result["choices"][0]["message"]["content"]
        log("test", "Inference test passed", response=response[:200])
        return True
    except Exception as e:
        log("test", "Inference test failed", error=str(e))
        return False
    finally:
        proc.terminate()
        proc.wait(timeout=10)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, default=1, help="Generation number")
    parser.add_argument("--quant", type=str, default="Q3_K_M",
                        help="Quantization type (Q3_K_M, Q4_K_M, Q5_K_M)")
    parser.add_argument("--test", action="store_true", help="Run inference test")
    args = parser.parse_args()

    model_path = OUTPUT_DIR / f"anubis_v{args.gen}"
    if not model_path.exists():
        log("error", f"Model not found: {model_path}")
        sys.exit(1)

    GGUF_DIR.mkdir(parents=True, exist_ok=True)

    # Convert to GGUF
    gguf_f16_path = convert_to_gguf(model_path, GGUF_DIR)

    # Quantize
    quantized_path = quantize_gguf(gguf_f16_path, args.quant, GGUF_DIR)

    # Test
    test_passed = False
    if args.test:
        test_passed = test_inference(quantized_path)

    # Record metadata
    metadata = {
        "generation": args.gen,
        "model_path": str(model_path),
        "gguf_f16_path": str(gguf_f16_path),
        "quantized_path": str(quantized_path),
        "quant_type": args.quant,
        "quantized_size_gb": quantized_path.stat().st_size / 1e9,
        "test_passed": test_passed,
        "timestamp": datetime.utcnow().isoformat(),
    }

    metadata_path = GGUF_DIR / "conversion_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))

    log("convert", "Conversion complete", **metadata)

    # Clean up f16 to save disk space
    if quantized_path.exists():
        log("convert", "Cleaning up f16 GGUF to save disk space...")
        gguf_f16_path.unlink(missing_ok=True)

    print(f"\n=== GGUF Conversion Complete ===")
    print(f"Model: {quantized_path}")
    print(f"Size: {quantized_path.stat().st_size / 1e9:.1f} GB")
    print(f"Quantization: {args.quant}")
    print(f"Test passed: {test_passed}")


if __name__ == "__main__":
    main()
