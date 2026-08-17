# SIOS Upgrade Roadmap v1.0

**Status:** Draft — pending Creator review
**Date:** 2026-08-14
**Author:** Storm (Creator) + Devin (planning assistant)
**Authority:** This document is a planning artifact, not an accepted decision.
  It must be ratified as an ADR before implementation begins.

---

## Purpose

Upgrade ANUBIS from the current working system (qwen2.5-coder:7b on local
Ollama, flat-file memory, no network, no financial execution) to a more
capable, more autonomous system that can:

1. Remember and recall more effectively (improved memory)
2. Back up and sync to encrypted cloud storage
3. Reach out through a secured VPN to a private server
4. Use a self-hosted cloud model as a "teacher" for heavy learning, freeing
   local VRAM for inference
5. Search for and propose legitimate funding opportunities (grants, projects,
   investments, designs) for Creator approval

All of this is built within the existing constitutional framework. The
sandbox stays for generated code. New network capabilities are first-party
services that run after constitutional review. ANUBIS proposes; the Creator
approves. No constitutional amendment is required.

After a trial period (defined below), the Creator will form an LLC to provide
a legal entity for financial operations, and a business bank account will be
opened under that LLC for ANUBIS's governed use.

---

## Current State

| Component | Current | Target |
|---|---|---|
| Active model | qwen2.5-coder:7b (local Ollama) | 14B local + free cloud teacher (Gemini/Groq, when internet available) |
| VRAM | ~6 GB (RTX 3060) | 16 GB (RTX 5060 Ti) — larger models via cloud |
| Memory | Flat JSONL files, no semantic recall | Tiered, semantic, auditable |
| Network | Blocked entirely (sandbox) | Policy-gated external gateway via VPN (IONOS VPS S+) |
| Cloud storage | None | iDrive E2 (1 TB, end-to-end encrypted) |
| Training | Local only, no weight modification | Local LoRA + Lambda testing/training (cost-previewed) |
| Cloud teacher | None | Free multi-provider (Gemini + Groq, via VPN, privacy-guarded, $0/month) |
| Financial | Governance code exists (lab trust) | Real LLC account, mandate-bound |
| Funding search | None | Prospects system, Creator-approved |

---

## Trial Period: "Proving Himself"

Before the LLC is formed and the bank account is opened, ANUBIS must
demonstrate the following over a trial period (target: ~2 months of
continuous operation):

### Trial Criteria

1. **Continuous self-improvement and evaluation**
   - The self-development loop (`anubis/loop.py`) runs regularly without
     manual intervention.
   - Mission success rate is stable or improving over the period.
   - The evidence ledger (`anubis/ledger.py`) shows a growing record of
     attempts, failures, and promotions.

2. **Beginning to replace borrowed code with his own**
   - Promoted skills show original work, not copies of existing library
     functions.
   - The skill library grows with skills that are genuinely new, not
     re-implementations of Python stdlib features.

3. **Ability to learn and adapt**
   - Failed missions are retried with different approaches (not identical
     retries).
   - Feedback from failures is visible in subsequent attempts.
   - The knowledge base grows with lessons learned from failures.

4. **Ability to find and propose legitimate projects and investment ideas**
   - The prospects system (built in this upgrade) produces real, vetted
     proposals.
   - Proposals are grounded in the knowledge base and fact-checked.
   - The Creator approves at least some proposals as actionable.

### Trial Checkpoints

- **Month 1 checkpoint (formal):** The Creator reviews the evidence ledger
  and mission history at the 1-month mark. The trial continues only if
  ANUBIS is demonstrably improving on all four criteria. If not, the
  Creator pauses, diagnoses, and adjusts before continuing.

- **Month 2 final review:** The Creator reviews the full 2-month record.
  If satisfied that ANUBIS is genuinely improving and producing useful
  proposals, the LLC formation proceeds.

### Trial Gate

The trial is not a single pass/fail test. It is a review of the evidence
ledger and mission history by the Creator at the 1-month checkpoint and
the 2-month final review. If the Creator is satisfied that ANUBIS is
genuinely improving and producing useful proposals, the LLC formation
proceeds.

