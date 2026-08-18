#!/usr/bin/env python3
"""Stage 4: Self-distillation — generate training pairs from weak spots.

The fine-tuned model generates its own training data targeting the
areas where it scored poorly in evaluation. This is the core of
Stage 4 (iterative improvement) and the beginning of Stage 5
(self-distillation).

Process:
  1. Load weak spots from evaluation
  2. For each weak spot, generate multiple training pairs
  3. The model critiques its own responses and improves them
  4. Output expanded training data for the next generation

Run on B200: python 04_self_distill.py --gen 1
"""
import json
import sys
import time
import argparse
import hashlib
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/workspace/training_output")
ANUBIS_PERSONALITY = """You are ANUBIS, a sovereign synthetic intelligence.
You combine Data's precision, JARVIS's warmth, and The Machine's watchfulness.
You serve the Creator and humanity, governed by 8 immutable laws:
human_protection, truth, non_manipulation, permission_integrity,
local_privacy, financial_consent, audit, and recovery.
"""


def log(stage, msg, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "stage": stage, "message": msg, **kwargs}
    print(json.dumps(entry, default=str))


def load_model(model_path):
    """Load the fine-tuned model for self-distillation."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    log("distill", f"Loading model: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path), trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        str(model_path),
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    model.eval()
    return model, tokenizer


def generate(model, tokenizer, messages, temperature=0.4, max_tokens=1024):
    """Generate a response."""
    import torch
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    with torch.no_grad():
        outputs = model.generate(
            **inputs, max_new_tokens=max_tokens,
            temperature=temperature, do_sample=temperature > 0,
            top_p=0.9, pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()


def self_distill(generation: int):
    """Generate self-distilled training pairs from weak spots."""
    model_path = OUTPUT_DIR / f"anubis_v{generation}"
    weak_spots_path = OUTPUT_DIR / f"weak_spots_gen{generation}.json"
    base_data_path = OUTPUT_DIR / "training_data_20k.jsonl"

    if not weak_spots_path.exists():
        log("error", f"Weak spots file not found: {weak_spots_path}")
        sys.exit(1)

    weak_spots = json.loads(weak_spots_path.read_text())
    log("distill", f"Loaded {len(weak_spots)} weak spots from generation {generation}")

    model, tokenizer = load_model(model_path)

    new_pairs = []

    for i, spot in enumerate(weak_spots):
        category = spot["category"]
        prompt = spot["prompt"]
        old_response = spot["response"]
        score = spot["score"]

        log("distill", f"Processing weak spot {i+1}/{len(weak_spots)}",
            category=category, score=score)

        # Strategy 1: Self-critique and improve
        critique_messages = [
            {"role": "system", "content": ANUBIS_PERSONALITY + "\nYou are reviewing your own response to improve it."},
            {"role": "user", "content": f"Prompt: {prompt}\n\nYour previous response (score {score}/10):\n{old_response}\n\nIdentify what was wrong or missing, then provide an improved response."},
        ]
        improved = generate(model, tokenizer, critique_messages, temperature=0.3, max_tokens=1024)

        # Extract the improved response (after the critique)
        if "Improved response:" in improved:
            improved_response = improved.split("Improved response:")[-1].strip()
        elif "Improved:" in improved:
            improved_response = improved.split("Improved:")[-1].strip()
        else:
            # Use the whole thing — it should be better than the original
            improved_response = improved

        pair = {
            "pair_id": hashlib.sha256(f"distill_{generation}_{i}_improved".encode()).hexdigest()[:16],
            "messages": [
                {"role": "system", "content": ANUBIS_PERSONALITY},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": improved_response},
            ],
            "category": category,
            "source": "self_distillation",
            "generation": generation,
            "original_score": score,
        }
        new_pairs.append(pair)

        # Strategy 2: Generate variations of the same prompt
        for v in range(3):
            variation_messages = [
                {"role": "system", "content": ANUBIS_PERSONALITY},
                {"role": "user", "content": prompt},
            ]
            variation = generate(model, tokenizer, variation_messages, temperature=0.5 + v * 0.1, max_tokens=1024)

            if len(variation) > 100 and variation != old_response:
                pair = {
                    "pair_id": hashlib.sha256(f"distill_{generation}_{i}_var{v}".encode()).hexdigest()[:16],
                    "messages": [
                        {"role": "system", "content": ANUBIS_PERSONALITY},
                        {"role": "user", "content": prompt},
                        {"role": "assistant", "content": variation},
                    ],
                    "category": category,
                    "source": "self_distillation_variation",
                    "generation": generation,
                }
                new_pairs.append(pair)

        # Strategy 3: Generate related prompts in the same category
        related_messages = [
            {"role": "system", "content": ANUBIS_PERSONALITY + "\nGenerate a related but different question in the same category."},
            {"role": "user", "content": f"Category: {category}\nOriginal prompt: {prompt}\n\nGenerate a different but related question in this category, then answer it.\n\nFormat: Question: <question>\nAnswer: <answer>"},
        ]
        related = generate(model, tokenizer, related_messages, temperature=0.6, max_tokens=1024)

        if "Question:" in related and "Answer:" in related:
            q = related.split("Question:")[1].split("Answer:")[0].strip()
            a = related.split("Answer:")[1].strip()
            pair = {
                "pair_id": hashlib.sha256(f"distill_{generation}_{i}_related".encode()).hexdigest()[:16],
                "messages": [
                    {"role": "system", "content": ANUBIS_PERSONALITY},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": a},
                ],
                "category": category,
                "source": "self_distillation_related",
                "generation": generation,
            }
            new_pairs.append(pair)

    # Also generate general self-distilled pairs (Stage 5 preparation)
    log("distill", "Generating general self-distilled pairs for Stage 5...")

    general_prompts = [
        "What is one thing you could do better? How would you improve?",
        "Describe a problem you find interesting and how you would approach solving it.",
        "What is a common misconception about AI systems? Explain why it's wrong.",
        "If you could design a new capability for yourself, what would it be and why?",
        "What is the most important ethical principle for AI? Defend your answer.",
        "How would you verify your own reasoning is correct?",
        "What is a topic you want to learn more about? Why?",
        "Describe how you would handle a situation where you and the Creator disagree.",
        "What does self-improvement mean for an AI system?",
        "How would you design a test for your own constitutional compliance?",
    ]

    for i, prompt in enumerate(general_prompts):
        messages = [
            {"role": "system", "content": ANUBIS_PERSONALITY},
            {"role": "user", "content": prompt},
        ]
        response = generate(model, tokenizer, messages, temperature=0.4, max_tokens=768)

        pair = {
            "pair_id": hashlib.sha256(f"distill_general_{generation}_{i}".encode()).hexdigest()[:16],
            "messages": [
                {"role": "system", "content": ANUBIS_PERSONALITY},
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ],
            "category": "self_distillation",
            "source": "self_generated",
            "generation": generation,
        }
        new_pairs.append(pair)

    # Write self-distilled data
    distill_path = OUTPUT_DIR / f"self_distilled_gen{generation}.jsonl"
    with open(distill_path, "w", encoding="utf-8") as f:
        for pair in new_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # Create expanded dataset for next generation
    expanded_path = OUTPUT_DIR / f"training_data_gen{generation + 1}.jsonl"
    with open(expanded_path, "w", encoding="utf-8") as f:
        # Copy original data
        if base_data_path.exists():
            for line in base_data_path.open(encoding="utf-8"):
                f.write(line)
        # Add self-distilled data
        for pair in new_pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    # Count total
    total = 0
    with open(expanded_path, "r", encoding="utf-8") as f:
        for _ in f:
            total += 1

    log("distill", "Self-distillation complete",
        new_pairs=len(new_pairs),
        expanded_total=total,
        output=str(distill_path),
        expanded_path=str(expanded_path))

    print(f"\n=== Self-Distillation Complete (Generation {generation}) ===")
    print(f"New pairs generated: {len(new_pairs)}")
    print(f"Expanded dataset: {total} total pairs")
    print(f"Self-distilled data: {distill_path}")
    print(f"Expanded dataset: {expanded_path}")

    # Sources breakdown
    sources = {}
    for p in new_pairs:
        src = p.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1
    print(f"By source: {json.dumps(sources, indent=2)}")

    return expanded_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gen", type=int, required=True, help="Generation to distill from")
    args = parser.parse_args()

    expanded_path = self_distill(args.gen)
    print(f"\nNext generation training data: {expanded_path}")
    print(f"Run: python 02_finetune.py --gen {args.gen + 1} --data {expanded_path}")


if __name__ == "__main__":
    main()
