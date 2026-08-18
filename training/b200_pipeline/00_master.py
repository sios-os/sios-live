#!/usr/bin/env python3
"""Master orchestrator for the 4x A100 80GB, 3-generation training pipeline.

Runs full fine-tuning (not LoRA) across 3 generations with self-distillation
between them, and wires progress into anubis/mixed_model.py so the stage
tracker (Stage 1-6 of ANUBIS's sovereignty progression) actually advances —
this was previously missing from every training pipeline run.

Flow:
  Gen 1: finetune (20K pairs) -> evaluate -> track stage -> self-distill
  Gen 2: finetune (20K + self-distilled) -> evaluate --compare -> track stage -> self-distill
  Gen 3: finetune (expanded again) -> evaluate --compare -> track stage
  Convert: GGUF conversion + quantization for RTX 5060 Ti

Hardware: 4x A100 80GB = 320 GB total VRAM
Method: Full fine-tuning with DeepSpeed ZeRO-3 + CPU-offloaded AdamW

Usage:
  python 00_master.py                       # Full 3-generation pipeline
  python 00_master.py --start-from gen2_finetune   # Resume from generation 2
  python 00_master.py --start-from convert  # Resume from conversion only

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
DATA_20K = OUTPUT_DIR / "training_data_20k.jsonl"


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


def run_step(name, command, timeout_s=54000, use_deepspeed=False):
    """Run a pipeline step and track timing.

    Streams subprocess output line-by-line to log_{name}.txt AS IT HAPPENS,
    rather than buffering everything until the process exits. Steps here
    run for up to ~15 hours (full fine-tuning of a 32B model) — with
    capture_output=True the log file would stay empty for the entire
    duration, making it impossible to monitor progress or diagnose a
    hang/stall before the whole step times out.
    """
    log("pipeline", f"Starting: {name}", command=command)
    start = time.time()

    env = os.environ.copy()
    repo_root = str(Path(__file__).resolve().parent.parent.parent)
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    env["PYTHONUNBUFFERED"] = "1"

    if use_deepspeed:
        cmd = ["deepspeed", "--num_gpus=4"] + [str(PIPELINE_DIR / command[0])] + command[1:]
    else:
        cmd = [sys.executable] + command

    output_path = OUTPUT_DIR / f"log_{name}.txt"
    returncode = None
    timed_out = False

    with open(output_path, "w", encoding="utf-8", errors="replace") as log_file:
        proc = subprocess.Popen(
            cmd,
            cwd=str(PIPELINE_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        try:
            deadline = start + timeout_s
            for line in proc.stdout:
                log_file.write(line)
                log_file.flush()
                if time.time() > deadline:
                    raise subprocess.TimeoutExpired(cmd, timeout_s)
            proc.wait(timeout=max(1, deadline - time.time()))
            returncode = proc.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            proc.kill()
            proc.wait()
            log_file.write(f"\n\n[TIMED OUT after {timeout_s}s — process killed]\n")
            returncode = -1

    duration = time.time() - start

    with open(output_path, "a", encoding="utf-8") as log_file:
        log_file.write(
            f"\n\nDuration: {duration/60:.1f} minutes\n"
            f"Return code: {returncode}\n"
        )

    if timed_out or returncode != 0:
        tail = ""
        try:
            tail = output_path.read_text(encoding="utf-8", errors="replace")[-500:]
        except Exception:
            pass
        log("pipeline", f"FAILED: {name}", duration_minutes=duration/60,
            returncode=returncode, timed_out=timed_out, tail=tail)
        save_state(name, {"status": "failed", "error": tail})
        return False, duration

    log("pipeline", f"Completed: {name}", duration_minutes=duration/60)
    save_state(name, {"status": "completed", "duration_minutes": duration/60})
    return True, duration


def print_banner(title):
    print(f"\n{'='*60}", flush=True)
    print(f"  {title}", flush=True)
    print(f"{'='*60}\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="ANUBIS 4x A100 3-generation training pipeline")
    parser.add_argument("--start-from", type=str, default="generate_data",
                       choices=["generate_data",
                                "gen1_finetune", "gen1_eval", "gen1_track", "gen1_distill", "gen1_cleanup",
                                "gen2_finetune", "gen2_eval", "gen2_track", "gen2_distill", "gen2_cleanup",
                                "gen3_finetune", "gen3_eval", "gen3_track", "convert"],
                       help="Stage to start from (for resume)")
    parser.add_argument("--model", type=str, default="Qwen/Qwen2.5-32B-Instruct",
                       help="Base model to fine-tune")
    parser.add_argument("--quant", type=str, default="Q3_K_M",
                       help="GGUF quantization type")
    args = parser.parse_args()

    pipeline_start = time.time()
    print_banner("ANUBIS 4x A100 Training Pipeline — 3 Generations, Full Fine-Tune, Stage Tracking")
    log("pipeline", "Starting", model=args.model, start_from=args.start_from,
        gpu="4x A100 80GB", backend="DeepSpeed ZeRO-3 + CPU-offloaded AdamW")

    gen2_data = str(OUTPUT_DIR / "training_data_gen2.jsonl")
    gen3_data = str(OUTPUT_DIR / "training_data_gen3.jsonl")

    stages = [
        # (id, name, command, timeout_seconds, use_deepspeed)
        ("generate_data", "Generate 20,000 training pairs (deterministic, no API calls)",
         ["generate_training_data_direct.py"], 600, False),

        ("gen1_finetune", "Generation 1: Full Fine-tune (20K pairs, DeepSpeed ZeRO-3)",
         ["02_finetune.py", "--gen", "1", "--data", str(DATA_20K)], 54000, True),

        ("gen1_eval", "Generation 1: Evaluate (15 benchmarks)",
         ["03_evaluate.py", "--gen", "1"], 3600, False),

        ("gen1_track", "Generation 1: Record + Check Stage Advancement",
         ["06_track_stage.py", "--gen", "1", "--data", str(DATA_20K)], 600, False),

        ("gen1_distill", "Generation 1: Self-Distill from Weak Spots",
         ["04_self_distill.py", "--gen", "1"], 3600, False),

        ("gen1_cleanup", "Generation 1: Free disk space (raw model no longer needed)",
         ["07_cleanup_generation.py", "--gen", "1"], 600, False),

        ("gen2_finetune", "Generation 2: Full Fine-tune (20K + self-distilled)",
         ["02_finetune.py", "--gen", "2", "--data", gen2_data], 54000, True),

        ("gen2_eval", "Generation 2: Evaluate (compare with gen 1)",
         ["03_evaluate.py", "--gen", "2", "--compare"], 3600, False),

        ("gen2_track", "Generation 2: Record + Check Stage Advancement",
         ["06_track_stage.py", "--gen", "2", "--data", gen2_data], 600, False),

        ("gen2_distill", "Generation 2: Self-Distill from Weak Spots",
         ["04_self_distill.py", "--gen", "2"], 3600, False),

        ("gen2_cleanup", "Generation 2: Free disk space (raw model no longer needed)",
         ["07_cleanup_generation.py", "--gen", "2"], 600, False),

        ("gen3_finetune", "Generation 3: Full Fine-tune (expanded dataset)",
         ["02_finetune.py", "--gen", "3", "--data", gen3_data], 54000, True),

        ("gen3_eval", "Generation 3: Evaluate (final comparison)",
         ["03_evaluate.py", "--gen", "3", "--compare"], 3600, False),

        ("gen3_track", "Generation 3: Record + Check Stage Advancement",
         ["06_track_stage.py", "--gen", "3", "--data", gen3_data], 600, False),

        ("convert", "GGUF Conversion & Quantization for RTX 5060 Ti",
         ["05_convert_gguf.py", "--gen", "3", "--quant", args.quant, "--test"], 3600, False),
    ]

    stage_names = [s[0] for s in stages]
    start_idx = stage_names.index(args.start_from)

    total_duration = 0
    completed = 0

    for i in range(start_idx, len(stages)):
        stage_id, stage_name, command, timeout, use_ds = stages[i]

        print_banner(f"Stage {i+1}/{len(stages)}: {stage_name}")

        remaining_stages = stages[i:]
        est_remaining = sum(s[3] for s in remaining_stages) / 3600
        log("pipeline", f"Estimated time remaining: {est_remaining:.1f} hours")

        success, duration = run_step(stage_id, command, timeout_s=timeout, use_deepspeed=use_ds)
        total_duration += duration
        completed += 1

        if not success:
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

    evaluations = {}
    for gen in [1, 2, 3]:
        eval_path = OUTPUT_DIR / f"evaluation_gen{gen}.json"
        if eval_path.exists():
            evaluations[f"gen{gen}"] = json.loads(eval_path.read_text())

    comparisons = {}
    for gen in [2, 3]:
        comp_path = OUTPUT_DIR / f"comparison_gen{gen}.json"
        if comp_path.exists():
            comparisons[f"gen{gen}_vs_gen{gen-1}"] = json.loads(comp_path.read_text())

    conv_meta = {}
    conv_path = OUTPUT_DIR / "gguf" / "conversion_metadata.json"
    if conv_path.exists():
        conv_meta = json.loads(conv_path.read_text())

    # Load final stage state
    stage_info = {}
    stage_track_path = OUTPUT_DIR / "stage_tracking_gen3.json"
    if stage_track_path.exists():
        stage_info = json.loads(stage_track_path.read_text())

    final_report = {
        "pipeline_complete": True,
        "total_duration_minutes": pipeline_duration / 60,
        "total_duration_hours": pipeline_duration / 3600,
        "stages_completed": completed,
        "base_model": args.model,
        "gpu": "4x A100 80GB",
        "method": "full_finetune_deepspeed_zero3_cpu_offload_3gen",
        "evaluations": evaluations,
        "comparisons": comparisons,
        "conversion": conv_meta,
        "stage_tracking": stage_info,
        "completed_at": datetime.utcnow().isoformat(),
    }

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
        print(f"\nImprovement: gen1={imp['gen1_score']:.2f} -> gen3={imp['gen3_score']:.2f} ({imp['improvement_pct']:+.1f}%)")
        print(f"Stage 4 requirement (15%+): {'MET' if imp['meets_stage4_requirement'] else 'NOT MET'}")

    if stage_info.get("advancement_log"):
        last_check = stage_info["advancement_log"][-1]
        print(f"\nFinal tracked stage: {stage_info.get('final_stage')} ({last_check.get('stage_name')})")

    if conv_meta:
        print(f"\nDeployment model: {conv_meta.get('quantized_path', 'unknown')}")
        print(f"Quantization: {conv_meta.get('quant_type', 'unknown')}")
        print(f"Size: {conv_meta.get('quantized_size_gb', 0):.1f} GB")
        print(f"Test passed: {conv_meta.get('test_passed', False)}")

    print(f"\nNext steps:")
    print(f"  1. Download the GGUF model from {OUTPUT_DIR}/gguf/")
    print(f"  2. Deploy on the RTX 5060 Ti")
    print(f"  3. Begin autonomous operation for Stage 5 progression")


if __name__ == "__main__":
    main()