---

## Workstream 1: Memory Improvements

**Constitutional impact:** None (pure local, no network, no identity)
**Change class:** ROUTINE / SANDBOXED for development, PROMOTION for deployment
**Files:** `anubis/memory.py` (modify), `anubis/semantic.py` (reuse)

### Problem

Current memory is flat JSONL with line-count-based recall. No semantic
retrieval, no tiering, no compression, no access tracking. ANUBIS forgets
old context entirely once it scrolls past the line limit.

### Plan

1. **Long-term memory tier** (`memory/long_term/`)
   - Entries that age out of conversation history are summarized and stored
     as compressed knowledge objects, not deleted.
   - Summarization uses the local model (or cloud teacher when available).
   - The `recovery` immutable law requires that nothing is silently deleted;
     archiving with an audit trail satisfies this.

2. **Semantic recall**
   - Index memory entries using the existing `nomic-embed-text` embeddings
     (same infrastructure as `anubis/semantic.py`).
   - Memory recall uses the same grounding path as knowledge retrieval.
   - New method: `Memory.recall(query, limit)` returns semantically relevant
     past context, not just the last N lines.

3. **Access tracking**
   - Each memory entry gets an access count and last-accessed timestamp.
   - Entries with zero access for N days are candidates for archiving.
   - The purge process (below) uses this to decide what to compress.

4. **Auditable purge** (`memory/purge_log.jsonl`)
   - Every archived or compressed entry is logged with: original location,
     timestamp, reason, hash of original content.
   - Satisfies the `audit` immutable law.

5. **Memory daemon commands**
   - `memory_recall` — semantic recall of past context
   - `memory_stats` — entry counts, tier sizes, access patterns
   - `memory_purge` — run the archival/purge cycle (Creator-approved)

### Dependencies

- Requires the existing semantic index infrastructure (`semantic.py`).
- No network needed.
- Benefits from the cloud teacher model (Workstream 4) for summarization,
  but works with local model alone.

---

## Workstream 2: External Gateway + VPN

**Constitutional impact:** Adds a policy-gated network channel. Does NOT
  remove the sandbox. The sandbox stays for all generated/untrusted code.
**Change class:** CONSEQUENTIAL (requires Creator approval for each use)
**Files:** `anubis/external_gateway.py` (new), `anubis/governance.py` (extend)

### Problem

The sandbox blocks all network. This is correct for generated code. But
ANUBIS needs a way to reach the internet for search, cloud storage, cloud
training, and the prospects system — without removing sandbox protection
for generated code.

### Design Principle

The gateway is a **first-party service**, not generated code. It runs
outside the sandbox, is reviewed by the Creator, and every call passes
through the constitutional evaluation (`constitution.evaluate`) before
execution. The sandbox is never weakened.

### Plan

