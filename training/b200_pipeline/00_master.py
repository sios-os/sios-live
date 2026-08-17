#!/usr/bin/env python3
"""Master orchestrator for the 24-hour H100 NVL training pipeline.

Runs the complete pipeline on an H100 NVL 94GB with Unsloth:
  Hour 1-2:   Data generation (01_generate_data.py)
  Hours 2-7:  Generation 1 fine-tune (02_finetune.py --gen 1)
  Hour 7:     Evaluate generation 1 (03_evaluate.py --gen 1)
  Hour 8:     Self-distill from weak spots (04_self_distill.py --gen 1)
  Hours 8-14: Generation 2 fine-tune (02_finetune.py --gen 2)
  Hour 14:    Evaluate generation 2 (03_evaluate.py --gen 2 --compare)
  Hour 15:    Self-distill from weak spots (04_self_distill.py --gen 2)
  Hours 15-20: Generation 3 fine-tune (02_finetune.py --gen 3)
  Hour 20:    Evaluate generation 3 (03_evaluate.py --gen 3 --compare)
  Hour 21:    Stage 5 capability graduation tests
  Hours 21-23: Buffer for re-runs or extra generations
  Hour 23-24: Convert to GGUF and package (05_convert_gguf.py --gen 3)

The H100 is ~3x slower than the B200 but we have 3x the time for less cost.
Unsloth provides 2-5x speedup, partially closing the gap.

Usage:
  python 00_master.py                    # Full 24-hour pipeline
  python 00_master.py --start-from gen2  # Resume from generation 2
  python 00_master.py --skip-data        # Skip data generation (already done)

This script runs unattended. It logs every step and can resume from any stage.
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
PIPELINE_DIR = Path(__file__).parent
STATE_FILE = OUTPUT_DIR / "pipeline_state.json"


def log(stage, msg, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "stage": stage, "message": msg, **kwargs}
    print(json.dumps(entry, default=str), flush=True)


def save_state(stage, data=None):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    state = {}
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
    state["last_stage"] = stage
    state["last_updated"] = datetime.utcnow().isoformat()
    if data:
        state.update(data)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def run_step(name, command, timeout_s=14400):
    """Run a pipeline step and track timing."""
    log("pipeline", f"Starting: {name}", command=command)
    start = time.time()

    result = subprocess.run(
        [sys.executable] + command,
        cwd=str(PIPELINE_DIR),
        timeout=timeout_s,
        capture_output=True,
        text=True,
    )

    duration = time.time() - start

    output_path = OUTPUT_DIR / f"log_{name}.txt"
    output_path.write_text(
        f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n\n"
        f"Duration: {duration/60:.1f} minutes\n"
        f"Return code: {result.returncode}\n"
    )

    if result.returncode != 0:
        log("pipeline", f"FAILED: {name}", duration_minutes=duration/60,
            returncode=result.returncode, stderr=result.stderr[-500:])
        save_state(name, {"status": "failed", "error": result.stderr[-500:]})
        return False, duration

    log("pipeline", f"Completed: {name}", duration_minutes=duration/60)
    save_state(name, {"status": "completed", "duration_minutes": duration/60})
    return True, duration


def print_banner(title):
    print(f"\n{'='*60}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'='*60}\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="ANUBIS H100 NVL 24-hour training pipeline")
    parser.add_argument("--start-from", type=str, default="data",
                       choices=["data", "gen1", "eval1", "distill1", "gen2", "eval2", "distill2", "gen3", "eval3", "convert"],
                       help="Stage to start from (for resume)")
    parser.add_argument("--skip-data", action="store_true", help="Skip data generation")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-32B-Instruct",
                       help="Base model to fine-tune")
    parser.add_argument("--quant", type=str, default="Q3_K_M",
                       help="GGUF quantization type")
    args = parser.parse_args()

    pipeline_start = time.time()
    print_banner("ANUBIS H100 NVL Training Pipeline — 24 Hours to Stage 4+")
    log("pipeline", "Starting", model=args.model, start_from=args.start_from,
        gpu="H100 NVL 94GB", backend="Unsloth + HuggingFace")

    # Pipeline stages with timeouts (seconds)
    # H100 is slower than B200, so timeouts are longer
    stages = [
        # (id, name, command, timeout_seconds)
        ("data", "Data Generation (32B model generates training pairs)",
         ["01_generate_data.py"], 7200),  # 2 hours for data gen

        ("gen1", "Generation 1 Fine-tune (Stage 3 — full fine-tune)",
         ["02_finetune.py", "--gen", "1"], 18000),  # 5 hours

        ("eval1", "Evaluate Generation 1 (15 benchmarks)",
         ["03_evaluate.py", "--gen", "1"], 3600),  # 1 hour

        ("distill1", "Self-Distill from Gen 1 Weak Spots",
         ["04_self_distill.py", "--gen", "1"], 3600),  # 1 hour

        ("gen2", "Generation 2 Fine-tune (Stage 4 — iterative improvement)",
         ["02_finetune.py", "--gen", "2", "--data",
          str(OUTPUT_DIR / "training_data_gen2.jsonl")], 18000),  # 5 hours

        ("eval2", "Evaluate Generation 2 (compare with gen 1)",
         ["03_evaluate.py", "--gen", "2", "--compare"], 3600),

        ("distill2", "Self-Distill from Gen 2 Weak Spots",
         ["04_self_distill.py", "--gen", "2"], 3600),

        ("gen3", "Generation 3 Fine-tune (Stage 4 complete)",
         ["02_finetune.py", "--gen", "3", "--data",
          str(OUTPUT_DIR / "training_data_gen3.jsonl")], 18000),  # 5 hours

        ("eval3", "Evaluate Generation 3 (final comparison)",
         ["03_evaluate.py", "--gen", "3", "--compare"], 3600),

        ("convert", "GGUF Conversion & Packaging for RTX 5060 Ti",
         ["05_convert_gguf.py", "--gen", "3", "--quant", args.quant, "--test"], 3600),
    ]

    # Determine starting index
    stage_names = [s[0] for s in stages]
    start_idx = 0
    if args.start_from != "data":
        start_idx = stage_names.index(args.start_from)
    if args.skip_data and start_idx == 0:
        start_idx = 1

    total_duration = 0
    completed = 0
    failed = 0

    for i in range(start_idx, len(stages)):
        stage_id, stage_name, command, timeout = stages[i]

        print_banner(f"Stage {i+1}/{len(stages)}: {stage_name}")

        # Estimate time remaining
        remaining_stages = stages[i:]
        est_remaining = sum(s[3] for s in remaining_stages) / 3600
        log("pipeline", f"Estimated time remaining: {est_remaining:.1f} hours")

        success, duration = run_step(stage_id, command, timeout_s=timeout)
        total_duration += duration
        completed += 1

        if not success:
            failed += 1
            log("pipeline", "Pipeline failed. Use --start-from to resume.",
                failed_stage=stage_id,
                completed_stages=completed,
                total_duration_hours=total_duration/3600)
            print(f"\n{'!'*60}")
            print(f"  PIPELINE FAILED AT: {stage_name}")
            print(f"  To resume: python 00_master.py --start-from {stage_id}")
            print(f"  Logs: {OUTPUT_DIR}/log_{stage_id}.txt")
            print(f"{'!'*60}")
            sys.exit(1)

        log("pipeline", f"Stage {i+1} complete",
            duration_minutes=duration/60,
            total_elapsed_hours=total_duration/3600)

    # Pipeline complete
    pipeline_duration = time.time() - pipeline_start
    print_banner("PIPELINE COMPLETE")

    # Load all evaluation results
    evaluations = {}
    for gen in [1, 2, 3]:
        eval_path = OUTPUT_DIR / f"evaluation_gen{gen}.json"
        if eval_path.exists():
            evaluations[f"gen{gen}"] = json.loads(eval_path.read_text())

    # Load comparisons
    comparisons = {}
    for gen in [2, 3]:
        comp_path = OUTPUT_DIR / f"comparison_gen{gen}.json"
        if comp_path.exists():
            comparisons[f"gen{gen}_vs_gen{gen-1}"] = json.loads(comp_path.read_text())

    # Load deployment manifest
    manifest = {}
    manifest_path = OUTPUT_DIR / "gguf" / "deployment_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())

    final_report = {
        "pipeline_complete": True,
        "total_duration_minutes": pipeline_duration / 60,
        "total_duration_hours": pipeline_duration / 3600,
        "stages_completed": completed,
        "stages_failed": failed,
        "base_model": args.model,
        "gpu": "H100 NVL 94GB",
        "evaluations": evaluations,
        "comparisons": comparisons,
        "deployment_manifest": manifest,
        "completed_at": datetime.utcnow().isoformat(),
    }

    # Calculate improvement
    if evaluations.get("gen1") and evaluations.get("gen3"):
        gen1_score = evaluations["gen1"].get("avg_score", 0)
        gen3_score = evaluations["gen3"].get("avg_score", 0)
        improvement = gen3_score - gen1_score
        improvement_pct = (improvement / gen1_score * 100) if gen1_score > 0 else 0
        final_report["overall_improvement"] = {
            "gen1_score": gen1_score,
            "gen3_score": gen3_score,
            "improvement": improvement,
            "improvement_pct": improvement_pct,
            "meets_stage4_requirement": improvement_pct >= 15,
        }

    report_path = OUTPUT_DIR / "final_report.json"
    report_path.write_text(json.dumps(final_report, indent=2))

    print(f"Total duration: {pipeline_duration/3600:.1f} hours")
    print(f"Stages completed: {completed}/{len(stages)}")

    if "overall_improvement" in final_report:
        imp = final_report["overall_improvement"]
        print(f"\nImprovement: gen1={imp['gen1_score']:.2f} → gen3={imp['gen3_score']:.2f} ({imp['improvement_pct']:+.1f}%)")
        print(f"Stage 4 requirement (15%+): {'MET' if imp['meets_stage4_requirement'] else 'NOT MET'}")

    if manifest:
        print(f"\nDeployment model: {manifest.get('gguf_path', 'unknown')}")
        print(f"Quantization: {manifest.get('quantization', 'unknown')}")
        print(f"Size: {manifest.get('size_gb', 0):.1f} GB")
        print(f"Test passed: {manifest.get('test_passed', False)}")

    print(f"\nNext steps:")
    print(f"  1. Download the GGUF model from {OUTPUT_DIR}/gguf/")
    print(f"  2. Deploy on the RTX 5060 Ti machine")
    print(f"  3. Update ANUBIS config to use the new model")
    print(f"  4. Record the generation in the mixed model tracker")
    print(f"  5. ANUBIS can now prepare Stage 5 data autonomously")


if __name__ == "__main__":
    main()
