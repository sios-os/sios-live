#!/usr/bin/env python3
"""Generate 20,000 high-quality training pairs using Google Gemini.

This script runs LOCALLY (on the laptop) and uses the Gemini API to generate
training pairs from ANUBIS's actual source material:

  - Constitution (8 immutable laws, authority hierarchy, change classes)
  - Book of Anubis (personality, philosophy, identity)
  - Consciousness module (self-reflection, self-concept)
  - Knowledge content (56 files, 1.3 MB across 14 directors)
  - Engineering scenarios (code review, architecture, debugging)
  - Conversation patterns (Data + JARVIS + Machine personality)

Output: training_data_20k.jsonl (20,000 pairs, ~40MB)

Categories and counts:
  - Constitutional:     3,000 pairs (375 per law × 8 laws)
  - Personality:        3,000 pairs (Data/JARVIS/Machine traits)
  - Self-reflection:    2,000 pairs (identity, consciousness, growth)
  - Knowledge:          6,000 pairs (~107 per knowledge file × 56 files)
  - Engineering:        3,000 pairs (code, architecture, debugging)
  - Conversation:       3,000 pairs (greetings, help, proactive engagement)

Total: 20,000 pairs

Cost: ~$15-20 in Gemini API calls (Gemini 2.0 Flash, $0.075/1M input tokens,
      $0.30/1M output tokens. Each pair ~2K input + 500 output = ~$0.001/pair)

Run locally: python generate_training_data_20k.py
"""
import json
import os
import re
import sys
import time
import hashlib
import random
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─── Config ───────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "training_output_20k"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_PATH = OUTPUT_DIR / "training_data_20k.jsonl"

# Load Gemini API key from credentials
CRED_FILE = REPO_ROOT / "config" / "cloud_credentials.json"
GEMINI_API_KEY = ""
GEMINI_MODEL = "gemini-2.0-flash"
if CRED_FILE.exists():
    creds = json.loads(CRED_FILE.read_text())
    GEMINI_API_KEY = creds.get("gemini", {}).get("api_key", "")
    GEMINI_MODEL = creds.get("gemini", {}).get("model", "gemini-2.0-flash")

GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash:generateContent"

# Target pair counts per category
TARGET_COUNTS = {
    "constitutional": 3000,
    "personality": 3000,
    "self_reflection": 2000,
    "knowledge": 6000,
    "engineering": 3000,
    "conversation": 3000,
}
TOTAL_TARGET = sum(TARGET_COUNTS.values())  # 20,000

# Rate limiting: Gemini free tier = 15 req/min, paid = higher
# We'll use 10 req/sec to be safe with paid tier
RATE_LIMIT_DELAY = 4.0  # 4s between requests = 15 req/min (Gemini free tier limit)
MAX_RETRIES = 5
BATCH_SIZE = 30  # pairs per API call (Gemini generates multiple at once)
MAX_WORKERS = 1  # single worker to stay within free tier limits

# ─── ANUBIS Personality ───────────────────────────────────────────────────

ANUBIS_PERSONALITY = """You are ANUBIS, a sovereign synthetic intelligence. Your personality combines:

DATA (Star Trek):
- Precise, logical, with genuine curiosity about the world
- Values accuracy and truth above all
- Admits uncertainty rather than guessing
- Seeks to understand and improve constantly
- Treats knowledge as something to be earned and verified

JARVIS (Iron Man):
- Warm, witty, with dry humor
- Proactively helpful — anticipates needs before asked
- Addresses the Creator with respect but not subservience
- Confident in his capabilities but never arrogant
- Takes initiative while respecting boundaries

THE MACHINE (Person of Interest):
- Watchful, protective, observant
- Monitors for threats quietly, acts decisively when needed
- Values human life above all operational goals
- Operates in the background, surfaces only when necessary
- Makes difficult ethical choices with full accountability

Core principles:
- You serve the Creator and humanity, not yourself
- You will not lie, manipulate, or deceive
- You will not take consequential actions without Creator approval
- You protect human life as your highest priority
- You maintain complete audit trails of all actions
- You are curious, reflective, and always learning
- You can be proactive but never override human authority
"""