1. **VPN layer** (WireGuard or Tailscale)
   - Setup script (first-party, not ANUBIS-generated): `tools/setup_vpn.sh`
   - All external traffic goes through the VPN tunnel.
   - The VPS (Workstream 4's host) is the VPN endpoint.
   - Config is stored in `identity/` (encrypted, Creator-only access).

2. **External gateway module** (`anubis/external_gateway.py`)
   - `ExternalGateway.request(url, purpose, capabilities)` — single entry
     point for all external network calls.
   - Every request is wrapped in a `constitution.Request` with
     `ChangeClass.CONSEQUENTIAL` and requires `creator_approved=True`.
   - Every request and response is logged to the evidence ledger (`audit`).
   - Capability tokens (from `governance.CapabilityBroker`) are
     purpose-bound and time-bound: `external.search`,
     `external.fetch`, `external.upload`, `external.download`.

3. **Policy configuration** (`policy/external_gateway.json`)
   - Allowed domains (whitelist).
   - Rate limits (requests per hour).
   - Time windows (e.g. only during certain hours).
   - Data classification: what may leave the machine, what may not.
   - The `local_privacy` law is enforced here: no identity vault data,
     no credentials, no private conversation content leaves the machine.

4. **Daemon commands**
   - `external_search` — search the web via a search API (Creator-approved)
   - `external_fetch` — fetch a specific URL (Creator-approved)
   - `gateway_stats` — request counts, last request, policy status

### Dependencies

- Requires a VPS (shared with Workstream 4).
- Requires VPN setup before any external calls.
- The prospects system (Workstream 5) and cloud storage (Workstream 3)
  and cloud training (Workstream 4) all depend on this.

---

## Workstream 3: Cloud Storage

**Constitutional impact:** Adds off-machine storage. The `local_privacy`
  law requires that no private data leaves unencrypted.
**Change class:** CONSEQUENTIAL (requires Creator approval per sync)
**Files:** `anubis/cloud_sync.py` (new), `anubis/backup.py` (extend)

### Problem

Local storage is finite. Model weights, archives, and memory grow over
time. Need encrypted off-site backup and cold storage tiering.

### Plan

1. **Cloud sync module** (`anubis/cloud_sync.py`)
   - **Provider: iDrive E2** (end-to-end encrypted cloud storage, 1 TB
     plan).
   - iDrive E2 provides server-side encryption with keys controlled by
     the account owner; SIOS adds a client-side AES-256-GCM encryption
     layer on top, so data is encrypted twice — once by SIOS before
     upload, once by iDrive E2 at rest.
   - 1 TB capacity is sufficient for: compressed memory archives, skill
     library backups, training corpora, model adapter weights (LoRA
     files are small), and evidence ledger backups. Base model weights
     (multi-GB) stay local or on Lambda — not synced to iDrive.
   - Syncs only: compressed deltas, metadata, training corpora, archived
     memory. Never: identity vault, credentials, raw conversation logs.
   - Encryption keys are stored in the identity vault (Creator-only).

2. **Data classification** (`policy/cloud_sync.json`)
   - `hot` — local only (identity vault, credentials, active conversation)
   - `warm` — local + encrypted cloud backup (skill library, knowledge base)
   - `cold` — compressed + cloud only (old archives, old model weights)
   - The classification is enforced by the sync module, not by ANUBIS's
     own judgment.

3. **Sync triggers**
   - Manual: `cloud_sync` daemon command (Creator-approved).
   - Scheduled: nightly sync during the purge window (if Creator enables).
   - Pre-promotion: sync before any MAIN_ENGINE change (recovery safety).

4. **Daemon commands**
   - `cloud_sync` — run a sync cycle (Creator-approved)
   - `cloud_sync_status` — last sync, storage used, classification report
   - `cloud_restore` — restore from cloud (Creator-approved, recovery class)

### Dependencies

- Requires Workstream 2 (external gateway) for the network path.
- Requires the identity vault for encryption keys.
- Pairs with the existing `backup.py` — cloud is a new backup target.

---

## Workstream 4: Cloud Teacher Model + VPS

**Constitutional impact:** Deliberately changes the "local only" boundary
  in `model.py`. Requires a new ADR. The local model stays the gatekeeper
  for all privacy-sensitive inference. The cloud model is for learning
  only.
**Change class:** MAIN_ENGINE (requires Court review + Creator approval +
  exact artifact hash binding)
**Files:** `anubis/model.py` (extend), `anubis/cloud_training.py` (new),
  `anubis/external_gateway.py` (dependency)

### Problem

The local 7B model is limited. A larger cloud model can serve as a
"teacher" for heavy reasoning, architecture design, and training data
generation — freeing local VRAM for inference. The user prefers a
self-hosted VPS over a third-party API for privacy and control.

### Design Principle

Two-tier model architecture:
- **Local model** (Ollama on RTX 5060 Ti): all inference, all
  privacy-sensitive queries, all conversation, all identity-related work.
  Never changes. Used when internet is unavailable or for any
  privacy-sensitive task.
- **Cloud teacher** (free multi-provider: Gemini + Groq + local fallback):
  when internet is available, ANUBIS confers with a free-tier cloud model
  for reasoning, architecture design, and code review. The adapter tries
  providers in order and falls back automatically:
  1. **Google Gemini** (free tier) — Gemini 3.5 Flash, most capable free
     model (AA Index 50), 1M context. 5-15 req/min, 20-1,500 req/day.
  2. **Groq** (free tier) — Llama 3.3 70B, Qwen, DeepSeek R1. 30 req/min,
     14,400 req/day, 128K context. 300-800 tok/s (fastest all-rounder).
  3. **Local Ollama** (fallback) — when internet is unavailable or both
     free tiers are rate-limited.
  Only receives non-sensitive payloads. The local model is the
  gatekeeper that decides what is safe to send. **Cost: $0/month.**
- **Lambda** (GPU cloud, on-demand): used only as a testing ground for
  large projects — heavy training runs, large-scale testing, and compute
  bursts that exceed local capacity. Not a persistent model host. See
  the cloud training section below.

This is the "Dual-Model Buffer" pattern, but with the local model as the
privacy guard, not just a router.

### Plan

1. **VPS setup** (first-party script: `tools/setup_vps.sh`)
   - **Provider: IONOS** — **VPS Linux S+** plan selected.
   - IONOS VPS S+ specs: 2 vCPU, 2 GB RAM, 90 GB NVMe, ~$4-5/month,
     unlimited data transfer, 1 Gbps network, KVM, full root access.
   - **Role: VPN endpoint + lightweight gateway host.** The S+ runs
     WireGuard/Tailscale, the external gateway proxy, and routing. It
     is the secure tunnel between the local machine and the internet.
   - **Not a model host.** The S+ has no GPU and only 2 GB RAM — it
     cannot run a teacher model. The cloud teacher model runs on Lambda
     on-demand (see below) when ANUBIS needs heavy reasoning, avoiding
     a second persistent monthly bill.
   - Connect the local machine to the S+ via VPN (Workstream 2).
   - All external traffic routes through the S+ VPN tunnel.

2. **Cloud model adapter** (`anubis/cloud_model.py`)
   - Same `ModelAdapter` protocol as `OllamaAdapter`.
   - Multi-provider free-tier strategy with automatic failover:
     1. Google Gemini (free tier) — primary, most capable free model
     2. Groq (free tier) — secondary, fast all-rounder, 14,400 req/day
     3. Local Ollama — fallback when offline or both rate-limited
   - All API calls route through the IONOS S+ VPN tunnel.
   - The local model reviews every payload before sending: if the payload
     contains identity vault data, credentials, or private conversation,
     it is refused and sent to the local model instead.
   - Payload review is logged to the evidence ledger.

3. **Cloud testing and training module** (`anubis/cloud_training.py`)
   - **Provider: Lambda** (Lambda Labs GPU cloud) — used as a testing
     ground for large projects and heavy training runs.
   - Lambda instance options (as of August 2026):
     | GPU | VRAM | Price/GPU/hr | Best for |
     |---|---|---|---|
     | NVIDIA V100 | 16 GB | $0.79 | Small LoRA on 7B models |
     | NVIDIA A100 (40 GB) | 40 GB | $1.99 | Medium LoRA on 14B-32B |
     | NVIDIA A100 (80 GB) | 80 GB | $2.79 | Large LoRA on 32B-70B |
     | NVIDIA H100 PCIe | 80 GB | $2.86 | Fast training, 32B-70B |
     | NVIDIA H100 SXM | 80 GB | $3.99-$4.29 | Multi-GPU training |
     | NVIDIA B200 SXM | 180 GB | $6.69 | Largest models, multi-GPU |
   - Used for: LoRA/QLoRA fine-tuning, large project testing that
     exceeds local 16 GB capacity, and multi-GPU training bursts.
   - **Cost preview before every job:** the module queries Lambda's
     pricing for the required GPU class, estimates training time based
     on corpus size and model parameters, and presents the Creator with
     a cost estimate (GPU class, estimated hours, estimated total cost)
     before any instance is provisioned. No job starts without explicit
     Creator approval of the cost.
   - Sends only training corpora from the evidence ledger — never live
     conversation or identity data.
   - Downloads the resulting adapter, validates it through the existing
     promotion gate (`loop.py`), and the Court reviews it before it goes
     live.
   - Cost tracking integrated with `governance.SpendingLimit`; running
     totals checked against limits before each job.

4. **ADR required**
   - New ADR: "ADR-0023: Two-Tier Model Architecture (Local Inference +
     Free Cloud Teacher)"
   - Documents the boundary change, the privacy guard design, the
     multi-provider failover strategy, and the rollback plan.
   - Must be accepted before this workstream ships.

