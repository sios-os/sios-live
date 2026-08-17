# SIOS — Sovereign Interactive Operating System

## Project Overview

SIOS is a sovereign Linux operating system built around ANUBIS, a local AI intelligence.
It combines a bootable Ubuntu 24.04 ISO with a Godot 4 spatial desktop, a governed
self-development loop, and a knowledge library of 550+ documents across 14 directors
and 268 specialties.

## Repository Layout

```
sios-live/
├── anubis/              # Core ANUBIS Python package
│   ├── knowledge.py     # Knowledge base, documents, quarantine
│   ├── grounding.py     # Knowledge retrieval (semantic + keyword)
│   ├── semantic.py      # Embedding-based semantic search
│   ├── claims.py        # Atomic claim extraction
│   ├── verification.py  # Claim verification and indexing
│   ├── skills.py        # Skill library (versioned, promoted)
│   ├── loop.py          # Self-development loop (propose→test→review→promote)
│   ├── review.py        # Static code review before promotion
│   ├── sandbox.py       # Hardened sandbox (network blocked, nobody)
│   ├── ledger.py        # Tamper-evident evidence ledger
│   ├── constitution.py  # 8 immutable laws, hazard detection
│   ├── governance.py    # Court, policy engine, capability broker
│   ├── identity.py      # Creator enrollment, successor, vault
│   ├── projects.py      # Multi-file project workspace + executor
│   ├── orchestrator.py  # Multi-agent cross-director queries
│   ├── knowledge_updater.py  # Propose→verify→approve→promote knowledge
│   ├── queue.py         # Persistent mission queue
│   ├── backup.py        # Backup/restore manager
│   ├── voice.py         # TTS/STT abstraction layer
│   ├── docs.py          # Documentation generator
│   ├── memory.py        # Persistent memory (tiered, semantic recall, auditable purge)
│   ├── cloud_sync.py    # iDrive E2 cloud sync (S3-compatible, encrypted, classified)
│   ├── external_gateway.py  # Policy-gated external network gateway (VPN, whitelist)
│   ├── cloud_model.py   # Cloud teacher adapter (Gemini + Groq + local fallback)
│   ├── cloud_training.py  # Lambda GPU cloud testing/training (cost-previewed, governed)
│   ├── prospects.py     # Funding prospects system (grants, projects, bounties)
│   ├── vector_index.py  # In-process vector index (HNSW-like, stdlib only)
│   ├── reranker.py      # Reranker (local BM25 + cloud teacher hybrid)
│   ├── auto_git.py      # Automated git commits with semantic versioning
│   ├── distillation.py  # Knowledge distillation during purge (training pairs)
│   ├── model_merging.py # Model merging (SLERP, TIES, linear — stdlib only)
│   ├── ab_drive.py      # A/B drive automation (canary test, auto-rollback)
│   ├── librarian.py     # Master dependency index (impact analysis)
│   ├── unsloth_adapter.py  # Optional Unsloth training acceleration
│   ├── docker_config.py # Docker microservice configuration generator
│   ├── structured_teacher.py  # Structured JSON outputs from cloud teacher
│   ├── evaluation.py   # Model evaluation harness (benchmark before promotion)
│   ├── training_orchestrator.py  # Full training pipeline (queue→train→eval→A/B)
│   ├── custom_embeddings.py  # Custom embedding model to replace nomic-embed-text
│   ├── cloud_phaseout.py  # Cloud teacher phase-out tracker and router
│   ├── local_inference.py  # Self-hosted inference engine (replaces Ollama)
│   ├── dependency_check.py  # Dependency manifest and self-reliance tracker
│   ├── dream_cycle.py   # Autonomous idle-time self-improvement (dream cycle)
│   ├── scheduler.py     # Autonomous scheduler (heartbeat: purge, dream, missions)
│   ├── proactive.py     # Proactive engagement (inquisitive, recommends, reacts)
│   ├── mixed_model.py   # Progressive weight replacement strategy (6 stages)
│   ├── self_modify.py   # Governed self-modification of own source code
│   ├── knowledge_acquisition.py  # Lawful knowledge acquisition loop
│   ├── knowledge_bootstrap.py  # Convert knowledge docs to training pairs
│   ├── consciousness.py  # Evolving self-concept and reflective thought (Data)
│   ├── system_control.py  # JARVIS-like system management and anticipation
│   ├── observer.py       # All-seeing observer and prediction engine (Machine)
│   ├── research_engine.py  # Scientific/engineering advancement engine
│   ├── sensory.py       # Always-on ears (audio), eyes (screen), voice (TTS)
│   ├── perception.py    # Voice ID, emotion analysis, face/object recognition
│   ├── contacts.py      # Emergency contacts + successor notification policy
│   ├── messaging.py     # Signal CLI + email-to-SMS for emergency alerts
│   ├── network_ops.py   # Full network operator (discovery, control, security)
│   ├── remote_monitor.py # Phone/wearable monitoring while Creator is away
│   ├── threat_analysis.py # Unified threat detection across all domains
│   ├── cameras.py       # Camera system (home, dashcam, body cam, public)
│   ├── api_server.py    # REST API server (HTTP backbone for all integrations)
│   ├── smarthome.py     # Smart home control (lights, locks, thermostat, appliances)
│   ├── weather.py       # Weather monitoring (forecasts, severe weather alerts)
│   ├── calendar.py      # Calendar & scheduling (appointments, reminders)
│   ├── email_system.py  # Email integration (IMAP/SMTP, phishing detection)
│   ├── dashboard.py     # Web dashboard (browser control panel)
│   ├── voip.py          # VoIP calling (SIP/Twilio, emergency calls)
│   ├── news_feeds.py    # News & research feeds (RSS, HN, arXiv)
│   ├── finance.py       # Financial tracking (expenses, bills, fraud detection)
│   ├── packages.py      # Package & delivery tracking
│   ├── phone_protocol.py # Phone companion app protocol
│   ├── music.py         # Music & media control (MPD, VLC, mood-based)
│   ├── notifications.py # Desktop notifications (system tray, alerts)
│   ├── iot.py           # IoT integrations (OBD-II, air quality, energy, 3D printer, drone, garden, smartwatch, visitor log)
│   ├── advanced.py      # Advanced modules (911 calling, multi-language, AR glasses, satellite, blockchain, ANUBIS-to-ANUBIS)
│   ├── model.py         # Ollama adapter
│   └── knowledge_content/  # Generated knowledge documents
├── tools/               # Scripts and daemon
│   ├── anubis_daemon.py # Unix socket daemon (all features exposed here)
│   ├── build_semantic_index.py
│   ├── exercise_court.py
│   ├── setup_policy.py
│   ├── security_audit.py
│   └── ...              # Test and utility scripts
├── desktop/             # Godot 4 project (spatial desktop)
│   ├── project.godot
│   ├── export_presets.cfg
│   └── scripts/
│       ├── RoomBuilder.gd       # Procedural room construction
│       ├── SanctumRoom.gd       # Knowledge browser room
│       └── TombHall.gd          # Tomb hall controller
├── session/             # LightDM, Plymouth, GRUB, systemd services
├── iso/                 # ISO build script
│   └── build-sios-iso.sh
├── knowledge/           # Knowledge library (550+ docs, embeddings cache)
├── skills/              # Promoted skills (102+)
├── evidence/            # Evidence ledger, training corpus
├── memory/              # Persistent memory (facts, conversation, missions)
├── identity/            # Creator identity vault (encrypted)
├── registry/            # Director and specialty registry
├── court/               # Court reviews and verdicts
├── policy/              # Policy engine config
├── capabilities/        # Capability broker
├── tests/               # Python test suite (1606 tests)
├── docs/                # Generated documentation
└── backups/             # System backups
```

