#!/usr/bin/env python3
"""Rent a 4x A100 80GB instance on Vast.ai for ANUBIS training.

Searches for the cheapest 4x A100 80GB offer that ALSO has sufficient host
RAM and disk for full fine-tuning a 32B model with DeepSpeed ZeRO-3 +
CPU-offloaded optimizer:

  - Host RAM: ZeRO-3 CPU offload keeps the optimizer's fp32 master weights,
    momentum, and variance (~12+ bytes/param) in system RAM, not GPU VRAM.
    For 32B params that's roughly 400GB+. An instance without this WILL
    fail (CPU OOM / thrashing) partway through a multi-hour training run.
  - Disk: ~400GB for the base model HF cache, one generation's raw
    fine-tuned model at a time, f16 GGUF during conversion, and the final
    quantized artifact.

This script refuses to auto-select an offer that doesn't meet the RAM
requirement rather than silently renting something that will fail hours
into an expensive run.

Usage:
    python rent_4xa100.py [--dry-run] [--offer-id ID]

    --dry-run     Search and show offers but do NOT rent anything.
    --offer-id ID Rent a specific offer ID instead of auto-selecting.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

MIN_RAM_GB = 400
MIN_DISK_GB = 400
GPU_RAM_MB = 80 * 1024  # 80GB in MB (Vast.ai API uses MB for gpu_ram)

# Load Vast.ai API key
CRED_FILE = Path(__file__).resolve().parent.parent / "config" / "cloud_credentials.json"
creds = json.loads(CRED_FILE.read_text(encoding="utf-8"))
API_KEY = creds["vast"]["api_key"]
BASE_URL = "https://console.vast.ai/api/v0"
HEADERS = {"Authorization": "Bearer " + API_KEY}


def search_offers(payload):
    """Search Vast.ai offers via raw API (SDK Query class has format issues)."""
    resp = requests.post(f"{BASE_URL}/bundles/", json=payload, headers=HEADERS)
    if resp.status_code != 200:
        print(f"  Search error HTTP {resp.status_code}: {resp.text[:300]}")
        return []
    return resp.json().get("offers", [])


def normalize_ram_gb(raw_value):
    """Vast.ai cpu_ram is in MB. Convert to GB."""
    if raw_value > 10000:
        return raw_value / 1024
    return raw_value


def annotate_offers(offers):
    """Annotate offers with normalized RAM and qualification flags."""
    annotated = []
    for o in offers:
        ram_gb = normalize_ram_gb(o.get("cpu_ram", 0) or 0)
        disk_gb = o.get("disk_space", 0) or 0
        annotated.append({
            "offer": o,
            "ram_gb": ram_gb,
            "disk_gb": disk_gb,
            "meets_ram": ram_gb >= MIN_RAM_GB,
            "meets_disk": disk_gb >= MIN_DISK_GB,
            "dph": o.get("dph_total", 999) or 999,
            "gpu_ram_gb": (o.get("gpu_ram", 0) or 0) / 1024,
            "gpu_name": o.get("gpu_name", "?"),
            "num_gpus": o.get("num_gpus", 0),
            "country": (o.get("geolocation") if isinstance(o.get("geolocation"), str) else o.get("country", "?")) or "?",
            "reliability": o.get("reliability2", 0) or 0,
            "id": o.get("id", 0),
            "verified": o.get("verified", False),
        })
    return annotated


def search_all():
    """Search for suitable offers with correct API format and rate-limit handling."""
    import time as _time

    # GPU name variants — Vast.ai API uses specific names like "A100 SXM4", not "A100"
    gpu_names = ["A100 SXM4", "A100 PCIE", "A800 PCIE"]
    all_offers = []
    seen_ids = set()

    for name in gpu_names:
        print(f"Searching for 4x {name} 80GB (any verified status)...")
        offers = search_offers({
            "gpu_name": {"eq": name},
            "num_gpus": {"gte": 4},
            "gpu_ram": {"gte": GPU_RAM_MB},
            "rentable": {"eq": True},
            "external": {"eq": False},
            "order": [["dph_total", "asc"]],
            "limit": 50,
        })
        print(f"  Found {len(offers)} {name} offers")
        for o in offers:
            if o.get("id") not in seen_ids:
                seen_ids.add(o.get("id"))
                all_offers.append(o)
        _time.sleep(3)  # Rate limit: ~5 requests per few seconds

    return all_offers


def main():
    parser = argparse.ArgumentParser(description="Rent 4x A100 80GB on Vast.ai")
    parser.add_argument("--dry-run", action="store_true",
                        help="Search and show offers but do NOT rent")
    parser.add_argument("--offer-id", type=int, default=None,
                        help="Rent a specific offer ID instead of auto-selecting")
    args = parser.parse_args()

    if args.offer_id:
        print(f"Renting specific offer ID {args.offer_id}...")
        offers = search_offers({
            "id": {"eq": args.offer_id},
            "rentable": {"eq": True},
            "external": {"eq": False},
            "limit": 1,
        })
    else:
        offers = search_all()

    if not offers:
        print("\nERROR: No suitable A100 80GB offers found.")
        print("The Vast.ai market fluctuates. Try again later or use --offer-id.")
        sys.exit(1)

    annotated = annotate_offers(offers)
    annotated.sort(key=lambda a: a["dph"])

    print(f"\nTop 15 offers (RAM requirement: {MIN_RAM_GB}GB+ for ZeRO-3 CPU offload):")
    print(f"{'idx':>3} {'id':>8} {'gpus':>4} {'GPU':>14} {'VRAM':>5} {'$/hr':>7} "
          f"{'RAM_GB':>7} {'disk_GB':>8} {'rel':>5} {'verified':>8} {'country':>10} {'meets'}")
    for i, a in enumerate(annotated[:15]):
        flag = "OK" if a["meets_ram"] else "LOW RAM"
        print(f"{i+1:>3} {a['id']:>8} {a['num_gpus']:>4} {a['gpu_name']:>14} "
              f"{a['gpu_ram_gb']:>4.0f}G ${a['dph']:>6.3f} {a['ram_gb']:>6.0f} "
              f"{a['disk_gb']:>8.0f} {a['reliability']:>5.2f} {str(a['verified']):>8} "
              f"{a['country']:>10} {flag}")

    qualifying = [a for a in annotated if a["meets_ram"]]

    if not qualifying:
        print(f"\n!!! ERROR: No offers found with {MIN_RAM_GB}GB+ RAM.")
        print("!!! Renting an insufficient-RAM host will very likely fail partway")
        print("!!! through training (CPU OOM during DeepSpeed ZeRO-3 optimizer")
        print("!!! offload). Refusing to auto-select. Options:")
        print("!!!   1. Widen the search (different region/provider)")
        print("!!!   2. Manually verify a specific offer's RAM before renting")
        print("!!!   3. Reduce model size / use a different offload strategy")
        sys.exit(1)

    best = qualifying[0]
    offer_id = best["id"]
    dph = best["dph"]
    gpu_ram_gb = best["gpu_ram_gb"]
    num_gpus = best["num_gpus"]
    ram_gb = best["ram_gb"]
    gpu_name = best["gpu_name"]

    print(f"\nSelected offer {offer_id}: {num_gpus}x {gpu_name} {gpu_ram_gb:.0f}GB, "
          f"{ram_gb:.0f}GB RAM, at ${dph:.3f}/hr")
    print(f"Estimated 45-hour cost (3 generations): ${dph * 45:.2f}")

    if args.dry_run:
        print("\n[DRY RUN] Not renting. Use without --dry-run to rent this instance.")
        sys.exit(0)

    # Confirm before spending money
    print(f"\n!!! ABOUT TO SPEND MONEY !!!")
    print(f"This will rent instance from offer {offer_id} at ${dph:.3f}/hr.")
    print(f"Estimated total for 45 hours: ${dph * 45:.2f}")
    confirm = input("Type 'yes' to confirm and rent: ").strip().lower()
    if confirm != "yes":
        print("Aborted — no instance rented.")
        sys.exit(0)

    IMAGE = "pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel"

    print(f"\nCreating instance from offer {offer_id}...")
    create_data = {
        "client_id": "me",
        "image": IMAGE,
        "disk": MIN_DISK_GB,
        "label": "anubis-training-v2",
        "onstart": "/bin/bash",
        "runtype": "ssh",
        "env": {"JUPYTER_DIR": "/workspace"},
        "test": False,
    }

    # Try the /asks/{id}/ endpoint (current Vast.ai API)
    resp = requests.put(
        f"{BASE_URL}/asks/{offer_id}/",
        json=create_data,
        headers=HEADERS,
    )
    if resp.status_code == 200:
        result = resp.json()
        iid = result.get("id", 0)
        print(f"Instance created: {iid}")
    else:
        print(f"Create via /asks/ failed: HTTP {resp.status_code}: {resp.text[:300]}")
        # Fallback: try /create/ endpoint (older API)
        create_data["bundle"] = offer_id
        resp2 = requests.put(
            f"{BASE_URL}/create/",
            json=create_data,
            headers=HEADERS,
        )
        if resp2.status_code == 200:
            result2 = resp2.json()
            iid = result2.get("id", 0)
            print(f"Instance created via /create/: {iid}")
        else:
            print(f"Create via /create/ also failed: HTTP {resp2.status_code}: {resp2.text[:300]}")
            sys.exit(1)

    print("\nWaiting for instance to start...")
    for attempt in range(60):
        time.sleep(10)
        resp = requests.get(f"{BASE_URL}/instances/", headers=HEADERS)
        if resp.status_code != 200:
            continue
        instances = resp.json().get("instances", [])
        for inst in instances:
            if inst.get("id") == iid:
                status = inst.get("actual_status", "unknown")
                print(f"  Status: {status}")
                if status == "running":
                    ssh_addr = inst.get("ssh_host", "")
                    ssh_port = inst.get("ssh_port", 0)
                    print(f"\n=== Instance Ready ===")
                    print(f"Instance ID: {iid}")
                    print(f"SSH: ssh -p {ssh_port} root@{ssh_addr}")
                    print(f"GPUs: {num_gpus}x {gpu_name} {gpu_ram_gb:.0f}GB")
                    print(f"RAM: {ram_gb:.0f}GB")
                    print(f"Cost: ${dph:.3f}/hr")
                    print(f"\nIMPORTANT: verify actual RAM on the instance with "
                          f"'free -h' before starting training — the search API's "
                          f"reported RAM is not always exact.")

                    conn_info = {
                        "instance_id": iid,
                        "ssh_host": ssh_addr,
                        "ssh_port": ssh_port,
                        "ssh_command": f"ssh -p {ssh_port} root@{ssh_addr}",
                        "gpu": f"{num_gpus}x {gpu_name} {gpu_ram_gb:.0f}GB",
                        "ram_gb_reported": ram_gb,
                        "price_per_hour": dph,
                        "offer_id": offer_id,
                        "label": "anubis-training-v2",
                    }

                    conn_path = Path(__file__).resolve().parent.parent / "memory" / "training_jobs"
                    conn_path.mkdir(parents=True, exist_ok=True)
                    conn_file = conn_path / f"vast_{iid}.json"
                    conn_file.write_text(json.dumps(conn_info, indent=2), encoding="utf-8")
                    print(f"\nConnection info saved to: {conn_file}")
                    sys.exit(0)

    print("Instance did not start within 10 minutes. Check Vast.ai console.")
    sys.exit(1)


if __name__ == "__main__":
    main()
