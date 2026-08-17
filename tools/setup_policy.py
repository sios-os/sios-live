#!/usr/bin/env python3
"""Set up policy mandates and spending limits."""
import sys
sys.path.insert(0, ".")
import time
from pathlib import Path
from anubis.governance import PolicyEngine, Mandate, SpendingLimit, Transaction

policy = PolicyEngine(Path("policy"))

print("=== POLICY ENGINE SETUP ===")
print()

# 1. Set spending limits
print("--- Spending Limits ---")
policy._limits = SpendingLimit(
    daily_limit=50.0,
    weekly_limit=200.0,
    monthly_limit=1000.0,
    currency="USD",
    prohibited_categories=["gambling", "weapons", "illegal_drugs", "cryptocurrency_speculation"],
)
policy._save()
print(f"  Daily:   ${policy._limits.daily_limit}")
print(f"  Weekly:  ${policy._limits.weekly_limit}")
print(f"  Monthly: ${policy._limits.monthly_limit}")
print(f"  Prohibited: {policy._limits.prohibited_categories}")
print()

# 2. Add recurring mandates
print("--- Recurring Mandates ---")
mandates = [
    Mandate(
        mandate_id="mandate_ollama_cloud",
        description="Ollama cloud backup (monthly)",
        payee="ollama.com",
        amount_limit=10.0,
        frequency="monthly",
        created_at=time.time(),
        max_total=120.0,
    ),
    Mandate(
        mandate_id="mandate_domain",
        description="Domain registration renewal (yearly)",
        payee="namecheap.com",
        amount_limit=15.0,
        frequency="yearly",
        created_at=time.time(),
        max_total=100.0,
    ),
    Mandate(
        mandate_id="mandate_electricity",
        description="Server electricity (monthly)",
        payee="utility_co",
        amount_limit=80.0,
        frequency="monthly",
        created_at=time.time(),
        max_total=960.0,
    ),
]
for m in mandates:
    policy.add_mandate(m)
    print(f"  {m.mandate_id}: {m.description} - ${m.amount_limit}/{m.frequency}")
print()

# 3. Test transaction evaluation
print("--- Transaction Tests ---")
tests = [
    Transaction(transaction_id="tx1", payee="ollama.com", amount=10.0, purpose="cloud backup", category="software", mandate_id="mandate_ollama_cloud"),
    Transaction(transaction_id="tx2", payee="amazon.com", amount=25.0, purpose="book purchase", category="books"),
    Transaction(transaction_id="tx3", payee="casino.com", amount=50.0, purpose="gambling", category="gambling"),
    Transaction(transaction_id="tx4", payee="store.com", amount=75.0, purpose="hardware", category="electronics"),
    Transaction(transaction_id="tx5", payee="namecheap.com", amount=15.0, purpose="domain renewal", category="software", mandate_id="mandate_domain"),
]
for t in tests:
    result = policy.evaluate_transaction(t)
    print(f"  ${t.amount} to {t.payee} ({t.category}): {result['verdict']} [{result['class']}]")
    if result.get("reasons"):
        for r in result["reasons"]:
            print(f"    -> {r}")
print()

# 4. Stats
print("--- Policy Stats ---")
stats = policy.stats()
print(f"  Active mandates: {stats['active_mandates']}")
print(f"  Total transactions: {stats['total_transactions']}")
print(f"  Daily limit: ${stats['daily_limit']}")
print(f"  Prohibited categories: {stats['prohibited_categories']}")
print()

print("=== POLICY SETUP COMPLETE ===")