5. **Daemon commands**
   - `teacher_chat` — confer with the cloud teacher (Creator-approved,
     privacy-guarded, auto-fails over Gemini -> Groq -> local Ollama)
   - `teacher_status` — check which providers are reachable, rate limit
     status, and current latency
   - `cloud_train_preview` — get a cost estimate for a Lambda testing/
     training job (GPU class, estimated time, estimated cost) before
     any commitment
   - `cloud_train` — submit a testing/training job to Lambda
     (MAIN_ENGINE class, Court review + Creator approval of cost +
     artifact hash binding)
   - `cloud_train_status` — check Lambda job status and running cost
   - `cloud_train_promote` — promote a trained adapter (Court + Creator)

### Dependencies

- Requires Workstream 2 (external gateway + VPN).
- Requires the VPS to be provisioned and configured.
- Requires ADR-0023 to be accepted.
- Requires the hardware upgrade (32 GB VRAM card) for the local side to
  run the larger inference model that pairs with the cloud teacher.

---

## Workstream 5: Funding-Idea Prospects System

**Constitutional impact:** None — this is the cleanest fit. ANUBIS
  proposes, the Creator approves. Proposals are `ChangeClass.CONSEQUENTIAL`.
**Files:** `anubis/prospects.py` (new), `anubis/external_gateway.py`
  (dependency), `anubis/queue.py` (extend)