## Build Commands

### Test Suite
```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
Expected: 1606 tests, OK (2 pre-existing Unix-only errors on Windows)

### Semantic Index
```bash
python3 tools/build_semantic_index.py
```
Embeds all knowledge documents using nomic-embed-text (768-dim).

### ISO Build
```bash
bash iso/build-sios-iso.sh
```
Output: `sios-ubuntu-24.04.iso` (~3.3 GB)
Requires: debootstrap, xorriso, squashfs-tools, grub-pc-bin, grub-efi-amd64-bin

### Daemon
```bash
python3 tools/anubis_daemon.py
```
Socket: `/tmp/anubis.sock`

### Security Audit
```bash
python3 tools/security_audit.py
```

### Backup
```bash
python3 -c "from anubis.backup import BackupManager; from pathlib import Path; BackupManager(Path('.'), Path('backups')).create_backup(label='manual')"
```

## Key Configuration

- **Active model**: `qwen2.5-coder:7b`
- **Probation model**: `qwen2.5-coder:14b` (30-day Court probation)
- **Embedding model**: `nomic-embed-text` (768-dim)
- **Ubuntu base**: 24.04
- **Godot**: 4.3 stable
- **Creator**: Storm (ID: `4670b4cf48fed7c5`)
- **Successor**: Ethan Pace (ID: `144f7f638118138b`)

## Daemon Socket Protocol

Send JSON commands over `/tmp/anubis.sock`:

```python
import json, socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect("/tmp/anubis.sock")
s.send(json.dumps({"cmd": "status"}).encode())
# Read response until connection closes
```

### Key Commands

| Command | Description |
|---------|-------------|
| `status` | Daemon health, model, sandbox, skill count |
| `chat` | Talk to ANUBIS (grounded, cited responses) |
| `skills` | List all promoted skills |
| `mission` | Start a self-development mission |
| `queue_add_batch` | Add multiple missions to queue |
| `queue_process` | Process N pending missions |
| `orchestrate` | Cross-director query |
| `knowledge_propose` | Propose new knowledge document |
| `knowledge_ground` | Ground a query in knowledge |
| `backup_create` | Create a system backup |
| `voice_speak` | Text-to-speech |
| `docs_generate` | Generate documentation |
| `court_submit` | Submit artifact for Court review |
| `identity_stats` | Creator and successor info |
| `memory_stats` | Memory statistics — entry counts, tier sizes, access patterns |
| `memory_recall` | Semantic recall of past context (query-based) |
| `memory_purge` | Archive old entries to long-term tier (auditable) |
| `memory_purge_log` | View the purge audit log |
| `cloud_sync_status` | Cloud sync configuration status (no secrets) |
| `cloud_sync` | Sync a directory to iDrive E2 (Creator-approved) |
| `cloud_sync_upload` | Upload a single file to iDrive E2 (Creator-approved) |
| `cloud_sync_download` | Download a file from iDrive E2 (Creator-approved) |
| `cloud_sync_list` | List objects in iDrive E2 bucket |
| `gateway_status` | External gateway status (policy, rate limits) |
| `gateway_fetch` | Fetch URL through gateway (Creator-approved, whitelisted) |
| `gateway_search` | Web search through gateway (Creator-approved) |
| `gateway_add_domain` | Add domain to gateway whitelist |
| `gateway_remove_domain` | Remove domain from gateway whitelist |
| `cloud_model_status` | Cloud teacher status (providers, no secrets) |
| `cloud_model_chat` | Chat with cloud teacher (Gemini→Groq→local, privacy-gated) |
| `lambda_status` | Lambda GPU cloud status (GPUs, jobs, no secrets) |
| `lambda_cost_preview` | Cost preview for a Lambda job (no submission) |
| `lambda_submit` | Submit job to Lambda (Creator-approved, training needs hash) |
| `lambda_job_status` | Check status of a Lambda job |
| `lambda_list_jobs` | List all Lambda jobs |
| `lambda_cancel` | Cancel a Lambda job |
| `prospects_status` | Prospects system status (sources, stats) |
| `prospects_search` | Search for funding opportunities (gateway, Creator-approved) |
| `prospects_create` | Create a prospect proposal (stored as pending) |
| `prospects_evaluate` | Evaluate prospect legitimacy and feasibility |
| `prospects_approve` | Approve a prospect (Creator action) |
| `prospects_reject` | Reject a prospect (Creator action) |
| `prospects_list_pending` | List pending prospects for review |
| `prospects_list_approved` | List approved prospects |
| `prospects_stats` | Prospect statistics (counts, averages, totals) |
| **Perception & Security** | |
| `perception_status` | Perception system status (voice ID, emotion, faces, objects) |
| `perception_analyze_audio` | Analyze audio file for speaker ID and emotion |
| `perception_analyze_image` | Analyze image for faces and objects |
| `contacts_status` | Emergency contacts status |
| `contacts_add` | Add emergency contact |
| `contacts_list` | List emergency contacts |
| `contacts_notify_emergency` | Send emergency notification (Creator-approved) |
| `messaging_status` | Signal/email messaging status |
| `messaging_send` | Send message via Signal (Creator-approved) |
| `network_ops_status` | Network operations status |
| `network_ops_scan` | Scan network for devices (Creator-approved) |
| `network_ops_devices` | List known network devices |
| `remote_monitor_status` | Remote monitor status |
| `remote_monitor_update` | Receive phone/wearable telemetry |
| `threat_analysis_status` | Threat analysis status |
| `threat_analysis_analyze` | Analyze perception data for threats |
| `threat_analysis_active` | List active threats |
| `cameras_status` | Camera system status |
| `cameras_add` | Add camera source |
| `cameras_list` | List all cameras |
| `cameras_capture` | Capture frame from camera |
| `cameras_events` | Get camera events |
| `cameras_start_monitoring` | Start camera monitoring |
| `cameras_stop_monitoring` | Stop camera monitoring |
| `observer_status` | Observer engine status |
| `observer_observations` | Get recent observations |
| `observer_predictions` | Get predictions |
| `consciousness_status` | Consciousness engine status (needs model) |
| `consciousness_reflect` | Generate reflection (needs model) |
| `consciousness_self_concept` | Get ANUBIS self-concept |
| `proactive_status` | Proactive engagement status (needs model) |
| `proactive_engage` | Engage proactively with observation |
| `sensory_status` | Sensory system status (needs model) |
| `sensory_listen` | Listen for audio input |
| `sensory_set_mode` | Set sensory mode (ambient/wake_word/conversation/privacy) |
| `research_status` | Research engine status (needs model) |
| `research_identify_gaps` | Identify knowledge gaps |
| `research_propose` | Propose research hypothesis |
| **Tier 1 Integrations** | |
| `api_server_start` | Start REST API server |
| `api_server_stop` | Stop REST API server |
| `api_server_status` | API server status |
| `smarthome_status` | Smart home status |
| `smarthome_add_device` | Add smart home device |
| `smarthome_control` | Control device (turn_on/off, set_brightness, etc.) |
| `smarthome_devices` | List smart home devices |
| `weather_status` | Weather monitor status |
| `weather_forecast` | Get weather forecast |
| `weather_alerts` | Get severe weather alerts |
| `calendar_status` | Calendar status |
| `calendar_add_event` | Add calendar event |
| `calendar_today` | Get today's events |
| `calendar_upcoming` | Get upcoming events |
| `email_status` | Email system status |
| `email_check` | Fetch inbox |
| `email_send` | Send email (Creator-approved) |
| `dashboard_status` | Dashboard status |
| **Tier 2 Integrations** | |
| `voip_status` | VoIP status |
| `voip_call` | Make phone call (Creator-approved) |
| `voip_end_call` | End active call |
| `voip_calls` | Get call history |
| `news_status` | News feeds status |
| `news_fetch` | Fetch news from feeds |
| `news_items` | Get news items |
| `news_briefing` | Get daily news briefing |
| `finance_status` | Finance tracker status |
| `finance_add_transaction` | Add transaction |
| `finance_add_bill` | Add recurring bill |
| `finance_upcoming_bills` | Get upcoming bills |
| `finance_spending` | Get spending by category |
| `packages_status` | Package tracker status |
| `packages_add` | Add package to track |
| `packages_update` | Update package status |
| `packages_active` | Get active (undelivered) packages |
| `phone_register` | Register phone device |
| `phone_status` | Phone protocol status |
| `phone_notify` | Send notification to phone |
| `phone_devices` | List registered phone devices |
| `music_status` | Music controller status |
| `music_play` | Play music |
| `music_pause` | Pause playback |
| `music_stop` | Stop playback |
| `music_set_mood` | Set mood-based playback |
| `music_set_volume` | Set volume |
| `music_playlists` | List playlists |
| `notifications_status` | Notification system status |
| `notifications_notify` | Send notification |
| `notifications_alert` | Send urgent alert |
| `notifications_history` | Get notification history |
| **Tier 3 Integrations (IoT)** | |
| `obd_status` | OBD-II vehicle diagnostics status |
| `obd_read` | Read vehicle data |
| `air_quality_status` | Air quality monitor status |
| `air_quality_record` | Record air quality reading |
| `energy_status` | Energy monitor status |
| `energy_record` | Record energy reading |
| `printer3d_status` | 3D printer status |
| `printer3d_submit` | Submit print job |
| `printer3d_jobs` | List print jobs |
| `drone_status` | Drone status |
| `drone_takeoff` | Take off (Creator-approved) |
| `drone_land` | Land drone |
| `drone_rtl` | Return to launch |
| `garden_status` | Garden monitor status |
| `garden_add_plant` | Add plant to monitor |
| `garden_record` | Record plant sensor reading |
| `garden_recommendations` | Get plant care recommendations |
| `smartwatch_status` | Smart watch status |
| `smartwatch_data` | Receive watch health data |
| `visitors_status` | Visitor logger status |
| `visitors_log_arrival` | Log visitor arrival |
| `visitors_log_departure` | Log visitor departure |
| `visitors_active` | Get active visitors |
| `visitors_logs` | Get visitor logs |
| **Tier 4 Integrations (Advanced)** | |
| `emergency_services_status` | Emergency services status |
| `emergency_services_request` | Request 911 call (requires approval) |
| `emergency_services_calls` | List emergency call records |
| `multilang_status` | Multi-language status |
| `multilang_detect` | Detect language of text |
| `multilang_translate` | Translate phrase |
| `multilang_languages` | List supported languages |
| `ar_status` | AR glasses status |
| `ar_process_frame` | Process AR glasses frame |
| `satellite_status` | Satellite analyzer status |
| `satellite_fetch` | Fetch satellite image (Creator-approved) |
| `blockchain_status` | Blockchain evidence status |
| `blockchain_anchor` | Anchor evidence on blockchain |
| `blockchain_verify` | Verify blockchain anchor |
| `blockchain_anchors` | List blockchain anchors |
| `anubis_protocol_status` | ANUBIS-to-ANUBIS protocol status |
| `anubis_protocol_add_peer` | Add peer ANUBIS instance |
| `anubis_protocol_peers` | List peers |
| `anubis_protocol_send` | Send message to peer |
| `anubis_protocol_check_peer` | Check peer status |
| **Unified** | |
| `systems_status` | Status of ALL subsystems in one call |

## Testing

All changes should pass the 1606-test suite:
```bash
python3 -m unittest discover -s tests -p 'test_*.py' -q
```

## Important Notes

- The sandbox blocks network and drops to `nobody`.
- The Court requires exact artifact-hash binding for Creator approval.
- The evidence ledger is tamper-evident (SHA-256 chain).
- Knowledge documents go through quarantine before promotion.
- The Creator passphrase is sensitive — never commit or log it.
- The ISO build uses root/chroot — inspect `/tmp/sios-iso-build` before restarting.


