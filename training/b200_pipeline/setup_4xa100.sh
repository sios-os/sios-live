#!/bin/bash
# Setup script for 4x A100 80GB Vast.ai instance
# Installs: deepspeed, datasets, accelerate, and other dependencies
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

# CRITICAL: Full fine-tuning a 32B model with DeepSpeed ZeRO-3 + CPU-offloaded
# optimizer needs the optimizer's fp32 master weights + momentum + variance
# (~12+ bytes/param) in HOST RAM, not GPU VRAM — that's ~400GB+ for 32B
# params. Fail fast here instead of discovering this hours into training.
echo "=== System RAM Check ==="
TOTAL_RAM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_RAM_GB=$((TOTAL_RAM_KB / 1024 / 1024))
echo "Total system RAM: ${TOTAL_RAM_GB} GB"
if [ "$TOTAL_RAM_GB" -lt 400 ]; then
    echo "!!! WARNING: This host has only ${TOTAL_RAM_GB} GB RAM."
    echo "!!! Full fine-tuning a 32B model with DeepSpeed ZeRO-3 CPU-offloaded"
    echo "!!! optimizer needs ~400GB+ RAM. Training will likely OOM on the CPU"
    echo "!!! side or thrash badly. Consider renting a different instance."
fi

# Install dependencies (bitsandbytes NOT needed — DeepSpeed manages its own
# CPU-offloaded optimizer via DeepSpeedCPUAdam, incompatible with bnb kernels)
echo "=== Installing Python dependencies ==="
pip install --upgrade pip
pip install deepspeed datasets accelerate
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
which deepspeed || { echo "ERROR: deepspeed launcher not found on PATH"; exit 1; }

# Check disk space — full fine-tuning generations + GGUF conversion need
# room for: base model HF cache (~64GB), one generation's raw model at a
# time (~64GB, cleaned up between generations), f16 GGUF during conversion
# (~64GB, deleted after quantization), and final quantized GGUF (~13-16GB).
echo "=== Disk Space ==="
df -h /workspace
AVAIL_GB=$(df --output=avail -BG /workspace | tail -1 | tr -dc '0-9')
echo "Available: ${AVAIL_GB} GB"
if [ "$AVAIL_GB" -lt 300 ]; then
    echo "!!! WARNING: Only ${AVAIL_GB} GB free. Recommend 300GB+ for a full"
    echo "!!! 32B fine-tune pipeline across 3 generations."
fi

# Check VRAM
echo "=== VRAM Check ==="
nvidia-smi --query-gpu=memory.total,memory.free --format=csv

echo "=== Setup complete ==="
echo "To run the full 3-generation pipeline:"
echo "  cd /workspace/sios/training/b200_pipeline"
echo "  nohup python 00_master.py > /workspace/pipeline.log 2>&1 &"
echo ""
echo "To resume from a specific stage after an interruption:"
echo "  python 00_master.py --start-from gen2_finetune"