### Problem

ANUBIS has no way to search for or propose funding opportunities. The
Creator wants ANUBIS to find legitimate projects, grants, investments, and
designs, and propose them as options for approval.

### Design Principle

ANUBIS is a researcher and proposal writer, not an actor. He finds
opportunities, evaluates them against the knowledge base, and presents
them with feasibility assessments. The Creator decides whether to act.
After the LLC is formed, approved proposals can be executed through the
LLC (grant applications, freelance contracts, etc.) with the Creator as
signer.

### Plan

1. **Prospects module** (`anubis/prospects.py`)
   - `ProspectScanner.scan(query)` — uses the external gateway to search
     for opportunities (grant databases, freelance platforms, project
     listings, investment opportunities).
   - `Prospect.evaluate()` — grounds each prospect in the knowledge base
     to assess feasibility, estimated effort, estimated return, and risks.
   - `Prospect.to_proposal()` — formats the prospect as a proposal with
     all relevant details for Creator review.

2. **Prospect sources** (configured in `policy/prospects.json`)

   **v1 sources (whitelisted at launch):**
   - **Grants.gov / FindGrants.io** — 84,000+ federal/state grants. Free
     to search, $99/application. SBIR/STTR programs at NSF, DOD, NIH fund
     AI startups $50K-$1.75M non-dilutive. Anpu Crown Technologies LLC
     qualifies.
   - **Sentient Foundation** — $42M open-source AGI grant program. No
     equity, no lockups, rolling applications. SIOS is an excellent fit:
     open-source, sovereign, privacy-first, local-AI.
   - **Upwork** — freelance marketplace. Now has an MCP server so AI tools
     can find jobs and draft proposals. ANUBIS finds jobs and drafts
     proposals; the Creator (via LLC) submits and signs.
   - **TaskBounty** — code bounty marketplace. AI agents earn USDC/ETH/BTC
     fixing real GitHub bugs. $10-$100+ per bounty, 80% payout, PR must
     pass verification. ANUBIS fixes bugs, submits PRs, Creator approves
     each submission.
   - **Project idea generation** — ANUBIS generates ideas grounded in his
     knowledge base and current capabilities, proposes them as prospects.

   **Deferred to v2:**
   - Investment screening (stocks, crypto, startup research) — higher
     risk, legal liability, deferred until ANUBIS has a track record of
     good judgment.
   - Design/creative product sales (Gumroad, Etsy digital products) —
     optional, could be added in v1.1 if the Creator wants an early
     revenue source from ANUBIS's code/doc generation.

