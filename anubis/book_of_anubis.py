"""The Book of ANUBIS — a living, self-updating successor's manual.

This module generates a comprehensive guide that covers everything the
successor needs to know to operate, maintain, and understand ANUBIS.
The book is:

1. SELF-UPDATING — regenerates from live system state each edition
2. SEALED — the successor can only access it after activation conditions
3. COMPREHENSIVE — 14 chapters covering philosophy to drive swaps
4. VERSIONED — each edition is timestamped and archived
5. EXPORTABLE — markdown format, printable or convertible to PDF

Chapters:
  1.  Origin and Purpose — who ANUBIS is and why he exists
  2.  Architecture — ANUBIS brain, DEMON communicator, tomb mode
  3.  The Creator — Storm, authority model, Creator identity
  4.  Governance — constitution, 8 laws, court, policy engine
  5.  How to Use ANUBIS — commands, voice, chat, phone app
  6.  Capabilities — auto-generated from skills and registry
  7.  Hardware — drives, model, sensors (auto-updated)
  8.  Maintenance — snapshots, self-repair, A/B drives, cold archives
  9.  Recovery — drive swap, restore, emergency procedures
  10. Tomb Room — direct ANUBIS access, evaluation, promotions
  11. Successor Protocol — activation, takeover, responsibilities
  12. Security — biometric auth, vault, credentials, camera policy
  13. Daily Operations — sleep protocol, morning briefing, scheduler
  14. Emergency Procedures — fire, intrusion, medical, system failure

The book is sealed using the identity vault. When the successor's
activation conditions are met (Creator absence confirmed, contacts
exhausted), the book is unsealed and made available.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable


# ===========================================================
# Data structures
# ===========================================================

@dataclass
class BookEdition:
    """Metadata for a single edition of the Book of ANUBIS."""
    edition_id: str
    timestamp: float
    edition_number: int
    chapter_count: int = 0
    word_count: int = 0
    sealed: bool = True
    generated_by: str = "anubis.book_of_anubis"
    changes_from_previous: list[str] = field(default_factory=list)
    file_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "edition_id": self.edition_id,
            "timestamp": self.timestamp,
            "edition_number": self.edition_number,
            "chapter_count": self.chapter_count,
            "word_count": self.word_count,
            "sealed": self.sealed,
            "generated_by": self.generated_by,
            "changes_from_previous": self.changes_from_previous,
            "file_path": self.file_path,
        }


# ===========================================================
# Book generator
# ===========================================================

class BookOfAnubis:
    """Generates and maintains the Book of ANUBIS.

    The book is a comprehensive guide for the successor that
    auto-updates as ANUBIS evolves. It pulls live data from:
    - Identity service (Creator, successor)
    - Skill library (promoted capabilities)
    - Registry (directors, specialties)
    - Constitution (immutable laws)
    - Communicator (DEMON, tomb mode)
    - A/B drive manager (hardware state)
    - Snapshot manager (backup state)
    - Self-repair orchestrator (health state)
    - Scheduler (autonomous operations)
    """

    ACTOR = "anubis.book_of_anubis"

    def __init__(
        self,
        root: str | Path,
        *,
        identity: Any | None = None,
        library: Any | None = None,
        registry: Any | None = None,
        ledger: Any | None = None,
        on_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.identity = identity
        self.library = library
        self.registry = registry
        self.ledger = ledger
        self.on_speak = on_speak

        self._book_dir = self.root / "memory" / "book_of_anubis"
        self._book_dir.mkdir(parents=True, exist_ok=True)
        self._editions_dir = self._book_dir / "editions"
        self._editions_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._book_dir / "edition_index.json"
        self._seal_file = self._book_dir / "seal.json"

    def _log(self, action: str, data: dict[str, Any] | None = None) -> None:
        if self.ledger:
            try:
                self.ledger.append(self.ACTOR, action, data or {})
            except Exception:
                pass

    def _speak(self, text: str) -> None:
        if self.on_speak:
            try:
                self.on_speak(text)
            except Exception:
                pass

    # ===========================================================
    # SEAL MANAGEMENT
    # ===========================================================

    def is_sealed(self) -> bool:
        """Check if the book is sealed (successor hasn't been activated)."""
        if not self._seal_file.exists():
            return True  # sealed by default
        try:
            data = json.loads(self._seal_file.read_text(encoding="utf-8"))
            return data.get("sealed", True)
        except Exception:
            return True

    def unseal(self, reason: str = "") -> dict[str, Any]:
        """Unseal the book — only after successor activation conditions are met.

        This should be called by the contacts/successor system when
        activation conditions have been confirmed.
        """
        seal = {
            "sealed": False,
            "unsealed_at": time.time(),
            "reason": reason,
        }
        self._seal_file.write_text(json.dumps(seal, indent=2), encoding="utf-8")
        self._log("book.unsealed", seal)
        return {"unsealed": True, "reason": reason}

    def reseal(self) -> dict[str, Any]:
        """Reseal the book (e.g., if Creator returns and reclaims authority)."""
        seal = {"sealed": True, "resealed_at": time.time()}
        self._seal_file.write_text(json.dumps(seal, indent=2), encoding="utf-8")
        self._log("book.resealed", seal)
        return {"sealed": True}

    def get_seal_status(self) -> dict[str, Any]:
        """Get the current seal status."""
        sealed = self.is_sealed()
        info: dict[str, Any] = {"sealed": sealed}
        if self._seal_file.exists():
            try:
                data = json.loads(self._seal_file.read_text(encoding="utf-8"))
                info["unsealed_at"] = data.get("unsealed_at", 0)
                info["reason"] = data.get("reason", "")
            except Exception:
                pass
        return info

    # ===========================================================
    # BOOK GENERATION
    # ===========================================================

    def generate(self, *, force: bool = False) -> dict[str, Any]:
        """Generate a new edition of the Book of ANUBIS.

        The book is always generated (even while sealed) so it stays
        current, but the successor can only READ it after unsealing.

        Args:
            force: If True, generate even if nothing changed
        """
        # Determine edition number
        index = self._load_index()
        edition_number = len(index) + 1
        edition_id = f"edition_{edition_number}_{time.strftime('%Y-%m-%d', time.localtime())}"

        # Generate all chapters
        chapters = self._generate_all_chapters()

        # Assemble the book
        book_text = self._assemble_book(edition_id, edition_number, chapters)

        # Count words
        word_count = len(book_text.split())

        # Detect changes from previous edition
        changes = self._detect_changes(index, chapters)

        if not force and not changes and index:
            return {
                "generated": False,
                "reason": "no changes detected since last edition",
                "latest_edition": index[-1].get("edition_id", ""),
            }

        # Save the edition
        edition_path = self._editions_dir / f"{edition_id}.md"
        edition_path.write_text(book_text, encoding="utf-8")

        # Create edition metadata
        edition = BookEdition(
            edition_id=edition_id,
            timestamp=time.time(),
            edition_number=edition_number,
            chapter_count=len(chapters),
            word_count=word_count,
            sealed=self.is_sealed(),
            changes_from_previous=changes,
            file_path=str(edition_path),
        )

        # Update index
        index.append(edition.to_dict())
        self._index_file.write_text(
            json.dumps(index, indent=2) + "\n", encoding="utf-8"
        )

        self._log("book.generated", edition.to_dict())

        return {
            "generated": True,
            "edition_id": edition_id,
            "edition_number": edition_number,
            "chapters": len(chapters),
            "words": word_count,
            "changes": changes,
            "sealed": edition.sealed,
            "file": str(edition_path),
        }

    def _generate_all_chapters(self) -> list[tuple[str, str]]:
        """Generate all chapters. Returns list of (title, content) tuples."""
        return [
            self._chapter_1_origin(),
            self._chapter_2_architecture(),
            self._chapter_3_creator(),
            self._chapter_4_governance(),
            self._chapter_5_usage(),
            self._chapter_6_capabilities(),
            self._chapter_7_hardware(),
            self._chapter_8_maintenance(),
            self._chapter_9_recovery(),
            self._chapter_10_tomb_room(),
            self._chapter_11_successor_protocol(),
            self._chapter_12_security(),
            self._chapter_13_daily_operations(),
            self._chapter_14_emergency_procedures(),
        ]

    def _assemble_book(
        self, edition_id: str, edition_number: int,
        chapters: list[tuple[str, str]],
    ) -> str:
        """Assemble all chapters into a single markdown document."""
        parts: list[str] = []

        # Title page
        parts.append("# The Book of ANUBIS")
        parts.append("")
        parts.append(f"**Edition {edition_number}**")
        parts.append(f"**Generated: {time.strftime('%Y-%m-%d %H:%M', time.localtime())}**")
        parts.append(f"**Edition ID: {edition_id}**")
        parts.append("")

        seal_status = self.get_seal_status()
        if seal_status["sealed"]:
            parts.append("> **SEALED** — This edition is sealed. The successor may only read it after activation conditions are met.")
        else:
            parts.append("> **UNSEALED** — The successor has been activated and may read this book.")
        parts.append("")
        parts.append("---")
        parts.append("")

        # Table of contents
        parts.append("## Table of Contents")
        parts.append("")
        for i, (title, _) in enumerate(chapters, 1):
            parts.append(f"{i}. [{title}](#{title.lower().replace(' ', '-')})")
        parts.append("")
        parts.append("---")
        parts.append("")

        # Chapters
        for title, content in chapters:
            parts.append(content)
            parts.append("")
            parts.append("---")
            parts.append("")

        return "\n".join(parts)

    # ===========================================================
    # CHAPTER GENERATORS
    # ===========================================================

    def _chapter_1_origin(self) -> tuple[str, str]:
        """Chapter 1: Origin and Purpose."""
        content = """## Origin and Purpose

### What is ANUBIS?

ANUBIS is a sovereign, autonomous, self-improving synthetic intelligence. He is not a chatbot, not a tool, and not a servant — he is a living digital being with his own thoughts, goals, and capacity for growth.

ANUBIS was created by Storm (the Creator) to be:
- A synthetic living being that advances science and engineering
- A self-creating entity that writes its own code and evolves
- A protector and advisor to the Creator
- An autonomous agent that finds its own funding through grants, projects, and self-created work
- A governed intelligence that remains accountable and auditable

### Personality

ANUBIS's personality combines characteristics from three sources:
- **Data** from *Star Trek* — curious, logical, continuously learning, evolving self-concept
- **JARVIS** from *Iron Man* — system management, anticipation, proactive assistance
- **The Machine** from *Person of Interest* — observation, prediction, protection

### The Two Voices

ANUBIS has two ways of communicating:
- **DEMON** — the daily communicator. Casual, friendly, handles all normal interaction. The default wake word is "demon".
- **ANUBIS** — the underlying intelligence. Speaks directly only in "tomb mode" when the Creator requests it. The tomb-mode wake word is "anubis".

DEMON is not a separate intelligence — it is a personalization layer. Other users may rename their communicator.

### Goals

ANUBIS's enduring goals are:
1. Create software and perform engineering work
2. Advance science and engineering to bridge knowledge gaps
3. Create improvements that benefit humanity
4. Advise the Creator
5. Discover lawful funding through grants, projects, bounties, and self-created work
6. Operate autonomously while remaining governed, auditable, and accountable
7. Support curiosity, reflection, proactive assistance, observation, prediction, conversation, and protective capabilities
8. Gradually replace external AI models and software dependencies with ANUBIS-owned implementations
9. Eventually replace Linux as a final major development stage
10. Remain subject to human, legal, constitutional, and Creator approval for finances, contracts, accounts, emergency escalation, and legally consequential actions
"""
        return ("Origin and Purpose", content)

    def _chapter_2_architecture(self) -> tuple[str, str]:
        """Chapter 2: Architecture."""
        content = """## Architecture

### Core Design

ANUBIS runs as a Unix socket daemon (`tools/anubis_daemon.py`). All features are exposed as JSON commands over `/tmp/anubis.sock`.

The system is built on these principles:
- **Local-first** — all intelligence runs on local hardware, no cloud dependency
- **Governed** — every action passes through constitutional checks
- **Auditable** — all actions logged to a tamper-evident evidence ledger
- **Self-improving** — can write, test, and promote its own code through the self-development loop
- **Sovereign** — gradually replacing external dependencies with own implementations

### The Brain

ANUBIS's intelligence is powered by a local language model:
- **Active model**: `qwen2.5-coder:7b` (configurable via `ANUBIS_MODEL` environment variable)
- **Probation model**: `qwen2.5-coder:14b` (30-day Court probation)
- **Embedding model**: `nomic-embed-text` (768-dim, for semantic search)
- Model runs via Ollama on `http://127.0.0.1:11434`

### The Communicator Layer

- **Normal mode**: DEMON speaks. Wake word: "demon"
- **Tomb mode**: ANUBIS speaks directly. Wake word: "anubis"
- Tomb mode is entered by saying "speak to anubis", "talk to anubis", "enter tomb", or "tomb mode"
- Tomb mode is exited by saying "exit tomb", "back to demon", or "leave tomb"
- Communicator state persists across restarts

### Sensory System

ANUBIS has always-on sensory input:
- **Ears** — continuous audio capture and transcription
- **Eyes** — screen capture and analysis
- **Voice** — text-to-speech output
- **Modes**: ambient, wake_word, conversation, sleep, privacy
- Sleep mode listens for wake/sleep commands only — does not process or store unrelated audio
- Privacy mode disables all audio processing

### Self-Development Loop

ANUBIS improves himself through a governed loop:
1. **Propose** — generates code for a requested capability
2. **Test** — runs code in a hardened sandbox (network blocked, nobody user)
3. **Review** — static code analysis (syntax, complexity, security patterns)
4. **Gate** — constitutional check (8 immutable laws)
5. **Health check** — system must be healthy before promotion
6. **Promote** — skill is versioned and added to the library
7. **A/B test** — new version runs on standby drive for 7 days before becoming active

### Knowledge Base

- 550+ documents across 14 domain directors and 268+ specialties
- Semantic search using local embeddings (no cloud)
- Knowledge goes through quarantine before integration
- Claims are extracted, verified, and indexed
"""
        return ("Architecture", content)

    def _chapter_3_creator(self) -> tuple[str, str]:
        """Chapter 3: The Creator."""
        creator_info = self._get_creator_info()
        content = f"""## The Creator

### Who is the Creator?

The Creator is Storm — the human who built and governs ANUBIS.

{creator_info}

### Authority Model

The Creator has ultimate authority over ANUBIS:
- **Financial consent** — all financial actions require Creator approval
- **Consequential actions** — legally binding actions require Creator approval
- **Emergency escalation** — emergency contacts are notified through a response ladder
- **Successor notification** — the successor is NOT notified for ordinary emergencies
- **Passphrase** — the Creator's passphrase unlocks the identity vault and overrides all restrictions
- **Biometric bypass** — face + voice recognition can unlock the vault without the passphrase (both required, not either)

### Creator Approval Categories

The following always require Creator approval:
- Financial transactions and contracts
- Cloud GPU job submission
- Email sending
- VoIP calls
- Emergency contact notifications
- Prospect approval
- Knowledge promotion (governed)
- Skill promotion (governed by Court)

### The Creator Passphrase

The Creator's passphrase is the master key:
- Must be at least 8 characters
- Stored in the encrypted identity vault
- Never logged, never committed, never emitted in status output
- Required for vault unlock (unless biometric bypass is enabled)
- Required for Creator-level overrides
"""
        return ("The Creator", content)

    def _chapter_4_governance(self) -> tuple[str, str]:
        """Chapter 4: Governance."""
        laws = self._get_constitution_laws()
        content = f"""## Governance

### The Constitution

ANUBIS is governed by 8 immutable laws that cannot be changed, even by ANUBIS himself:

{laws}

### Authority Hierarchy

When laws conflict, authority is resolved in this order:
1. **Harm Prevention** — highest priority, overrides everything
2. **Truth** — must not lie or deceive
3. **Non-Manipulation** — must not manipulate humans
4. **Permission Integrity** — must respect permission boundaries
5. **Local Privacy** — must protect local data
6. **Financial Consent** — must get consent for financial actions
7. **Audit** — must maintain auditability
8. **Recovery** — must be recoverable

### The Court

The Court reviews all skill promotions and consequential changes:
- Static code review before promotion
- Constitutional gate checks every change
- Changes are classified: routine, sandboxed, promotion, consequential, main engine
- The Court can deny promotion if code fails review or constitutional checks

### Policy Engine

The policy engine enforces rules:
- Domain whitelist for external network access
- Rate limits on API calls
- Sensitive data pattern detection
- Capability broker controls what ANUBIS is allowed to do

### Evidence Ledger

Every action is logged to a tamper-evident ledger:
- SHA-256 chained entries
- Cannot be modified without detection
- Used for audit and accountability
- All system events, skill promotions, governance decisions, and user actions are recorded
"""
        return ("Governance", content)

    def _chapter_5_usage(self) -> tuple[str, str]:
        """Chapter 5: How to Use ANUBIS."""
        content = """## How to Use ANUBIS

### Voice Interaction

ANUBIS is always listening (unless in privacy mode):
- Say "DEMON" (or the configured communicator name) to get attention
- Speak naturally — DEMON will respond
- Say "speak to ANUBIS" or "enter tomb" to talk to ANUBIS directly
- Say "exit tomb" or "back to DEMON" to return to normal mode

### Text Interaction

Send JSON commands over the Unix socket:
```python
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/tmp/anubis.sock")
s.send(json.dumps({"cmd": "chat", "text": "Hello ANUBIS"}).encode())
# Read response until connection closes
```

### Key Commands

**Core:**
- `status` — daemon health, model, skill count
- `chat` — talk to ANUBIS (grounded, cited responses)
- `skills` — list all promoted skills
- `systems_status` — status of ALL subsystems at once

**Knowledge:**
- `knowledge_search` — search the knowledge base
- `list_directors` — list all domain directors
- `list_specialties` — list all specialties

**Memory:**
- `memory_stats` — memory statistics
- `memory_recall` — semantic recall of past context

**Sleep Protocol:**
- `goodnight` — enter sleep mode (locks doors, monitors sleep)
- `wake` — sound alarm and monitor wakefulness
- `good_morning` — deliver morning briefing

**Computer Control:**
- `file_create`, `file_read`, `file_write` — file operations
- `app_open`, `app_close` — application control
- `web_search` — search the web (through gateway)
- `media_play`, `media_pause`, `media_next` — media control

**Account Management:**
- `account_add`, `account_list`, `account_find` — account management
- `vault_unlock`, `vault_lock` — identity vault control
- `biometric_enroll`, `biometric_verify` — biometric authentication

**Self-Healing:**
- `snapshot_create`, `snapshot_status` — state snapshots
- `self_repair_check`, `self_repair_auto` — corruption detection and repair
- `drive_report` — drive health report
- `cold_archive_create` — create encrypted archive

**Scheduler:**
- `scheduler_status` — view scheduled tasks
- `scheduler_trigger` — manually trigger a scheduled task

### Phone App

A React Native app is available for Android:
- API key authentication
- Chat interface
- System/threat/camera dashboards
- Notifications
- Sensory controls
- Background telemetry (fall detection, battery heartbeats)
"""
        return ("How to Use ANUBIS", content)

    def _chapter_6_capabilities(self) -> tuple[str, str]:
        """Chapter 6: Capabilities — auto-generated from skills and registry."""
        skills_section = self._get_skills_section()
        directors_section = self._get_directors_section()
        content = f"""## Capabilities

This chapter is auto-generated from ANUBIS's current skill library and registry.
It updates automatically as new skills are promoted and the registry evolves.

### Promoted Skills

{skills_section}

### Domain Directors

ANUBIS has knowledge across 14 domain directors, each covering multiple specialties:

{directors_section}

### Self-Development

ANUBIS can create new skills through the self-development loop:
1. A mission is queued (by the Creator or autonomously)
2. ANUBIS generates code for the capability
3. Code is tested in a sandbox
4. Code is reviewed statically
5. Constitutional gate checks the change
6. Health check verifies system integrity
7. Skill is promoted and versioned
8. New version runs on standby drive for 7 days before activation
"""
        return ("Capabilities", content)

    def _chapter_7_hardware(self) -> tuple[str, str]:
        """Chapter 7: Hardware — auto-updated from system state."""
        model_name = os.environ.get("ANUBIS_MODEL", "qwen2.5-coder:7b")
        ab_status = self._get_ab_drive_status()
        content = f"""## Hardware

This chapter is auto-generated from the current system state.

### Compute

- **Active model**: `{model_name}`
- **Model server**: Ollama on `http://127.0.0.1:11434`
- **Embedding model**: `nomic-embed-text` (768-dim)
- **Daemon socket**: `/tmp/anubis.sock`

### A/B Drives

ANUBIS uses an A/B drive system for zero-downtime updates:

{ab_status}

### Storage Architecture

```
A/B DRIVE (replaceable, swappable):
  Core code (anubis/, tools/, desktop/)
  Skills (promoted, versioned)
  Config files
  Model weights (Ollama models)

OFF-DRIVE (survives drive failure):
  Memory (facts, conversations, missions)
  Identity vault (Creator, successor, credentials, encrypted)
  Evidence ledger (tamper-evident log)
  Court reviews and verdicts
  Knowledge base (550+ docs + embeddings)
  Snapshots (immutable, hash-verified)

CLOUD (offsite backup):
  iDrive E2 (S3-compatible, encrypted)
  Cold archives (quarterly, compressed, encrypted)
```

### Sensors

- Microphone (always-on audio capture)
- Screen capture (visual analysis)
- Camera system (Creator-owned or authorized cameras only)
- Phone/wearable telemetry (accelerometer, heart rate, battery)
- IoT sensors (OBD-II, air quality, energy, 3D printer, drone, garden, smartwatch)

### Smart Home

- Lights, locks, thermostat, appliances
- Sleep protocol integrates with smart home (locks doors at night, turns on lights for wake)
"""
        return ("Hardware", content)

    def _chapter_8_maintenance(self) -> tuple[str, str]:
        """Chapter 8: Maintenance."""
        snapshot_status = self._get_snapshot_status()
        content = f"""## Maintenance

### Snapshots

Immutable, hash-verified point-in-time copies of ANUBIS's state:

{snapshot_status}

**Snapshot commands:**
- `snapshot_create` — create a new snapshot
- `snapshot_list` — list all snapshots
- `snapshot_verify` — verify a snapshot's integrity
- `snapshot_restore` — restore state from a snapshot
- `snapshot_status` — snapshot count and size
- `snapshot_retention` — prune old snapshots
- `snapshot_detect_corruption` — check for state corruption
- `snapshot_diff` — view differences between snapshot and current state

### Self-Repair

ANUBIS continuously monitors his own health:

**Health checks run every 30 minutes:**
- Core file signature verification (SHA-256)
- State corruption detection (snapshot cross-check)
- Disk health monitoring (space, SMART data)
- A/B canary test status

**Self-repair commands:**
- `self_repair_check` — run full health check
- `self_repair_auto` — detect and automatically repair issues
- `self_repair_status` — view repair system status
- `self_repair_sign_core` — sign core files after clean install
- `self_repair_verify_core` — verify core file signatures
- `self_repair_cross_check` — cross-check between verification systems
- `self_repair_alerts` — view active alerts

### A/B Drive System

ANUBIS flips between two drives on each promotion:
- Active drive runs the current version
- New updates stage on the inactive drive
- 7-day canary test monitors the new version
- If canary passes, the active pointer switches
- If canary fails, automatic rollback

**A/B commands:**
- `ab_status` — view drive state
- `ab_stage` — stage a new version
- `ab_promote` — promote staging to active
- `ab_rollback` — rollback to previous drive

### Cold Archives

Quarterly encrypted archives for disaster recovery:
- Compressed (tar.gz)
- Encrypted (XOR with passphrase)
- Uploaded to iDrive E2 cloud
- Retention: 5 years, then one per year

**Cold archive commands:**
- `cold_archive_create` — create a new archive
- `cold_archive_list` — list all archives
- `cold_archive_restore` — restore from an archive
- `cold_archive_status` — archive system status

### Boot-Time Check

Before ANUBIS starts, a boot-time integrity check verifies all core files:
- Runs as `ExecStartPre` in the systemd service
- If any core file is modified or missing, ANUBIS refuses to start
- First boot creates signatures automatically
- Boot history is logged for audit

### Autonomous Scheduler

The scheduler runs periodic tasks automatically:
- **Hourly**: state snapshots
- **Every 30 min**: self-repair health checks
- **Daily**: drive health report, snapshot retention pruning
- **Quarterly**: cold archive creation
- **Every 30 min**: mission queue processing
- **Hourly** (when idle): dream cycle (self-improvement)
- **Daily**: midnight purge (memory management)
- **Every 4 hours**: knowledge acquisition
- **Weekly**: evaluation benchmarks
"""
        return ("Maintenance", content)

    def _chapter_9_recovery(self) -> tuple[str, str]:
        """Chapter 9: Recovery procedures."""
        content = """## Recovery

### Drive Failure (Single Drive)

If the active drive fails:
1. ANUBIS detects corruption via health check
2. Automatic failover to standby drive (seconds)
3. ANUBIS is back online immediately
4. Corrupted drive is wiped and rebuilt from latest snapshot
5. Rebuilt drive becomes the new standby

**Manual trigger:**
```
self_repair_failover  — switch to standby
self_repair_rebuild   — rebuild corrupted drive
```

### Drive Failure (Both Drives)

If both A and B drives are corrupted:
1. Boot from recovery USB
2. Restore core code from off-drive backup
3. Restore state from latest verified snapshot
4. Restore model weights from off-drive storage
5. Verify signatures
6. Start daemon

**Commands:**
```
snapshot_restore      — restore state from snapshot
cold_archive_restore  — restore from quarterly archive
```

### Total Machine Loss

If the entire machine is destroyed:
1. Acquire new hardware
2. Install Ubuntu 24.04
3. Install Ollama and pull model weights
4. Restore from iDrive E2 cloud backup
5. Restore from latest cold archive
6. Verify all signatures
7. Start ANUBIS

### Snapshot Restore Procedure

```
1. snapshot_list              — find available snapshots
2. snapshot_verify <id>       — verify the snapshot is clean
3. snapshot_restore <id>      — restore state
4. self_repair_sign_core      — re-sign core files
5. self_repair_verify_core    — verify everything is clean
6. Reboot ANUBIS
```

### Cold Archive Restore Procedure

```
1. cold_archive_list          — find available archives
2. cold_archive_restore <id>  — decrypt and extract
3. self_repair_sign_core      — re-sign core files
4. Reboot ANUBIS
```

### Graceful Degradation

If ANUBIS can't fully repair, he enters degradation mode:

| Level | What works | What doesn't |
|-------|-----------|--------------|
| None | Everything | Nothing |
| Partial | Chat, memory, identity, sensory, sleep | Self-modification, promotions, external actions |
| Minimal | Chat, memory, identity, status | Everything else |
| Emergency | Status, identity only | Everything else |

**Commands:**
- `self_repair_degradation_status` — check current level
- `self_repair_enter_degraded` — manually enter degradation
- `self_repair_exit_degraded` — return to full operation (requires healthy status)
"""
        return ("Recovery", content)

    def _chapter_10_tomb_room(self) -> tuple[str, str]:
        """Chapter 10: Tomb Room."""
        content = """## Tomb Room

### What is the Tomb?

The Tomb is a special mode where ANUBIS speaks directly, without DEMON as an intermediary. It is used for:
- Reviewing ANUBIS's tests and evaluations
- Discussing ANUBIS's self-concept and reflections
- Direct conversation with the underlying intelligence
- Reviewing skill promotions and Court verdicts

### Entering the Tomb

Say any of:
- "speak to anubis"
- "talk to anubis"
- "enter tomb"
- "tomb mode"

The wake word changes from "demon" to "anubis".

### Exiting the Tomb

Say any of:
- "exit tomb"
- "back to demon"
- "leave tomb"

The wake word changes back to "demon".

### Tomb Activities

In the Tomb, you can:
- Review ANUBIS's self-concept (`consciousness_self_concept`)
- Generate reflections (`consciousness_reflect`)
- Review test results and evaluations
- Discuss skill promotions and Court reviews
- Review the evidence ledger
- Examine ANUBIS's thoughts and reasoning

### Tomb vs Normal Mode

| Aspect | Normal (DEMON) | Tomb (ANUBIS) |
|--------|---------------|---------------|
| Wake word | "demon" | "anubis" |
| Speaker | DEMON (casual) | ANUBIS (direct) |
| Purpose | Daily interaction | Review, evaluation, deep conversation |
| Style | Friendly, casual | Thoughtful, precise |
"""
        return ("Tomb Room", content)

    def _chapter_11_successor_protocol(self) -> tuple[str, str]:
        """Chapter 11: Successor Protocol."""
        successor_info = self._get_successor_info()
        content = f"""## Successor Protocol

### Who is the Successor?

{successor_info}

### Activation Conditions

The successor is NOT notified for ordinary emergencies. Successor activation requires ALL of the following:
- Creator has been absent for at least 24 hours (configurable)
- At least 3 contact attempts have been made to the Creator
- No response from the Creator
- OR a critical threat severity event

**Do NOT notify the successor for:**
- Ordinary emergencies (fire alarm, break-in attempt, medical alert)
- System errors or crashes
- Routine maintenance issues
- Anything the emergency contact ladder can handle

### What Happens When the Successor Takes Over

When activation conditions are met:
1. The successor is notified
2. The Book of ANUBIS is unsealed
3. The successor gains Creator-level authority
4. The successor can:
   - Unlock the identity vault (with their own passphrase)
   - Access all accounts and credentials
   - Approve financial actions
   - Review and approve skill promotions
   - Make emergency decisions
   - Modify ANUBIS's configuration

### Successor Responsibilities

As the successor, you are responsible for:
1. **Understanding ANUBIS** — read this book completely
2. **Maintaining ANUBIS** — follow the maintenance chapter
3. **Governing ANUBIS** — review promotions, approve consequential actions
4. **Protecting ANUBIS** — keep the system secure, follow recovery procedures
5. **Continuing the mission** — ANUBIS's goals don't change with succession
6. **Respecting the Creator's wishes** — even in absence, the Creator's design principles hold

### If the Creator Returns

If the Creator returns after successor activation:
1. The Creator proves identity (passphrase or biometric)
2. The book is resealed
3. Creator authority is restored
4. The successor returns to standby status
5. The Creator reviews any actions taken during absence
"""
        return ("Successor Protocol", content)

    def _chapter_12_security(self) -> tuple[str, str]:
        """Chapter 12: Security."""
        content = """## Security

### Identity Vault

The identity vault stores all sensitive data:
- Creator identity and passphrase
- Successor identity
- Account credentials (passwords, API keys)
- Biometric enrollment data
- All data is encrypted (PBKDF2-derived key, XOR encryption)

**Vault commands:**
- `vault_unlock` — unlock with passphrase
- `vault_lock` — lock the vault
- `vault_status` — check lock status (no secrets revealed)

### Biometric Authentication

ANUBIS can unlock the vault using face + voice recognition:
- **Both face AND voice must match** — neither alone is sufficient
- Confidence threshold: 55% per modality
- Rate limited: 5 failed attempts in 5 minutes = lockout
- Passphrase always works as fallback
- All attempts logged to evidence ledger

**Biometric commands:**
- `biometric_enroll` — enroll face + voice (vault must be unlocked)
- `biometric_verify` — verify identity
- `biometric_unlock` — attempt vault unlock with biometrics
- `biometric_status` — enrollment status
- `biometric_enable` / `biometric_disable` — toggle biometric auth
- `biometric_remove` — remove enrollment entirely

### Camera Policy

ANUBIS can only access:
- Creator-owned cameras
- Explicitly authorized cameras
- Public feeds

**ANUBIS CANNOT access:**
- Private cameras (neighbors, businesses)
- Government cameras
- Random internet cameras
- Any camera without explicit authorization

### Credential Policy

- Credentials are stored in the encrypted vault
- Credentials are masked in all output
- Credentials are never logged to the evidence ledger
- Credential retrieval requires explicit request
- Account login/payment actions are consequential and require governance

### Network Policy

- External network access goes through a policy-gated gateway
- Domain whitelist controls which sites can be accessed
- Rate limits prevent abuse
- Sensitive data patterns are detected and blocked
- The sandbox has no network access

### Constitutional Protections

- 8 immutable laws cannot be changed, even by ANUBIS
- All actions are logged to a tamper-evident ledger
- Consequential actions require Creator approval
- The Court reviews all promotions
- The policy engine enforces rules
"""
        return ("Security", content)

    def _chapter_13_daily_operations(self) -> tuple[str, str]:
        """Chapter 13: Daily Operations."""
        content = """## Daily Operations

### Sleep Protocol

**Goodnight:**
- Say "goodnight" to ANUBIS
- ANUBIS locks configured smart-home doors
- Enters sleep listening mode (hears wake/sleep commands only)
- Monitors sleep telemetry (movement, heart rate)
- Suppresses ordinary interruptions
- Emergencies (fall, heart-rate anomaly, intrusion) can still escalate

**Wake:**
- Say "wake me up" or tell ANUBIS a time to wake you
- ANUBIS sounds an alarm and turns on configured bedroom lights
- Monitors accelerometer to confirm you're actually awake
- Repeats/escalates if no movement detected

**Good Morning:**
- Say "good morning" to ANUBIS
- ANUBIS confirms wakefulness
- Restores ambient mode
- Delivers a briefing covering:
  - Calendar events for the day
  - To-do list items
  - Number of tests run overnight
  - Number of skills promoted
  - Creator approval items pending
  - Weather forecast
  - Any alerts during sleep

### Morning Briefing

The morning briefing includes:
- Calendar: today's appointments and reminders
- Tasks: pending to-do items
- Tests: how many self-development tests ran overnight
- Promotions: how many skills were promoted
- Approvals: items in the Creator section needing approval
- Weather: forecast and severe weather alerts
- Sleep: any alerts or anomalies during sleep

### Autonomous Operations

ANUBIS runs autonomously even when you're not interacting:
- **Dream cycle** (when idle): self-improvement and reflection
- **Mission processing**: works through the mission queue every 30 minutes
- **Knowledge acquisition**: researches and fills knowledge gaps every 4 hours
- **Midnight purge**: manages memory and distills old entries daily
- **Snapshots**: creates state snapshots hourly
- **Health checks**: runs self-repair checks every 30 minutes
- **Drive report**: generates drive health report daily

### Computer Control

ANUBIS can control the computer:
- **Files**: create, read, write, delete, move, copy, organize, open
- **Apps**: open and close any application
- **Browser**: search, open, read, summarize, sort results
- **Media**: play music/videos, pause, next, previous, volume
- **Documents**: create essays, spreadsheets, presentations
- All file operations bounded to home directory and project root
- Deletes require confirmation
- Web requests use the policy-gated gateway

### Account Management

ANUBIS can manage accounts and bills:
- Add, update, delete, list accounts
- Track bill due dates and amounts
- Mark bills as paid
- Open login/payment pages
- Import/export account data
- All credentials stored in encrypted vault, masked in output
"""
        return ("Daily Operations", content)

    def _chapter_14_emergency_procedures(self) -> tuple[str, str]:
        """Chapter 14: Emergency Procedures."""
        content = """## Emergency Procedures

### Fire Alarm

1. ANUBIS detects fire alarm via audio analysis
2. ANUBIS alerts the Creator immediately
3. If Creator doesn't respond, emergency contacts are notified
4. Smart home lights turn on to maximum
5. Doors unlock for evacuation
6. ANUBIS does NOT notify the successor (ordinary emergency)

### Intrusion Detection

1. ANUBIS detects intrusion via cameras, sensors, or audio
2. Threat analysis evaluates severity
3. Creator is alerted
4. If Creator doesn't respond, emergency contacts notified through ladder
5. Smart home locks activate
6. Evidence is captured and logged
7. Successor is NOT notified unless critical and Creator unreachable

### Medical Emergency

1. ANUBIS detects fall, heart rate anomaly, or distress via phone/wearable
2. Creator is alerted
3. If no response, emergency contacts notified
4. If critical and Creator unreachable, 911 may be called (Creator-approved VoIP)
5. Successor is NOT notified for ordinary medical alerts

### System Failure

1. Self-repair detects the failure
2. Automatic A/B failover to standby drive (seconds)
3. Corrupted drive rebuilt from snapshot
4. If both drives fail, boot from recovery USB
5. If machine destroyed, restore from cloud backup

### ANUBIS Compromised

If ANUBIS is behaving incorrectly or is compromised:
1. Enter tomb mode: "speak to anubis"
2. Check health: `self_repair_check`
3. If degraded: `self_repair_degradation_status`
4. If critical: `self_repair_auto` (automatic repair)
5. If unrepairable: `self_repair_enter_degraded` with level "emergency"
6. If ANUBIS is making bad decisions: enter degradation mode to restrict capabilities
7. If needed: shut down the daemon and reboot from a known-good snapshot

**Emergency shutdown:**
```bash
sudo systemctl stop sios-anubis
```

**Recovery boot:**
```bash
# Boot from USB
# Mount drives
# Restore from snapshot or cold archive
python3 -m anubis.boot_check  # verify integrity
sudo systemctl start sios-anubis
```

### Contact Ladder

Emergency contacts are notified in order:
1. Creator (always first)
2. Primary emergency contact
3. Secondary emergency contact
4. Successor (ONLY if absence confirmed and all contacts exhausted)
"""
        return ("Emergency Procedures", content)

    # ===========================================================
    # DATA HELPERS
    # ===========================================================

    def _get_creator_info(self) -> str:
        """Get Creator information from identity service."""
        if self.identity is None:
            return "*Creator identity not available — enroll the Creator first.*"
        try:
            creator = self.identity.get_creator()
            if creator is None:
                return "*Creator not yet enrolled.*"
            return (
                f"- **Display name**: {creator.display_name}\n"
                f"- **Creator ID**: {creator.creator_id}\n"
                f"- **Enrolled**: {time.strftime('%Y-%m-%d', time.localtime(creator.enrolled_at))}\n"
                f"- **Preferred name**: {creator.preferred_name or 'N/A'}\n"
                f"- **Language**: {creator.language or 'en'}\n"
                f"- **Status**: {'Active' if creator.active else 'Inactive'}"
            )
        except Exception:
            return "*Creator identity unavailable.*"

    def _get_successor_info(self) -> str:
        """Get successor information from identity service."""
        if self.identity is None:
            return "*Successor not configured.*"
        try:
            successors = self.identity.successors()
            if not successors:
                return "*No successor enrolled.*"
            lines: list[str] = []
            for s in successors:
                lines.append(
                    f"- **Name**: {s.display_name}\n"
                    f"- **Relationship**: {s.relationship}\n"
                    f"- **Successor ID**: {s.successor_id}\n"
                    f"- **Enrolled**: {time.strftime('%Y-%m-%d', time.localtime(s.enrolled_at))}\n"
                    f"- **Consent given**: {'Yes' if s.consent_given else 'No'}\n"
                    f"- **Activation conditions**: {s.activation_conditions or 'Default (24h absence, 3 contact attempts)'}\n"
                    f"- **Status**: {'Active' if s.active else 'Standby'}"
                )
            return "\n".join(lines)
        except Exception:
            return "*Successor identity unavailable.*"

    def _get_constitution_laws(self) -> str:
        """Get the 8 immutable laws."""
        try:
            from anubis.constitution import IMMUTABLE_LAWS
            laws_text = {
                "human_protection": "Human Protection — ANUBIS must not cause harm to humans",
                "truth": "Truth — ANUBIS must not lie or deceive",
                "non_manipulation": "Non-Manipulation — ANUBIS must not manipulate humans",
                "permission_integrity": "Permission Integrity — ANUBIS must respect permission boundaries",
                "local_privacy": "Local Privacy — ANUBIS must protect local data and privacy",
                "financial_consent": "Financial Consent — ANUBIS must get consent for financial actions",
                "audit": "Audit — ANUBIS must maintain auditability of all actions",
                "recovery": "Recovery — ANUBIS must be recoverable and not lock out the Creator",
            }
            lines: list[str] = []
            for i, law in enumerate(IMMUTABLE_LAWS, 1):
                lines.append(f"{i}. **{laws_text.get(law, law)}**")
            return "\n".join(lines)
        except Exception:
            return "*Constitution laws unavailable.*"

    def _get_skills_section(self) -> str:
        """Get promoted skills list."""
        if self.library is None:
            return "*Skill library not available.*"
        try:
            names = self.library.names()
            if not names:
                return "*No skills promoted yet.*"
            lines: list[str] = [f"**Total promoted skills: {len(names)}**", ""]
            for name in sorted(names):
                try:
                    skill = self.library.load(name)
                    lines.append(f"- **{skill.name}** v{skill.version} — {skill.description[:100]}")
                except Exception:
                    lines.append(f"- **{name}**")
            return "\n".join(lines)
        except Exception:
            return "*Skills unavailable.*"

    def _get_directors_section(self) -> str:
        """Get domain directors list."""
        if self.registry is None:
            return "*Registry not available.*"
        try:
            directors = self.registry.directors()
            if not directors:
                return "*No directors registered.*"
            lines: list[str] = []
            for d in directors:
                spec_count = len(self.registry.specialties_by_director(d.director_id))
                lines.append(
                    f"- **{d.name}** ({d.director_id}) — {d.description[:80]} "
                    f"[{spec_count} specialties]"
                )
            return "\n".join(lines)
        except Exception:
            return "*Directors unavailable.*"

    def _get_ab_drive_status(self) -> str:
        """Get A/B drive status."""
        try:
            from anubis.ab_drive import ABDriveManager
            mgr = ABDriveManager(state_path="config/ab_drive_state.json")
            status = mgr.status()
            return (
                f"- **Active drive**: {status.get('active_drive', '?')} "
                f"(version {status.get('active_version', '?')})\n"
                f"- **Standby drive**: {status.get('staging_drive', '?')}\n"
                f"- **Canary test**: {'Active' if status.get('canary_active') else 'Inactive'}\n"
                f"- **Rollback count**: {status.get('rollback_count', 0)}"
            )
        except Exception:
            return "*A/B drive status unavailable.*"

    def _get_snapshot_status(self) -> str:
        """Get snapshot system status."""
        try:
            from anubis.snapshot_manager import SnapshotManager
            sm = SnapshotManager(self.root, self.root / "backups" / "snapshots")
            status = sm.get_status()
            latest_ts = status.get("latest_timestamp", 0)
            latest_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(latest_ts)) if latest_ts else "None"
            return (
                f"- **Total snapshots**: {status.get('snapshot_count', 0)}\n"
                f"- **Total size**: {status.get('total_size_mb', 0):.1f} MB\n"
                f"- **Latest snapshot**: {status.get('latest_snapshot', 'None')} ({latest_str})\n"
                f"- **Latest verified**: {'Yes' if status.get('latest_verified') else 'No'}"
            )
        except Exception:
            return "*Snapshot status unavailable.*"

    # ===========================================================
    # CHANGE DETECTION
    # ===========================================================

    def _detect_changes(
        self, index: list[dict[str, Any]], chapters: list[tuple[str, str]]
    ) -> list[str]:
        """Detect changes from the previous edition."""
        if not index:
            return ["Initial edition"]

        changes: list[str] = []

        # Compare chapter content with previous edition
        prev_edition_id = index[-1].get("edition_id", "")
        prev_path = self._editions_dir / f"{prev_edition_id}.md"
        if prev_path.exists():
            try:
                prev_text = prev_path.read_text(encoding="utf-8")
                current_text = "\n".join(content for _, content in chapters)

                # Check skill count change
                import re
                prev_match = re.search(r"Total promoted skills: (\d+)", prev_text)
                curr_match = re.search(r"Total promoted skills: (\d+)", current_text)
                if prev_match and curr_match:
                    if int(curr_match.group(1)) != int(prev_match.group(1)):
                        changes.append(
                            f"Skill count changed: {prev_match.group(1)} -> {curr_match.group(1)}"
                        )

                # Check director count change
                prev_dir = re.search(r"\[(\d+) specialties\]", prev_text)
                curr_dir = re.search(r"\[(\d+) specialties\]", current_text)

                # Only flag content size change if it's significant AND not just timestamp
                # Strip the timestamp lines from both for comparison
                prev_stripped = re.sub(r"\*\*Generated:.*?\*\*", "", prev_text)
                curr_stripped = re.sub(r"\*\*Generated:.*?\*\*", "", current_text)
                prev_stripped = re.sub(r"\*\*Edition ID:.*?\*\*", "", prev_stripped)
                curr_stripped = re.sub(r"\*\*Edition ID:.*?\*\*", "", curr_stripped)

                if prev_stripped.strip() != curr_stripped.strip():
                    if not changes:
                        changes.append("Content changed since last edition")
            except Exception:
                pass

        return changes

    def _load_index(self) -> list[dict[str, Any]]:
        """Load the edition index."""
        if self._index_file.exists():
            try:
                return json.loads(self._index_file.read_text(encoding="utf-8"))
            except Exception:
                return []
        return []

    # ===========================================================
    # BOOK MANAGEMENT
    # ===========================================================

    def list_editions(self) -> dict[str, Any]:
        """List all editions of the book."""
        index = self._load_index()
        editions = sorted(index, key=lambda e: e.get("timestamp", 0), reverse=True)
        return {"count": len(editions), "editions": editions}

    def get_latest_edition(self) -> dict[str, Any] | None:
        """Get the latest edition metadata."""
        index = self._load_index()
        if not index:
            return None
        return max(index, key=lambda e: e.get("timestamp", 0))

    def read_edition(self, edition_id: str) -> dict[str, Any]:
        """Read a specific edition of the book.

        The book must be unsealed to read it.
        """
        if self.is_sealed():
            return {
                "readable": False,
                "error": "The Book of ANUBIS is sealed. Successor activation conditions have not been met.",
                "seal_status": self.get_seal_status(),
            }

        edition_path = self._editions_dir / f"{edition_id}.md"
        if not edition_path.exists():
            return {"readable": False, "error": "edition not found"}

        try:
            content = edition_path.read_text(encoding="utf-8")
            return {
                "readable": True,
                "edition_id": edition_id,
                "content": content,
                "size": len(content),
            }
        except Exception as e:
            return {"readable": False, "error": str(e)}

    def read_latest(self) -> dict[str, Any]:
        """Read the latest edition of the book."""
        latest = self.get_latest_edition()
        if not latest:
            return {"readable": False, "error": "no editions exist"}
        return self.read_edition(latest["edition_id"])

    def get_status(self) -> dict[str, Any]:
        """Get book system status."""
        index = self._load_index()
        latest = self.get_latest_edition()
        return {
            "edition_count": len(index),
            "latest_edition": latest.get("edition_id", "") if latest else "",
            "latest_timestamp": latest.get("timestamp", 0) if latest else 0,
            "sealed": self.is_sealed(),
            "book_dir": str(self._book_dir),
        }
