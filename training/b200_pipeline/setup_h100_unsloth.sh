#!/usr/bin/env bash
# Setup script for Unsloth Studio template on Vast.ai H100 NVL 94GB.
# The Unsloth Studio template already has CUDA 12.4, PyTorch, and Unsloth.
# This script installs the remaining dependencies and clones the repo.
#
# Usage:
#   bash setup_h100_unsloth.sh

set -e

echo "=== ANUBIS H100 NVL Training Pipeline — Setup ==="

# 1. Verify GPU
echo "--- Verifying GPU ---"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    print(f'VRAM: {vram:.0f} GB')
    print(f'PyTorch version: {torch.__version__}')
    print(f'CUDA version: {torch.version.cuda}')
"

# 2. Install additional Python dependencies
echo "--- Installing additional dependencies ---"
pip install --upgrade pip wheel 2>/dev/null || true
pip install \
    transformers accelerate \
    datasets sentencepiece \
    bitsandbytes \
    peft trl \
    numpy scipy scikit-learn \
    2>/dev/null || true

# Unsloth should already be in the template, but verify
echo "--- Verifying Unsloth ---"
python3 -c "
try:
    from unsloth import FastLanguageModel
    print('Unsloth: available')
except ImportError:
    print('Unsloth: not found — installing...')
    import subprocess
    subprocess.run(['pip', 'install', 'unsloth'], check=False)
" || true

# 3. Install build tools for llama.cpp (needed for GGUF conversion)
echo "--- Installing build tools ---"
sudo apt-get update -qq 2>/dev/null || apt-get update -qq 2>/dev/null || true
sudo apt-get install -y -qq \
    git cmake build-essential \
    libcurl4-openssl-dev \
    2>/dev/null || apt-get install -y -qq \
    git cmake build-essential \
    libcurl4-openssl-dev \
    2>/dev/null || true

# 4. Clone SIOS repository
if [ ! -d "/workspace/sios" ]; then
    echo "--- Cloning SIOS repository ---"
    mkdir -p /workspace
    git clone https://github.com/sios-os/sios-live.git /workspace/sios || {
        echo "Git clone failed — copying from local mount if available..."
        if [ -d "/mnt/d/SIOS-Build/sios-live" ]; then
            cp -r /mnt/d/SIOS-Build/sios-live /workspace/sios
        else
            echo "ERROR: Cannot obtain repository. Upload manually."
            exit 1
        fi
    }
fi

# 5. Create output directory
mkdir -p /workspace/training_output

# 6. Symlink pipeline scripts to /workspace
ln -sf /workspace/sios/training/b200_pipeline /workspace/pipeline 2>/dev/null || true

# 7. Final verification
echo ""
echo "=== Setup Verification ==="
python3 -c "
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.version.cuda}')
print(f'GPU VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.0f} GB')

try:
    from unsloth import FastLanguageModel
    print('Unsloth: ready')
except:
    print('Unsloth: not available (will use standard training)')

import transformers
print(f'Transformers: {transformers.__version__}')
print('All dependencies ready.')
"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next step:"
echo "  python /workspace/sios/training/b200_pipeline/00_master.py"
echo ""
echo "Or run individual stages:"
echo "  python /workspace/sios/training/b200_pipeline/01_generate_data.py"
echo "  python /workspace/sios/training/b200_pipeline/02_finetune.py --gen 1"
echo ""
echo "The pipeline is configured for:"
echo "  GPU: H100 NVL 94GB"
echo "  Model: Qwen 2.5 32B (full fine-tune)"
echo "  Duration: ~24 hours (3 generations)"
echo "  Cost: ~$40"