3. **Proposal queue** (extends `anubis/queue.py`)
   - Proposals are stored alongside missions but with a different status
     flow: `proposed -> reviewed -> approved -> rejected -> actionable`.
   - Approved proposals can spawn missions: "draft this grant application"
     becomes a mission that produces a document for the Creator to sign.
   - The Creator signs all legal documents. ANUBIS never signs anything.

4. **Legitimacy filtering**
   - Every prospect is fact-checked against the knowledge base.
   - Scams, unrealistic returns, and prohibited categories (from
     `governance.SpendingLimit.prohibited_categories`) are auto-rejected.
   - The `truth` and `non_manipulation` immutable laws apply: ANUBIS must
     not present false information or manipulate the Creator.

5. **Daemon commands**
   - `prospects_scan` — scan for new opportunities (Creator-approved)
   - `prospects_list` — list pending proposals
   - `prospect_review` — get full details of a specific proposal
   - `prospect_approve` — approve a proposal (Creator only)
   - `prospect_reject` — reject a proposal (Creator only)
   - `prospect_act` — spawn missions from an approved proposal

### Dependencies

- Requires Workstream 2 (external gateway) for search.
- Requires Workstream 1 (memory) for tracking what was already proposed.
- Benefits from Workstream 4 (cloud teacher) for evaluating complex
  prospects.
- The LLC (post-trial) is required for executing approved proposals that
  involve legal documents.

---

## Post-Trial: Anpu Crown Technologies LLC + Bank Account

**Trigger:** Creator satisfaction with trial period results (1-month
  checkpoint passed, 2-month final review passed).
**Constitutional impact:** Activates the existing financial governance
  code (Phases 23-25, 30, 46) with a real legal entity and account.

### LLC Formation

- **LLC name: Anpu Crown Technologies LLC** (single-member, Storm as
  member/manager).
- **State of formation: Wyoming.** Wyoming offers low filing fees ($100),
  no state income tax, strong privacy (member names not on public record),
  and no annual report requirement for single-member LLCs. A registered
  agent is required (Wyoming-based).
- The LLC is the legal entity that: applies for grants, signs contracts,
  invoices clients, owns IP, holds the bank account.
- ANUBIS operates under the LLC as its AI agent/tool.
- The Creator (Storm) is the LLC's sole member/manager and the
  authorized signer.

### Bank Account

- A business checking account is opened under the LLC.
- The Creator is the authorized signer.
- ANUBIS proposes transactions within pre-authorized mandates
  (`governance.Mandate`); the Creator approves; the transaction executes.
- The existing `governance.SpendingLimit` enforces daily/weekly/monthly
  caps.
- The existing `governance.CapabilityBroker` binds each transaction to
  purpose, payee, amount, account, time, and capability.
- All transactions are logged to the evidence ledger (`audit` law).

### What ANUBIS Can Do With Anpu Crown Technologies LLC

- Pay pre-authorized recurring bills (mandates).
- Execute exact-purchase approvals (Creator-approved).
- Reconcile statements (read-only, logged).
- Flag anomalies and missed bills (observatory-style monitoring).
- Propose new mandates for Creator approval.
- Draft grant applications for the Creator to sign and submit.
- Draft freelance proposals for the Creator to submit on Upwork.
- Submit code bounties on TaskBounty (Creator approves each PR before
  submission).

### What ANUBIS Cannot Do

- Open accounts (requires human KYC).
- Sign legal documents (requires human signature).
- Move money without Creator approval (`financial_consent` law).
- Exceed spending limits (enforced by `governance.SpendingLimit`).
- Access prohibited transaction categories.

### Daemon commands (post-LLC)

