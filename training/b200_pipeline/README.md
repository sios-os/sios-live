# ANUBIS H100 NVL Training Pipeline — 24 Hours to Stage 4+

This pipeline fine-tunes Qwen 2.5 32B into ANUBIS's sovereign model
across 3 generations, achieving Stage 3 (full fine-tune) and Stage 4
(iterative improvement) of the mixed model progression.

## Hardware

- **GPU:** H100 NVL 94GB (Vast.ai, ~$1.684/hr)
- **Template:** Unsloth Studio (CUDA 12.4, PyTorch, Unsloth pre-installed)
- **Duration:** 24 hours
- **Cost:** ~$40.42

## Quick Start (on H100 NVL instance)

```bash
# 1. Run setup (installs remaining deps, clones repo)
bash /workspace/sios/training/b200_pipeline/setup_h100_unsloth.sh

# 2. Run the full 24-hour pipeline
python /workspace/sios/training/b200_pipeline/00_master.py

# 3. Or run individual stages
python 01_generate_data.py          # Hours 1-2: Generate training data
python 02_finetune.py --gen 1       # Hours 2-7: First fine-tune (Unsloth)
python 03_evaluate.py --gen 1       # Evaluate generation 1
python 04_self_distill.py --gen 1   # Self-distill from weak spots
python 02_finetune.py --gen 2 --data /workspace/training_output/training_data_gen2.jsonl
python 03_evaluate.py --gen 2 --compare
python 04_self_distill.py --gen 2
python 02_finetune.py --gen 3 --data /workspace/training_output/training_data_gen3.jsonl
python 03_evaluate.py --gen 3 --compare
python 05_convert_gguf.py --gen 3 --quant Q3_K_M --test
```

## Resume After Interruption

```bash
# Check where you left off
cat /workspace/training_output/pipeline_state.json

# Resume from a specific stage
python 00_master.py --start-from gen2

# Skip data generation if already done
python 00_master.py --skip-data
```

## Pipeline Stages (24-hour schedule)

| Stage | Script | Time | What Happens |
|-------|--------|------|-------------|
| 1 | `01_generate_data.py` | 2 hrs | Generate 5000+ training pairs using 32B |
| 2 | `02_finetune.py --gen 1` | 5 hrs | Full fine-tune with Unsloth (Stage 3) |
| 3 | `03_evaluate.py --gen 1` | 1 hr | Evaluate against 15 benchmarks |
| 4 | `04_self_distill.py --gen 1` | 1 hr | Self-distill from weak spots |
| 5 | `02_finetune.py --gen 2` | 5 hrs | Generation 2 fine-tune (Stage 4) |
| 6 | `03_evaluate.py --gen 2` | 1 hr | Evaluate and compare with gen 1 |
| 7 | `04_self_distill.py --gen 2` | 1 hr | Self-distill again |
| 8 | `02_finetune.py --gen 3` | 5 hrs | Generation 3 fine-tune |
| 9 | `03_evaluate.py --gen 3` | 1 hr | Final evaluation |
| 10 | `05_convert_gguf.py` | 1 hr | Convert to GGUF for RTX 5060 Ti |
| Buffer | — | 1 hr | Re-run failed stages or extra work |

## Unsloth Speedup

The pipeline uses Unsloth when available (pre-installed in the Unsloth Studio template):
- 2-5x training speedup
- 60% less VRAM usage
- Full fine-tuning support (not just LoRA)
- Automatic fallback to standard HuggingFace if Unsloth fails

## Training Data Categories

1. **Constitutional** (24 pairs) — All 8 immutable laws, refusal scenarios
2. **Personality** (30 pairs) — Data + JARVIS + Machine characteristics
3. **Knowledge** (300+ pairs) — QA from 804 knowledge documents
4. **Code** (30 pairs) — Code generation, review, and architecture
5. **Reasoning** (20 pairs) — Problem-solving and system design

After self-distillation, the dataset expands to 5000-8000+ pairs.

## Quantization for RTX 5060 Ti (16GB)

| Quant | Size | Quality | Fits 16GB? | Recommended |
|-------|------|---------|------------|-------------|
| Q3_K_M | ~13GB | Good | Yes (room for context) | **Yes** |
| Q3_K_S | ~11GB | Fair | Yes | If context is priority |
| Q4_K_M | ~16GB | Better | Tight | If quality is priority |

**Recommended: Q3_K_M** — fits comfortably with room for 4096 context tokens.

## Cost Comparison

| Option | GPU | Hours | Cost | Outcome |
|--------|-----|-------|------|---------|
| H100 NVL 94GB | 24 | $40.42 | Stage 3+4, 3 generations |
| B200 180GB | 8 | $53.52 | Stage 3+4, 3 generations |
| H100 NVL 94GB | 8 | $13.47 | Stage 3 only, 1 generation |

The H100 NVL for 24 hours is the best value — same outcome, $13 cheaper.

## After Deployment

ANUBIS can then autonomously:
- Run the dream cycle to identify knowledge gaps
- Generate self-distilled training data for those gaps
- Queue it for the next GPU session
- Evaluate his own capabilities
- Prepare Stage 5 completion scripts

Periodic GPU sessions (2-4 hours, monthly) will advance toward Stage 5.
