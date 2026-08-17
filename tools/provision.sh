#!/usr/bin/env bash
# SIOS build environment provisioning + sanity checks.
set -uo pipefail

ROOT=/mnt/d/SIOS-Build/sios-live

echo "=== mount check ==="
if [ -d /mnt/d ]; then echo "D: mounted OK"; else echo "D: NOT MOUNTED"; exit 1; fi

echo "=== write check ==="
mkdir -p "$ROOT/.probe" && echo "writable OK" && rmdir "$ROOT/.probe"

echo "=== 9p write perf (200 small files) ==="
start=$(date +%s.%N)
for i in $(seq 1 200); do echo test > "$ROOT/.t$i"; done
end=$(date +%s.%N)
rm -f "$ROOT"/.t*
echo "200 files in $(echo "$end - $start" | bc)s"

echo "=== native ext4 write perf (comparison) ==="
mkdir -p /tmp/perfprobe
start=$(date +%s.%N)
for i in $(seq 1 200); do echo test > "/tmp/perfprobe/.t$i"; done
end=$(date +%s.%N)
rm -rf /tmp/perfprobe
echo "200 files in $(echo "$end - $start" | bc)s"

echo "=== gpu check (CUDA in WSL) ==="
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo "nvidia-smi not present in WSL (Ollama runs on Windows host, so not blocking)"
fi

echo "=== ollama reachability from WSL ==="
if curl -s --max-time 5 http://127.0.0.1:11434/api/version >/dev/null 2>&1; then
  echo "ollama OK: $(curl -s --max-time 5 http://127.0.0.1:11434/api/version)"
else
  echo "ollama UNREACHABLE"
fi

echo "=== DONE ==="