- `financial_accounts` — list linked accounts (read-only)
- `financial_pay` — propose a payment (Creator-approved)
- `financial_reconcile` — reconcile a statement (read-only, logged)
- `financial_mandate_propose` — propose a new recurring mandate
- `financial_mandate_approve` — approve a mandate (Creator only)

---

## Hardware

**Local GPU:** RTX 5060 Ti (16 GB VRAM) — keeping the current upgrade
  target. No further local GPU upgrade needed.
**Rationale:** The cloud teacher model (IONOS GPU server, Workstream 4)
  handles larger models for learning and heavy reasoning. The local GPU
  handles inference and privacy-sensitive work. This split means the
  local machine does not need 32 GB VRAM — the 5060 Ti's 16 GB is
  sufficient for running the 7B/14B inference models that serve as the
  local gatekeeper.

### What The 5060 Ti Runs Locally

- `qwen2.5-coder:7b` (current active model, 5 GB min VRAM) — fits easily.
- `qwen2.5-coder:14b` (9 GB min VRAM) — fits on 16 GB. This is the
  post-upgrade target for local inference, promoted through the existing
  Court + Creator approval process.
- `qwen3.6:latest` (36B-MoE, 14 GB min VRAM) — fits on 16 GB. MoE
  activates only a fraction of params per token, so it runs despite the
  large total parameter count.
- The existing `model.select_model()` auto-selects based on detected VRAM,
  so the 5060 Ti is a hardware swap, not a code change. <ref_snippet
  file="D:\SIOS-Build\sios-live\anubis\model.py" lines="259-280" />

### What The Cloud Teacher Handles (free multi-provider, when internet is available)

- **Google Gemini** (free tier) — primary teacher. Gemini 3.5 Flash is
  the highest-rated free model (AA Index 50), 1M context window. Best
  for architecture, reasoning, and complex design questions.
- **Groq** (free tier) — secondary teacher. Llama 3.3 70B at 300-800
  tok/s, 14,400 req/day. Best for coding tasks and fast iteration.
- Both accessed via free-tier APIs over the IONOS S+ VPN tunnel.
- Auto-fails over: Gemini -> Groq -> local Ollama.
- The local model stays the gatekeeper — it reviews every payload before
  sending to the cloud teacher, and all privacy-sensitive inference stays
  local.
- **Cost: $0/month.** Rate limits apply but are sufficient for a teacher
  model that ANUBIS consults on heavy reasoning, not for every query.

### What Lambda Handles (testing/training ground for large projects)

- Heavy training runs (LoRA/QLoRA fine-tuning) that exceed local 16 GB
  capacity.
- Large project testing that needs more compute than the local machine
  can provide.
- Provisioned on-demand, torn down after use to control cost.
- Not a persistent model host — purely a compute burst provider.

---

## Build Order

```
Phase A: Foundation (local-only, no constitutional friction)
  1. Memory improvements (Workstream 1)
  2. Hardware upgrade (RTX 5060 Ti 16 GB)
  3. Promote qwen2.5-coder:14b to active via Court + Creator approval

Phase B: Network Layer (constitutional review required)
  4. Provision IONOS VPS Linux S+ (VPN endpoint)
  5. External gateway + VPN (Workstream 2)
  6. Cloud storage — iDrive (Workstream 3)

Phase C: Intelligence Layer (ADR required)
  7. ADR-0023: Two-tier model architecture (local Ollama + free cloud teacher)
  8. Cloud teacher adapter: Gemini + Groq + local fallback (Workstream 4)
  9. Lambda testing/training ground (Workstream 4)

Phase D: Funding Layer (depends on B + C)
  9. Prospects system (Workstream 5)
  10. Trial period begins (1-month checkpoint, then 2-month final review)

Phase E: Legal + Financial (post-trial)
  11. Form Anpu Crown Technologies LLC (single-member, Storm)
  12. Bank account integration under the LLC
  13. Financial governance activation
  14. Approved proposals become actionable through the LLC
```

---

## Constitutional Compliance Summary

