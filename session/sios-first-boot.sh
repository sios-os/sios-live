#!/bin/bash
# sios-first-boot.sh — Pull Ollama models on first boot.
#
# This script runs once on first boot to download the required models
# since they are not pre-installed in the ISO (to keep it under 4 GiB).
#
# It checks if the model is already present before pulling.
set -e

MODEL="${ANUBIS_MODEL:-qwen2.5-coder:7b}"
EMBED_MODEL="nomic-embed-text"
FLAG="/var/lib/sios/.first-boot-models-done"

echo "[SIOS] First-boot model pull starting..."

# Skip if already done
if [ -f "$FLAG" ]; then
    echo "[SIOS] Models already pulled. Skipping."
    exit 0
fi

# Wait for Ollama to be ready
echo "[SIOS] Waiting for Ollama..."
for i in $(seq 1 60); do
    if curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
        echo "[SIOS] Ollama is ready."
        break
    fi
    sleep 2
done

# Check if we can reach Ollama
if ! curl -s http://127.0.0.1:11434/api/tags > /dev/null 2>&1; then
    echo "[SIOS] WARNING: Ollama not reachable. Models will need to be pulled manually."
    echo "[SIOS] Run: ollama pull $MODEL"
    exit 0
fi

# Check if the coding model is already present
MODELS=$(curl -s http://127.0.0.1:11434/api/tags 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get('models', []):
        print(m.get('name', ''))
except:
    pass
" 2>/dev/null || echo "")

if echo "$MODELS" | grep -q "$MODEL"; then
    echo "[SIOS] Model $MODEL already present."
else
    echo "[SIOS] Pulling $MODEL (this will take a while)..."
    ollama pull "$MODEL" 2>&1 || {
        echo "[SIOS] WARNING: Failed to pull $MODEL."
        echo "[SIOS] Check network connectivity and run: ollama pull $MODEL"
    }
fi

# Check if the embedding model is present
if echo "$MODELS" | grep -q "$EMBED_MODEL"; then
    echo "[SIOS] Embedding model $EMBED_MODEL already present."
else
    echo "[SIOS] Pulling $EMBED_MODEL..."
    ollama pull "$EMBED_MODEL" 2>&1 || {
        echo "[SIOS] WARNING: Failed to pull $EMBED_MODEL."
        echo "[SIOS] Semantic search will use keyword fallback."
    }
fi

# Mark as done
mkdir -p /var/lib/sios
touch "$FLAG"
echo "[SIOS] First-boot model pull complete."