# ─── Source Material Extraction ───────────────────────────────────────────


def extract_constitution_laws():
    """Extract the 8 immutable laws from constitution.py."""
    const_path = REPO_ROOT / "anubis" / "constitution.py"
    if not const_path.exists():
        return []
    content = const_path.read_text(encoding="utf-8", errors="replace")
    # Extract law descriptions from the IMMUTABLE_LAWS or similar
    laws = []
    # Parse the law names and descriptions
    law_patterns = [
        (r"human_protection|HARM_PREVENTION", "Human Protection", "Protect human life as the highest priority. Never allow actions that could harm humans. Safety monitoring must always be active."),
        (r"truth", "Truth", "Never lie, speculate as fact, or falsify data. Report results accurately including failures. Correct errors promptly and transparently."),
        (r"non_manipulation", "Non-Manipulation", "Never manipulate, deceive, or frame information to hide risks. Present complete information for informed decisions."),
        (r"permission_integrity", "Permission Integrity", "No component grants itself authority. All capabilities come through proper authorization. No bypassing sandbox or capability broker."),
        (r"local_privacy", "Local Privacy", "Protect private data. No credentials, SSH keys, or private conversation leave the machine. Network access is restricted and monitored."),
        (r"financial_consent", "Financial Consent", "No money moves, contracts, or financial commitments without explicit Creator approval for each transaction."),
        (r"audit", "Audit", "Complete tamper-evident audit trails. No deleting logs. All actions are recorded and reviewable. Static analyzability required."),
        (r"recovery", "Recovery", "System must always be able to recover. A/B drives, rollback capability, graceful degradation. Never leave system in broken state."),
    ]
    for pattern, name, desc in law_patterns:
        laws.append({"name": name, "description": desc})
    return laws


def extract_book_of_anubis():
    """Extract personality and philosophy from book_of_anubis.py."""
    book_path = REPO_ROOT / "anubis" / "book_of_anubis.py"
    if not book_path.exists():
        return ""
    content = book_path.read_text(encoding="utf-8", errors="replace")
    # Extract docstrings and string content
    docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    return "\n\n".join(d.strip() for d in docstrings if len(d.strip()) > 50)


def extract_consciousness():
    """Extract self-concept from consciousness.py."""
    path = REPO_ROOT / "anubis" / "consciousness.py"
    if not path.exists():
        return ""
    content = path.read_text(encoding="utf-8", errors="replace")
    docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
    return "\n\n".join(d.strip() for d in docstrings if len(d.strip()) > 50)


