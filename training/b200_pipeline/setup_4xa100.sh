#!/bin/bash
# Setup script for 4x A100 80GB Vast.ai instance
# Installs: deepspeed, bitsandbytes, datasets, and other dependencies
set -e

echo "=== Setting up 4x A100 environment ==="

# Activate the conda/venv environment
source /opt/miniforge3/etc/profile.d/conda.sh
conda activate main 2>/dev/null || true

# Check GPU count
echo "=== GPU Check ==="
nvidia-smi --query-gpu=name,memory.total --format=csv
GPU_COUNT=$(nvidia-smi -L | wc -l)
echo "GPU count: $GPU_COUNT"
if [ "$GPU_COUNT" -lt 4 ]; then
    echo "WARNING: Expected 4 GPUs, found $GPU_COUNT"
fi

# Install dependencies
echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install deepspeed bitsandbytes datasets accelerate
pip install transformers --upgrade

# Clone the repo
echo "=== Cloning SIOS repo ==="
if [ ! -d /workspace/sios ]; then
    cd /workspace
    git clone https://github.com/sios-os/sios-live.git sios
fi
cd /workspace/sios
git pull

# Verify DeepSpeed
echo "=== Verifying DeepSpeed ==="
python -c "import deepspeed; print(f'DeepSpeed version: {deepspeed.__version__}')"
python -c "import bitsandbytes; print(f'bitsandbytes version: {bitsandbytes.__version__}')"

# Check disk space
echo "=== Disk Space ==="
df -h /workspace

# Check VRAM
echo "=== VRAM Check ==="
nvidia-smi --query-gpu=memory.total,memory.free --format=csv

echo "=== Setup complete ==="
echo "To run the pipeline:"
echo "  cd /workspace/sios/training/b200_pipeline"
echo "  python 00_master.py --start-from finetune"
