# SIOS User Guide

## What is SIOS?

SIOS (Sovereign Interactive Operating System) is a bootable Linux operating system built around ANUBIS — a local AI intelligence that can write code, learn from mistakes, and govern its own development.

Everything runs locally. No network required after boot. No cloud. No telemetry.

## Booting SIOS

### From USB
1. Flash the ISO to a USB drive:
   ```
   dd if=sios-ubuntu-24.04.iso of=/dev/sdX bs=4M status=progress
   ```
2. Boot from the USB drive.
3. GRUB will show three options:
   - **SIOS — Sovereign Interactive Operating System** (default)
   - **SIOS — Safe Mode (no splash)**
   - **SIOS — Recovery Console**
4. Select the default option or wait 5 seconds for auto-boot.

### In a VM
```
qemu-system-x86_64 -m 4096 -cdrom sios-ubuntu-24.04.iso
```

## First Boot

After boot, you'll see:
1. **Plymouth boot splash** with the SIOS brand.
2. **LightDM login screen** — default credentials: `sios / sios`
3. **SIOS spatial desktop** — a 3D environment with rooms.

## The Spatial Desktop

The desktop is a Godot 4 3D environment organized into rooms:

### Open Rooms (no authentication required)
| Room | Purpose |
|------|---------|
| **Workspace** | Write and test code with ANUBIS |
| **Command Chamber** | System oversight and control |
| **Observatory** | External data and observation |
| **Sanctum** | Identity, knowledge browser, personalization |
| **Forge** | Build, test, package, and sign artifacts |
| **Mission Queue** | View and manage the autonomous work queue |
| **The Court** | Governance and constitutional review |
| **Project Workshop** | Multi-file project builder |
| **Knowledge Archive** | Browse 800+ documents across 14 directors |

### Creator-Only Rooms
| Room | Purpose |
|------|---------|
| **Tomb Entrance** | Gateway to the inner halls |
| **Hall of Genesis** | ANUBIS's first moments |
| **Hall of Evolution** | Skill version history |
| **Hall of Architects** | Constitutional framework |
| **Hall of Sovereignty** | Governance and policy |
| **Hall of Memory** | Evidence ledger |
| **Hall of Creation** | Mission archive |
| **The Throne** | Creator's seat of authority |

## Talking to ANUBIS

Press `T` or click the DEMON panel to open the chat interface.

ANUBIS responds with:
- **Grounded answers** — every response is grounded in the knowledge library
- **Citations** — sources are listed with each response
- **Memory** — he remembers past conversations
- **Skill awareness** — he knows what skills he has

Example conversations:
- "Who are you?"
- "What is object-oriented programming?"
- "Write a function that reverses a string"
- "Search for ancient Egyptian burial practices"
- "What skills do you have?"

## ANUBIS's Capabilities

### Self-Development Loop
ANUBIS can write code, test it in a sandbox, review it, and promote it:
1. **Propose** — ANUBIS generates code for a task
2. **Test** — code runs in a hardened sandbox (network blocked, nobody user)
3. **Review** — static analysis checks for hazards
4. **Gate** — constitutional governance checks
5. **Promote** — if all checks pass, the skill is promoted to the library

### Mission Queue
Queue tasks for ANUBIS to work on autonomously:
- Add individual missions or batches
- ANUBIS processes them one by one
- Each mission goes through the full self-development loop
- Results are tracked (promoted, failed, skipped)

### Project Workspace
Build multi-file projects that chain skills together:
- Define a project with multiple steps
- Each step reuses an existing skill or creates a new one
- ANUBIS integrates all steps into a single program with tests

### Knowledge Library
- **804 documents** across 14 directors and 268 specialties
- **15,677+ claims** extracted and verified
- **Semantic search** using nomic-embed-text (768-dim embeddings)
- **Knowledge updater** — propose, verify, approve, promote new documents

### Governance
- **8 immutable laws** (constitution)
- **Court** — reviews artifacts before promotion
- **Policy engine** — spending limits, prohibited categories
- **Evidence ledger** — tamper-evident SHA-256 chain
- **Creator approval** — required for all promotions

## Creator Identity

The Creator is Storm. The successor is Ethan Pace.

### Vault
The identity vault stores encrypted credentials:
- Unlock with the Creator passphrase
- Contains 9 encrypted values
- Passphrase can be rotated

### Recovery
If the Creator is unavailable for 90 days or verifies death:
1. Recovery contacts verify identity in person
2. Successor (Ethan Pace) takes control
3. Encrypted backup can be restored

## Backups

Create backups from the daemon or desktop:
```
python3 -c "from anubis.backup import BackupManager; from pathlib import Path; BackupManager(Path('.'), Path('backups')).create_backup(label='manual')"
```

Backups include: identity, knowledge, skills, memory, evidence, registry, policy, court, capabilities, projects.

## Voice I/O

ANUBIS supports voice through the daemon:
- **Text-to-speech** (espeak-ng) — ANUBIS can speak responses
- **Speech-to-text** (whisper) — speak to ANUBIS (requires whisper installed)

Toggle voice from the Sanctum room or daemon commands.

## Security

- **Sandbox**: network blocked, filesystem masked, runs as nobody
- **Constitution**: 8 immutable laws, hazard detection
- **Court**: all promotions require review and Creator approval
- **Evidence ledger**: tamper-evident, SHA-256 chained
- **No network**: everything runs locally
- **Encrypted vault**: credentials encrypted at rest

## Troubleshooting

### ANUBIS daemon not connected
Start the daemon:
```
python3 tools/anubis_daemon.py
```

### Model not available
Ensure Ollama is running and the model is pulled:
```
ollama pull qwen2.5-coder:7b
```

### Desktop won't start
Check if Godot is installed:
```
godot --version
```

### Tests
Run the full test suite:
```
python3 -m unittest discover -s tests -p 'test_*.py'
```
