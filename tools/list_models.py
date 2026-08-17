#!/usr/bin/env python3
"""List available Ollama models with details."""
import json, subprocess, sys

result = subprocess.run(
    ["curl", "-s", "http://127.0.0.1:11434/api/tags"],
    capture_output=True, text=True
)
data = json.loads(result.stdout)
for m in data.get("models", []):
    d = m.get("details", {})
    size_gb = m.get("size", 0) / 1e9
    caps = d.get("capabilities", [])
    print(f"{m['name']:30s}  {size_gb:5.1f}GB  {d.get('parameter_size','?'):>8s}  "
          f"{d.get('quantization_level','?'):>8s}  ctx={d.get('context_length','?')}  "
          f"caps={caps}")