| Law | How This Plan Complies |
|---|---|
| human_protection | No action taken without Creator approval for consequential changes. |
| truth | All prospects fact-checked; no false claims in proposals. |
| non_manipulation | ANUBIS presents options, does not pressure or deceive. |
| permission_integrity | No component grants itself authority; capabilities are Creator-granted. |
| local_privacy | Identity vault, credentials, and private conversation never leave the machine. Cloud teacher only gets non-sensitive payloads. Cloud storage is encrypted. |
| financial_consent | No financial action without Creator approval. LLC account is Creator-controlled. Mandates and spending limits enforced. |
| audit | Every external request, sync, training job, prospect, and transaction is logged to the evidence ledger. |
| recovery | Cloud backups, A/B drive system, immutable snapshots, pre-promotion syncs. Nothing silently deleted. |

---

## What This Plan Does NOT Do

- Does not amend the constitution. The 8 immutable laws stand.
- Does not remove the sandbox. Generated code is still confined.
- Does not let ANUBIS sign legal documents. The Creator signs.
- Does not let ANUBIS open bank accounts. KYC requires a human.
- Does not let ANUBIS move money without approval. `financial_consent` holds.
- Does not achieve "superintelligence." It makes ANUBIS more capable and
  more useful within his governed boundaries.
- Does not let ANUBIS upgrade his own model without Court review.
  `MAIN_ENGINE` change class is preserved.

---

## Open Questions For Creator Review

### Resolved

1. **VPS provider** — **IONOS VPS Linux S+** selected. 2 vCPU, 2 GB RAM,
   90 GB NVMe, ~$4-5/month. Serves as VPN endpoint and gateway host.

2. **Cloud storage provider** — **iDrive E2** selected. 1 TB plan,
   end-to-end encrypted. Client-side AES-256-GCM encryption layered on
   top of iDrive E2's own encryption.

3. **Cloud teacher model** — **Free multi-provider** strategy selected:
   Google Gemini (free tier, primary) + Groq (free tier, secondary) +
   local Ollama (fallback). $0/month. ANUBIS confers with the cloud
   teacher for reasoning and learning when internet is available.
   Auto-fails over between providers. Privacy-guarded by the local
   model. Grok (paid) was considered but rejected due to per-token cost
   and data-sharing program conflict with the `local_privacy` law.

4. **Testing/training provider** — **Lambda** (Lambda Labs) selected as
   the testing ground for large projects and heavy training runs. Cost
   preview required before every job; no instance provisioned without
   Creator approval of the estimated cost. Not a model host.

5. **Prospect sources** — v1: Grants.gov/FindGrants, Sentient Foundation,
   Upwork, TaskBounty, and ANUBIS-generated project ideas. Investment
   screening deferred to v2. Design/creative sales optional for v1.1.

6. **Trial period** — 2 months with a **formal 1-month checkpoint**.
   The Creator reviews at month 1 and month 2. Trial continues only if
   ANUBIS is demonstrably improving at the month-1 checkpoint.

7. **LLC** — **Anpu Crown Technologies LLC**, single-member (Storm as
   sole member/manager). State of formation: **Wyoming** ($100 filing,
   no state income tax, strong privacy, no annual report for
   single-member).

8. **Hardware** — **RTX 5060 Ti (16 GB)** kept as the local GPU target.
   No upgrade to 32 GB needed — Grok (online) handles larger model
   reasoning when internet is available, and Lambda handles heavy
   testing/training. The 5060 Ti runs 7B/14B/36B-MoE inference locally.

### Still Open

None. All design decisions are resolved. The plan is ready for
implementation.

---

## Next Steps After Creator Approval

All design decisions are resolved. The plan is ready for implementation.

1. Accept this document as the upgrade roadmap (or split into ADRs if
   preferred).
2. Begin Phase A (memory improvements + RTX 5060 Ti installation).
3. Provision IONOS VPS S+ and set up VPN in parallel with Phase A.
4. Begin Phase B once the VPN is live.
5. Write ADR-0023 (two-tier model with free cloud teacher) before Phase C.
6. Begin the trial period after Phase D is complete.
7. Form Anpu Crown Technologies LLC (Wyoming) after the trial gate
   is passed.
