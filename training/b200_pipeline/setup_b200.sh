#!/usr/bin/env bash
# Setup script — run this FIRST on the B200 GPU instance.
# Installs all dependencies needed for the training pipeline.
#
# Usage:
#   wget -O - https://raw.githubusercontent.com/.../setup_b200.sh | bash
#   OR:
#   bash setup_b200.sh

set -e

echo "=== ANUBIS B200 Training Pipeline — Setup ==="

# 1. System packages
echo "--- Installing system packages ---"
sudo apt-get update -qq
sudo apt-get install -y -qq \
    python3 python3-pip python3-venv \
    git cmake build-essential \
    libcurl4-openssl-dev \
    nvidia-cuda-toolkit \
    2>/dev/null || true

# 2. Python environment
echo "--- Setting up Python environment ---"
python3 -m venv /workspace/venv
source /workspace/venv/bin/activate
pip install --upgrade pip wheel

# 3. ML dependencies
echo "--- Installing ML dependencies ---"
pip install \
    torch torchvision torchaudio \
    transformers accelerate \
    datasets sentencepiece \
    bitsandbytes \
    peft trl \
    wandb \
    numpy scipy scikit-learn

# 4. Clone SIOS repository (if not already present)
if [ ! -d "/workspace/anubis" ]; then
    echo "--- Cloning SIOS repository ---"
    # If the repo is available locally, copy it. Otherwise clone from git.
    if [ -d "/mnt/d/SIOS-Build/sios-live" ]; then
        cp -r /mnt/d/SIOS-Build/sios-live/* /workspace/
    else
        git clone https://github.com/AnpuCrownTechnologies/sios-live.git /workspace/sios
        cp -r /workspace/sios/* /workspace/
    fi
fi

# 5. Create output directory
mkdir -p /workspace/training_output

# 6. Verify GPU
echo "--- Verifying GPU ---"
python3 -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
    print(f'VRAM: {torch.cuda.get_device_properties(0).total_memory / 1e9:.0f} GB')
    print(f'PyTorch version: {torch.__version__}')
"

# 7. Verify transformers
echo "--- Verifying transformers ---"
python3 -c "
from transformers import AutoModelForCausalLM, AutoTokenizer
import transformers
print(f'Transformers version: {transformers.__version__}')
"

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Upload training data (or let the pipeline generate it)"
echo "  2. Run: python /workspace/training/b200_pipeline/00_master.py"
echo "  3. Monitor progress — the pipeline runs unattended for ~8 hours"
echo "  4. Download the GGUF model from /workspace/training_output/gguf/"
echo ""
echo "To resume if interrupted:"
echo "  python /workspace/training/b200_pipeline/00_master.py --start-from <stage>"
echo ""
echo "Stages: data, gen1, eval1, distill1, gen2, eval2, distill2, gen3, eval3, convert"