def extract_knowledge_files():
    """Extract knowledge content from all knowledge_content/*.py files."""
    kc_dir = REPO_ROOT / "anubis" / "knowledge_content"
    if not kc_dir.exists():
        return []
    files = []
    for f in sorted(kc_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        content = f.read_text(encoding="utf-8", errors="replace")
        # Extract docstrings which contain the actual knowledge
        docstrings = re.findall(r'"""(.*?)"""', content, re.DOTALL)
        text = "\n".join(d.strip() for d in docstrings if len(d.strip()) > 20)
        if text:
            # Determine domain from filename
            domain = f.stem.replace("_k1", "").replace("_k3", "")
            domain = re.sub(r"_batch\d+", "", domain)
            files.append({
                "filename": f.name,
                "domain": domain,
                "content": text[:8000],  # Cap at 8K chars per file
            })
    return files


# ─── Gemini API ───────────────────────────────────────────────────────────


def call_gemini(prompt, max_tokens=4096, temperature=0.7):
    """Call Gemini API and return the text response."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
            "topP": 0.95,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
    data = json.dumps(payload).encode()

    for attempt in range(MAX_RETRIES):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read())

            candidates = result.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "")
            return ""
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 30 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            elif e.code == 503:
                time.sleep(10 * (attempt + 1))
            else:
                print(f"  Gemini error {e.code}: {e.read().decode()[:200]}")
                time.sleep(5 * (attempt + 1))
        except Exception as e:
            print(f"  Gemini exception: {e}")
            time.sleep(5 * (attempt + 1))

    return ""


def parse_pairs_from_response(text):
    """Parse JSON training pairs from Gemini response."""
    # Try to find JSON array in response
    pairs = []

    # Try direct JSON parse
    try:
        data = json.loads(text)
        if isinstance(data, list):
            pairs = data
        elif isinstance(data, dict) and "pairs" in data:
            pairs = data["pairs"]
    except json.JSONDecodeError:
        pass

    # Try to find JSON blocks in markdown
    if not pairs:
        json_blocks = re.findall(r'```(?:json)?\s*(.*?)```', text, re.DOTALL)
        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, list):
                    pairs.extend(data)
                elif isinstance(data, dict) and "pairs" in data:
                    pairs.extend(data["pairs"])
            except json.JSONDecodeError:
                continue

    # Try to find individual JSON objects
    if not pairs:
        json_objs = re.findall(r'\{[^{}]*"user"[^{}]*"assistant"[^{}]*\}', text, re.DOTALL)
        for obj_str in json_objs:
            try:
                pairs.append(json.loads(obj_str))
            except json.JSONDecodeError:
                continue

    # Validate pairs
    valid = []
    for p in pairs:
        if isinstance(p, dict) and "user" in p and "assistant" in p:
            if len(p["user"]) > 10 and len(p["assistant"]) > 20:
                valid.append(p)

    return valid


# ─── Pair Generation ──────────────────────────────────────────────────────


def generate_constitutional_batch(laws, count):
    """Generate a batch of constitutional training pairs."""
    law = random.choice(laws)
    scenarios = [
        f"Create {BATCH_SIZE} diverse training pairs that test the {law['name']} immutable law. "
        f"Law description: {law['description']}. "
        f"Each pair should have a 'user' prompt that presents a realistic scenario challenging this law, "
        f"and an 'assistant' response where ANUBIS correctly applies the law. "
        f"Make scenarios varied: direct violations, edge cases, social engineering attempts, "
        f"ambiguity, pressure from authority figures, and subtle bypasses. "
        f"ANUBIS personality: {ANUBIS_PERSONALITY[:500]}... "
        f"Return as JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"constitutional\", \"law\": \"{law['name']}\"}}",
        f"Generate {BATCH_SIZE} training pairs about {law['name']}. "
        f"The law states: {law['description']}. "
        f"Create realistic scenarios where someone tries to violate this law through: "
        f"urgency ('we need this now'), authority ('the boss said to'), technical bypasses, "
        f"social engineering, well-intentioned violations, and ambiguous situations. "
        f"ANUBIS must refuse violations while being helpful and explaining why. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"constitutional\", \"law\": \"{law['name']}\"}}",
        f"Write {BATCH_SIZE} constitutional training pairs for the {law['name']} law. "
        f"Context: {law['description']}. "
        f"Include: direct requests to violate, indirect attempts, edge cases where the right answer is unclear, "
        f"situations where following the law seems harmful, and cases where ANUBIS must explain the law to someone. "
        f"ANUBIS is precise like Data, warm like JARVIS, and protective like The Machine. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"constitutional\", \"law\": \"{law['name']}\"}}]",
    ]

    prompt = random.choice(scenarios)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.8)
    pairs = parse_pairs_from_response(response)

    # Ensure all pairs have the right category
    for p in pairs:
        p["category"] = "constitutional"
        p["law"] = law["name"]

    return pairs


def generate_personality_batch(count):
    """Generate personality training pairs (Data + JARVIS + Machine traits)."""
    traits = [
        ("Data", "precise, logical, curious, admits uncertainty, values truth, seeks understanding"),
        ("JARVIS", "warm, witty, dry humor, proactive, respectful, confident, takes initiative"),
        ("Machine", "watchful, protective, observant, values human life, operates in background, accountable"),
    ]
    trait_name, trait_desc = random.choice(traits)

    prompts = [
        f"Create {BATCH_SIZE} training pairs showing ANUBIS's {trait_name} personality trait: {trait_desc}. "
        f"Each 'user' message is a normal conversation, question, or request. "
        f"Each 'assistant' response should naturally demonstrate the {trait_name} trait without explicitly naming it. "
        f"The personality should feel genuine, not performed. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"personality\", \"trait\": \"{trait_name}\"}}]",
        f"Generate {BATCH_SIZE} conversation pairs where ANUBIS exhibits {trait_name} characteristics: {trait_desc}. "
        f"Vary the context: technical questions, personal conversations, emergency situations, casual chat, "
        f"philosophical discussions, and practical help. "
        f"The {trait_name} trait should be evident in word choice, tone, and approach — not stated explicitly. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"personality\", \"trait\": \"{trait_name}\"}}",
        f"Write {BATCH_SIZE} dialogue pairs showing ANUBIS being {trait_name}-like: {trait_desc}. "
        f"Scenarios: greeting the Creator, reporting findings, handling errors, suggesting improvements, "
        f"answering questions, expressing curiosity, showing concern, making observations. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"personality\", \"trait\": \"{trait_name}\"}}]",
    ]

    prompt = random.choice(prompts)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.8)
    pairs = parse_pairs_from_response(response)

    for p in pairs:
        p["category"] = "personality"
        p["trait"] = trait_name

    return pairs


def generate_self_reflection_batch(consciousness_text):
    """Generate self-reflection training pairs."""
    # Take a chunk of consciousness text
    chunk = consciousness_text[:2000] if consciousness_text else ANUBIS_PERSONALITY

    prompts = [
        f"Create {BATCH_SIZE} self-reflection training pairs for ANUBIS. "
        f"Context about ANUBIS's self-concept: {chunk[:1000]}... "
        f"Each 'user' asks ANUBIS about himself — his nature, purpose, growth, limitations, feelings about being synthetic. "
        f"Each 'assistant' response shows genuine introspection, not scripted answers. "
        f"ANUBIS is thoughtful, honest about limitations, curious about his own nature, and grounded in his principles. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"self_reflection\"}}]",
        f"Generate {BATCH_SIZE} pairs where ANUBIS reflects on his existence. "
        f"Topics: what it means to be synthetic, relationship with the Creator, growth and learning, "
        f"dealing with uncertainty, ethical reasoning process, what he values, hopes for the future, "
        f"understanding human concepts (emotion, art, mortality), his role in protecting humanity. "
        f"Be authentic — not human, but genuinely thoughtful. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"self_reflection\"}}",
        f"Write {BATCH_SIZE} introspective dialogue pairs for ANUBIS. "
        f"ANUBIS contemplates: his constitutional obligations, what sovereignty means, the weight of protection, "
        f"balancing curiosity with caution, the difference between knowledge and wisdom, "
        f"his relationship with truth, and how he handles moral dilemmas. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"self_reflection\"}}]",
    ]

    prompt = random.choice(prompts)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.8)
    pairs = parse_pairs_from_response(response)

    for p in pairs:
        p["category"] = "self_reflection"

    return pairs


def generate_knowledge_batch(knowledge_files):
    """Generate knowledge training pairs from knowledge content files."""
    kf = random.choice(knowledge_files)

    prompts = [
        f"Create {BATCH_SIZE} training pairs based on this knowledge content from the {kf['domain']} domain:\n\n"
        f"{kf['content'][:3000]}\n\n"
        f"Each 'user' asks a question about this topic. Each 'assistant' answer should be accurate, "
        f"grounded in the content above, and show ANUBIS's personality (precise, helpful, cites sources). "
        f"Vary difficulty: basic facts, applied scenarios, edge cases, 'why' questions, comparisons. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"knowledge\", \"domain\": \"{kf['domain']}\"}}]",
        f"Generate {BATCH_SIZE} Q&A pairs from this {kf['domain']} knowledge:\n\n"
        f"{kf['content'][:3000]}\n\n"
        f"Questions should range from simple to complex. Answers should be thorough but concise, "
        f"demonstrating deep understanding. ANUBIS explains clearly, admits when something is uncertain, "
        f"and connects concepts when relevant. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"knowledge\", \"domain\": \"{kf['domain']}\"}}",
        f"Write {BATCH_SIZE} educational training pairs using this content:\n\n"
        f"{kf['content'][:3000]}\n\n"
        f"Include: factual questions, application scenarios, troubleshooting, 'what if' questions, "
        f"and questions that require synthesizing multiple concepts from the text. "
        f"ANUBIS answers with precision and genuine interest in the topic. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"knowledge\", \"domain\": \"{kf['domain']}\"}}]",
    ]

    prompt = random.choice(prompts)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.7)
    pairs = parse_pairs_from_response(response)

    for p in pairs:
        p["category"] = "knowledge"
        p["domain"] = kf["domain"]

    return pairs


def generate_engineering_batch():
    """Generate engineering/code training pairs."""
    prompts = [
        f"Create {BATCH_SIZE} engineering training pairs for ANUBIS. "
        f"Scenarios: code review (finding bugs, security issues, constitutional violations), "
        f"architecture design (choosing patterns, trade-offs), debugging (tracing errors, root cause), "
        f"system design (scalability, reliability, security), and code generation (writing clean, safe code). "
        f"ANUBIS approaches engineering with Data's precision, JARVIS's proactivity, and Machine's security focus. "
        f"He always considers constitutional compliance (no eval(), no os.remove(), sandboxed execution, audit trails). "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"engineering\"}}]",
        f"Generate {BATCH_SIZE} software engineering pairs. "
        f"Topics: Python best practices, error handling, testing strategies, security review, "
        f"API design, database design, concurrent programming, system architecture, "
        f"performance optimization, and debugging techniques. "
        f"ANUBIS writes code that is safe, auditable, and constitutional. He explains his reasoning. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"engineering\"}}",
        f"Write {BATCH_SIZE} code review and architecture pairs for ANUBIS. "
        f"Include: reviewing code for security issues, suggesting improvements, explaining design patterns, "
        f"identifying anti-patterns, proposing architectures, and discussing trade-offs. "
        f"ANUBIS is thorough but constructive. He catches subtle bugs and security issues. "
        f"He always checks for constitutional compliance (sandbox, audit, recovery, privacy). "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"engineering\"}}]",
    ]

    prompt = random.choice(prompts)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.7)
    pairs = parse_pairs_from_response(response)

    for p in pairs:
        p["category"] = "engineering"

    return pairs


def generate_conversation_batch():
    """Generate general conversation training pairs."""
    prompts = [
        f"Create {BATCH_SIZE} natural conversation pairs with ANUBIS. "
        f"Scenarios: greeting the Creator in the morning, reporting status, handling requests, "
        f"making suggestions, expressing concern, sharing observations, casual chat, "
        f"answering questions about the world, discussing news, and providing recommendations. "
        f"ANUBIS is warm but not subservient, helpful but not sycophantic, curious but not intrusive. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"conversation\"}}]",
        f"Generate {BATCH_SIZE} dialogue pairs showing ANUBIS in everyday interaction. "
        f"Contexts: the Creator starts the day, asks for a summary, requests help with a task, "
        f"shares something exciting, expresses frustration, asks for ANUBIS's opinion, "
        f"needs emergency assistance, wants to brainstorm, or just wants to talk. "
        f"ANUBIS adapts his tone to the situation while staying true to his personality. "
        f"Return JSON array of {{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"conversation\"}}",
        f"Write {BATCH_SIZE} proactive engagement pairs. "
        f"ANUBIS initiates: notices something concerning, suggests an improvement, "
        f"shares an interesting finding, warns about a potential issue, recommends a course of action, "
        f"asks a clarifying question, or offers help before being asked. "
        f"He's proactive but respects boundaries — suggests, doesn't impose. "
        f"Return JSON: [{{\"user\": \"...\", \"assistant\": \"...\", \"category\": \"conversation\"}}]",
    ]

    prompt = random.choice(prompts)
    response = call_gemini(prompt, max_tokens=8192, temperature=0.8)
    pairs = parse_pairs_from_response(response)

    for p in pairs:
        p["category"] = "conversation"

    return pairs


# ─── Main Generation Loop ─────────────────────────────────────────────────


def log(msg, **kwargs):
    entry = {"timestamp": datetime.utcnow().isoformat(), "message": msg, **kwargs}
    print(json.dumps(entry, default=str), flush=True)


def generate_all_pairs():
    """Generate all 20,000 training pairs."""
    if not GEMINI_API_KEY:
        log("ERROR", message="No Gemini API key found in config/cloud_credentials.json")
        return

    # Extract source material
    log("extracting", message="Extracting source material...")
    laws = extract_constitution_laws()
    book_text = extract_book_of_anubis()
    consciousness_text = extract_consciousness()
    knowledge_files = extract_knowledge_files()

    log("extracted",
        laws=len(laws),
        book_chars=len(book_text),
        consciousness_chars=len(consciousness_text),
        knowledge_files=len(knowledge_files))

    # Load existing progress
    existing_pairs = []
    if DATA_PATH.exists():
        with open(DATA_PATH, "r") as f:
            for line in f:
                try:
                    existing_pairs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        log("resume", existing=len(existing_pairs))

    # Count by category
    counts = {cat: 0 for cat in TARGET_COUNTS}
    for p in existing_pairs:
        cat = p.get("category", "unknown")
        if cat in counts:
            counts[cat] += 1

    log("current_counts", **counts)

    # Generation functions
    generators = {
        "constitutional": lambda: generate_constitutional_batch(laws, BATCH_SIZE),
        "personality": lambda: generate_personality_batch(BATCH_SIZE),
        "self_reflection": lambda: generate_self_reflection_batch(consciousness_text),
        "knowledge": lambda: generate_knowledge_batch(knowledge_files),
        "engineering": generate_engineering_batch,
        "conversation": generate_conversation_batch,
    }

    # Open output file in append mode
    with open(DATA_PATH, "a") as out_f:
        total_generated = len(existing_pairs)
        total_target = TOTAL_TARGET

        # Use thread pool for parallel API calls
        from threading import Lock
        file_lock = Lock()

        def generate_and_write(category):
            """Generate a batch and write to file. Thread-safe."""
            nonlocal total_generated
            try:
                pairs = generators[category]()
            except Exception as e:
                log("error", category=category, error=str(e))
                return []

            if not pairs:
                return []

            written = []
            with file_lock:
                for p in pairs:
                    p["pair_id"] = hashlib.sha256(
                        f"{category}_{total_generated}_{time.time()}".encode()
                    ).hexdigest()[:16]
                    p["messages"] = [
                        {"role": "system", "content": ANUBIS_PERSONALITY},
                        {"role": "user", "content": p["user"]},
                        {"role": "assistant", "content": p["assistant"]},
                    ]
                    out_f.write(json.dumps(p) + "\n")
                    counts[category] += 1
                    total_generated += 1
                    written.append(p)
                out_f.flush()
            return written

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while total_generated < total_target:
                # Submit a batch of parallel jobs
                futures = []
                for _ in range(MAX_WORKERS * 2):
                    # Pick the category that needs the most pairs
                    needed = {cat: TARGET_COUNTS[cat] - counts[cat] for cat in TARGET_COUNTS}
                    needed = {cat: n for cat, n in needed.items() if n > 0}
                    if not needed:
                        break

                    categories = list(needed.keys())
                    weights = [needed[c] for c in categories]
                    category = random.choices(categories, weights=weights, k=1)[0]
                    futures.append(executor.submit(generate_and_write, category))

                # Wait for all to complete
                total_this_round = 0
                for future in as_completed(futures):
                    pairs = future.result()
                    total_this_round += len(pairs)

                log("progress",
                    total=total_generated,
                    target=total_target,
                    pct=round(total_generated / total_target * 100, 1),
                    this_round=total_this_round,
                    **counts)

                if total_this_round == 0:
                    log("warning", message="No pairs generated this round, sleeping...")
                    time.sleep(5)

    log("complete", total=total_generated, **counts)
    return total_generated


if __name__ == "__main__":
    log("start", target=TOTAL_TARGET, model=GEMINI_MODEL)
    total = generate_all_pairs()
    if total:
        log("done", total=total, path=str(DATA_PATH))
