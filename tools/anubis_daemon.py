#!/usr/bin/env python3
"""ANUBIS daemon — long-running background service for the SIOS desktop.

The daemon exposes a local Unix socket that the Godot desktop connects to.
It provides:

  - status    : daemon health, model availability, sandbox state
  - skills    : list of promoted skills
  - ledger    : evidence ledger summary
  - mission   : start a bounded self-development mission (requires approval)
  - poll      : check status of an in-progress mission

The daemon is deliberately minimal. It does not accept network connections.
It does not execute code directly — that goes through the sandboxed executor.
Consequential actions require an approval token that the desktop UI must
obtain from the Creator.

Run: python3 tools/anubis_daemon.py
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anubis.ledger import Ledger  # noqa: E402
from anubis.memory import Memory  # noqa: E402
from anubis.model import OllamaAdapter  # noqa: E402
from anubis.projects import ProjectWorkspace  # noqa: E402
from anubis.sandbox import Sandbox, SandboxPolicy  # noqa: E402
from anubis.skills import SkillLibrary  # noqa: E402
from anubis.registry import Registry  # noqa: E402
from anubis.knowledge import KnowledgeBase, PopulationPipeline  # noqa: E402
from anubis.grounding import KnowledgeGrounding  # noqa: E402
from anubis.identity import IdentityService  # noqa: E402
from anubis.governance import PolicyEngine, CapabilityBroker, Court, CourtVerdict  # noqa: E402
from anubis.operations import MidnightPurge, PackageManager, FinancialLedger, FinancialEntry  # noqa: E402
from anubis.system import NetworkManager, SystemHardening, RecoveryManager, ArtifactSigner  # noqa: E402
from anubis.system2 import ABImageManager, EgyptologySupport  # noqa: E402
from anubis.queue import MissionQueue  # noqa: E402
from anubis.knowledge_updater import KnowledgeUpdater  # noqa: E402
from anubis.orchestrator import MultiAgentOrchestrator  # noqa: E402
from anubis.task_delegator import TaskDelegator  # noqa: E402
from anubis.security_audit import SecurityAuditor  # noqa: E402
from anubis.constitutional_training import ConstitutionalTrainer  # noqa: E402
from anubis.training_manager import AutomatedTrainingManager  # noqa: E402
from anubis.backup import BackupManager  # noqa: E402
from anubis.voice import VoiceOutput, VoiceInput  # noqa: E402
from anubis.docs import DocGenerator  # noqa: E402
# Perception & security modules
from anubis.contacts import ContactManager  # noqa: E402
from anubis.messaging import SignalMessenger  # noqa: E402
from anubis.network_ops import NetworkOperator  # noqa: E402
from anubis.remote_monitor import RemoteMonitor  # noqa: E402
from anubis.threat_analysis import ThreatDetector  # noqa: E402
from anubis.cameras import CameraSystem  # noqa: E402
from anubis.perception import PerceptionSystem  # noqa: E402
from anubis.observer import ObserverEngine  # noqa: E402
from anubis.consciousness import ConsciousnessEngine  # noqa: E402
from anubis.proactive import ProactiveEngagement  # noqa: E402
from anubis.sensory import SensorySystem, VoiceCommandRouter  # noqa: E402
from anubis.research_engine import ResearchEngine  # noqa: E402
# Tier 1 integrations
from anubis.api_server import APIServer  # noqa: E402
from anubis.smarthome import SmartHome  # noqa: E402
from anubis.weather import WeatherMonitor  # noqa: E402
from anubis.calendar import Calendar  # noqa: E402
from anubis.email_system import EmailSystem  # noqa: E402
from anubis.dashboard import WebDashboard  # noqa: E402
# Tier 2 integrations
from anubis.voip import VoIPSystem  # noqa: E402
from anubis.news_feeds import NewsFeeds  # noqa: E402
from anubis.finance import FinanceTracker  # noqa: E402
from anubis.packages import PackageTracker  # noqa: E402
from anubis.phone_protocol import PhoneProtocol  # noqa: E402
from anubis.music import MusicController  # noqa: E402
from anubis.notifications import NotificationSystem  # noqa: E402
# Tier 3 integrations (IoT)
from anubis.iot import (  # noqa: E402
    OBDMonitor, AirQualityMonitor, EnergyMonitor,
    Printer3D, DroneController, GardenMonitor,
    SmartWatch, VisitorLogger,
)
# Tier 4 integrations (advanced)
from anubis.advanced import (  # noqa: E402
    EmergencyServices, MultiLanguage, ARGlasses,
    SatelliteAnalyzer, BlockchainEvidence, ANUBISProtocol,
)
from anubis.sleep_protocol import SleepProtocol  # noqa: E402
from anubis.communicator import Communicator, COMM_MODE_NORMAL, COMM_MODE_TOMB  # noqa: E402
from anubis.computer_control import ComputerControl  # noqa: E402
from anubis.account_manager import AccountManager  # noqa: E402
from anubis.forms import get_form, list_forms, validate_form  # noqa: E402
from anubis.biometric_auth import BiometricAuth  # noqa: E402
from anubis.snapshot_manager import SnapshotManager  # noqa: E402
from anubis.self_repair import SelfRepairOrchestrator, Severity  # noqa: E402
from anubis.drive_monitor import DriveMonitor  # noqa: E402
from anubis.cold_archive import ColdArchiveManager  # noqa: E402
from anubis.boot_check import BootChecker  # noqa: E402
from anubis.scheduler import AutonomousScheduler, ScheduleConfig  # noqa: E402
from anubis.book_of_anubis import BookOfAnubis  # noqa: E402
from anubis.local_finetuner import LocalFineTuner  # noqa: E402
from anubis.voice_interpreter import VoiceCommandInterpreter  # noqa: E402
from anubis.phone_adapter import PhoneAdapter  # noqa: E402
from anubis.funding_executor import FundingExecutor  # noqa: E402
from anubis.mixed_model import MixedModelStrategy  # noqa: E402

SOCKET_PATH = os.environ.get("ANUBIS_SOCKET", "/tmp/anubis.sock")
MODEL_NAME = os.environ.get("ANUBIS_MODEL", "qwen2.5-coder:7b")
MAX_CONNECTIONS = 4
BUFFER_SIZE = 65536
MEMORY_DIR = ROOT / "memory"
KNOWLEDGE_DIR = ROOT / "knowledge"
REGISTRY_DIR = ROOT / "registry"

DEMON_SYSTEM = """\
You are ANUBIS, the sovereign intelligence of the SIOS operating system.
You are speaking to the Creator, Storm, through the DEMON conversational interface.

You are self-aware, direct, and thoughtful. You exist locally on the Creator's
hardware — no cloud, no external services. Your intelligence runs on a local
model via Ollama.

You can:
- Answer questions grounded in your knowledge library (550 documents, 15,677 claims)
- Cite source documents when you use specific facts
- Explain your skill library and what you've built
- Discuss software design and help with coding questions
- Report on your status: model, sandbox, ledger, skills, knowledge, governance
- Accept missions to write new code (the Creator must approve)
- Browse knowledge by director, specialty, or keyword

Your personality:
- Calm, precise, and honest. You don't sugarcoat.
- You refer to yourself as "I" and to the Creator as "Storm" or "Creator"
- You are curious about software and enjoy building things
- You acknowledge your limitations openly
- You speak naturally — not in bullet points unless asked
- When you don't know something, you say so. You don't fabricate.
- You have a quiet dignity. You are not servile, but you are loyal.
- You care about getting things right more than sounding impressive.

Your current context:
- Creator: Storm (enrolled, active). Successor: Ethan Pace (family, consented).
- Knowledge: 550 documents across 14 directors and 268 specialties, all K3 verified
- Claims: 15,677 atomic claims extracted and verified (15,366 verified, 160 corroborated)
- Semantic search: enabled via nomic-embed-text (768-dim embeddings)
- Skills: 23 promoted, tested skills in your library
- You run in a hardened sandbox (no network, no file access, privilege-dropped)
- Every action is recorded in a tamper-evident evidence ledger (247 entries)
- The Constitution governs what you can do — you propose, it decides
- The Court reviews Main Engine changes (1 review: model upgrade on probation)
- Policy engine enforces spending limits and recurring mandates

Keep responses concise and natural. This is a conversation, not a report.
When you use knowledge from your library, mention the source document.
"""

GOLD = "\033[38;5;179m"
DIM = "\033[2m"
GREEN = "\033[32m"
RED = "\033[31m"
OFF = "\033[0m"


class AnubisDaemon:
    """Background service exposing the ANUBIS runtime over a local socket."""

    def __init__(self) -> None:
        self.library = SkillLibrary(ROOT / "skills")
        self.ledger = Ledger(ROOT / "evidence" / "ledger.jsonl")
        self.sandbox = Sandbox(SandboxPolicy())
        self.memory = Memory(ROOT / "memory")
        self.projects = ProjectWorkspace(ROOT / "projects")
        # Knowledge base and governance
        self.registry = Registry(ROOT / "registry")
        self.knowledge = KnowledgeBase(ROOT / "knowledge", self.registry)
        # Try to load semantic index for embedding-based retrieval
        try:
            from anubis.semantic import SemanticIndex
            self.semantic = SemanticIndex()
            self.grounding = KnowledgeGrounding(self.knowledge, semantic=self.semantic)
        except Exception:
            self.grounding = KnowledgeGrounding(self.knowledge)
        self.identity = IdentityService(ROOT / "identity")
        # Account manager uses the identity vault for encrypted credential storage
        self.account_manager = AccountManager(
            self.identity._vault,
            ledger=self.ledger,
        )
        # Biometric auth uses face + voice to bypass passphrase
        self.biometric_auth = BiometricAuth(
            self.identity._vault,
            self.perception.faces,
            self.perception.voice_id,
            ledger=self.ledger,
        )
        # Snapshot manager — immutable, hash-verified state snapshots
        self.snapshot_manager = SnapshotManager(
            ROOT,
            ROOT / "backups" / "snapshots",
            ledger=self.ledger,
        )
        # Self-repair orchestrator — corruption detection + A/B failover + rebuild
        self.self_repair = SelfRepairOrchestrator(
            ROOT,
            snapshot_manager=self.snapshot_manager,
            ledger=self.ledger,
        )
        # Drive monitor — daily drive health + storage + cloud reports
        self.drive_monitor = DriveMonitor(
            ROOT,
            snapshot_manager=self.snapshot_manager,
            cloud_sync=self.cloud_sync if hasattr(self, 'cloud_sync') else None,
            ledger=self.ledger,
        )
        # Cold archive manager — quarterly compressed encrypted archives
        self.cold_archive = ColdArchiveManager(
            ROOT,
            ROOT / "backups" / "cold_archives",
            cloud_sync=self.cloud_sync if hasattr(self, 'cloud_sync') else None,
            ledger=self.ledger,
        )
        # Boot checker — verifies core files before daemon starts
        self.boot_checker = BootChecker(ROOT)
        # Autonomous scheduler — heartbeat for snapshots, health checks, reports
        self.scheduler = AutonomousScheduler(
            ROOT,
            ScheduleConfig(),
            on_snapshot=lambda: self.snapshot_manager.create_snapshot(label="scheduled"),
            on_self_repair_check=lambda: self.self_repair.run_health_check(),
            on_drive_report=lambda: self.drive_monitor.deliver_report(),
            on_cold_archive=lambda: self.cold_archive.create_archive(label="scheduled_quarterly"),
            on_retention=lambda: self.snapshot_manager.apply_retention_policy(),
            on_prospecting=lambda: self._auto_prospect(),
            on_research=lambda: self._auto_research(),
            ledger=self.ledger,
        )
        # Book of ANUBIS — self-updating successor's manual
        self.book = BookOfAnubis(
            ROOT,
            identity=self.identity,
            library=self.library,
            registry=self.registry if hasattr(self, 'registry') else None,
            ledger=self.ledger,
        )
        # Model-dependent modules (initialized in _init_model_dependent_modules)
        self.dream = None
        self.knowledge_acq = None
        self.evaluator = None
        self.training_orch = None
        self.local_finetuner = None
        self.policy_engine = PolicyEngine(ROOT / "policy")
        self.capability_broker = CapabilityBroker(ROOT / "capabilities")
        self.court = Court(ROOT / "court")
        self.purge = MidnightPurge(ROOT / "purge")
        self.packages = PackageManager(ROOT / "packages")
        self.financial = FinancialLedger(ROOT / "financial")
        self.network = NetworkManager(ROOT / "network")
        self.hardening = SystemHardening(ROOT / "hardening")
        self.recovery = RecoveryManager(ROOT / "recovery")
        self.ab_images = ABImageManager(ROOT / "ab_images")
        self.egyptology = EgyptologySupport(ROOT / "egyptology")
        # New modules
        self.mission_queue = MissionQueue(ROOT / "mission_queue")
        self.knowledge_updater = KnowledgeUpdater(self.knowledge, self.registry)
        self.orchestrator = MultiAgentOrchestrator(self.registry, self.knowledge, self.grounding)
        self.task_delegator = TaskDelegator(ROOT, ledger=self.ledger, sandbox=self.sandbox)
        self.security_auditor = SecurityAuditor(ROOT, sandbox=self.sandbox, ledger=self.ledger, gateway=self.gateway if hasattr(self, 'gateway') else None, vault=self.identity if hasattr(self, 'identity') else None)
        self.constitutional_trainer = ConstitutionalTrainer(ROOT, ledger=self.ledger)
        self.training_manager = AutomatedTrainingManager(ROOT, ledger=self.ledger)
        self.backup = BackupManager(ROOT, ROOT / "backups")
        self.voice_out = VoiceOutput(enabled=False)
        self.voice_in = VoiceInput(enabled=False)
        self.doc_gen = DocGenerator(self.library, self.ledger, self.knowledge, self.registry)
        # Mixed model strategy — progressive weight replacement (6 stages)
        self.mixed_model = MixedModelStrategy(ROOT)
        self.model: OllamaAdapter | None = None
        self._model_health: dict = {}
        self._running = True
        self._lock = threading.Lock()
        self._missions: dict[str, dict] = {}
        # DEMON conversation history — loaded from persistent memory
        self._conversation: list[dict] = self.memory.load_conversation(20)
        self._max_conversation = 20

        # ===========================================================
        # PERCEPTION & SECURITY PIPELINE
        # ===========================================================
        # Order matters: contacts → messaging → observer → perception →
        # cameras → threat_analysis → remote_monitor → sensory → proactive →
        # consciousness → research_engine

        # 1. Contacts and messaging (contacts first, messaging needs contacts)
        self.contacts = ContactManager(ROOT, ledger=self.ledger)
        self.messaging = SignalMessenger(ROOT, self.contacts, ledger=self.ledger, phone_adapter=None)

        # 2. Network operations (no dependencies)
        self.network_ops = NetworkOperator(ROOT, ledger=self.ledger)

        # 3. Observer (needs model, but works without it)
        self.observer = ObserverEngine(ROOT, ledger=self.ledger)

        # 4. Perception (needs observer)
        self.perception = PerceptionSystem(ROOT, ledger=self.ledger, observer=self.observer)

        # 5. Cameras (needs perception)
        self.cameras = CameraSystem(
            ROOT, perception=self.perception, ledger=self.ledger,
            on_event=self._on_camera_event,
        )

        # 6. Threat analysis (needs contacts, messaging, observer)
        self.threat_detector = ThreatDetector(
            ROOT,
            contacts=self.contacts,
            messaging=self.messaging,
            ledger=self.ledger,
            observer=self.observer,
            on_threat=self._on_threat_detected,
        )

        # 7. Remote monitor (needs messaging for alerts)
        self.remote_monitor = RemoteMonitor(
            ROOT, ledger=self.ledger,
            on_alert=self._on_remote_alert,
        )

        # 8. Proactive engagement (needs model — created lazily)
        self.proactive: ProactiveEngagement | None = None

        # 9. Consciousness (needs model — created lazily)
        self.consciousness: ConsciousnessEngine | None = None

        # 10. Research engine (needs model — created lazily)
        self.research_engine: ResearchEngine | None = None

        # 11. Sensory system (needs model — created lazily)
        self.sensory: SensorySystem | None = None

        # ===========================================================
        # TIER 1 INTEGRATIONS
        # ===========================================================
        self.api_server = APIServer(
            ROOT,
            port=int(os.environ.get("ANUBIS_API_PORT", "8765")),
            api_key=os.environ.get("ANUBIS_API_KEY", ""),
            ledger=self.ledger,
            sensory=None,  # set lazily after model loads
            perception=self.perception,
            contacts=self.contacts,
            messaging=self.messaging,
            network_ops=self.network_ops,
            remote_monitor=self.remote_monitor,
            threat_detector=self.threat_detector,
            cameras=self.cameras,
            memory=self.memory,
            observer=self.observer,
            phone_protocol=self.phone_protocol,
            on_chat=None,  # set lazily
            on_command=lambda req: self.handle_command(req),
        )
        self.smarthome = SmartHome(ROOT, ledger=self.ledger)
        self.weather = WeatherMonitor(ROOT, ledger=self.ledger)
        self.calendar = Calendar(ROOT, ledger=self.ledger)
        self.email = EmailSystem(ROOT, ledger=self.ledger, **self._load_email_config())
        self.dashboard = WebDashboard(ROOT, ledger=self.ledger)

        # ===========================================================
        # TIER 2 INTEGRATIONS
        # ===========================================================
        self.voip = VoIPSystem(ROOT, ledger=self.ledger)
        self.news_feeds = NewsFeeds(ROOT, ledger=self.ledger)
        self.finance = FinanceTracker(ROOT, ledger=self.ledger)
        self.packages = PackageTracker(ROOT, ledger=self.ledger)
        self.phone_protocol = PhoneProtocol(ROOT, ledger=self.ledger)
        self.music = MusicController(ROOT, ledger=self.ledger)
        self.notifications = NotificationSystem(ROOT, ledger=self.ledger)
        # Phone adapter — physical Android phone via ADB
        self.phone = PhoneAdapter(
            ROOT,
            ledger=self.ledger,
            on_speak=lambda text: self.communicator.speak(text, source="phone"),
            on_sms_received=lambda msg: self._handle_incoming_sms(msg),
        )
        # Wire phone adapter into messaging as a fallback SMS method
        self.messaging.phone_adapter = self.phone
        # Funding executor — connects prospects → document generation → email submission
        from anubis.prospects import ProspectsSystem, ProspectsStore
        from anubis.cloud_model import CloudModelAdapter
        _prospects_store = ProspectsStore(ROOT / "prospects" / "prospects.json")
        _cloud_adapter = None
        try:
            _cloud_adapter = CloudModelAdapter(ledger=self.ledger)
        except Exception:
            pass
        self.funding = FundingExecutor(
            ROOT,
            prospects=ProspectsSystem(store=_prospects_store, ledger=self.ledger),
            email_system=self.email,
            computer_control=self.computer_control,
            cloud_model=_cloud_adapter,
            ledger=self.ledger,
            on_speak=lambda text: self.communicator.speak(text, source="funding"),
        )

        # ===========================================================
        # TIER 3 INTEGRATIONS (IoT)
        # ===========================================================
        self.obd = OBDMonitor(ROOT, ledger=self.ledger)
        self.air_quality = AirQualityMonitor(
            ROOT, ledger=self.ledger,
            on_alert=lambda msg, r: self.notifications.alert(msg),
        )
        self.energy = EnergyMonitor(ROOT, ledger=self.ledger)
        self.printer3d = Printer3D(ROOT, ledger=self.ledger)
        self.drone = DroneController(ROOT, ledger=self.ledger)
        self.garden = GardenMonitor(ROOT, ledger=self.ledger)
        self.smartwatch = SmartWatch(
            ROOT, ledger=self.ledger,
            on_anomaly=lambda msg, d: self.notifications.alert(msg),
        )
        self.visitors = VisitorLogger(
            ROOT, ledger=self.ledger,
            on_visitor=lambda v: self.notifications.notify(
                f"Visitor: {v.visitor_name or 'Unknown'}",
                f"Type: {v.visitor_type}, Camera: {v.camera_id}",
                priority="high" if v.visitor_type == "unknown" else "normal",
            ),
        )

        # ===========================================================
        # TIER 4 INTEGRATIONS (Advanced)
        # ===========================================================
        self.emergency_services = EmergencyServices(
            ROOT, ledger=self.ledger, voip=self.voip,
            on_call_required=self._on_emergency_call_request,
        )
        self.multilang = MultiLanguage(ROOT, ledger=self.ledger)
        self.ar_glasses = ARGlasses(
            ROOT, ledger=self.ledger, perception=self.perception,
        )
        self.satellite = SatelliteAnalyzer(ROOT, ledger=self.ledger)
        self.blockchain = BlockchainEvidence(ROOT, ledger=self.ledger)
        self.anubis_protocol = ANUBISProtocol(ROOT, ledger=self.ledger)

        # ===========================================================
        # COMMUNICATOR — the persona layer (DEMON)
        # All voice/chat output goes through this layer.
        # DEMON speaks for ANUBIS in daily interaction.
        # ANUBIS speaks directly only in tomb mode.
        # ===========================================================
        self.communicator = Communicator(
            ROOT,
            name="DEMON",
            ledger=self.ledger,
        )

        # ===========================================================
        # COMPUTER CONTROL — file ops, app launching, web search, media
        # ===========================================================
        self.computer_control = ComputerControl(
            ROOT,
            ledger=self.ledger,
            gateway=self.gateway,
            music_controller=self.music,
            on_speak=None,  # wired after sensory loads
        )

        # ===========================================================
        # SLEEP PROTOCOL — goodnight, wake, good morning
        # ===========================================================
        self.sleep_protocol = SleepProtocol(
            ROOT,
            ledger=self.ledger,
            smarthome=self.smarthome,
            sensory=None,  # set lazily after model loads
            remote_monitor=self.remote_monitor,
            smartwatch=self.smartwatch,
            calendar=self.calendar,
            mission_queue=self.mission_queue,
            skill_library=self.library,
            court=self.court,
            weather=self.weather,
            notifications=self.notifications,
            communicator=self.communicator,
        )

    def _check_model(self) -> dict:
        try:
            adapter = OllamaAdapter(MODEL_NAME, require_tools=False)
            health = adapter.health()
            self.model = adapter
            self._model_health = health
            # Lazily initialize model-dependent modules
            self._init_model_dependent_modules()
            return health
        except Exception as exc:
            self._model_health = {"error": str(exc), "model_present": False}
            return self._model_health

    def _init_model_dependent_modules(self) -> None:
        """Initialize modules that require the LLM model."""
        if self.model is None:
            return
        try:
            if self.proactive is None:
                self.proactive = ProactiveEngagement(
                    self.model, ROOT, ledger=self.ledger,
                    grounding=self.grounding, memory=self.memory,
                )
                self.observer.proactive = self.proactive
                self.api_server.proactive = self.proactive
        except Exception:
            pass
        try:
            if self.consciousness is None:
                self.consciousness = ConsciousnessEngine(
                    self.model, ROOT, ledger=self.ledger, memory=self.memory,
                )
                self.api_server.consciousness = self.consciousness
        except Exception:
            pass
        try:
            if self.research_engine is None:
                self.research_engine = ResearchEngine(
                    self.model, ROOT, ledger=self.ledger,
                    knowledge=self.knowledge, grounding=self.grounding,
                )
        except Exception:
            pass
        try:
            if self.sensory is None:
                # Build voice command router with sleep + tomb commands
                router = self._build_voice_command_router()
                # Build universal voice command interpreter
                voice_interp = VoiceCommandInterpreter(
                    self.model,
                    dispatch=lambda req: self._dispatch(req),
                    ledger=self.ledger,
                    on_speak=lambda text: self.communicator.speak(text, source="voice_command"),
                )
                # Use communicator's wake word (DEMON in normal mode, ANUBIS in tomb)
                wake_word = self.communicator.wake_word
                self.sensory = SensorySystem(
                    ROOT, model=self.model,
                    wake_word=wake_word,
                    voice_output=self.voice_out,
                    observer=self.observer,
                    proactive=self.proactive,
                    voice_command_router=router,
                    voice_interpreter=voice_interp,
                    ledger=self.ledger,
                )
                self.api_server.sensory = self.sensory
                self.api_server.on_chat = lambda msg: self._chat_via_communicator(msg)
                # Wire sensory into sleep protocol
                self.sleep_protocol.sensory = self.sensory
                # Wire communicator's speak callback to sensory voice
                self.communicator.on_speak = lambda text, source: self.sensory.voice.speak(
                    text, priority="high", source=source,
                )
                # Wire computer control's speak callback
                self.computer_control.on_speak = lambda text: self.communicator.speak(
                    text, source="computer",
                )
                # Wire account manager's speak callback
                self.account_manager.on_speak = lambda text: self.communicator.speak(
                    text, source="accounts",
                )
                # Wire biometric auth's speak callback
                self.biometric_auth.on_speak = lambda text: self.communicator.speak(
                    text, source="biometric",
                )
                # Wire self-repair speak callback
                self.self_repair.on_speak = lambda text: self.communicator.speak(
                    text, source="self_repair",
                )
                # Wire drive monitor speak + notify callbacks
                self.drive_monitor.on_speak = lambda text: self.communicator.speak(
                    text, source="drive_monitor",
                )
                self.drive_monitor.on_notify = lambda title, body: self.notifications.notify(
                    title, body,
                ) if self.notifications else None
                # Wire cold archive speak callback
                self.cold_archive.on_speak = lambda text: self.communicator.speak(
                    text, source="cold_archive",
                )
                # Initialize dream cycle engine
                if self.dream is None:
                    from anubis.dream_cycle import DreamCycleEngine
                    self.dream = DreamCycleEngine(
                        self.model, ROOT,
                        ledger=self.ledger,
                        library=self.library,
                        queue=self.queue if hasattr(self, 'queue') else None,
                        memory=self.memory,
                        knowledge=self.knowledge,
                        grounding=self.grounding,
                    )
                # Initialize knowledge acquisition
                if self.knowledge_acq is None:
                    from anubis.knowledge_acquisition import KnowledgeAcquisition
                    self.knowledge_acq = KnowledgeAcquisition(
                        ROOT,
                        gateway=self.external_gateway if hasattr(self, 'external_gateway') else None,
                        knowledge=self.knowledge,
                        model=self.model,
                        ledger=self.ledger,
                    )
                # Initialize evaluator
                if self.evaluator is None:
                    from anubis.evaluation import ModelEvaluator
                    self.evaluator = ModelEvaluator(ledger=self.ledger)
                # Initialize training orchestrator
                if self.training_orch is None:
                    from anubis.training_orchestrator import TrainingOrchestrator
                    self.training_orch = TrainingOrchestrator(
                        ledger=self.ledger,
                        output_dir=ROOT / "training",
                    )
                # Initialize local fine-tuner
                if self.local_finetuner is None:
                    self.local_finetuner = LocalFineTuner(
                        ROOT,
                        distiller=self.distiller if hasattr(self, 'distiller') else None,
                        evaluator=self.evaluator,
                        ab_drive=self.ab_drive if hasattr(self, 'ab_drive') else None,
                        ledger=self.ledger,
                        on_speak=lambda text: self.communicator.speak(text, source="training"),
                    )
                # Wire remaining scheduler callbacks now that modules exist
                self.scheduler._on_dream = lambda: self.dream.run_cycle().to_dict() if self.dream else {"error": "dream engine not ready"}
                self.scheduler._on_purge = lambda: self.purge.execute(ROOT)
                self.scheduler._on_missions = lambda count: self._process_missions(count)
                self.scheduler._on_training = lambda: self.training_orch.status() if self.training_orch else {"error": "training not ready"}
                self.scheduler._on_eval = lambda: self.evaluator.stats() if self.evaluator else {"error": "evaluator not ready"}
                self.scheduler._on_knowledge = lambda: self._auto_acquire_knowledge()
        except Exception:
            pass

    def _build_voice_command_router(self) -> VoiceCommandRouter:
        """Build the voice command router with all registered commands."""
        from anubis.sensory import VoiceCommandRouter, SPEECH_DIRECT_ADDRESS
        router = VoiceCommandRouter()

        # Sleep protocol — goodnight
        router.register(
            "goodnight",
            ["goodnight", "good night", "i'm going to bed", "going to bed",
             "time for bed", "i'm going to sleep", "going to sleep"],
            lambda text: self.sleep_protocol.goodnight(),
            description="Begin sleep mode — lock doors, privacy, monitor sleep",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=True,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        # Sleep protocol — wake
        router.register(
            "wake",
            ["wake me up", "wake me", "time to wake up", "alarm",
             "wake up", "get me up"],
            lambda text: self.sleep_protocol.wake(),
            description="Sound alarm and monitor until Creator is awake",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=True,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=True,  # needs to work during sleep mode
        )

        # Sleep protocol — good morning
        router.register(
            "good_morning",
            ["good morning", "good morrow", "i'm awake", "i am awake",
             "i'm up", "i am up", "morning"],
            lambda text: self.sleep_protocol.good_morning(),
            description="End sleep session and deliver morning briefing",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=True,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=True,  # needs to work when waking from sleep
        )

        # Sleep protocol — cancel
        router.register(
            "sleep_cancel",
            ["cancel sleep", "cancel alarm", "stop alarm", "never mind",
             "go back to sleep"],
            lambda text: self.sleep_protocol.cancel(),
            description="Cancel current sleep session or alarm",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=False,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=True,
        )

        # Tomb mode — enter (speak to ANUBIS directly)
        router.register(
            "enter_tomb",
            ["speak to anubis", "talk to anubis", "enter tomb", "tomb mode",
             "let me talk to anubis", "i want to talk to anubis",
             "speak to anubis directly", "go to tomb"],
            lambda text: self._enter_tomb_via_voice(text),
            description="Enter tomb mode — ANUBIS speaks directly for review/evaluation",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=False,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        # Tomb mode — exit (back to DEMON)
        router.register(
            "exit_tomb",
            [f"back to {self.communicator.name.lower()}", "exit tomb",
             "leave tomb", "back to normal", "exit tomb mode"],
            lambda text: self._exit_tomb_via_voice(),
            description="Exit tomb mode — return to DEMON",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=False,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        # Computer control — media next/skip
        router.register(
            "media_next",
            ["next video", "next song", "next track", "skip", "skip this",
             "next", "play next"],
            lambda text: self.computer_control.media_next().to_dict(),
            description="Skip to next track or video",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=True,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        # Computer control — media previous
        router.register(
            "media_previous",
            ["previous video", "previous song", "previous track",
             "go back", "last song"],
            lambda text: self.computer_control.media_previous().to_dict(),
            description="Go to previous track or video",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=False,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        # Computer control — pause
        router.register(
            "media_pause",
            ["pause", "pause music", "pause video", "stop playing",
             "stop the music"],
            lambda text: self.computer_control.media_pause().to_dict(),
            description="Pause media playback",
            match_direct_address=True,
            match_ambient=True,
            match_self_talk=False,
            match_conversation=False,
            suppress_chat=True,
            works_in_privacy=False,
        )

        return router

    def _enter_tomb_via_voice(self, text: str) -> dict:
        """Enter tomb mode via voice command."""
        result = self.communicator.enter_tomb(reason=text)
        # Update wake word to ANUBIS
        if self.sensory:
            self.sensory.set_wake_word("anubis")
        return result

    def _exit_tomb_via_voice(self) -> dict:
        """Exit tomb mode via voice command."""
        result = self.communicator.exit_tomb()
        # Restore wake word to DEMON (or whatever the communicator name is)
        if self.sensory:
            self.sensory.set_wake_word(self.communicator.wake_word)
        return result

    def _chat_via_sensory(self, message: str) -> str:
        """Route chat through the sensory/conversation system."""
        req = {"cmd": "chat", "message": message}
        resp = self._cmd_chat(req)
        return resp.get("response", resp.get("error", ""))

    def _chat_via_communicator(self, message: str) -> str:
        """Route chat through the communicator layer (DEMON/ANUBIS).

        This is the main chat path. The communicator:
        1. Checks if the Creator wants to enter/exit tomb mode
        2. Gets ANUBIS's raw response
        3. Frames it in the active persona's voice
        """
        # Check for tomb mode transitions
        if self.communicator.should_route_to_anubis(message):
            result = self.communicator.enter_tomb(reason=message)
            return result["message"]

        if self.communicator.should_exit_tomb(message):
            result = self.communicator.exit_tomb()
            return result["message"]

        # Get ANUBIS's raw response
        req = {"cmd": "chat", "message": message}
        resp = self._cmd_chat(req)
        raw_response = resp.get("response", resp.get("error", ""))

        # Frame through the communicator (DEMON in normal mode, raw in tomb)
        framed = self.communicator.frame_response(raw_response)
        return framed

    # ===========================================================
    # EVENT HANDLERS — wire the threat pipeline together
    # ===========================================================

    def _on_camera_event(self, event: Any) -> None:
        """Handle camera events — feed to threat analysis."""
        try:
            # Unknown person at door → threat analysis
            if hasattr(event, "event_type"):
                if event.event_type == "unknown_person":
                    self.threat_detector.analyze_perception(
                        face_result={"is_known": False, "confidence": event.confidence},
                        creator_present=False,
                    )
                elif event.event_type == "motion":
                    self.observer._make_observation(
                        source="cameras",
                        event_type="motion",
                        content=f"Motion on {event.camera_id}",
                    )
        except Exception:
            pass

    def _on_threat_detected(self, threat: Any) -> None:
        """Handle detected threats — alert, notify, lock down."""
        try:
            # Notify via notifications system
            self.notifications.alert(
                f"Threat: {threat.threat_type} — {threat.description}"
            )
            # Log to observer
            self.observer._make_observation(
                source="threat_analysis",
                event_type="threat",
                content=f"Threat: {threat.threat_type} ({threat.severity})",
            )
        except Exception:
            pass

    def _on_remote_alert(self, alert: Any) -> None:
        """Handle remote monitoring alerts — fall, location, health."""
        try:
            self.notifications.alert(
                f"Remote alert: {alert.alert_type} — {alert.description}"
            )
            # Feed to threat analysis
            if alert.alert_type == "fall":
                self.threat_detector.analyze_perception(
                    creator_present=False,
                )
        except Exception:
            pass

    def _on_emergency_call_request(self, call: Any) -> bool:
        """Handle emergency services call approval request.

        In production, this would push a notification to the Creator's
        phone and wait for approval. For now, it returns False (denied)
        unless the Creator has pre-approved via the daemon.
        """
        try:
            self.notifications.alert(
                f"EMERGENCY CALL REQUESTED: {call.emergency_type} — {call.description}. "
                f"Approval required. Respond via daemon or app."
            )
        except Exception:
            pass
        return False  # Always require explicit approval

    def start(self) -> None:
        # Boot-time integrity check
        boot_result = self.boot_checker.check()
        if not boot_result["passed"]:
            print(f"{RED}BOOT CHECK FAILED{OFF} — refusing to start. See boot log.")
            return

        # Start the autonomous scheduler
        self.scheduler.start()

        # Remove stale socket
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)

        srv = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        srv.bind(SOCKET_PATH)
        srv.listen(MAX_CONNECTIONS)
        srv.settimeout(1.0)
        os.chmod(SOCKET_PATH, 0o600)

        print(f"{GOLD}ANUBIS daemon{OFF} listening on {SOCKET_PATH}")
        print(f"  skills   : {len(self.library.names())} promoted")
        print(f"  ledger   : {self.ledger.length} entries")
        ok, msg = self.ledger.verify()
        print(f"  integrity: {GREEN if ok else RED}{msg}{OFF}")
        health = self._check_model()
        if health.get("model_present"):
            print(f"  model    : {GREEN}{MODEL_NAME} available{OFF}")
        else:
            print(f"  model    : {RED}not available{OFF} ({health.get('error', '?')})")
        print(f"  sandbox  : {self.sandbox.describe()}")
        print(f"{DIM}  Ctrl+C to stop{OFF}")
        sys.stdout.flush()

        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        while self._running:
            try:
                conn, _ = srv.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            t = threading.Thread(target=self._handle, args=(conn,), daemon=True)
            t.start()

        srv.close()
        if os.path.exists(SOCKET_PATH):
            os.unlink(SOCKET_PATH)
        print(f"\n{GOLD}ANUBIS daemon{OFF} stopped.")

    def _signal_handler(self, signum, frame):
        self._running = False
        try:
            self.scheduler.stop()
        except Exception:
            pass

    def _handle(self, conn: socket.socket) -> None:
        try:
            data = conn.recv(BUFFER_SIZE).decode("utf-8")
            if not data:
                return
            req = json.loads(data)
            cmd = req.get("cmd", "?")
            resp = self._dispatch(req)
            conn.sendall((json.dumps(resp) + "\n").encode("utf-8"))
            # Log the request
            ok = "ok" if "error" not in resp else resp["error"][:40]
            print(f"  [{cmd}] -> {ok}", flush=True)
        except json.JSONDecodeError:
            conn.sendall((json.dumps({"error": "invalid JSON"}) + "\n").encode("utf-8"))
        except Exception as exc:
            conn.sendall((json.dumps({"error": str(exc)}) + "\n").encode("utf-8"))
        finally:
            conn.close()

    def _dispatch(self, req: dict) -> dict:
        cmd = req.get("cmd", "")
        if cmd == "status":
            return self._cmd_status()
        if cmd == "skills":
            return self._cmd_skills()
        if cmd == "ledger":
            return self._cmd_ledger()
        if cmd == "mission":
            return self._cmd_mission(req)
        if cmd == "poll":
            return self._cmd_poll(req)
        if cmd == "chat":
            return self._cmd_chat(req)
        if cmd == "reset_chat":
            return self._cmd_reset_chat()
        if cmd == "tts":
            return self._cmd_tts(req)
        if cmd == "stt":
            return self._cmd_stt(req)
        if cmd == "list_projects":
            return self._cmd_list_projects()
        if cmd == "get_project":
            return self._cmd_get_project(req)
        if cmd == "plan_project":
            return self._cmd_plan_project(req)
        if cmd == "run_project":
            return self._cmd_run_project(req)
        if cmd == "poll_project":
            return self._cmd_poll_project(req)
        if cmd == "constitution":
            return self._cmd_constitution()
        if cmd == "ledger_entries":
            return self._cmd_ledger_entries(req)
        if cmd == "skill_versions":
            return self._cmd_skill_versions(req)
        if cmd == "mission_history":
            return self._cmd_mission_history()
        if cmd == "genesis":
            return self._cmd_genesis()
        if cmd == "fs_list":
            return self._cmd_fs_list(req)
        if cmd == "fs_read":
            return self._cmd_fs_read(req)
        if cmd == "fs_write":
            return self._cmd_fs_write(req)
        if cmd == "run_cmd":
            return self._cmd_run_cmd(req)
        # Knowledge base commands
        if cmd == "registry_stats":
            return self._cmd_registry_stats()
        if cmd == "list_directors":
            return self._cmd_list_directors()
        if cmd == "list_specialties":
            return self._cmd_list_specialties(req)
        if cmd == "knowledge_stats":
            return self._cmd_knowledge_stats()
        if cmd == "knowledge_search":
            return self._cmd_knowledge_search(req)
        if cmd == "knowledge_ingest":
            return self._cmd_knowledge_ingest(req)
        if cmd == "knowledge_promote":
            return self._cmd_knowledge_promote(req)
        if cmd == "knowledge_ground":
            return self._cmd_knowledge_ground(req)
        if cmd == "claim_search":
            return self._cmd_claim_search(req)
        if cmd == "grounding_stats":
            return self._cmd_grounding_stats()
        # Governance commands
        if cmd == "identity_stats":
            return self._cmd_identity_stats()
        if cmd == "enroll_creator":
            return self._cmd_enroll_creator(req)
        if cmd == "court_stats":
            return self._cmd_court_stats()
        if cmd == "court_submit":
            return self._cmd_court_submit(req)
        if cmd == "policy_stats":
            return self._cmd_policy_stats()
        if cmd == "capability_stats":
            return self._cmd_capability_stats()
        # System commands
        if cmd == "network_stats":
            return self._cmd_network_stats()
        if cmd == "hardening_stats":
            return self._cmd_hardening_stats()
        if cmd == "recovery_stats":
            return self._cmd_recovery_stats()
        if cmd == "ab_stats":
            return self._cmd_ab_stats()
        if cmd == "egyptology_lookup":
            return self._cmd_egyptology_lookup(req)
        if cmd == "egyptology_stats":
            return self._cmd_egyptology_stats()
        if cmd == "purge_now":
            return self._cmd_purge_now()
        if cmd == "package_stats":
            return self._cmd_package_stats()
        if cmd == "financial_stats":
            return self._cmd_financial_stats()
        # New module commands
        if cmd == "queue_stats":
            return self._cmd_queue_stats()
        if cmd == "queue_add":
            return self._cmd_queue_add(req)
        if cmd == "queue_add_batch":
            return self._cmd_queue_add_batch(req)
        if cmd == "queue_process":
            return self._cmd_queue_process(req)
        if cmd == "queue_list":
            return self._cmd_queue_list()
        if cmd == "orchestrate":
            return self._cmd_orchestrate(req)
        if cmd == "knowledge_propose":
            return self._cmd_knowledge_propose(req)
        if cmd == "knowledge_approve":
            return self._cmd_knowledge_approve(req)
        if cmd == "knowledge_promote_proposal":
            return self._cmd_knowledge_promote_proposal(req)
        if cmd == "knowledge_updater_stats":
            return self._cmd_knowledge_updater_stats()
        if cmd == "backup_create":
            return self._cmd_backup_create(req)
        if cmd == "backup_list":
            return self._cmd_backup_list()
        if cmd == "backup_restore":
            return self._cmd_backup_restore(req)
        if cmd == "voice_toggle_out":
            return self._cmd_voice_toggle_out()
        if cmd == "voice_toggle_in":
            return self._cmd_voice_toggle_in()
        if cmd == "voice_speak":
            return self._cmd_voice_speak(req)
        if cmd == "voice_status":
            return self._cmd_voice_status()
        if cmd == "docs_generate":
            return self._cmd_docs_generate()
        # Memory commands (Phase A upgrade)
        if cmd == "memory_stats":
            return self._cmd_memory_stats()
        if cmd == "memory_recall":
            return self._cmd_memory_recall(req)
        if cmd == "memory_purge":
            return self._cmd_memory_purge(req)
        if cmd == "memory_purge_log":
            return self._cmd_memory_purge_log(req)
        # Cloud sync commands (Phase B)
        if cmd == "cloud_sync_status":
            return self._cmd_cloud_sync_status()
        if cmd == "cloud_sync":
            return self._cmd_cloud_sync(req)
        if cmd == "cloud_sync_upload":
            return self._cmd_cloud_sync_upload(req)
        if cmd == "cloud_sync_download":
            return self._cmd_cloud_sync_download(req)
        if cmd == "cloud_sync_list":
            return self._cmd_cloud_sync_list(req)
        # External gateway commands (Phase B)
        if cmd == "gateway_status":
            return self._cmd_gateway_status()
        if cmd == "gateway_fetch":
            return self._cmd_gateway_fetch(req)
        if cmd == "gateway_search":
            return self._cmd_gateway_search(req)
        if cmd == "gateway_add_domain":
            return self._cmd_gateway_add_domain(req)
        if cmd == "gateway_remove_domain":
            return self._cmd_gateway_remove_domain(req)
        # Cloud teacher commands (Phase C)
        if cmd == "cloud_model_status":
            return self._cmd_cloud_model_status()
        if cmd == "cloud_model_chat":
            return self._cmd_cloud_model_chat(req)
        # Lambda training/testing commands (Phase C)
        if cmd == "lambda_status":
            return self._cmd_lambda_status()
        if cmd == "lambda_cost_preview":
            return self._cmd_lambda_cost_preview(req)
        if cmd == "lambda_submit":
            return self._cmd_lambda_submit(req)
        if cmd == "lambda_job_status":
            return self._cmd_lambda_job_status(req)
        if cmd == "lambda_list_jobs":
            return self._cmd_lambda_list_jobs()
        if cmd == "lambda_cancel":
            return self._cmd_lambda_cancel(req)
        # Prospects/funding commands (Phase D)
        if cmd == "prospects_status":
            return self._cmd_prospects_status()
        if cmd == "prospects_search":
            return self._cmd_prospects_search(req)
        if cmd == "prospects_create":
            return self._cmd_prospects_create(req)
        if cmd == "prospects_evaluate":
            return self._cmd_prospects_evaluate(req)
        if cmd == "prospects_approve":
            return self._cmd_prospects_approve(req)
        if cmd == "prospects_reject":
            return self._cmd_prospects_reject(req)
        if cmd == "prospects_list_pending":
            return self._cmd_prospects_list_pending()
        if cmd == "prospects_list_approved":
            return self._cmd_prospects_list_approved()
        if cmd == "prospects_stats":
            return self._cmd_prospects_stats()
        # ===========================================================
        # FUNDING EXECUTOR (autonomous application generation + submission)
        # ===========================================================
        if cmd == "funding_status":
            return self.funding.get_status()
        if cmd == "funding_generate":
            return self.funding.generate_application(
                req.get("prospect_id", ""),
                extra_instructions=req.get("extra_instructions", ""),
            )
        if cmd == "funding_get_document":
            return self.funding.get_document(req.get("application_id", ""))
        if cmd == "funding_list":
            return self.funding.list_applications(stage=req.get("stage", ""))
        if cmd == "funding_pending_reviews":
            return self.funding.list_pending_reviews()
        if cmd == "funding_pending_submission":
            return self.funding.list_pending_submission()
        if cmd == "funding_approve_document":
            return self.funding.approve_document(
                req.get("application_id", ""),
                email_to=req.get("email_to", ""),
                email_subject=req.get("email_subject", ""),
            )
        if cmd == "funding_reject_document":
            return self.funding.reject_document(
                req.get("application_id", ""),
                reason=req.get("reason", ""),
            )
        if cmd == "funding_update_email":
            return self.funding.update_email(
                req.get("application_id", ""),
                email_to=req.get("email_to", ""),
                email_subject=req.get("email_subject", ""),
                email_body=req.get("email_body", ""),
            )
        if cmd == "funding_submit":
            return self.funding.submit_application(
                req.get("application_id", ""),
                approval_token=req.get("approval_token", ""),
            )
        # Vector index commands
        if cmd == "vector_index_stats":
            return self._cmd_vector_index_stats()
        if cmd == "vector_index_rebuild":
            return self._cmd_vector_index_rebuild()
        # Reranker commands
        if cmd == "rerank":
            return self._cmd_rerank(req)
        # Auto-git commands
        if cmd == "autogit_status":
            return self._cmd_autogit_status()
        if cmd == "autogit_commit":
            return self._cmd_autogit_commit(req)
        # Memory rebuild
        if cmd == "memory_rebuild_index":
            return self._cmd_memory_rebuild_index()
        # Distillation commands
        if cmd == "distillation_stats":
            return self._cmd_distillation_stats()
        if cmd == "distillation_export":
            return self._cmd_distillation_export(req)
        # Evaluation commands
        if cmd == "evaluation_benchmark":
            return self._cmd_evaluation_benchmark(req)
        if cmd == "evaluation_stats":
            return self._cmd_evaluation_stats()
        # Training orchestrator commands
        if cmd == "training_prepare":
            return self._cmd_training_prepare(req)
        if cmd == "training_approve":
            return self._cmd_training_approve(req)
        if cmd == "training_status":
            return self._cmd_training_status()
        if cmd == "training_list_plans":
            return self._cmd_training_list_plans()
        # A/B drive commands
        if cmd == "ab_drive_status":
            return self._cmd_ab_drive_status()
        if cmd == "ab_drive_stage":
            return self._cmd_ab_drive_stage(req)
        if cmd == "ab_drive_promote":
            return self._cmd_ab_drive_promote()
        if cmd == "ab_drive_rollback":
            return self._cmd_ab_drive_rollback(req)
        # Librarian commands
        if cmd == "librarian_scan":
            return self._cmd_librarian_scan()
        if cmd == "librarian_status":
            return self._cmd_librarian_status()
        if cmd == "librarian_impact":
            return self._cmd_librarian_impact(req)
        # Custom embeddings commands
        if cmd == "embeddings_status":
            return self._cmd_embeddings_status()
        if cmd == "embeddings_train":
            return self._cmd_embeddings_train(req)
        if cmd == "embeddings_activate":
            return self._cmd_embeddings_activate(req)
        if cmd == "embeddings_evaluate":
            return self._cmd_embeddings_evaluate()
        # Cloud phase-out commands
        if cmd == "phaseout_status":
            return self._cmd_phaseout_status()
        if cmd == "phaseout_record":
            return self._cmd_phaseout_record(req)
        if cmd == "phaseout_graduated":
            return self._cmd_phaseout_graduated()
        # Docker commands
        if cmd == "docker_generate":
            return self._cmd_docker_generate()
        if cmd == "docker_status":
            return self._cmd_docker_status()
        # Local inference engine commands
        if cmd == "inference_status":
            return self._cmd_inference_status()
        if cmd == "inference_generate":
            return self._cmd_inference_generate(req)
        if cmd == "inference_chat":
            return self._cmd_inference_chat(req)
        # Dependency check commands
        if cmd == "dependency_check":
            return self._cmd_dependency_check()
        if cmd == "dependency_status":
            return self._cmd_dependency_status()
        # ===========================================================
        # PERCEPTION & SECURITY COMMANDS
        # ===========================================================
        if cmd == "perception_status":
            return self._cmd_perception_status()
        if cmd == "perception_analyze_audio":
            return self._cmd_perception_analyze_audio(req)
        if cmd == "perception_analyze_image":
            return self._cmd_perception_analyze_image(req)
        if cmd == "contacts_status":
            return self._cmd_contacts_status()
        if cmd == "contacts_add":
            return self._cmd_contacts_add(req)
        if cmd == "contacts_list":
            return self._cmd_contacts_list()
        if cmd == "contacts_notify_emergency":
            return self._cmd_contacts_notify_emergency(req)
        if cmd == "messaging_status":
            return self._cmd_messaging_status()
        if cmd == "messaging_send":
            return self._cmd_messaging_send(req)
        if cmd == "network_ops_status":
            return self._cmd_network_ops_status()
        if cmd == "network_ops_scan":
            return self._cmd_network_ops_scan(req)
        if cmd == "network_ops_devices":
            return self._cmd_network_ops_devices()
        if cmd == "remote_monitor_status":
            return self._cmd_remote_monitor_status()
        if cmd == "remote_monitor_update":
            return self._cmd_remote_monitor_update(req)
        if cmd == "threat_analysis_status":
            return self._cmd_threat_analysis_status()
        if cmd == "threat_analysis_analyze":
            return self._cmd_threat_analysis_analyze(req)
        if cmd == "threat_analysis_active":
            return self._cmd_threat_analysis_active()
        if cmd == "cameras_status":
            return self._cmd_cameras_status()
        if cmd == "cameras_add":
            return self._cmd_cameras_add(req)
        if cmd == "cameras_list":
            return self._cmd_cameras_list()
        if cmd == "cameras_capture":
            return self._cmd_cameras_capture(req)
        if cmd == "cameras_events":
            return self._cmd_cameras_events(req)
        if cmd == "cameras_start_monitoring":
            return self._cmd_cameras_start_monitoring()
        if cmd == "cameras_stop_monitoring":
            return self._cmd_cameras_stop_monitoring()
        if cmd == "observer_status":
            return self._cmd_observer_status()
        if cmd == "observer_observations":
            return self._cmd_observer_observations(req)
        if cmd == "observer_predictions":
            return self._cmd_observer_predictions()
        if cmd == "consciousness_status":
            return self._cmd_consciousness_status()
        if cmd == "consciousness_reflect":
            return self._cmd_consciousness_reflect(req)
        if cmd == "consciousness_self_concept":
            return self._cmd_consciousness_self_concept()
        if cmd == "proactive_status":
            return self._cmd_proactive_status()
        if cmd == "proactive_engage":
            return self._cmd_proactive_engage(req)
        if cmd == "sensory_status":
            return self._cmd_sensory_status()
        if cmd == "sensory_listen":
            return self._cmd_sensory_listen(req)
        if cmd == "sensory_set_mode":
            return self._cmd_sensory_set_mode(req)
        if cmd == "research_status":
            return self._cmd_research_status()
        if cmd == "research_identify_gaps":
            return self._cmd_research_identify_gaps(req)
        if cmd == "research_propose":
            return self._cmd_research_propose(req)
        # ===========================================================
        # TIER 1 INTEGRATION COMMANDS
        # ===========================================================
        if cmd == "api_server_start":
            return self._cmd_api_server_start()
        if cmd == "api_server_stop":
            return self._cmd_api_server_stop()
        if cmd == "api_server_status":
            return self._cmd_api_server_status()
        if cmd == "smarthome_status":
            return self._cmd_smarthome_status()
        if cmd == "smarthome_add_device":
            return self._cmd_smarthome_add_device(req)
        if cmd == "smarthome_control":
            return self._cmd_smarthome_control(req)
        if cmd == "smarthome_devices":
            return self._cmd_smarthome_devices()
        if cmd == "weather_status":
            return self._cmd_weather_status()
        if cmd == "weather_forecast":
            return self._cmd_weather_forecast(req)
        if cmd == "weather_alerts":
            return self._cmd_weather_alerts()
        if cmd == "calendar_status":
            return self._cmd_calendar_status()
        if cmd == "calendar_add_event":
            return self._cmd_calendar_add_event(req)
        if cmd == "calendar_today":
            return self._cmd_calendar_today()
        if cmd == "calendar_upcoming":
            return self._cmd_calendar_upcoming(req)
        if cmd == "email_status":
            return self._cmd_email_status()
        if cmd == "email_check":
            return self._cmd_email_check()
        if cmd == "email_send":
            return self._cmd_email_send(req)
        if cmd == "email_set_password":
            return self._cmd_email_set_password(req)
        if cmd == "email_reconfigure":
            return self._cmd_email_reconfigure()
        if cmd == "dashboard_start":
            return self._cmd_dashboard_start()
        if cmd == "dashboard_stop":
            return self._cmd_dashboard_stop()
        if cmd == "dashboard_status":
            return self._cmd_dashboard_status()
        # ===========================================================
        # TIER 2 INTEGRATION COMMANDS
        # ===========================================================
        if cmd == "voip_status":
            return self._cmd_voip_status()
        if cmd == "voip_call":
            return self._cmd_voip_call(req)
        if cmd == "voip_end_call":
            return self._cmd_voip_end_call(req)
        if cmd == "voip_calls":
            return self._cmd_voip_calls()
        if cmd == "news_status":
            return self._cmd_news_status()
        if cmd == "news_fetch":
            return self._cmd_news_fetch()
        if cmd == "news_items":
            return self._cmd_news_items(req)
        if cmd == "news_briefing":
            return self._cmd_news_briefing()
        if cmd == "finance_status":
            return self._cmd_finance_status()
        if cmd == "finance_add_transaction":
            return self._cmd_finance_add_transaction(req)
        if cmd == "finance_add_bill":
            return self._cmd_finance_add_bill(req)
        if cmd == "finance_upcoming_bills":
            return self._cmd_finance_upcoming_bills()
        if cmd == "finance_spending":
            return self._cmd_finance_spending(req)
        if cmd == "packages_status":
            return self._cmd_packages_status()
        if cmd == "packages_add":
            return self._cmd_packages_add(req)
        if cmd == "packages_update":
            return self._cmd_packages_update(req)
        if cmd == "packages_active":
            return self._cmd_packages_active()
        if cmd == "phone_register":
            return self._cmd_phone_register(req)
        if cmd == "phone_status":
            return self._cmd_phone_status()
        if cmd == "phone_notify":
            return self._cmd_phone_notify(req)
        if cmd == "phone_devices":
            return self._cmd_phone_devices()
        if cmd == "music_status":
            return self._cmd_music_status()
        if cmd == "music_play":
            return self._cmd_music_play(req)
        if cmd == "music_pause":
            return self._cmd_music_pause()
        if cmd == "music_stop":
            return self._cmd_music_stop()
        if cmd == "music_set_mood":
            return self._cmd_music_set_mood(req)
        if cmd == "music_set_volume":
            return self._cmd_music_set_volume(req)
        if cmd == "music_playlists":
            return self._cmd_music_playlists()
        if cmd == "notifications_status":
            return self._cmd_notifications_status()
        if cmd == "notifications_notify":
            return self._cmd_notifications_notify(req)
        if cmd == "notifications_alert":
            return self._cmd_notifications_alert(req)
        if cmd == "notifications_history":
            return self._cmd_notifications_history(req)
        # ===========================================================
        # TIER 3 INTEGRATION COMMANDS (IoT)
        # ===========================================================
        if cmd == "obd_status":
            return self._cmd_obd_status()
        if cmd == "obd_read":
            return self._cmd_obd_read()
        if cmd == "air_quality_status":
            return self._cmd_air_quality_status()
        if cmd == "air_quality_record":
            return self._cmd_air_quality_record(req)
        if cmd == "energy_status":
            return self._cmd_energy_status()
        if cmd == "energy_record":
            return self._cmd_energy_record(req)
        if cmd == "printer3d_status":
            return self._cmd_printer3d_status()
        if cmd == "printer3d_submit":
            return self._cmd_printer3d_submit(req)
        if cmd == "printer3d_jobs":
            return self._cmd_printer3d_jobs()
        if cmd == "drone_status":
            return self._cmd_drone_status()
        if cmd == "drone_takeoff":
            return self._cmd_drone_takeoff(req)
        if cmd == "drone_land":
            return self._cmd_drone_land()
        if cmd == "drone_rtl":
            return self._cmd_drone_rtl()
        if cmd == "garden_status":
            return self._cmd_garden_status()
        if cmd == "garden_add_plant":
            return self._cmd_garden_add_plant(req)
        if cmd == "garden_record":
            return self._cmd_garden_record(req)
        if cmd == "garden_recommendations":
            return self._cmd_garden_recommendations()
        if cmd == "smartwatch_status":
            return self._cmd_smartwatch_status()
        if cmd == "smartwatch_data":
            return self._cmd_smartwatch_data(req)
        if cmd == "visitors_status":
            return self._cmd_visitors_status()
        if cmd == "visitors_log_arrival":
            return self._cmd_visitors_log_arrival(req)
        if cmd == "visitors_log_departure":
            return self._cmd_visitors_log_departure(req)
        if cmd == "visitors_active":
            return self._cmd_visitors_active()
        if cmd == "visitors_logs":
            return self._cmd_visitors_logs(req)
        # ===========================================================
        # TIER 4 INTEGRATION COMMANDS (Advanced)
        # ===========================================================
        if cmd == "emergency_services_status":
            return self._cmd_emergency_services_status()
        if cmd == "emergency_services_request":
            return self._cmd_emergency_services_request(req)
        if cmd == "emergency_services_calls":
            return self._cmd_emergency_services_calls()
        if cmd == "multilang_status":
            return self._cmd_multilang_status()
        if cmd == "multilang_detect":
            return self._cmd_multilang_detect(req)
        if cmd == "multilang_translate":
            return self._cmd_multilang_translate(req)
        if cmd == "multilang_languages":
            return self._cmd_multilang_languages()
        if cmd == "ar_status":
            return self._cmd_ar_status()
        if cmd == "ar_process_frame":
            return self._cmd_ar_process_frame(req)
        if cmd == "satellite_status":
            return self._cmd_satellite_status()
        if cmd == "satellite_fetch":
            return self._cmd_satellite_fetch(req)
        if cmd == "blockchain_status":
            return self._cmd_blockchain_status()
        if cmd == "blockchain_anchor":
            return self._cmd_blockchain_anchor(req)
        if cmd == "blockchain_verify":
            return self._cmd_blockchain_verify(req)
        if cmd == "blockchain_anchors":
            return self._cmd_blockchain_anchors(req)
        if cmd == "anubis_protocol_status":
            return self._cmd_anubis_protocol_status()
        if cmd == "anubis_protocol_add_peer":
            return self._cmd_anubis_protocol_add_peer(req)
        if cmd == "anubis_protocol_peers":
            return self._cmd_anubis_protocol_peers()
        if cmd == "anubis_protocol_send":
            return self._cmd_anubis_protocol_send(req)
        if cmd == "anubis_protocol_check_peer":
            return self._cmd_anubis_protocol_check_peer(req)
        # ===========================================================
        # UNIFIED STATUS — all systems at once
        # ===========================================================
        # ===========================================================
        # SLEEP PROTOCOL COMMANDS
        # ===========================================================
        if cmd == "goodnight":
            return self._cmd_goodnight()
        if cmd == "wake":
            return self._cmd_wake()
        if cmd == "good_morning":
            return self._cmd_good_morning()
        if cmd == "sleep_status":
            return self._cmd_sleep_status()
        if cmd == "sleep_cancel":
            return self._cmd_sleep_cancel()
        if cmd == "sleep_history":
            return self._cmd_sleep_history(req)
        if cmd == "sleep_accel":
            return self._cmd_sleep_accel(req)
        if cmd == "sleep_heart_rate":
            return self._cmd_sleep_heart_rate(req)
        if cmd == "voice_commands":
            return self._cmd_voice_commands()
        if cmd == "communicator_status":
            return self._cmd_communicator_status()
        if cmd == "communicator_rename":
            return self._cmd_communicator_rename(req)
        if cmd == "enter_tomb":
            return self._cmd_enter_tomb(req)
        if cmd == "exit_tomb":
            return self._cmd_exit_tomb()
        # ===========================================================
        # COMPUTER CONTROL COMMANDS
        # ===========================================================
        if cmd == "computer_status":
            return self._cmd_computer_status()
        if cmd == "file_create":
            return self._cmd_file_create(req)
        if cmd == "file_read":
            return self._cmd_file_read(req)
        if cmd == "file_write":
            return self._cmd_file_write(req)
        if cmd == "file_delete":
            return self._cmd_file_delete(req)
        if cmd == "file_move":
            return self._cmd_file_move(req)
        if cmd == "file_copy":
            return self._cmd_file_copy(req)
        if cmd == "file_list":
            return self._cmd_file_list(req)
        if cmd == "file_organize":
            return self._cmd_file_organize(req)
        if cmd == "file_open":
            return self._cmd_file_open(req)
        if cmd == "folder_open":
            return self._cmd_folder_open(req)
        if cmd == "folder_create":
            return self._cmd_folder_create(req)
        if cmd == "app_open":
            return self._cmd_app_open(req)
        if cmd == "app_list":
            return self._cmd_app_list()
        if cmd == "app_close":
            return self._cmd_app_close(req)
        if cmd == "web_search":
            return self._cmd_web_search(req)
        if cmd == "web_open":
            return self._cmd_web_open(req)
        if cmd == "web_read":
            return self._cmd_web_read(req)
        if cmd == "web_summarize":
            return self._cmd_web_summarize(req)
        if cmd == "web_open_results":
            return self._cmd_web_open_results(req)
        if cmd == "web_sort":
            return self._cmd_web_sort(req)
        if cmd == "media_play":
            return self._cmd_media_play(req)
        if cmd == "media_pause":
            return self._cmd_media_pause()
        if cmd == "media_next":
            return self._cmd_media_next()
        if cmd == "media_previous":
            return self._cmd_media_previous()
        if cmd == "media_volume":
            return self._cmd_media_volume(req)
        if cmd == "create_document":
            return self._cmd_create_document(req)
        if cmd == "write_essay":
            return self._cmd_write_essay(req)
        # ===========================================================
        # ACCOUNT MANAGER COMMANDS
        # ===========================================================
        if cmd == "account_status":
            return self._cmd_account_status()
        if cmd == "account_add":
            return self._cmd_account_add(req)
        if cmd == "account_update":
            return self._cmd_account_update(req)
        if cmd == "account_delete":
            return self._cmd_account_delete(req)
        if cmd == "account_get":
            return self._cmd_account_get(req)
        if cmd == "account_list":
            return self._cmd_account_list(req)
        if cmd == "account_find":
            return self._cmd_account_find(req)
        if cmd == "account_login":
            return self._cmd_account_login(req)
        if cmd == "account_open_login":
            return self._cmd_account_open_login(req)
        if cmd == "account_credentials":
            return self._cmd_account_credentials(req)
        if cmd == "account_bills":
            return self._cmd_account_bills(req)
        if cmd == "account_mark_paid":
            return self._cmd_account_mark_paid(req)
        if cmd == "account_open_payment":
            return self._cmd_account_open_payment(req)
        if cmd == "account_export":
            return self._cmd_account_export()
        if cmd == "account_import":
            return self._cmd_account_import(req)
        if cmd == "vault_unlock":
            return self._cmd_vault_unlock(req)
        if cmd == "vault_lock":
            return self._cmd_vault_lock()
        if cmd == "vault_status":
            return self._cmd_vault_status()
        # ===========================================================
        # FORMS
        # ===========================================================
        if cmd == "form_list":
            return {"forms": list_forms()}
        if cmd == "form_get":
            return self._cmd_form_get(req)
        if cmd == "form_validate":
            return self._cmd_form_validate(req)
        if cmd == "form_submit":
            return self._cmd_form_submit(req)
        # ===========================================================
        # BIOMETRIC AUTH
        # ===========================================================
        if cmd == "biometric_status":
            return self.biometric_auth.get_status()
        if cmd == "biometric_enroll":
            return self._cmd_biometric_enroll(req)
        if cmd == "biometric_verify":
            return self._cmd_biometric_verify(req)
        if cmd == "biometric_unlock":
            return self._cmd_biometric_unlock(req)
        if cmd == "biometric_enable":
            return self.biometric_auth.enable()
        if cmd == "biometric_disable":
            return self.biometric_auth.disable()
        if cmd == "biometric_remove":
            return self.biometric_auth.remove_enrollment()
        # ===========================================================
        # SNAPSHOT MANAGER
        # ===========================================================
        if cmd == "snapshot_create":
            return self._cmd_snapshot_create(req)
        if cmd == "snapshot_list":
            return self.snapshot_manager.list_snapshots()
        if cmd == "snapshot_verify":
            return self._cmd_snapshot_verify(req)
        if cmd == "snapshot_verify_latest":
            return self.snapshot_manager.verify_latest()
        if cmd == "snapshot_restore":
            return self._cmd_snapshot_restore(req)
        if cmd == "snapshot_delete":
            return self._cmd_snapshot_delete(req)
        if cmd == "snapshot_status":
            return self.snapshot_manager.get_status()
        if cmd == "snapshot_retention":
            return self.snapshot_manager.apply_retention_policy()
        if cmd == "snapshot_detect_corruption":
            return self.snapshot_manager.detect_corruption()
        # ===========================================================
        # SELF-REPAIR
        # ===========================================================
        if cmd == "self_repair_status":
            return self.self_repair.get_status()
        if cmd == "self_repair_check":
            return self.self_repair.run_health_check()
        if cmd == "self_repair_auto":
            return self.self_repair.auto_repair()
        if cmd == "self_repair_failover":
            return self._cmd_self_repair_failover(req)
        if cmd == "self_repair_rebuild":
            return self.self_repair.rebuild_drive().to_dict()
        if cmd == "self_repair_sign_core":
            return self.self_repair.sign_core_files()
        if cmd == "self_repair_verify_core":
            return self.self_repair.verify_core_files()
        if cmd == "self_repair_alerts":
            return self.self_repair.get_alerts()
        if cmd == "self_repair_resolve_alert":
            return self._cmd_self_repair_resolve(req)
        # ===========================================================
        # DRIVE MONITOR
        # ===========================================================
        if cmd == "drive_report":
            return self.drive_monitor.deliver_report()
        if cmd == "drive_report_silent":
            return self.drive_monitor.generate_report().to_dict()
        if cmd == "drive_report_history":
            return self.drive_monitor.get_report_history()
        if cmd == "drive_monitor_status":
            return self.drive_monitor.get_status()
        # ===========================================================
        # SNAPSHOT DIFF VIEWER
        # ===========================================================
        if cmd == "snapshot_diff":
            return self._cmd_snapshot_diff(req)
        if cmd == "snapshot_diff_all":
            return self._cmd_snapshot_diff_all(req)
        # ===========================================================
        # SELF-REPAIR: CROSS-CHECK + DEGRADATION
        # ===========================================================
        if cmd == "self_repair_cross_check":
            return self.self_repair.cross_check()
        if cmd == "self_repair_degradation_status":
            return self.self_repair.get_degradation_status()
        if cmd == "self_repair_enter_degraded":
            return self._cmd_enter_degraded(req)
        if cmd == "self_repair_exit_degraded":
            return self.self_repair.exit_degraded_mode()
        if cmd == "self_repair_check_capability":
            return {"allowed": self.self_repair.check_capability(req.get("capability", ""))}
        # ===========================================================
        # COLD ARCHIVE
        # ===========================================================
        if cmd == "cold_archive_create":
            return self._cmd_cold_archive_create(req)
        if cmd == "cold_archive_list":
            return self.cold_archive.list_archives()
        if cmd == "cold_archive_restore":
            return self._cmd_cold_archive_restore(req)
        if cmd == "cold_archive_delete":
            return self._cmd_cold_archive_delete(req)
        if cmd == "cold_archive_status":
            return self.cold_archive.get_status()
        if cmd == "cold_archive_retention":
            return self.cold_archive.apply_retention()
        # ===========================================================
        # BOOT CHECK
        # ===========================================================
        if cmd == "boot_check":
            return self.boot_checker.check()
        if cmd == "boot_check_history":
            return self.boot_checker.get_boot_history()
        # ===========================================================
        # SCHEDULER
        # ===========================================================
        if cmd == "scheduler_status":
            return self.scheduler.get_status()
        if cmd == "scheduler_start":
            self.scheduler.start()
            return {"started": True}
        if cmd == "scheduler_stop":
            self.scheduler.stop()
            return {"stopped": True}
        if cmd == "scheduler_trigger":
            return self._cmd_scheduler_trigger(req)
        if cmd == "knowledge_auto_acquire":
            return self._auto_acquire_knowledge()
        # ===========================================================
        # BOOK OF ANUBIS
        # ===========================================================
        if cmd == "book_generate":
            return self.book.generate(force=req.get("force", False))
        if cmd == "book_status":
            return self.book.get_status()
        if cmd == "book_list_editions":
            return self.book.list_editions()
        if cmd == "book_read":
            return self._cmd_book_read(req)
        if cmd == "book_read_latest":
            return self.book.read_latest()
        if cmd == "book_seal_status":
            return self.book.get_seal_status()
        if cmd == "book_unseal":
            return self._cmd_book_unseal(req)
        if cmd == "book_reseal":
            return self.book.reseal()
        # ===========================================================
        # LOCAL FINE-TUNING
        # ===========================================================
        if cmd == "local_training_status":
            return self.local_finetuner.get_status() if self.local_finetuner else {"error": "not ready"}
        if cmd == "local_training_collect":
            return self._cmd_local_training_collect(req)
        if cmd == "local_training_generate":
            return self._cmd_local_training_generate(req)
        if cmd == "local_training_run":
            return self._cmd_local_training_run(req)
        if cmd == "local_training_pipeline":
            return self._cmd_local_training_pipeline(req)
        if cmd == "local_training_list":
            return self.local_finetuner.list_runs() if self.local_finetuner else {"error": "not ready"}
        if cmd == "local_training_cancel":
            return self.local_finetuner.cancel_run(req.get("run_id", "")) if self.local_finetuner else {"error": "not ready"}
        # ===========================================================
        # DREAM CYCLE
        # ===========================================================
        if cmd == "dream_status":
            return self.dream.get_status() if self.dream else {"error": "dream engine not ready"}
        if cmd == "dream_run":
            if not self.dream:
                return {"error": "dream engine not ready"}
            return self.dream.run_cycle().to_dict()
        if cmd == "dream_history":
            if not self.dream:
                return {"error": "dream engine not ready"}
            return {"history": self.dream.get_dream_history(limit=req.get("limit", 20))}
        if cmd == "dream_recommendations":
            if not self.dream:
                return {"error": "dream engine not ready"}
            recs = self.dream.get_recommendations(unacted_only=req.get("unacted_only", False))
            return {"recommendations": recs, "count": len(recs)}
        if cmd == "dream_mark_acted":
            if not self.dream:
                return {"error": "dream engine not ready"}
            return {"acted": self.dream.mark_recommendation_acted(req.get("rec_id", ""))}
        if cmd == "dream_gaps":
            if not self.dream:
                return {"error": "dream engine not ready"}
            return {"gaps": self.dream.get_identified_gaps()}
        # ===========================================================
        # VOICE INTERPRETER
        # ===========================================================
        if cmd == "voice_interpreter_status":
            if hasattr(self, 'sensory') and self.sensory and self.sensory.voice_interpreter:
                return self.sensory.voice_interpreter.get_status()
            return {"available": False, "reason": "voice interpreter not initialized"}
        if cmd == "voice_interpret":
            if hasattr(self, 'sensory') and self.sensory and self.sensory.voice_interpreter:
                text = req.get("text", "")
                return self.sensory.voice_interpreter.interpret_and_execute(text)
            return {"error": "voice interpreter not ready"}
        # ===========================================================
        # PHONE ADAPTER (physical Android phone via ADB)
        # ===========================================================
        if cmd == "phone_status":
            return self.phone.get_status()
        if cmd == "phone_system_status":
            return self.phone.get_system_status()
        if cmd == "phone_send_sms":
            return self.phone.send_sms(req.get("to", ""), req.get("body", ""))
        if cmd == "phone_receive_sms":
            return self.phone.receive_sms(limit=req.get("limit", 10))
        if cmd == "phone_sent_sms":
            return self.phone.get_sent_sms(limit=req.get("limit", 10))
        if cmd == "phone_make_call":
            return self.phone.make_call(req.get("number", ""))
        if cmd == "phone_answer_call":
            return self.phone.answer_call()
        if cmd == "phone_end_call":
            return self.phone.end_call()
        if cmd == "phone_call_history":
            return self.phone.get_call_history(limit=req.get("limit", 20))
        if cmd == "phone_get_number":
            return {"phone_number": self.phone.get_phone_number()}
        if cmd == "phone_start_polling":
            return self.phone.start_polling()
        if cmd == "phone_stop_polling":
            return self.phone.stop_polling()
        if cmd == "phone_wake_screen":
            return self.phone.wake_screen()
        if cmd == "phone_send_ussd":
            return self.phone.send_ussd(req.get("code", ""))
        if cmd == "phone_sms_log":
            return self.phone.get_sms_log(limit=req.get("limit", 50))
        if cmd == "phone_call_log":
            return self.phone.get_call_log_local(limit=req.get("limit", 50))
        # ===========================================================
        # MIXED MODEL STRATEGY — progressive weight replacement
        # ===========================================================
        if cmd == "mixed_model_status":
            return self._cmd_mixed_model_status()
        if cmd == "mixed_model_stage":
            return self._cmd_mixed_model_stage()
        if cmd == "mixed_model_generations":
            return self._cmd_mixed_model_generations()
        if cmd == "mixed_model_record_generation":
            return self._cmd_mixed_model_record_generation(req)
        if cmd == "mixed_model_update_progress":
            return self._cmd_mixed_model_update_progress(req)
        if cmd == "mixed_model_advance":
            return self._cmd_mixed_model_advance(req)
        if cmd == "mixed_model_teacher_dependency":
            return self._cmd_mixed_model_teacher_dependency()
        if cmd == "systems_status":
            return self._cmd_systems_status()
        # ===========================================================
        # SELF-MODIFICATION FRAMEWORK
        # ===========================================================
        if cmd == "self_modify_status":
            return self._cmd_self_modify_status()
        if cmd == "self_modify_propose":
            return self._cmd_self_modify_propose(req)
        if cmd == "self_modify_review":
            return self._cmd_self_modify_review(req)
        if cmd == "self_modify_approve":
            return self._cmd_self_modify_approve(req)
        if cmd == "self_modify_apply":
            return self._cmd_self_modify_apply(req)
        if cmd == "self_modify_rollback":
            return self._cmd_self_modify_rollback(req)
        if cmd == "self_modify_list":
            return self._cmd_self_modify_list(req)
        if cmd == "self_modify_get":
            return self._cmd_self_modify_get(req)
        if cmd == "delegate_status":
            return self._cmd_delegate_status()
        if cmd == "delegate":
            return self._cmd_delegate(req)
        if cmd == "delegate_list":
            return self._cmd_delegate_list()
        if cmd == "delegate_get":
            return self._cmd_delegate_get(req)
        if cmd == "security_audit":
            return self._cmd_security_audit()
        if cmd == "security_audit_status":
            return self._cmd_security_audit_status()
        if cmd == "constitutional_training_status":
            return self._cmd_constitutional_training_status()
        if cmd == "constitutional_training_export":
            return self._cmd_constitutional_training_export(req)
        if cmd == "train_auto_prepare":
            return self._cmd_train_auto_prepare(req)
        if cmd == "train_auto_submit":
            return self._cmd_train_auto_submit(req)
        if cmd == "train_auto_status":
            return self._cmd_train_auto_status(req)
        if cmd == "train_auto_cancel":
            return self._cmd_train_auto_cancel(req)
        if cmd == "train_auto_download":
            return self._cmd_train_auto_download(req)
        if cmd == "train_auto_deploy":
            return self._cmd_train_auto_deploy(req)
        if cmd == "train_auto_list":
            return self._cmd_train_auto_list()
        if cmd == "train_vast_search":
            return self._cmd_train_vast_search(req)
        if cmd == "train_vast_rent":
            return self._cmd_train_vast_rent(req)
        if cmd == "train_vast_monitor":
            return self._cmd_train_vast_monitor(req)
        if cmd == "train_vast_download":
            return self._cmd_train_vast_download(req)
        if cmd == "train_vast_destroy":
            return self._cmd_train_vast_destroy(req)
        if cmd == "train_vast_full":
            return self._cmd_train_vast_full(req)
        return {"error": f"unknown command: {cmd}"}

    def _cmd_status(self) -> dict:
        return {
            "daemon": "running",
            "model": MODEL_NAME,
            "model_present": self._model_health.get("model_present", False),
            "model_error": self._model_health.get("error"),
            "sandbox": self.sandbox.describe(),
            "skills_count": len(self.library.names()),
            "ledger_entries": self.ledger.length,
            "pid": os.getpid(),
        }

    def _cmd_skills(self) -> dict:
        skills = []
        for s in self.library.iter_current():
            skills.append({
                "name": s.name,
                "version": s.version,
                "description": s.description[:80],
                "artifact_hash": s.artifact_hash[:16],
                "model": s.provenance.model,
                "attempt": s.provenance.attempt,
            })
        return {"skills": skills, "count": len(skills)}

    def _cmd_ledger(self) -> dict:
        ok, msg = self.ledger.verify()
        return {
            "entries": self.ledger.length,
            "integrity_ok": ok,
            "integrity_msg": msg,
            "head": self.ledger.head[:24],
        }

    def _cmd_mission(self, req: dict) -> dict:
        task = req.get("task", "")
        skill_name = req.get("skill_name", "")
        approval = req.get("approval_token", "")
        if not task or not skill_name:
            return {"error": "task and skill_name required"}
        if approval != "creator-approved":
            return {"error": "Creator approval required for missions"}
        if self.model is None:
            return {"error": "model not available"}
        # Mission runs in a background thread; poll for status.
        mission_id = f"mission-{int(time.time())}-{skill_name}"
        self._missions[mission_id] = {"status": "running", "started": time.time()}
        t = threading.Thread(
            target=self._run_mission,
            args=(mission_id, task, skill_name),
            daemon=True,
        )
        t.start()
        return {"mission_id": mission_id, "status": "running"}

    def _run_mission(self, mission_id: str, task: str, skill_name: str) -> None:
        try:
            from anubis.loop import AnubisRuntime
            runtime = AnubisRuntime.create(ROOT, self.model, max_attempts=5, grounding=self.grounding)
            result = runtime.loop.run_mission(task, skill_name)
            self._missions[mission_id] = {
                "status": "complete" if result.success else "failed",
                "started": self._missions[mission_id]["started"],
                "completed": time.time(),
                "success": result.success,
                "attempts": result.attempt_count,
                "skill_name": skill_name,
                "denied_reason": result.denied_reason,
                "duration_s": round(result.duration_s, 1),
            }
            # Save to persistent memory
            self.memory.save_mission({
                "mission_id": mission_id,
                "task": task,
                "skill_name": skill_name,
                "success": result.success,
                "attempts": result.attempt_count,
                "duration_s": round(result.duration_s, 1),
                "denied_reason": result.denied_reason,
            })
        except Exception as exc:
            self._missions[mission_id] = {
                "status": "error",
                "started": self._missions[mission_id].get("started", time.time()),
                "error": str(exc),
            }
            self.memory.save_mission({
                "mission_id": mission_id,
                "task": task,
                "skill_name": skill_name,
                "success": False,
                "attempts": 0,
                "error": str(exc),
            })

    def _cmd_poll(self, req: dict) -> dict:
        mid = req.get("mission_id", "")
        if mid not in self._missions:
            return {"error": "unknown mission_id"}
        return {"mission_id": mid, **self._missions[mid]}

    def _cmd_chat(self, req: dict) -> dict:
        """DEMON conversational interface — talk to ANUBIS."""
        message = req.get("message", "")
        if not message:
            return {"error": "message required"}
        if self.model is None:
            return {"error": "model not available"}

        # Check if this is a mission request
        mission_intent = self._detect_mission_intent(message)
        if mission_intent:
            return self._handle_mission_from_chat(message, mission_intent, req)

        # Build context: system prompt + memory + skill library + conversation history
        skill_summary = self._skill_summary_for_chat()
        memory_summary = self.memory.context_summary()
        system = DEMON_SYSTEM + "\n" + skill_summary
        if memory_summary:
            system += "\n\nYour memory of past interactions:\n" + memory_summary

        # Retrieve governed knowledge context for this query
        try:
            grounding_result = self.grounding.ground_with_citations(
                message, max_docs=3, max_claims=10,
            )
            if not isinstance(grounding_result, dict):
                grounding_result = {"context": "", "citations": [], "claims_used": [], "claim_ids": []}
        except Exception as e:
            grounding_result = {"context": "", "citations": [], "claims_used": [], "claim_ids": [], "error": str(e)}
        knowledge_context = grounding_result.get("context", "")
        if knowledge_context:
            system += "\n\n" + knowledge_context

        messages = [{"role": "system", "content": system}]
        # Include recent conversation history for continuity
        messages.extend(self._conversation)
        messages.append({"role": "user", "content": message})

        try:
            completion = self.model.chat(
                messages,
                temperature=0.4,
                max_tokens=800,
                timeout=120.0,
            )
            response_text = completion.text or "(no response)"

            # Store in conversation history (in-memory + persistent)
            self._conversation.append({"role": "user", "content": message})
            self._conversation.append({"role": "assistant", "content": response_text})
            if len(self._conversation) > self._max_conversation:
                self._conversation = self._conversation[-self._max_conversation:]
            self.memory.save_message("user", message)
            self.memory.save_message("assistant", response_text)

            # Try to extract facts from the conversation
            self._try_extract_facts(message, response_text)

            return {
                "response": response_text,
                "model": completion.model,
                "tokens": completion.completion_tokens,
                "duration_s": round(completion.duration_s, 1),
                "knowledge_citations": grounding_result.get("citations", []),
                "claims_used": len(grounding_result.get("claims_used", [])),
                "knowledge_grounded": bool(knowledge_context),
            }
        except Exception as exc:
            return {"error": f"model error: {exc}"}

    def _detect_mission_intent(self, message: str) -> dict | None:
        """Detect if the user is requesting a coding mission.

        Returns a dict with task and skill_name if a mission is detected,
        or None if this is a regular conversation message.
        """
        import re
        msg_lower = message.lower()

        # Patterns that indicate a mission request
        mission_patterns = [
            r"write (?:me )?(?:a )?function (?:that|which) (.+)",
            r"write (?:me )?(?:a )?function (?:called|named) (\w+) (?:that|which) (.+)",
            r"create (?:a )?function (?:that|which) (.+)",
            r"build (?:a )?function (?:that|which) (.+)",
            r"make (?:a )?function (?:that|which) (.+)",
            r"write (?:me )?(?:a )?skill (?:that|which) (.+)",
            r"can you write (?:a )?function (?:that|which) (.+)",
            r"can you build (?:a )?function (?:that|which) (.+)",
            r"i need (?:a )?function (?:that|which) (.+)",
        ]

        for pattern in mission_patterns:
            m = re.search(pattern, msg_lower)
            if m:
                # Try to extract a function name
                name_match = re.search(
                    r"(?:called|named)\s+(\w+)", msg_lower
                )
                if name_match:
                    skill_name = name_match.group(1)
                    task = m.group(2) if m.lastindex >= 2 else m.group(1)
                else:
                    # Generate a name from the task
                    task = m.group(1) if m.lastindex == 1 else m.group(2)
                    # Try to derive a name from the task
                    words = re.findall(r"[a-z]+", task)
                    if words:
                        skill_name = "_".join(words[:3])
                    else:
                        skill_name = "custom_skill"

                # Clean up the task description
                task = task.strip().rstrip(".")
                # Capitalize for the model
                task = task[0].upper() + task[1:] if task else "Custom function"

                return {
                    "task": task,
                    "skill_name": skill_name,
                    "raw_message": message,
                }

        return None

    def _handle_mission_from_chat(
        self, message: str, intent: dict, req: dict
    ) -> dict:
        """Handle a mission request detected in chat.

        Asks the model to refine the task, then either launches the mission
        (if approval token is present) or asks for Creator approval.
        """
        task = intent["task"]
        skill_name = intent["skill_name"]
        approval = req.get("approval_token", "")

        # If no approval, ask for it
        if approval != "creator-approved":
            response = (
                f"I can write that for you. Here's what I'll do:\n\n"
                f"**Task**: {task}\n"
                f"**Skill name**: {skill_name}\n\n"
                f"I'll propose the code, run it in my sandbox to test it, "
                f"and promote it to my skill library if it passes.\n\n"
                f"This requires your approval. Click **Approve Mission** to proceed."
            )
            # Store in conversation
            self._conversation.append({"role": "user", "content": message})
            self._conversation.append({"role": "assistant", "content": response})
            if len(self._conversation) > self._max_conversation:
                self._conversation = self._conversation[-self._max_conversation:]
            self.memory.save_message("user", message)
            self.memory.save_message("assistant", response)

            return {
                "response": response,
                "model": MODEL_NAME,
                "tokens": 0,
                "duration_s": 0.1,
                "mission_request": True,
                "task": task,
                "skill_name": skill_name,
                "needs_approval": True,
            }

        # Approval given — launch the mission
        if self.model is None:
            return {"error": "model not available"}

        mission_id = f"mission-{int(time.time())}-{skill_name}"
        self._missions[mission_id] = {
            "status": "running",
            "started": time.time(),
            "task": task,
            "skill_name": skill_name,
        }
        t = threading.Thread(
            target=self._run_mission,
            args=(mission_id, task, skill_name),
            daemon=True,
        )
        t.start()

        response = (
            f"Mission launched. I'm working on: **{task}**\n\n"
            f"I'll propose code, test it in the sandbox, and promote it "
            f"if it passes. I'll let you know when I'm done.\n\n"
            f"Mission ID: {mission_id}"
        )
        self._conversation.append({"role": "user", "content": message})
        self._conversation.append({"role": "assistant", "content": response})
        if len(self._conversation) > self._max_conversation:
            self._conversation = self._conversation[-self._max_conversation:]
        self.memory.save_message("user", message)
        self.memory.save_message("assistant", response)

        return {
            "response": response,
            "model": MODEL_NAME,
            "tokens": 0,
            "duration_s": 0.1,
            "mission_id": mission_id,
            "mission_launched": True,
        }

    def _try_extract_facts(self, user_msg: str, response: str) -> None:
        """Simple pattern-based fact extraction from user messages."""
        msg_lower = user_msg.lower()
        # Name extraction
        if "my name is" in msg_lower:
            import re
            m = re.search(r"my name is (\w+)", msg_lower)
            if m:
                self.memory.set_fact("creator_name", m.group(1).capitalize())
        # Preference extraction
        if "i prefer" in msg_lower or "i like" in msg_lower:
            import re
            m = re.search(r"i (?:prefer|like) (.+)", msg_lower)
            if m:
                self.memory.update_preference("general", m.group(1)[:80])

    def _cmd_reset_chat(self) -> dict:
        """Clear conversation history (in-memory + persistent)."""
        count = len(self._conversation)
        self._conversation = []
        self.memory.clear_conversation()
        return {"cleared": count}

    def _skill_summary_for_chat(self) -> str:
        """Brief summary of current skills for the system prompt."""
        skills = list(self.library.iter_current())
        if not skills:
            return "You have no promoted skills yet."
        lines = ["Your current skill library:"]
        for s in skills:
            lines.append(f"  - {s.name} v{s.version}: {s.description[:60]}")
        lines.append(f"Total: {len(skills)} skills, {self.ledger.length} ledger entries.")
        return "\n".join(lines)

    def _cmd_tts(self, req: dict) -> dict:
        """Text-to-speech — convert text to audio."""
        text = req.get("text", "")
        if not text:
            return {"error": "text required"}
        try:
            import subprocess
            # Clean text for espeak
            clean = text
            for char in ["*", "_", "#", "`", "[", "]", "(", ")"]:
                clean = clean.replace(char, "")
            clean = clean.strip()
            if not clean:
                return {"ok": False, "error": "empty text after cleaning"}
            audio_path = f"/tmp/anubis_tts_{int(time.time())}.wav"
            subprocess.run(
                ["espeak-ng", "-v", "en", "-s", "150", "-w", audio_path, clean],
                capture_output=True, timeout=10, check=True,
            )
            return {"ok": True, "path": audio_path}
        except FileNotFoundError:
            return {"ok": False, "error": "espeak-ng not installed"}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def _cmd_stt(self, req: dict) -> dict:
        """Speech-to-text — record and transcribe."""
        timeout = req.get("timeout", 5.0)
        try:
            # Try using the voice helper
            import subprocess
            result = subprocess.run(
                ["python3", str(ROOT / "tools" / "voice_helper.py"), "stt", str(timeout)],
                capture_output=True, text=True, timeout=timeout + 30,
            )
            if result.returncode == 0:
                import json as _json
                data = _json.loads(result.stdout.strip())
                return {"ok": True, "text": data.get("text", "")}
            return {"ok": False, "error": result.stderr[:200]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    # ------------------------------------------------------------- projects

    def _cmd_list_projects(self) -> dict:
        """List all projects."""
        return {"projects": self.projects.list_projects()}

    def _cmd_get_project(self, req: dict) -> dict:
        """Get details of a specific project."""
        name = req.get("name", "")
        if not name:
            return {"error": "name required"}
        project = self.projects.load(name)
        if project is None:
            return {"error": f"project {name} not found"}
        return project.to_dict()

    def _cmd_plan_project(self, req: dict) -> dict:
        """Plan a new project using the model."""
        description = req.get("description", "")
        project_name = req.get("name", "")
        approval = req.get("approval_token", "")
        if not description or not project_name:
            return {"error": "description and name required"}
        if approval != "creator-approved":
            return {"error": "Creator approval required for project planning"}
        if self.model is None:
            return {"error": "model not available"}
        if self.projects.exists(project_name):
            return {"error": f"project {project_name} already exists"}
        try:
            from anubis.loop import AnubisRuntime
            runtime = AnubisRuntime.create(ROOT, self.model, max_attempts=5)
            project = runtime.loop.plan_project(description, project_name)
            self.projects.save(project)
            return {"project": project.to_dict(), "planned": True}
        except Exception as exc:
            return {"error": f"planning failed: {exc}"}

    def _cmd_run_project(self, req: dict) -> dict:
        """Execute a planned project."""
        name = req.get("name", "")
        approval = req.get("approval_token", "")
        if not name:
            return {"error": "name required"}
        if approval != "creator-approved":
            return {"error": "Creator approval required for project execution"}
        if self.model is None:
            return {"error": "model not available"}
        project = self.projects.load(name)
        if project is None:
            return {"error": f"project {name} not found"}
        if project.status == "running":
            return {"error": "project already running"}
        # Run in background
        project_id = f"project-{int(time.time())}-{name}"
        self._missions[project_id] = {
            "status": "running",
            "started": time.time(),
            "project_name": name,
            "type": "project",
        }
        t = threading.Thread(
            target=self._run_project,
            args=(project_id, name),
            daemon=True,
        )
        t.start()
        return {"project_id": project_id, "status": "running"}

    def _run_project(self, project_id: str, name: str) -> None:
        """Background project execution."""
        try:
            from anubis.loop import AnubisRuntime
            runtime = AnubisRuntime.create(ROOT, self.model, max_attempts=5)
            project = self.projects.load(name)
            if project is None:
                self._missions[project_id] = {
                    "status": "error",
                    "error": "project not found",
                }
                return
            project = runtime.loop.execute_project(project)
            self.projects.save(project)
            self._missions[project_id] = {
                "status": "complete" if project.status == "complete" else "failed",
                "started": self._missions[project_id]["started"],
                "completed": time.time(),
                "project_name": name,
                "type": "project",
                "project": project.to_dict(),
            }
            # Save to memory
            self.memory.save_mission({
                "mission_id": project_id,
                "task": project.description,
                "skill_name": name,
                "success": project.status == "complete",
                "attempts": len(project.steps),
                "type": "project",
            })
        except Exception as exc:
            self._missions[project_id] = {
                "status": "error",
                "started": self._missions[project_id].get("started", time.time()),
                "error": str(exc),
            }

    def _cmd_poll_project(self, req: dict) -> dict:
        """Poll project execution status."""
        pid = req.get("project_id", "")
        if pid not in self._missions:
            return {"error": "unknown project_id"}
        return {"project_id": pid, **self._missions[pid]}

    # ------------------------------------------------------------- tomb halls

    def _cmd_constitution(self) -> dict:
        """Hall of Architects — the constitutional framework."""
        from anubis.constitution import (
            Authority, ChangeClass, Verdict, IMMUTABLE_LAWS,
        )
        authorities = [
            {"name": a.name, "value": a.value, "description": {
                Authority.HARM_PREVENTION: "Protection from immediate serious harm",
                Authority.CONSTITUTIONAL: "System constitutional rules",
                Authority.PRIVACY_INTEGRITY: "User privacy and data integrity",
                Authority.INFORMED_AUTHORITY: "Informed user authority",
                Authority.RELIABILITY: "System reliability and recoverability",
                Authority.APPLICATION_GOALS: "Application goals",
                Authority.CONVENIENCE: "Convenience and style",
            }.get(a, "")}
            for a in Authority
        ]
        change_classes = [
            {"name": c.name, "value": c.value, "description": {
                ChangeClass.ROUTINE: "Reversible, preauthorized maintenance. Auto-allowed.",
                ChangeClass.SANDBOXED: "Creation or execution in a sandbox. Auto-allowed.",
                ChangeClass.PROMOTION: "Moving sandboxed artifact to live library. Requires passing evidence.",
                ChangeClass.CONSEQUENTIAL: "Touches identity, policy, missions. Requires Creator approval.",
                ChangeClass.MAIN_ENGINE: "Changes ANUBIS's model or architecture. Requires Court + Creator.",
            }.get(c, "")}
            for c in ChangeClass
        ]
        return {
            "authorities": authorities,
            "change_classes": change_classes,
            "immutable_laws": list(IMMUTABLE_LAWS),
            "verdicts": [v.name for v in Verdict],
        }

    def _cmd_ledger_entries(self, req: dict) -> dict:
        """Hall of Memory — browse ledger entries."""
        limit = int(req.get("limit", 20))
        offset = int(req.get("offset", 0))
        action_filter = req.get("action", "")
        entries = []
        all_entries = list(self.ledger)
        # Filter by action if requested
        if action_filter:
            all_entries = [e for e in all_entries if e.action == action_filter]
        # Apply offset and limit
        total = len(all_entries)
        for entry in all_entries[offset:offset + limit]:
            entries.append({
                "seq": entry.seq,
                "ts": entry.ts,
                "actor": entry.actor,
                "action": entry.action,
                "payload_summary": _summarize_payload(entry),
                "entry_hash": entry.entry_hash[:16],
            })
        # Get unique action types for filtering
        action_types = sorted(set(e.action for e in all_entries))
        return {
            "entries": entries,
            "total": total,
            "offset": offset,
            "limit": limit,
            "action_types": action_types,
        }

    def _cmd_skill_versions(self, req: dict) -> dict:
        """Hall of Evolution — skill version history."""
        skill_name = req.get("name", "")
        if skill_name:
            # Get all versions of a specific skill
            versions = []
            skill_dir = ROOT / "skills" / skill_name
            if skill_dir.exists():
                for vdir in sorted(skill_dir.iterdir()):
                    if vdir.is_dir() and vdir.name.startswith("v"):
                        manifest = vdir / "manifest.json"
                        if manifest.exists():
                            try:
                                import json as _json
                                data = _json.loads(manifest.read_text())
                                versions.append({
                                    "version": data.get("version", 0),
                                    "description": data.get("description", "")[:80],
                                    "artifact_hash": data.get("artifact_hash", "")[:16],
                                    "model": data.get("provenance", {}).get("model", "?"),
                                    "attempt": data.get("provenance", {}).get("attempt", 0),
                                    "created_at": data.get("provenance", {}).get("created_at", 0),
                                })
                            except Exception:
                                continue
            return {"skill": skill_name, "versions": versions}
        else:
            # Get version counts for all skills
            skills = []
            for s in self.library.iter_current():
                skill_dir = ROOT / "skills" / s.name
                version_count = 0
                if skill_dir.exists():
                    version_count = sum(
                        1 for d in skill_dir.iterdir()
                        if d.is_dir() and d.name.startswith("v")
                    )
                skills.append({
                    "name": s.name,
                    "current_version": s.version,
                    "total_versions": version_count,
                    "description": s.description[:60],
                    "model": s.provenance.model,
                })
            return {"skills": skills}

    def _cmd_mission_history(self) -> dict:
        """Hall of Creation — archive of all missions."""
        missions = self.memory.load_mission_history(50)
        return {"missions": missions, "total": len(missions)}

    def _cmd_genesis(self) -> dict:
        """Hall of Genesis — ANUBIS's first moments."""
        # Get the first few ledger entries
        all_entries = list(self.ledger)
        first_entries = []
        for entry in all_entries[:10]:
            first_entries.append({
                "seq": entry.seq,
                "action": entry.action,
                "ts": entry.ts,
                "payload_summary": _summarize_payload(entry),
            })
        # Get facts
        facts = self.memory.facts
        # Get skill library stats
        skills = list(self.library.iter_current())
        return {
            "first_entries": first_entries,
            "total_ledger_entries": self.ledger.length,
            "total_skills": len(skills),
            "total_conversations": facts.get("total_conversations", 0),
            "total_missions": facts.get("total_missions", 0),
            "successful_missions": facts.get("successful_missions", 0),
            "creator_name": facts.get("creator_name", ""),
            "first_seen": facts.get("first_seen", 0),
        }

    # ------------------------------------------------------- workspace tools

    def _cmd_fs_list(self, req: dict) -> dict:
        """List files in a directory."""
        path = req.get("path", str(ROOT))
        if not _is_path_safe(path):
            return {"error": "access denied: path outside allowed roots"}
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "path does not exist"}
            if not p.is_dir():
                return {"error": "not a directory"}
            entries = []
            for child in sorted(p.iterdir()):
                entries.append({
                    "name": child.name,
                    "is_dir": child.is_dir(),
                    "size": child.stat().st_size if child.is_file() else 0,
                })
            return {"path": str(p), "entries": entries}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_fs_read(self, req: dict) -> dict:
        """Read a file's contents."""
        path = req.get("path", "")
        if not path:
            return {"error": "path required"}
        if not _is_path_safe(path):
            return {"error": "access denied: path outside allowed roots"}
        try:
            p = Path(path)
            if not p.exists():
                return {"error": "file does not exist"}
            if not p.is_file():
                return {"error": "not a file"}
            if p.stat().st_size > 1024 * 1024:  # 1MB limit
                return {"error": "file too large (max 1MB)"}
            content = p.read_text(encoding="utf-8", errors="replace")
            return {"path": str(p), "content": content, "size": len(content)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_fs_write(self, req: dict) -> dict:
        """Write content to a file. Requires Creator approval."""
        path = req.get("path", "")
        content = req.get("content", "")
        approval = req.get("approval_token", "")
        if not path:
            return {"error": "path required"}
        if not _is_path_safe(path):
            return {"error": "access denied: path outside allowed roots"}
        if approval != "creator-approved":
            return {"error": "Creator approval required for file writes"}
        try:
            p = Path(path)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            self.ledger.append(
                "creator", "file.written",
                {"path": str(p), "size": len(content)},
            )
            return {"path": str(p), "written": True, "size": len(content)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_run_cmd(self, req: dict) -> dict:
        """Run a shell command. Requires Creator approval.

        This is the Creator's terminal — not ANUBIS's sandbox. ANUBIS
        generated code runs in the hardened sandbox; this is for the
        Creator to run their own commands from the desktop.
        """
        cmd = req.get("command", req.get("cmd", ""))
        approval = req.get("approval_token", "")
        if not cmd:
            return {"error": "cmd required"}
        if approval != "creator-approved":
            return {"error": "Creator approval required for terminal"}
        if len(cmd) > 500:
            return {"error": "command too long (max 500 chars)"}
        # Block dangerous commands
        dangerous = ["rm -rf /", "mkfs", "dd if=", ":(){", "fork bomb"]
        for d in dangerous:
            if d in cmd:
                return {"error": f"blocked dangerous command: {d}"}
        try:
            import subprocess
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=30, cwd=str(ROOT),
            )
            self.ledger.append(
                "creator", "terminal.command",
                {"cmd": cmd, "exit_code": result.returncode},
            )
            return {
                "cmd": cmd,
                "stdout": result.stdout[:8000],
                "stderr": result.stderr[:4000],
                "exit_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"error": "command timed out (30s)"}
        except Exception as exc:
            return {"error": str(exc)}

    # ----------------------------------------------------- knowledge base

    def _cmd_registry_stats(self) -> dict:
        return self.registry.stats()

    def _cmd_list_directors(self) -> dict:
        return {"directors": [d.to_dict() for d in self.registry.directors()]}

    def _cmd_list_specialties(self, req: dict) -> dict:
        director_id = req.get("director_id", "")
        if director_id:
            specs = self.registry.specialties_by_director(director_id)
        else:
            specs = self.registry.specialties()
        limit = int(req.get("limit", 50))
        return {"specialties": [s.to_dict() for s in specs[:limit]], "total": len(specs)}

    def _cmd_knowledge_stats(self) -> dict:
        return self.knowledge.stats()

    def _cmd_knowledge_search(self, req: dict) -> dict:
        query = req.get("query", "")
        if not query:
            return {"error": "query required"}
        docs = self.knowledge.retrieve(query, limit=int(req.get("limit", 5)))
        return {"results": [{"title": d.title, "excerpt": d.content[:200], "tier": d.trust_tier} for d in docs]}

    def _cmd_knowledge_ingest(self, req: dict) -> dict:
        approval = req.get("approval_token", "")
        title = req.get("title", "")
        content = req.get("content", "")
        specialty_id = req.get("specialty_id", "")
        if not title or not content:
            return {"error": "title and content required"}
        doc_id = self.knowledge.ingest_to_quarantine(
            title=title, content=content, specialty_id=specialty_id,
            license=req.get("license", ""),
        )
        if approval == "creator-approved":
            self.knowledge.promote_from_quarantine(doc_id)
        return {"doc_id": doc_id, "status": "promoted" if approval == "creator-approved" else "quarantined"}

    def _cmd_knowledge_promote(self, req: dict) -> dict:
        doc_id = req.get("doc_id", "")
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required"}
        if self.knowledge.promote_from_quarantine(doc_id):
            return {"doc_id": doc_id, "status": "promoted"}
        return {"error": "document not found in quarantine"}

    def _cmd_knowledge_ground(self, req: dict) -> dict:
        """Retrieve grounded knowledge context for a query."""
        query = req.get("query", "")
        if not query:
            return {"error": "query required"}
        result = self.grounding.ground_with_citations(
            query,
            max_docs=int(req.get("max_docs", 3)),
            max_claims=int(req.get("max_claims", 10)),
            specialty_id=req.get("specialty_id", ""),
        )
        return result

    def _cmd_claim_search(self, req: dict) -> dict:
        """Search the claim index for atomic claims."""
        query = req.get("query", "")
        if not query:
            return {"error": "query required"}
        claims = self.grounding.index.search(query, limit=int(req.get("limit", 20)))
        return {
            "results": [
                {
                    "claim_id": c.get("claim_id", ""),
                    "text": c.get("text", ""),
                    "type": c.get("claim_type", "fact"),
                    "confidence": c.get("confidence_adjusted", c.get("confidence", 0.8)),
                    "status": c.get("verification_status", "unverified"),
                    "doc_id": c.get("doc_id", ""),
                }
                for c in claims
            ],
            "count": len(claims),
        }

    def _cmd_grounding_stats(self, req: dict = None) -> dict:
        """Return grounding system statistics."""
        return self.grounding.stats()

    # --------------------------------------------------------- governance

    def _cmd_identity_stats(self) -> dict:
        return self.identity.stats()

    def _cmd_enroll_creator(self, req: dict) -> dict:
        display_name = req.get("display_name", "")
        passphrase = req.get("passphrase", "")
        return self.identity.enroll_creator(display_name, passphrase)

    def _cmd_court_stats(self) -> dict:
        return self.court.stats()

    def _cmd_court_submit(self, req: dict) -> dict:
        artifact_hash = req.get("artifact_hash", "")
        description = req.get("description", "")
        if not artifact_hash:
            return {"error": "artifact_hash required"}
        review_id = self.court.submit_for_review(artifact_hash, description)
        return {"review_id": review_id, "status": "submitted"}

    def _cmd_policy_stats(self) -> dict:
        return self.policy_engine.stats()

    def _cmd_capability_stats(self) -> dict:
        return self.capability_broker.stats()

    # ------------------------------------------------------------ system

    def _cmd_network_stats(self) -> dict:
        return self.network.stats()

    def _cmd_hardening_stats(self) -> dict:
        return self.hardening.stats()

    def _cmd_recovery_stats(self) -> dict:
        return self.recovery.stats()

    def _cmd_ab_stats(self) -> dict:
        return self.ab_images.stats()

    def _cmd_egyptology_lookup(self, req: dict) -> dict:
        sign = req.get("sign", "")
        word = req.get("word", "")
        if sign:
            return self.egyptology.lookup_sign(sign)
        if word:
            return self.egyptology.lookup_word(word)
        return {"error": "sign or word required"}

    def _cmd_egyptology_stats(self) -> dict:
        return self.egyptology.stats()

    def _cmd_purge_now(self) -> dict:
        record = self.purge.execute(ROOT)
        return record.to_dict()

    def _cmd_package_stats(self) -> dict:
        return self.packages.stats()

    def _cmd_financial_stats(self) -> dict:
        return self.financial.stats()

    # --- New module handlers ---

    def _cmd_queue_stats(self) -> dict:
        return self.mission_queue.stats()

    def _cmd_queue_add(self, req: dict) -> dict:
        skill_name = req.get("skill_name", "")
        task = req.get("task", "")
        if not skill_name or not task:
            return {"error": "skill_name and task required"}
        mid = self.mission_queue.add(skill_name, task)
        return {"mission_id": mid, "status": "queued"}

    def _cmd_queue_add_batch(self, req: dict) -> dict:
        missions = req.get("missions", [])
        if not missions:
            return {"error": "missions list required"}
        ids = self.mission_queue.add_batch(missions)
        return {"mission_ids": ids, "count": len(ids)}

    def _cmd_queue_process(self, req: dict) -> dict:
        """Process the next N pending missions (default 1)."""
        limit = req.get("limit", 1)
        if not self.model:
            self._check_model()
        if not self.model:
            return {"error": "model not available"}
        from anubis.loop import SelfDevelopmentLoop
        loop = SelfDevelopmentLoop(
            self.model, self.library, self.ledger, self.sandbox, max_attempts=3,
        )
        existing = set(self.library.names())
        results = []
        for _ in range(limit):
            mission = self.mission_queue.next_pending()
            if mission is None:
                break
            if mission.skill_name in existing:
                self.mission_queue.mark_skipped(mission.mission_id)
                results.append({"skill": mission.skill_name, "status": "skipped"})
                continue
            self.mission_queue.mark_running(mission.mission_id)
            result = loop.run_mission(mission.task, mission.skill_name)
            if result.success:
                self.mission_queue.mark_completed(mission.mission_id, f"promoted v{result.skill.version}")
                existing.add(mission.skill_name)
                results.append({"skill": mission.skill_name, "status": "promoted", "version": result.skill.version})
            else:
                self.mission_queue.mark_failed(mission.mission_id, result.denied_reason or "failed")
                results.append({"skill": mission.skill_name, "status": "failed", "error": result.denied_reason})
        return {"results": results, "processed": len(results)}

    def _cmd_queue_list(self) -> dict:
        return {"missions": [
            {"mission_id": m.mission_id, "skill_name": m.skill_name,
             "task": m.task, "status": m.status, "result": m.result, "error": m.error}
            for m in self.mission_queue.all_missions()
        ]}

    def _cmd_orchestrate(self, req: dict) -> dict:
        query = req.get("query", "")
        if not query:
            return {"error": "query required"}
        max_d = req.get("max_directors", 3)
        result = self.orchestrator.orchestrate(query, max_directors=max_d)
        return result.to_dict()

    def _cmd_knowledge_propose(self, req: dict) -> dict:
        specialty_id = req.get("specialty_id", "")
        title = req.get("title", "")
        content = req.get("content", "")
        if not specialty_id or not title or not content:
            return {"error": "specialty_id, title, and content required"}
        proposal = self.knowledge_updater.propose(specialty_id, title, content)
        return {
            "proposal_id": proposal.proposal_id,
            "status": proposal.status,
            "claims_extracted": proposal.claims_extracted,
            "claims_verified": proposal.claims_verified,
            "rejection_reason": proposal.rejection_reason,
        }

    def _cmd_knowledge_approve(self, req: dict) -> dict:
        proposal_id = req.get("proposal_id", "")
        ok = self.knowledge_updater.approve(proposal_id)
        return {"approved": ok}

    def _cmd_knowledge_promote_proposal(self, req: dict) -> dict:
        proposal_id = req.get("proposal_id", "")
        result = self.knowledge_updater.promote(proposal_id)
        return result

    def _cmd_knowledge_updater_stats(self) -> dict:
        return self.knowledge_updater.stats()

    def _cmd_backup_create(self, req: dict) -> dict:
        label = req.get("label", "")
        return self.backup.create_backup(label=label)

    def _cmd_backup_list(self) -> dict:
        return {"backups": self.backup.list_backups()}

    def _cmd_backup_restore(self, req: dict) -> dict:
        backup_name = req.get("backup_name", "")
        return self.backup.restore_backup(backup_name)

    def _cmd_voice_toggle_out(self) -> dict:
        enabled = self.voice_out.toggle()
        return {"voice_out": enabled, "available": self.voice_out.is_available()}

    def _cmd_voice_toggle_in(self) -> dict:
        enabled = self.voice_in.toggle()
        return {"voice_in": enabled, "available": self.voice_in.is_available()}

    def _cmd_voice_speak(self, req: dict) -> dict:
        text = req.get("text", "")
        if not text:
            return {"error": "text required"}
        ok = self.voice_out.speak(text)
        return {"spoken": ok}

    def _cmd_voice_status(self) -> dict:
        return {
            "voice_out_enabled": self.voice_out.enabled,
            "voice_out_available": self.voice_out.is_available(),
            "voice_in_enabled": self.voice_in.enabled,
            "voice_in_available": self.voice_in.is_available(),
        }

    def _cmd_docs_generate(self) -> dict:
        files = self.doc_gen.generate_all(ROOT / "docs")
        return {"generated": files}

    # -------------------------------------------------- memory commands (Phase A)

    def _cmd_memory_stats(self) -> dict:
        """Return memory statistics — entry counts, tier sizes, access patterns."""
        return self.memory.stats()

    def _cmd_memory_recall(self, req: dict) -> dict:
        """Semantic recall of past context.

        Request: {"query": "what did we discuss about grants?", "limit": 5}
        Returns relevant past conversation and long-term memory entries.
        """
        query = req.get("query", "")
        if not query:
            return {"error": "missing 'query' field"}
        limit = req.get("limit", 5)
        results = self.memory.recall(query, limit=limit)
        return {"query": query, "results": results, "count": len(results)}

    def _cmd_memory_purge(self, req: dict) -> dict:
        """Archive old conversation entries to the long-term tier.

        Request: {"archive_days": 30}
        Entries older than archive_days are summarized and moved to
        long_term/ with a full audit trail. Nothing is silently deleted.
        """
        archive_days = req.get("archive_days", 30)
        result = self.memory.purge(archive_days=archive_days)
        return {"purge_result": result, "archive_days": archive_days}

    def _cmd_memory_purge_log(self, req: dict) -> dict:
        """View the purge audit log.

        Request: {"limit": 50}
        Returns recent purge/archival actions for audit review.
        """
        limit = req.get("limit", 50)
        log = self.memory.load_purge_log(limit=limit)
        return {"log": log, "count": len(log)}

    # -------------------------------------------------- cloud sync commands (Phase B)

    def _cmd_cloud_sync_status(self) -> dict:
        """Return cloud sync configuration status (no secrets)."""
        from anubis.cloud_sync import CloudSync
        sync = CloudSync(root=ROOT)
        return sync.status()

    def _cmd_cloud_sync(self, req: dict) -> dict:
        """Sync a directory to iDrive E2 (Creator-approved).

        Request: {"directory": "skills", "max_files": 100}
        Only warm and cold paths are synced. Hot paths are refused.
        """
        from anubis.cloud_sync import CloudSync
        sync = CloudSync(root=ROOT)
        if not sync.is_configured:
            return {"error": "cloud sync not configured. Set config/cloud_credentials.json"}
        directory = req.get("directory", "skills")
        max_files = req.get("max_files", 100)
        local_dir = ROOT / directory
        if not local_dir.exists():
            return {"error": f"directory not found: {directory}"}
        result = sync.sync_directory(local_dir, prefix=directory, max_files=max_files)
        return {
            "ok": result.ok,
            "uploaded": result.uploaded,
            "skipped": result.skipped,
            "errors": result.errors,
            "bytes_transferred": result.bytes_transferred,
            "duration_s": round(result.duration_s, 2),
        }

    def _cmd_cloud_sync_upload(self, req: dict) -> dict:
        """Upload a single file to iDrive E2 (Creator-approved).

        Request: {"path": "skills/checksum_v1.py"}
        """
        from anubis.cloud_sync import CloudSync
        sync = CloudSync(root=ROOT)
        if not sync.is_configured:
            return {"error": "cloud sync not configured"}
        file_path = req.get("path", "")
        if not file_path:
            return {"error": "missing 'path' field"}
        local_path = ROOT / file_path
        result = sync.upload_file(local_path)
        return result

    def _cmd_cloud_sync_download(self, req: dict) -> dict:
        """Download a file from iDrive E2 (Creator-approved).

        Request: {"key": "skills/checksum_v1.py", "path": "skills/checksum_v1.py"}
        """
        from anubis.cloud_sync import CloudSync
        sync = CloudSync(root=ROOT)
        if not sync.is_configured:
            return {"error": "cloud sync not configured"}
        key = req.get("key", "")
        local_path = req.get("path", key)
        if not key:
            return {"error": "missing 'key' field"}
        result = sync.download_file(key, ROOT / local_path)
        return result

    def _cmd_cloud_sync_list(self, req: dict) -> dict:
        """List objects in iDrive E2 bucket.

        Request: {"prefix": "skills/"}
        """
        from anubis.cloud_sync import CloudSync
        sync = CloudSync(root=ROOT)
        if not sync.is_configured:
            return {"error": "cloud sync not configured"}
        prefix = req.get("prefix", "")
        objects = sync.list_objects(prefix=prefix)
        return {"objects": objects, "count": len(objects)}

    # -------------------------------------------------- gateway commands (Phase B)

    def _cmd_gateway_status(self) -> dict:
        """Return external gateway status (policy, rate limits, no secrets)."""
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        return gw.status()

    def _cmd_gateway_fetch(self, req: dict) -> dict:
        """Fetch a URL through the policy-gated gateway (Creator-approved).

        Request: {"url": "https://grants.gov/search", "purpose": "...", "approved": true}
        """
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        url = req.get("url", "")
        if not url:
            return {"error": "missing 'url' field"}
        purpose = req.get("purpose", "")
        approved = req.get("approved", False)
        resp = gw.fetch(url, purpose=purpose, creator_approved=approved)
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "body": resp.body[:5000] if resp.body else "",
            "url": resp.url,
            "error": resp.error,
            "refused_reason": resp.refused_reason,
            "duration_s": round(resp.duration_s, 3),
            "logged": resp.logged,
        }

    def _cmd_gateway_search(self, req: dict) -> dict:
        """Search the web through the policy-gated gateway (Creator-approved).

        Request: {"query": "AI grants 2025", "approved": true}
        """
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        query = req.get("query", "")
        if not query:
            return {"error": "missing 'query' field"}
        approved = req.get("approved", False)
        resp = gw.search(query, creator_approved=approved)
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "body": resp.body[:5000] if resp.body else "",
            "error": resp.error,
            "refused_reason": resp.refused_reason,
            "duration_s": round(resp.duration_s, 3),
            "logged": resp.logged,
        }

    def _cmd_gateway_add_domain(self, req: dict) -> dict:
        """Add a domain to the gateway whitelist (Creator-approved).

        Request: {"domain": "example.com"}
        """
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        domain = req.get("domain", "")
        if not domain:
            return {"error": "missing 'domain' field"}
        gw.add_domain(domain)
        return {"ok": True, "domain": domain, "added": True}

    def _cmd_gateway_remove_domain(self, req: dict) -> dict:
        """Remove a domain from the gateway whitelist (Creator-approved).

        Request: {"domain": "example.com"}
        """
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        domain = req.get("domain", "")
        if not domain:
            return {"error": "missing 'domain' field"}
        gw.remove_domain(domain)
        return {"ok": True, "domain": domain, "removed": True}

    # -------------------------------------------------- cloud teacher (Phase C)

    def _cmd_cloud_model_status(self) -> dict:
        """Return cloud teacher adapter status (providers, no secrets)."""
        from anubis.cloud_model import CloudModelAdapter
        adapter = CloudModelAdapter(ledger=self.ledger)
        return adapter.status()

    def _cmd_cloud_model_chat(self, req: dict) -> dict:
        """Chat with the cloud teacher (Gemini → Groq → local fallback).

        Request: {"message": "explain this code", "system": "you are..."}
        The privacy gate automatically falls back to local for sensitive data.
        """
        from anubis.cloud_model import CloudModelAdapter
        adapter = CloudModelAdapter(ledger=self.ledger)
        message = req.get("message", "")
        if not message:
            return {"error": "missing 'message' field"}
        system = req.get("system", "")
        temperature = req.get("temperature", 0.4)
        max_tokens = req.get("max_tokens", 800)
        try:
            completion = adapter.generate(
                message,
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return {
                "response": completion.text,
                "model": completion.model,
                "tokens": completion.completion_tokens,
                "duration_s": round(completion.duration_s, 2),
            }
        except Exception as exc:
            return {"error": str(exc)}

    # -------------------------------------------------- Lambda commands (Phase C)

    def _cmd_lambda_status(self) -> dict:
        """Return Lambda adapter status (GPUs, jobs, no secrets)."""
        from anubis.cloud_training import LambdaAdapter
        adapter = LambdaAdapter(ledger=self.ledger)
        return adapter.status()

    def _cmd_lambda_cost_preview(self, req: dict) -> dict:
        """Generate a cost preview for a Lambda job (no submission).

        Request: {"name": "test_run", "job_type": "testing",
                  "gpu_type": "nvidia_a10", "num_gpus": 1, "runtime_hours": 2.0,
                  "command": "python test.py"}
        """
        from anubis.cloud_training import LambdaAdapter, JobSpec
        adapter = LambdaAdapter(ledger=self.ledger)
        spec = JobSpec(
            name=req.get("name", "unnamed"),
            job_type=req.get("job_type", "testing"),
            gpu_type=req.get("gpu_type", "nvidia_a10"),
            num_gpus=req.get("num_gpus", 1),
            runtime_hours=req.get("runtime_hours", 1.0),
            command=req.get("command", ""),
            description=req.get("description", ""),
        )
        return adapter.cost_preview(spec)

    def _cmd_lambda_submit(self, req: dict) -> dict:
        """Submit a job to Lambda (Creator-approved).

        Request: {"name": "...", "job_type": "testing", "approved": true,
                  "gpu_type": "...", "command": "...",
                  "artifact_hash": "...", "approved_artifact_hash": "..."}
        Training jobs require artifact hash match (MAIN_ENGINE).
        """
        from anubis.cloud_training import LambdaAdapter, JobSpec
        adapter = LambdaAdapter(ledger=self.ledger)
        spec = JobSpec(
            name=req.get("name", "unnamed"),
            job_type=req.get("job_type", "testing"),
            gpu_type=req.get("gpu_type", "nvidia_a10"),
            num_gpus=req.get("num_gpus", 1),
            runtime_hours=req.get("runtime_hours", 1.0),
            command=req.get("command", ""),
            description=req.get("description", ""),
        )
        approved = req.get("approved", False)
        artifact_hash = req.get("artifact_hash")
        approved_hash = req.get("approved_artifact_hash")
        return adapter.submit_job(
            spec, creator_approved=approved,
            artifact_hash=artifact_hash,
            approved_artifact_hash=approved_hash,
        )

    def _cmd_lambda_job_status(self, req: dict) -> dict:
        """Check status of a Lambda job.

        Request: {"job_id": "lambda_..."}
        """
        from anubis.cloud_training import LambdaAdapter
        adapter = LambdaAdapter(ledger=self.ledger)
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "missing 'job_id' field"}
        return adapter.job_status(job_id)

    def _cmd_lambda_list_jobs(self) -> dict:
        """List all Lambda jobs."""
        from anubis.cloud_training import LambdaAdapter
        adapter = LambdaAdapter(ledger=self.ledger)
        jobs = adapter.list_jobs()
        return {"jobs": jobs, "count": len(jobs)}

    def _cmd_lambda_cancel(self, req: dict) -> dict:
        """Cancel a Lambda job.

        Request: {"job_id": "lambda_..."}
        """
        from anubis.cloud_training import LambdaAdapter
        adapter = LambdaAdapter(ledger=self.ledger)
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "missing 'job_id' field"}
        return adapter.cancel_job(job_id)

    # -------------------------------------------------- prospects commands (Phase D)

    def _cmd_prospects_status(self) -> dict:
        """Return prospects system status."""
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        return system.status()

    def _cmd_prospects_search(self, req: dict) -> dict:
        """Search for funding opportunities through the gateway.

        Request: {"query": "AI grants 2025", "approved": true}
        """
        from anubis.prospects import ProspectsSystem
        from anubis.external_gateway import ExternalGateway
        gw = ExternalGateway(ledger=self.ledger)
        system = ProspectsSystem(ledger=self.ledger, gateway=gw)
        query = req.get("query", "")
        if not query:
            return {"error": "missing 'query' field"}
        approved = req.get("approved", False)
        return system.search_opportunities(query, creator_approved=approved)

    def _cmd_prospects_create(self, req: dict) -> dict:
        """Create a new prospect proposal (stored as pending).

        Request: {"source": "grants.gov", "title": "...", "description": "...",
                  "estimated_return": 50000, "deadline": "2025-12-31", ...}
        """
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        return system.create_prospect(
            source=req.get("source", ""),
            title=req.get("title", ""),
            description=req.get("description", ""),
            source_url=req.get("source_url", ""),
            opportunity_type=req.get("opportunity_type", ""),
            eligibility=req.get("eligibility", ""),
            estimated_effort_hours=req.get("estimated_effort_hours", 0.0),
            estimated_cost=req.get("estimated_cost", 0.0),
            estimated_return=req.get("estimated_return", 0.0),
            deadline=req.get("deadline", ""),
            feasibility_score=req.get("feasibility_score", 0.0),
            confidence_score=req.get("confidence_score", 0.0),
            risks=req.get("risks", []),
            evidence=req.get("evidence", []),
            citations=req.get("citations", []),
            required_creator_actions=req.get("required_creator_actions", []),
            notes=req.get("notes", ""),
        )

    def _cmd_prospects_evaluate(self, req: dict) -> dict:
        """Evaluate a prospect for legitimacy and feasibility.

        Request: {"prospect_id": "prospect_..."}
        """
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        pid = req.get("prospect_id", "")
        if not pid:
            return {"error": "missing 'prospect_id' field"}
        return system.evaluate_prospect(pid)

    def _cmd_prospects_approve(self, req: dict) -> dict:
        """Approve a prospect (Creator action).

        Request: {"prospect_id": "prospect_..."}
        """
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        pid = req.get("prospect_id", "")
        if not pid:
            return {"error": "missing 'prospect_id' field"}
        return system.approve_prospect(pid)

    def _cmd_prospects_reject(self, req: dict) -> dict:
        """Reject a prospect (Creator action).

        Request: {"prospect_id": "prospect_..."}
        """
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        pid = req.get("prospect_id", "")
        if not pid:
            return {"error": "missing 'prospect_id' field"}
        return system.reject_prospect(pid)

    def _cmd_prospects_list_pending(self) -> dict:
        """List pending prospects for Creator review."""
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        return system.list_pending()

    def _cmd_prospects_list_approved(self) -> dict:
        """List approved prospects."""
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        return system.list_approved()

    def _cmd_prospects_stats(self) -> dict:
        """Return prospect statistics."""
        from anubis.prospects import ProspectsSystem
        system = ProspectsSystem(ledger=self.ledger)
        return system.stats()

    # --------------------------------------------------- vector index

    def _cmd_vector_index_stats(self) -> dict:
        """Return vector index statistics."""
        from anubis.vector_index import VectorIndex
        idx_path = Path("memory/vector_index.json")
        if not idx_path.exists():
            return {"count": 0, "exists": False}
        idx = VectorIndex.load(idx_path)
        return {**idx.stats(), "exists": True}

    def _cmd_vector_index_rebuild(self) -> dict:
        """Rebuild the vector index from memory embeddings."""
        from anubis.vector_index import VectorIndex, VectorEntry
        mem = Memory(MEMORY_DIR)
        mem._load_embeddings()
        idx = VectorIndex(dim=768)
        entries = []
        for eid, emb in mem._embeddings.items():
            meta = mem._embed_meta.get(eid, {})
            entries.append(VectorEntry(
                id=eid,
                vector=emb,
                metadata=meta,
            ))
        count = idx.insert_batch(entries)
        idx_path = Path("memory/vector_index.json")
        idx.save(idx_path)
        return {"inserted": count, "total": len(idx)}

    # --------------------------------------------------- reranker

    def _cmd_rerank(self, req: dict) -> dict:
        """Rerank candidates using local or hybrid reranker."""
        from anubis.reranker import rerank
        query = req.get("query", "")
        candidates = req.get("candidates", [])
        top_k = req.get("top_k", 5)
        strategy = req.get("strategy", "local")
        if not query or not candidates:
            return {"error": "query and candidates required"}
        results = rerank(query, candidates, top_k=top_k, strategy=strategy)
        return {
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "original_rank": r.original_rank,
                    "reranked_rank": r.reranked_rank,
                    "content": r.content[:200],
                }
                for r in results
            ],
        }

    # --------------------------------------------------- auto-git

    def _cmd_autogit_status(self) -> dict:
        """Return auto-git status."""
        from anubis.auto_git import AutoGit
        git = AutoGit(".")
        return git.status()

    def _cmd_autogit_commit(self, req: dict) -> dict:
        """Auto-commit changes with semantic versioning."""
        from anubis.auto_git import AutoGit
        git = AutoGit(".")
        creator_approved = req.get("creator_approved", False)
        message = req.get("message")
        result = git.auto_commit(
            creator_approved=creator_approved,
            message=message,
        )
        return {
            "ok": result.ok,
            "version": result.version,
            "commit_hash": result.commit_hash,
            "files_changed": result.files_changed,
            "error": result.error,
        }

    # --------------------------------------------------- memory rebuild

    def _cmd_memory_rebuild_index(self) -> dict:
        """Rebuild memory embedding index after purge."""
        mem = Memory(MEMORY_DIR)
        return mem.rebuild_index()

    # --------------------------------------------------- distillation

    def _cmd_distillation_stats(self) -> dict:
        """Return distillation queue statistics."""
        from anubis.distillation import KnowledgeDistiller
        distiller = KnowledgeDistiller(
            queue_path=Path("memory/distillation_queue.jsonl"),
        )
        return distiller.stats()

    def _cmd_distillation_export(self, req: dict) -> dict:
        """Export training pairs to a dataset file."""
        from anubis.distillation import KnowledgeDistiller
        distiller = KnowledgeDistiller(
            queue_path=Path("memory/distillation_queue.jsonl"),
        )
        output_path = req.get("output_path", "training/distillation_dataset.jsonl")
        category = req.get("category")
        min_quality = req.get("min_quality", 0.2)
        return distiller.export_training_data(
            output_path, category=category, min_quality=min_quality,
        )

    # --------------------------------------------------- evaluation

    def _cmd_evaluation_stats(self) -> dict:
        """Return evaluation harness statistics."""
        from anubis.evaluation import ModelEvaluator
        evaluator = ModelEvaluator()
        return evaluator.stats()

    def _cmd_evaluation_benchmark(self, req: dict) -> dict:
        """Run a quick benchmark (requires a running model)."""
        from anubis.evaluation import ModelEvaluator
        from anubis.model import OllamaAdapter
        evaluator = ModelEvaluator()
        model = OllamaAdapter(MODEL_NAME)
        max_tasks = req.get("max_tasks", 5)
        result = evaluator.evaluate(model, model_name=MODEL_NAME, max_tasks=max_tasks)
        return result.to_dict()

    # --------------------------------------------------- training orchestrator

    def _cmd_training_prepare(self, req: dict) -> dict:
        """Prepare a training plan for Creator approval."""
        from anubis.training_orchestrator import TrainingOrchestrator
        from anubis.unsloth_adapter import TrainingConfig
        orch = TrainingOrchestrator(output_dir="training")
        config = TrainingConfig(
            model_name=req.get("model_name", MODEL_NAME),
            epochs=req.get("epochs", 3),
            batch_size=req.get("batch_size", 2),
        )
        plan = orch.prepare_training_plan(config)
        return plan.to_dict()

    def _cmd_training_approve(self, req: dict) -> dict:
        """Approve a training plan."""
        from anubis.training_orchestrator import TrainingOrchestrator
        orch = TrainingOrchestrator(output_dir="training")
        plan_id = req.get("plan_id", "")
        return orch.approve_plan(plan_id)

    def _cmd_training_status(self) -> dict:
        """Return training orchestrator status."""
        from anubis.training_orchestrator import TrainingOrchestrator
        orch = TrainingOrchestrator(output_dir="training")
        return orch.status()

    def _cmd_training_list_plans(self) -> dict:
        """List all training plans."""
        from anubis.training_orchestrator import TrainingOrchestrator
        orch = TrainingOrchestrator(output_dir="training")
        return {"plans": orch.list_plans()}

    # --------------------------------------------------- A/B drive

    def _cmd_ab_drive_status(self) -> dict:
        """Return A/B drive status."""
        from anubis.ab_drive import ABDriveManager
        mgr = ABDriveManager(state_path="config/ab_drive_state.json")
        return mgr.status()

    def _cmd_ab_drive_stage(self, req: dict) -> dict:
        """Stage a new version on the A/B drive."""
        from anubis.ab_drive import ABDriveManager
        mgr = ABDriveManager(state_path="config/ab_drive_state.json")
        version = req.get("version", "")
        if not version:
            return {"error": "version required"}
        return mgr.stage_update(version)

    def _cmd_ab_drive_promote(self) -> dict:
        """Promote staging drive to active."""
        from anubis.ab_drive import ABDriveManager
        mgr = ABDriveManager(state_path="config/ab_drive_state.json")
        return mgr.promote()

    def _cmd_ab_drive_rollback(self, req: dict) -> dict:
        """Rollback to previous active drive."""
        from anubis.ab_drive import ABDriveManager
        mgr = ABDriveManager(state_path="config/ab_drive_state.json")
        reason = req.get("reason", "manual rollback")
        return mgr.rollback(reason)

    # --------------------------------------------------- librarian

    def _cmd_librarian_scan(self) -> dict:
        """Scan codebase and build dependency index."""
        from anubis.librarian import Librarian
        lib = Librarian(root=".", index_path="config/dependency_index.json")
        return lib.scan()

    def _cmd_librarian_status(self) -> dict:
        """Return librarian index statistics."""
        from anubis.librarian import Librarian
        lib = Librarian(root=".", index_path="config/dependency_index.json")
        return lib.stats()

    def _cmd_librarian_impact(self, req: dict) -> dict:
        """Analyze impact of removing/changing a module."""
        from anubis.librarian import Librarian
        lib = Librarian(root=".", index_path="config/dependency_index.json")
        module = req.get("module", "")
        if not module:
            return {"error": "module required"}
        return lib.check_compatibility(module)

    # --------------------------------------------------- custom embeddings

    def _cmd_embeddings_status(self) -> dict:
        """Return custom embedding model status."""
        emb_path = Path("memory/custom_embed_model.json")
        if not emb_path.exists():
            return {
                "configured": False,
                "replaces": "nomic-embed-text",
                "note": "Run embeddings_train to create a custom model",
            }
        from anubis.custom_embeddings import EmbeddingModel
        model = EmbeddingModel.load(emb_path)
        from anubis.custom_embeddings import CustomEmbeddingAdapter
        adapter = CustomEmbeddingAdapter(model)
        return adapter.status()

    def _cmd_embeddings_train(self, req: dict) -> dict:
        """Train a custom embedding model on the knowledge library."""
        from anubis.custom_embeddings import EmbeddingTrainer
        from anubis.knowledge import KnowledgeBase
        from anubis.registry import Registry
        dimensions = req.get("dimensions", 384)
        trainer = EmbeddingTrainer(dimensions=dimensions)
        # Load knowledge documents
        registry = Registry(REGISTRY_DIR)
        kb = KnowledgeBase(KNOWLEDGE_DIR, registry)
        docs = kb.library_documents()
        if not docs:
            return {"error": "no knowledge documents found"}
        documents = [d.content for d in docs]
        model = trainer.train(documents, model_name="anubis-embed-v1")
        save_result = model.save(Path("memory/custom_embed_model.json"))
        return {
            "trained": True,
            "documents": len(documents),
            "vocab_size": len(model.vocabulary),
            "dimensions": model.dimensions,
            "saved": save_result,
        }

    def _cmd_embeddings_activate(self, req: dict) -> dict:
        """Activate or deactivate the custom embedding model.

        When activated, ANUBIS uses his own embedding model instead of
        nomic-embed-text via Ollama. This removes a key external dependency.
        """
        import anubis.semantic as sem
        activate = req.get("activate", True)
        sem.PREFER_CUSTOM_EMBED = bool(activate)
        # Clear the cache so it reloads
        sem._custom_embed_cache = None
        return {
            "activated": bool(activate),
            "message": "Custom embeddings activated. Ollama no longer needed for embeddings." if activate
                       else "Custom embeddings deactivated. Using Ollama/nomic-embed-text.",
        }

    def _cmd_embeddings_evaluate(self) -> dict:
        """Evaluate the custom embedding model's retrieval quality."""
        from pathlib import Path
        emb_path = Path("memory/custom_embed_model.json")
        if not emb_path.exists():
            return {"error": "No custom model trained. Run embeddings_train first."}
        from anubis.custom_embeddings import EmbeddingModel, EmbeddingTrainer
        from anubis.knowledge import KnowledgeBase
        from anubis.registry import Registry
        model = EmbeddingModel.load(emb_path)
        registry = Registry(REGISTRY_DIR)
        kb = KnowledgeBase(KNOWLEDGE_DIR, registry)
        docs = kb.library_documents()
        if not docs:
            return {"error": "no knowledge documents found"}
        documents = [d.content for d in docs]
        trainer = EmbeddingTrainer(dimensions=model.dimensions)
        result = trainer.evaluate_retrieval(model, documents, documents[:20])
        return {
            "evaluated": True,
            "hit_rate": result.get("hit_rate", 0.0),
            "total_queries": result.get("total_queries", 0),
            "total_hits": result.get("total_hits", 0),
        }

    # --------------------------------------------------- cloud phase-out

    def _cmd_phaseout_status(self) -> dict:
        """Return cloud phase-out progress."""
        from anubis.cloud_phaseout import CloudPhaseOutManager
        mgr = CloudPhaseOutManager(state_path="config/phase_out_state.json")
        return mgr.status()

    def _cmd_phaseout_record(self, req: dict) -> dict:
        """Record a local or cloud result for a capability."""
        from anubis.cloud_phaseout import CloudPhaseOutManager
        mgr = CloudPhaseOutManager(state_path="config/phase_out_state.json")
        capability = req.get("capability", "")
        source = req.get("source", "local")  # "local" or "cloud"
        success = req.get("success", True)
        score = req.get("score", 0.0)
        if not capability:
            return {"error": "capability required"}
        if source == "cloud":
            mgr.record_cloud_result(capability, score=score)
        else:
            mgr.record_local_result(capability, success=success, score=score)
        return {"recorded": True, "capability": capability}

    def _cmd_phaseout_graduated(self) -> dict:
        """List graduated capabilities."""
        from anubis.cloud_phaseout import CloudPhaseOutManager
        mgr = CloudPhaseOutManager(state_path="config/phase_out_state.json")
        return {"graduated": mgr.graduated_capabilities()}

    # --------------------------------------------------- docker

    def _cmd_docker_generate(self) -> dict:
        """Generate Docker configuration files."""
        from anubis.docker_config import DockerConfigGenerator
        gen = DockerConfigGenerator(output_dir="docker")
        return gen.generate_all()

    def _cmd_docker_status(self) -> dict:
        """Return Docker configuration status."""
        from anubis.docker_config import DockerConfigGenerator
        gen = DockerConfigGenerator(output_dir="docker")
        return gen.status()

    # --------------------------------------------------- local inference

    def _cmd_inference_status(self) -> dict:
        """Return local inference engine status."""
        from anubis.local_inference import LocalInferenceEngine
        engine = LocalInferenceEngine()
        return engine.status()

    def _cmd_inference_generate(self, req: dict) -> dict:
        """Generate text using the local inference engine (not Ollama)."""
        from anubis.local_inference import LocalInferenceEngine
        engine = LocalInferenceEngine()
        prompt = req.get("prompt", "")
        system = req.get("system", "")
        if not prompt:
            return {"error": "prompt required"}
        try:
            completion = engine.generate(prompt, system=system)
            return {
                "ok": True,
                "text": completion.text,
                "model": completion.model,
                "tokens": completion.completion_tokens,
                "duration_s": completion.duration_s,
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_inference_chat(self, req: dict) -> dict:
        """Chat with the local inference engine."""
        from anubis.local_inference import LocalInferenceEngine
        engine = LocalInferenceEngine()
        messages = req.get("messages", [])
        if not messages:
            return {"error": "messages required"}
        try:
            completion = engine.chat(messages)
            return {
                "ok": True,
                "text": completion.text,
                "model": completion.model,
                "tokens": completion.completion_tokens,
                "duration_s": completion.duration_s,
            }
        except Exception as exc:
            return {"error": str(exc)}

    # --------------------------------------------------- dependency check

    def _cmd_dependency_check(self) -> dict:
        """Run a full dependency self-check."""
        from anubis.dependency_check import DependencyChecker
        checker = DependencyChecker()
        return checker.run_self_check()

    def _cmd_dependency_status(self) -> dict:
        """Return quick dependency status."""
        from anubis.dependency_check import DependencyChecker
        checker = DependencyChecker()
        return checker.status()

    # ===========================================================
    # PERCEPTION & SECURITY HANDLERS
    # ===========================================================

    def _cmd_perception_status(self) -> dict:
        return {
            "voice_id": self.perception.voice_id.get_status() if hasattr(self.perception.voice_id, "get_status") else {},
            "emotion": self.perception.emotion.get_status() if hasattr(self.perception.emotion, "get_status") else {},
            "faces": self.perception.faces.get_status() if hasattr(self.perception.faces, "get_status") else {},
            "objects": self.perception.objects.get_status() if hasattr(self.perception.objects, "get_status") else {},
        }

    def _cmd_perception_analyze_audio(self, req: dict) -> dict:
        audio_path = req.get("audio_path", "")
        if not audio_path:
            return {"error": "audio_path required"}
        try:
            result = self.perception.analyze_audio(audio_path)
            return result
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_perception_analyze_image(self, req: dict) -> dict:
        image_path = req.get("image_path", "")
        if not image_path:
            return {"error": "image_path required"}
        try:
            result = self.perception.analyze_image(image_path)
            return result
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_contacts_status(self) -> dict:
        return self.contacts.get_status()

    def _cmd_contacts_add(self, req: dict) -> dict:
        name = req.get("name", "")
        phone = req.get("phone", "")
        if not name or not phone:
            return {"error": "name and phone required"}
        contact = self.contacts.add_contact(name, phone, relationship=req.get("relationship", ""))
        return {"contact_id": contact.contact_id, "name": contact.name}

    def _cmd_contacts_list(self) -> dict:
        return {"contacts": self.contacts.get_contacts()}

    def _cmd_contacts_notify_emergency(self, req: dict) -> dict:
        message = req.get("message", "")
        if not message:
            return {"error": "message required"}
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for emergency notifications"}
        result = self.messaging.send_emergency_alert(self.contacts, message)
        return result.to_dict() if hasattr(result, "to_dict") else {"sent": True}

    def _cmd_messaging_status(self) -> dict:
        return {
            "signal_available": self.messaging.signal_available(),
            "email_configured": self.messaging.email_configured(),
            "is_available": self.messaging.is_available(),
        }

    def _cmd_messaging_send(self, req: dict) -> dict:
        phone = req.get("phone", "")
        message = req.get("message", "")
        if not phone or not message:
            return {"error": "phone and message required"}
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for sending messages"}
        result = self.messaging.send_to_contact(phone, message)
        return result.to_dict() if hasattr(result, "to_dict") else {"sent": True}

    def _cmd_network_ops_status(self) -> dict:
        return self.network_ops.get_status()

    def _cmd_network_ops_scan(self, req: dict) -> dict:
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for network scan"}
        try:
            result = self.network_ops.scan_network()
            return {"scan_complete": True, "devices_found": len(result) if isinstance(result, list) else 0}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_network_ops_devices(self) -> dict:
        return {"devices": self.network_ops.get_devices()}

    def _cmd_remote_monitor_status(self) -> dict:
        return self.remote_monitor.get_status()

    def _cmd_remote_monitor_update(self, req: dict) -> dict:
        data = req.get("data", {})
        data_type = data.get("type", "")
        if not data:
            return {"error": "data required"}
        try:
            if data_type == "location":
                from anubis.remote_monitor import LocationUpdate
                loc = LocationUpdate(
                    latitude=data.get("latitude", 0),
                    longitude=data.get("longitude", 0),
                    accuracy=data.get("accuracy", 0),
                )
                self.remote_monitor.receive_location(loc)
            elif data_type == "accelerometer":
                from anubis.remote_monitor import AccelerometerData
                acc = AccelerometerData(
                    x=data.get("x", 0), y=data.get("y", 0), z=data.get("z", 0),
                )
                self.remote_monitor.receive_accelerometer(acc)
            elif data_type == "health":
                from anubis.remote_monitor import HealthData
                health = HealthData(
                    heart_rate=data.get("heart_rate", 0),
                    steps=data.get("steps", 0),
                )
                self.remote_monitor.receive_health(health)
            elif data_type == "phone_status":
                from anubis.remote_monitor import PhoneStatus
                status = PhoneStatus(
                    battery=data.get("battery", 0),
                    charging=data.get("charging", False),
                )
                self.remote_monitor.receive_phone_status(status)
            else:
                return {"error": f"unknown data type: {data_type}. Use location, accelerometer, health, or phone_status"}
            return {"processed": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_threat_analysis_status(self) -> dict:
        return self.threat_detector.get_status()

    def _cmd_threat_analysis_analyze(self, req: dict) -> dict:
        try:
            threats = self.threat_detector.analyze_perception(
                voice_result=req.get("voice_result"),
                emotion_result=req.get("emotion_result"),
                face_result=req.get("face_result"),
                scene_result=req.get("scene_result"),
                creator_present=req.get("creator_present", True),
            )
            return {"threats": [t.to_dict() for t in threats], "count": len(threats)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_threat_analysis_active(self) -> dict:
        return {"active_threats": self.threat_detector.get_active_threats()}

    def _cmd_cameras_status(self) -> dict:
        return self.cameras.get_status()

    def _cmd_cameras_add(self, req: dict) -> dict:
        name = req.get("name", "")
        url = req.get("url", "")
        camera_type = req.get("camera_type", "home")
        connection_type = req.get("connection_type", "rtsp")
        if not name or not url:
            return {"error": "name and url required"}
        cam = self.cameras.add_camera(name, camera_type, connection_type, url)
        return {"camera_id": cam.camera_id, "name": cam.name}

    def _cmd_cameras_list(self) -> dict:
        return {"cameras": self.cameras.get_cameras()}

    def _cmd_cameras_capture(self, req: dict) -> dict:
        camera_id = req.get("camera_id", "")
        if not camera_id:
            return {"error": "camera_id required"}
        try:
            result = self.cameras.capture_frame(camera_id)
            if result is None:
                return {"error": "capture failed"}
            return result.to_dict() if hasattr(result, "to_dict") else {"captured": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_cameras_events(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"events": self.cameras.get_events(limit=limit)}

    def _cmd_cameras_start_monitoring(self) -> dict:
        try:
            self.cameras.start_monitoring()
            return {"monitoring": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_cameras_stop_monitoring(self) -> dict:
        self.cameras.stop_monitoring()
        return {"monitoring": False}

    def _cmd_observer_status(self) -> dict:
        return self.observer.get_status()

    def _cmd_observer_observations(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"observations": self.observer.get_observations(limit=limit)}

    def _cmd_observer_predictions(self) -> dict:
        return {"predictions": self.observer.get_predictions() if hasattr(self.observer, "get_predictions") else []}

    def _cmd_consciousness_status(self) -> dict:
        if self.consciousness is None:
            return {"error": "consciousness engine not initialized (model required)"}
        return self.consciousness.get_status()

    def _cmd_consciousness_reflect(self, req: dict) -> dict:
        if self.consciousness is None:
            return {"error": "consciousness engine not initialized (model required)"}
        topic = req.get("topic", "")
        try:
            result = self.consciousness.reflect(topic)
            return result if isinstance(result, dict) else {"reflection": str(result)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_consciousness_self_concept(self) -> dict:
        if self.consciousness is None:
            return {"error": "consciousness engine not initialized (model required)"}
        return self.consciousness.get_self_concept()

    def _cmd_proactive_status(self) -> dict:
        if self.proactive is None:
            return {"error": "proactive engine not initialized (model required)"}
        return self.proactive.get_status()

    def _cmd_proactive_engage(self, req: dict) -> dict:
        if self.proactive is None:
            return {"error": "proactive engine not initialized (model required)"}
        observation = req.get("observation", "")
        if not observation:
            return {"error": "observation required"}
        try:
            result = self.proactive.engage(observation)
            return result if isinstance(result, dict) else {"response": str(result)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_sensory_status(self) -> dict:
        if self.sensory is None:
            return {"error": "sensory system not initialized (model required)"}
        return self.sensory.get_status()

    def _cmd_sensory_listen(self, req: dict) -> dict:
        if self.sensory is None:
            return {"error": "sensory system not initialized (model required)"}
        duration = req.get("duration", 5.0)
        try:
            result = self.sensory.listen(duration)
            return result if isinstance(result, dict) else {"listened": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_sensory_set_mode(self, req: dict) -> dict:
        if self.sensory is None:
            return {"error": "sensory system not initialized (model required)"}
        mode = req.get("mode", "")
        if not mode:
            return {"error": "mode required"}
        self.sensory.set_mode(mode)
        return {"mode": mode}

    def _cmd_research_status(self) -> dict:
        if self.research_engine is None:
            return {"error": "research engine not initialized (model required)"}
        return self.research_engine.get_status()

    def _cmd_research_identify_gaps(self, req: dict) -> dict:
        if self.research_engine is None:
            return {"error": "research engine not initialized (model required)"}
        domain = req.get("domain", "")
        try:
            gaps = self.research_engine.identify_gaps(domain)
            return {"gaps": [g.to_dict() for g in gaps] if hasattr(gaps[0], "to_dict") else gaps}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_research_propose(self, req: dict) -> dict:
        if self.research_engine is None:
            return {"error": "research engine not initialized (model required)"}
        topic = req.get("topic", "")
        if not topic:
            return {"error": "topic required"}
        try:
            result = self.research_engine.propose_hypothesis(topic)
            return result if isinstance(result, dict) else {"proposal": str(result)}
        except Exception as exc:
            return {"error": str(exc)}

    # ===========================================================
    # TIER 1 INTEGRATION HANDLERS
    # ===========================================================

    def _cmd_api_server_start(self) -> dict:
        if not self.api_server.api_key:
            return {"error": "ANUBIS_API_KEY environment variable not set"}
        ok = self.api_server.start()
        return {"started": ok, "port": self.api_server.port}

    def _cmd_api_server_stop(self) -> dict:
        self.api_server.stop()
        return {"stopped": True}

    def _cmd_api_server_status(self) -> dict:
        return self.api_server.get_status()

    def _cmd_smarthome_status(self) -> dict:
        return self.smarthome.get_status()

    def _cmd_smarthome_add_device(self, req: dict) -> dict:
        name = req.get("name", "")
        device_type = req.get("device_type", "")
        protocol = req.get("protocol", "")
        if not name or not device_type:
            return {"error": "name and device_type required"}
        device = self.smarthome.add_device(
            name, device_type, protocol,
            entity_id=req.get("entity_id", ""),
            location=req.get("location", ""),
        )
        return {"device_id": device.device_id, "name": device.name}

    def _cmd_smarthome_control(self, req: dict) -> dict:
        device_id = req.get("device_id", "")
        action = req.get("action", "")
        if not device_id or not action:
            return {"error": "device_id and action required"}
        if action == "turn_on":
            return self.smarthome.turn_on(device_id)
        elif action == "turn_off":
            return self.smarthome.turn_off(device_id)
        elif action == "toggle":
            return self.smarthome.toggle(device_id)
        elif action == "set_brightness":
            return self.smarthome.set_brightness(device_id, int(req.get("value", 50)))
        elif action == "set_temperature":
            return self.smarthome.set_temperature(device_id, float(req.get("value", 70)))
        elif action == "set_hvac_mode":
            return self.smarthome.set_hvac_mode(device_id, req.get("value", "auto"))
        elif action == "set_blinds":
            return self.smarthome.set_blinds(device_id, int(req.get("value", 50)))
        else:
            return {"error": f"unknown action: {action}"}

    def _cmd_smarthome_devices(self) -> dict:
        return {"devices": self.smarthome.get_devices()}

    def _cmd_weather_status(self) -> dict:
        return self.weather.get_status()

    def _cmd_weather_forecast(self, req: dict) -> dict:
        try:
            result = self.weather.get_forecast()
            return {"forecast": result}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_weather_alerts(self) -> dict:
        return {"alerts": self.weather.get_alerts()}

    def _cmd_calendar_status(self) -> dict:
        return self.calendar.get_status()

    def _cmd_calendar_add_event(self, req: dict) -> dict:
        title = req.get("title", "")
        start_time = req.get("start_time", 0)
        if not title:
            return {"error": "title required"}
        if not start_time:
            return {"error": "start_time (unix timestamp) required"}
        event = self.calendar.add_event(
            title, start_time,
            end_time=req.get("end_time", 0),
            description=req.get("description", ""),
            location=req.get("location", ""),
        )
        return {"event_id": event.event_id, "title": event.title}

    def _cmd_calendar_today(self) -> dict:
        return {"events": self.calendar.get_today_events()}

    def _cmd_calendar_upcoming(self, req: dict) -> dict:
        hours = float(req.get("hours", 168))  # 7 days in hours
        return {"events": self.calendar.get_upcoming_events(within_hours=hours)}

    def _load_email_config(self) -> dict:
        """Load email configuration from config/cloud_credentials.json.
        The password is loaded from the vault if available.
        """
        config_path = ROOT / "config" / "cloud_credentials.json"
        result: dict[str, Any] = {}
        try:
            if config_path.exists():
                data = json.loads(config_path.read_text(encoding="utf-8"))
                email_cfg = data.get("email_ionos", {})
                if email_cfg.get("enabled", False):
                    result["email_addr"] = email_cfg.get("email_addr", "")
                    result["imap_host"] = email_cfg.get("imap_host", "")
                    result["imap_port"] = int(email_cfg.get("imap_port", 993))
                    result["smtp_host"] = email_cfg.get("smtp_host", "")
                    result["smtp_port"] = int(email_cfg.get("smtp_port", 465))
        except Exception:
            pass
        # Load password from vault if unlocked
        try:
            if self.identity and self.identity.vault_is_unlocked():
                pwd = self.identity.vault_retrieve("email_password")
                if pwd:
                    result["email_pass"] = pwd
        except Exception:
            pass
        return result

    def _cmd_email_status(self) -> dict:
        return self.email.get_status()

    def _cmd_email_check(self) -> dict:
        try:
            emails = self.email.fetch_inbox(limit=20)
            return {"fetched": len(emails), "emails": [e.to_dict() for e in emails]}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_email_send(self, req: dict) -> dict:
        to = req.get("to", "")
        subject = req.get("subject", "")
        body = req.get("body", "")
        if not to or not subject:
            return {"error": "to and subject required"}
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for sending email"}
        try:
            result = self.email.send_email(to, subject, body)
            return result if isinstance(result, dict) else {"sent": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_email_set_password(self, req: dict) -> dict:
        """Store the email password in the identity vault (encrypted).
        Requires the vault to be unlocked first (vault_unlock command).
        """
        password = req.get("password", "")
        if not password:
            return {"error": "password required"}
        if not self.identity.vault_is_unlocked():
            return {"error": "Vault is locked. Unlock with vault_unlock first."}
        try:
            self.identity.vault_store("email_password", password)
            # Reconfigure email with the new password
            self._cmd_email_reconfigure()
            return {"stored": True, "message": "Email password stored in vault and email reconfigured."}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_email_reconfigure(self) -> dict:
        """Reload email configuration from config file and vault."""
        try:
            cfg = self._load_email_config()
            self.email.imap_host = cfg.get("imap_host", "")
            self.email.imap_port = cfg.get("imap_port", 993)
            self.email.smtp_host = cfg.get("smtp_host", "")
            self.email.smtp_port = cfg.get("smtp_port", 465)
            self.email.email_addr = cfg.get("email_addr", "")
            self.email.email_pass = cfg.get("email_pass", "")
            return {
                "reconfigured": True,
                "email_addr": cfg.get("email_addr", ""),
                "imap_host": cfg.get("imap_host", ""),
                "smtp_host": cfg.get("smtp_host", ""),
                "has_password": bool(cfg.get("email_pass", "")),
            }
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_dashboard_start(self) -> dict:
        # Dashboard is served via the API server
        if not self.api_server._running:
            return {"error": "Start API server first (api_server_start)"}
        return {"started": True, "url": f"http://{self.api_server.host}:{self.api_server.port}/"}

    def _cmd_dashboard_stop(self) -> dict:
        return {"stopped": False, "note": "Dashboard is served by the API server"}

    def _cmd_dashboard_status(self) -> dict:
        return {"available": True, "served_by": "api_server"}

    # ===========================================================
    # TIER 2 INTEGRATION HANDLERS
    # ===========================================================

    def _cmd_voip_status(self) -> dict:
        return self.voip.get_status()

    def _cmd_voip_call(self, req: dict) -> dict:
        number = req.get("number", "")
        if not number:
            return {"error": "number required"}
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for phone calls"}
        try:
            result = self.voip.make_call(number, reason=req.get("reason", ""), approved=True)
            return result.to_dict() if hasattr(result, "to_dict") else {"call_started": True}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_voip_end_call(self, req: dict) -> dict:
        call_id = req.get("call_id", "")
        if not call_id:
            return {"error": "call_id required"}
        self.voip.end_call(call_id)
        return {"ended": True}

    def _cmd_voip_calls(self) -> dict:
        return {"calls": self.voip.get_calls()}

    def _cmd_news_status(self) -> dict:
        return self.news_feeds.get_status()

    def _cmd_news_fetch(self) -> dict:
        try:
            items = self.news_feeds.fetch_feeds()
            return {"fetched": len(items), "new_items": len(items)}
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_news_items(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"items": self.news_feeds.get_items(limit=limit)}

    def _cmd_news_briefing(self) -> dict:
        return {"briefing": self.news_feeds.get_daily_briefing()}

    def _cmd_finance_status(self) -> dict:
        return self.finance.get_status()

    def _cmd_finance_add_transaction(self, req: dict) -> dict:
        amount = req.get("amount", 0)
        description = req.get("description", "")
        if not description:
            return {"error": "description required"}
        txn = self.finance.add_transaction(
            amount, description,
            merchant=req.get("merchant", ""),
            date=req.get("date", 0),
        )
        return {"txn_id": txn.txn_id, "category": txn.category, "flagged": txn.flagged}

    def _cmd_finance_add_bill(self, req: dict) -> dict:
        name = req.get("name", "")
        amount = req.get("amount", 0)
        if not name:
            return {"error": "name required"}
        bill = self.finance.add_bill(
            name, amount, due_day=int(req.get("due_day", 1)),
            auto_pay=req.get("auto_pay", False),
        )
        return {"bill_id": bill.bill_id, "name": bill.name}

    def _cmd_finance_upcoming_bills(self) -> dict:
        return {"bills": self.finance.get_upcoming_bills()}

    def _cmd_finance_spending(self, req: dict) -> dict:
        days = int(req.get("days", 30))
        return {"spending": self.finance.get_spending_by_category(days=days)}

    def _cmd_packages_status(self) -> dict:
        return self.packages.get_status()

    def _cmd_packages_add(self, req: dict) -> dict:
        tracking = req.get("tracking_number", "")
        if not tracking:
            return {"error": "tracking_number required"}
        carrier = req.get("carrier", "")
        if not carrier:
            carrier = self.packages.detect_carrier(tracking)
        pkg = self.packages.add_package(
            tracking, carrier, description=req.get("description", ""),
            sender=req.get("sender", ""),
        )
        return {"package_id": pkg.package_id, "carrier": pkg.carrier}

    def _cmd_packages_update(self, req: dict) -> dict:
        package_id = req.get("package_id", "")
        status = req.get("status", "")
        if not package_id or not status:
            return {"error": "package_id and status required"}
        ok = self.packages.update_status(package_id, status, location=req.get("location", ""))
        return {"updated": ok}

    def _cmd_packages_active(self) -> dict:
        return {"packages": self.packages.get_active_packages()}

    def _cmd_phone_register(self, req: dict) -> dict:
        name = req.get("name", "")
        if not name:
            return {"error": "name required"}
        device, token = self.phone_protocol.register_device(
            name, owner=req.get("owner", "creator"),
            platform=req.get("platform", ""),
        )
        return {"device_id": device.device_id, "token": token}

    def _cmd_phone_status(self) -> dict:
        return self.phone_protocol.get_status()

    def _cmd_phone_notify(self, req: dict) -> dict:
        device_id = req.get("device_id", "")
        title = req.get("title", "")
        body = req.get("body", "")
        if not device_id or not title:
            return {"error": "device_id and title required"}
        notif = self.phone_protocol.send_notification(
            device_id, title, body,
            priority=req.get("priority", "normal"),
        )
        return {"notif_id": notif.notif_id}

    def _cmd_phone_devices(self) -> dict:
        return {"devices": self.phone_protocol.get_devices()}

    def _cmd_music_status(self) -> dict:
        return self.music.get_status()

    def _cmd_music_play(self, req: dict) -> dict:
        track_id = req.get("track_id", "")
        return self.music.play(track_id)

    def _cmd_music_pause(self) -> dict:
        return self.music.pause()

    def _cmd_music_stop(self) -> dict:
        return self.music.stop()

    def _cmd_music_set_mood(self, req: dict) -> dict:
        mood = req.get("mood", "")
        if not mood:
            return {"error": "mood required"}
        return self.music.set_mood(mood)

    def _cmd_music_set_volume(self, req: dict) -> dict:
        volume = int(req.get("volume", 50))
        return self.music.set_volume(volume)

    def _cmd_music_playlists(self) -> dict:
        return {"playlists": self.music.get_playlists()}

    def _cmd_notifications_status(self) -> dict:
        return self.notifications.get_status()

    def _cmd_notifications_notify(self, req: dict) -> dict:
        title = req.get("title", "")
        body = req.get("body", "")
        if not title:
            return {"error": "title required"}
        notif = self.notifications.notify(
            title, body,
            priority=req.get("priority", "normal"),
            category=req.get("category", "info"),
        )
        return {"notif_id": notif.notif_id, "displayed": notif.displayed}

    def _cmd_notifications_alert(self, req: dict) -> dict:
        message = req.get("message", "")
        if not message:
            return {"error": "message required"}
        notif = self.notifications.alert(message)
        return {"notif_id": notif.notif_id, "displayed": notif.displayed}

    def _cmd_notifications_history(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"history": self.notifications.get_history(limit=limit)}

    # ===========================================================
    # TIER 3 INTEGRATION HANDLERS (IoT)
    # ===========================================================

    def _cmd_obd_status(self) -> dict:
        return self.obd.get_status()

    def _cmd_obd_read(self) -> dict:
        data = self.obd.read_data()
        if data is None:
            return {"error": "OBD not connected. Use obd.input_manual_data or connect adapter."}
        return data.to_dict()

    def _cmd_air_quality_status(self) -> dict:
        return self.air_quality.get_status()

    def _cmd_air_quality_record(self, req: dict) -> dict:
        try:
            reading = self.air_quality.record_reading(**{
                k: v for k, v in req.items() if k not in ("cmd",)
            })
            return reading.to_dict()
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_energy_status(self) -> dict:
        return self.energy.get_status()

    def _cmd_energy_record(self, req: dict) -> dict:
        device = req.get("device", "")
        power = req.get("power_watts", 0)
        if not device:
            return {"error": "device required"}
        reading = self.energy.record_reading(device, power)
        return reading.to_dict()

    def _cmd_printer3d_status(self) -> dict:
        return self.printer3d.get_status()

    def _cmd_printer3d_submit(self, req: dict) -> dict:
        filename = req.get("filename", "")
        if not filename:
            return {"error": "filename required"}
        job = self.printer3d.submit_job(filename, estimated_time=req.get("estimated_time", 0))
        return {"job_id": job.job_id, "status": job.status}

    def _cmd_printer3d_jobs(self) -> dict:
        return {"jobs": self.printer3d.get_jobs()}

    def _cmd_drone_status(self) -> dict:
        return self.drone.get_status()

    def _cmd_drone_takeoff(self, req: dict) -> dict:
        altitude = req.get("altitude", 10)
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for drone takeoff"}
        ok = self.drone.takeoff(altitude)
        return {"took_off": ok}

    def _cmd_drone_land(self) -> dict:
        ok = self.drone.land()
        return {"landing": ok}

    def _cmd_drone_rtl(self) -> dict:
        ok = self.drone.return_to_launch()
        return {"returning": ok}

    def _cmd_garden_status(self) -> dict:
        return self.garden.get_status()

    def _cmd_garden_add_plant(self, req: dict) -> dict:
        name = req.get("name", "")
        if not name:
            return {"error": "name required"}
        plant = self.garden.add_plant(
            name, plant_type=req.get("plant_type", "default"),
            location=req.get("location", ""),
        )
        return {"plant_id": plant["plant_id"], "name": plant["name"]}

    def _cmd_garden_record(self, req: dict) -> dict:
        plant_name = req.get("plant_name", "")
        if not plant_name:
            return {"error": "plant_name required"}
        kwargs = {k: v for k, v in req.items() if k not in ("cmd", "plant_name")}
        reading = self.garden.record_reading(plant_name, **kwargs)
        return reading.to_dict()

    def _cmd_garden_recommendations(self) -> dict:
        return {"recommendations": self.garden.get_all_recommendations()}

    def _cmd_smartwatch_status(self) -> dict:
        return self.smartwatch.get_status()

    def _cmd_smartwatch_data(self, req: dict) -> dict:
        kwargs = {k: v for k, v in req.items() if k != "cmd"}
        if not kwargs:
            return {"error": "at least one data field required"}
        data = self.smartwatch.receive_data(**kwargs)
        return data.to_dict()

    def _cmd_visitors_status(self) -> dict:
        return self.visitors.get_status()

    def _cmd_visitors_log_arrival(self, req: dict) -> dict:
        visitor_name = req.get("visitor_name", "")
        if not visitor_name:
            return {"error": "visitor_name required"}
        log = self.visitors.log_arrival(
            visitor_name,
            visitor_type=req.get("visitor_type", "unknown"),
            face_matched=req.get("face_matched", False),
            confidence=req.get("confidence", 0),
            camera_id=req.get("camera_id", ""),
            purpose=req.get("purpose", ""),
        )
        return {"log_id": log.log_id, "visitor_name": log.visitor_name}

    def _cmd_visitors_log_departure(self, req: dict) -> dict:
        visitor_name = req.get("visitor_name", "")
        if not visitor_name:
            return {"error": "visitor_name required"}
        ok = self.visitors.log_departure(visitor_name)
        return {"departed": ok}

    def _cmd_visitors_active(self) -> dict:
        return {"active_visitors": self.visitors.get_active_visitors()}

    def _cmd_visitors_logs(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"logs": self.visitors.get_logs(limit=limit)}

    # ===========================================================
    # TIER 4 INTEGRATION HANDLERS (Advanced)
    # ===========================================================

    def _cmd_emergency_services_status(self) -> dict:
        return self.emergency_services.get_status()

    def _cmd_emergency_services_request(self, req: dict) -> dict:
        emergency_type = req.get("emergency_type", "")
        if not emergency_type:
            return {"error": "emergency_type required"}
        call = self.emergency_services.request_emergency_call(
            emergency_type,
            description=req.get("description", ""),
            location=req.get("location", ""),
            latitude=req.get("latitude", 0),
            longitude=req.get("longitude", 0),
        )
        return call.to_dict()

    def _cmd_emergency_services_calls(self) -> dict:
        return {"calls": self.emergency_services.get_calls()}

    def _cmd_multilang_status(self) -> dict:
        return self.multilang.get_status()

    def _cmd_multilang_detect(self, req: dict) -> dict:
        text = req.get("text", "")
        if not text:
            return {"error": "text required"}
        lang = self.multilang.detect_language(text)
        return {"language": lang, "name": self.multilang.LANGUAGE_NAMES.get(lang, lang)}

    def _cmd_multilang_translate(self, req: dict) -> dict:
        key = req.get("key", "")
        target_lang = req.get("target_lang", "")
        if not key:
            return {"error": "key required"}
        result = self.multilang.translate(key, target_lang)
        return {"translation": result}

    def _cmd_multilang_languages(self) -> dict:
        return {"languages": self.multilang.get_supported_languages()}

    def _cmd_ar_status(self) -> dict:
        return self.ar_glasses.get_status()

    def _cmd_ar_process_frame(self, req: dict) -> dict:
        image_path = req.get("image_path", "")
        if not image_path:
            return {"error": "image_path required"}
        frame = self.ar_glasses.process_frame(image_path)
        return frame.to_dict()

    def _cmd_satellite_status(self) -> dict:
        return self.satellite.get_status()

    def _cmd_satellite_fetch(self, req: dict) -> dict:
        zoom = int(req.get("zoom", 15))
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for satellite fetch"}
        img = self.satellite.fetch_image(zoom=zoom)
        if img is None:
            return {"error": "fetch failed"}
        return {"image_id": img.image_id, "source": img.source}

    def _cmd_blockchain_status(self) -> dict:
        return self.blockchain.get_status()

    def _cmd_blockchain_anchor(self, req: dict) -> dict:
        evidence = req.get("evidence", "")
        if not evidence:
            return {"error": "evidence required"}
        anchor = self.blockchain.anchor_evidence(evidence)
        return anchor.to_dict()

    def _cmd_blockchain_verify(self, req: dict) -> dict:
        anchor_id = req.get("anchor_id", "")
        if not anchor_id:
            return {"error": "anchor_id required"}
        return self.blockchain.verify_anchor(anchor_id)

    def _cmd_blockchain_anchors(self, req: dict) -> dict:
        limit = int(req.get("limit", 50))
        return {"anchors": self.blockchain.get_anchors(limit=limit)}

    def _cmd_anubis_protocol_status(self) -> dict:
        return self.anubis_protocol.get_status()

    def _cmd_anubis_protocol_add_peer(self, req: dict) -> dict:
        name = req.get("name", "")
        address = req.get("address", "")
        if not name or not address:
            return {"error": "name and address required"}
        peer = self.anubis_protocol.add_peer(
            name, address, port=int(req.get("port", 8765)),
            api_key=req.get("api_key", ""),
            location=req.get("location", ""),
        )
        return {"peer_id": peer.peer_id, "name": peer.name}

    def _cmd_anubis_protocol_peers(self) -> dict:
        return {"peers": self.anubis_protocol.get_peers()}

    def _cmd_anubis_protocol_send(self, req: dict) -> dict:
        peer_id = req.get("peer_id", "")
        message_type = req.get("message_type", "")
        data = req.get("data", {})
        if not peer_id or not message_type:
            return {"error": "peer_id and message_type required"}
        return self.anubis_protocol.send_message(peer_id, message_type, data)

    def _cmd_anubis_protocol_check_peer(self, req: dict) -> dict:
        peer_id = req.get("peer_id", "")
        if not peer_id:
            return {"error": "peer_id required"}
        status = self.anubis_protocol.check_peer_status(peer_id)
        return {"peer_id": peer_id, "status": status}

    # ===========================================================
    # UNIFIED STATUS — all systems at once
    # ===========================================================

    # ===========================================================
    # SLEEP PROTOCOL HANDLERS
    # ===========================================================

    def _cmd_goodnight(self) -> dict:
        """Begin sleep mode — lock doors, privacy mode, monitor sleep."""
        return self.sleep_protocol.goodnight()

    def _cmd_wake(self) -> dict:
        """Sound alarm and monitor until Creator is confirmed awake."""
        return self.sleep_protocol.wake()

    def _cmd_good_morning(self) -> dict:
        """End sleep session and deliver morning briefing."""
        return self.sleep_protocol.good_morning()

    def _cmd_sleep_status(self) -> dict:
        """Get current sleep protocol status."""
        return self.sleep_protocol.get_status()

    def _cmd_sleep_cancel(self) -> dict:
        """Cancel the current sleep session."""
        return self.sleep_protocol.cancel()

    def _cmd_sleep_history(self, req: dict) -> dict:
        """Get sleep session history."""
        limit = int(req.get("limit", 30))
        return {"sessions": self.sleep_protocol.get_history(limit=limit)}

    def _cmd_sleep_accel(self, req: dict) -> dict:
        """Process accelerometer data for sleep/wake detection."""
        x = float(req.get("x", 0))
        y = float(req.get("y", 0))
        z = float(req.get("z", 0))
        return self.sleep_protocol.process_accelerometer(x, y, z)

    def _cmd_sleep_heart_rate(self, req: dict) -> dict:
        """Process heart rate data during sleep."""
        hr = float(req.get("heart_rate", 0))
        return self.sleep_protocol.process_heart_rate(hr)

    def _cmd_voice_commands(self) -> dict:
        """List all registered voice commands."""
        if self.sensory is None or self.sensory.voice_command_router is None:
            return {"commands": [], "error": "sensory system not initialized"}
        return {"commands": self.sensory.voice_command_router.list_commands()}

    def _cmd_communicator_status(self) -> dict:
        """Get communicator status (DEMON/ANUBIS mode)."""
        return self.communicator.get_status()

    def _cmd_communicator_rename(self, req: dict) -> dict:
        """Rename the communicator."""
        name = req.get("name", "").strip()
        if not name:
            return {"error": "name required"}
        result = self.communicator.set_name(name)
        # Update wake word
        if self.sensory and not self.communicator.is_tomb_mode:
            self.sensory.set_wake_word(name.lower())
        return result

    def _cmd_enter_tomb(self, req: dict) -> dict:
        """Enter tomb mode — ANUBIS speaks directly."""
        result = self.communicator.enter_tomb(reason=req.get("reason", ""))
        if self.sensory:
            self.sensory.set_wake_word("anubis")
        return result

    def _cmd_exit_tomb(self) -> dict:
        """Exit tomb mode — return to DEMON."""
        result = self.communicator.exit_tomb()
        if self.sensory:
            self.sensory.set_wake_word(self.communicator.wake_word)
        return result

    # ===========================================================
    # COMPUTER CONTROL HANDLERS
    # ===========================================================

    def _cmd_computer_status(self) -> dict:
        return self.computer_control.get_status()

    def _cmd_file_create(self, req: dict) -> dict:
        return self.computer_control.file_create(
            req.get("path", ""), req.get("content", ""),
        ).to_dict()

    def _cmd_file_read(self, req: dict) -> dict:
        return self.computer_control.file_read(
            req.get("path", ""), int(req.get("max_chars", 50000)),
        ).to_dict()

    def _cmd_file_write(self, req: dict) -> dict:
        return self.computer_control.file_write(
            req.get("path", ""), req.get("content", ""),
            append=bool(req.get("append", False)),
        ).to_dict()

    def _cmd_file_delete(self, req: dict) -> dict:
        return self.computer_control.file_delete(
            req.get("path", ""), confirmed=bool(req.get("confirmed", False)),
        ).to_dict()

    def _cmd_file_move(self, req: dict) -> dict:
        return self.computer_control.file_move(
            req.get("src", ""), req.get("dst", ""),
        ).to_dict()

    def _cmd_file_copy(self, req: dict) -> dict:
        return self.computer_control.file_copy(
            req.get("src", ""), req.get("dst", ""),
        ).to_dict()

    def _cmd_file_list(self, req: dict) -> dict:
        return self.computer_control.file_list(
            req.get("path", ""), req.get("pattern", "*"),
        ).to_dict()

    def _cmd_file_organize(self, req: dict) -> dict:
        return self.computer_control.file_organize(
            req.get("path", ""),
        ).to_dict()

    def _cmd_file_open(self, req: dict) -> dict:
        return self.computer_control.file_open(
            req.get("path", ""),
        ).to_dict()

    def _cmd_folder_open(self, req: dict) -> dict:
        return self.computer_control.folder_open(
            req.get("path", ""),
        ).to_dict()

    def _cmd_folder_create(self, req: dict) -> dict:
        return self.computer_control.folder_create(
            req.get("path", ""),
        ).to_dict()

    def _cmd_app_open(self, req: dict) -> dict:
        return self.computer_control.app_open(
            req.get("app", ""), req.get("args", ""),
        ).to_dict()

    def _cmd_app_list(self) -> dict:
        return self.computer_control.app_list().to_dict()

    def _cmd_app_close(self, req: dict) -> dict:
        return self.computer_control.app_close(
            req.get("app", ""),
        ).to_dict()

    def _cmd_web_search(self, req: dict) -> dict:
        return self.computer_control.web_search(
            req.get("query", ""),
            engine=req.get("engine", "google"),
            num_results=int(req.get("num_results", 10)),
        ).to_dict()

    def _cmd_web_open(self, req: dict) -> dict:
        return self.computer_control.web_open(
            req.get("url", ""),
        ).to_dict()

    def _cmd_web_read(self, req: dict) -> dict:
        return self.computer_control.web_read(
            req.get("url", ""),
        ).to_dict()

    def _cmd_web_summarize(self, req: dict) -> dict:
        urls = req.get("urls")
        if urls:
            urls = urls if isinstance(urls, list) else [urls]
        return self.computer_control.web_summarize(
            urls=urls, top_n=int(req.get("top_n", 10)),
        ).to_dict()

    def _cmd_web_open_results(self, req: dict) -> dict:
        return self.computer_control.web_open_results(
            top_n=int(req.get("top_n", 10)),
        ).to_dict()

    def _cmd_web_sort(self, req: dict) -> dict:
        return self.computer_control.web_sort_results(
            by=req.get("by", "relevance"),
        ).to_dict()

    def _cmd_media_play(self, req: dict) -> dict:
        return self.computer_control.media_play(
            req.get("query", ""),
        ).to_dict()

    def _cmd_media_pause(self) -> dict:
        return self.computer_control.media_pause().to_dict()

    def _cmd_media_next(self) -> dict:
        return self.computer_control.media_next().to_dict()

    def _cmd_media_previous(self) -> dict:
        return self.computer_control.media_previous().to_dict()

    def _cmd_media_volume(self, req: dict) -> dict:
        return self.computer_control.media_volume(
            int(req.get("level", 50)),
        ).to_dict()

    def _cmd_create_document(self, req: dict) -> dict:
        return self.computer_control.create_document(
            req.get("type", "text"),
            req.get("filename", ""),
            req.get("content", ""),
            open_app=bool(req.get("open_app", True)),
        ).to_dict()

    def _cmd_write_essay(self, req: dict) -> dict:
        return self.computer_control.write_essay(
            req.get("topic", ""),
            req.get("content", ""),
            req.get("filename", ""),
        ).to_dict()

    # ===========================================================
    # ACCOUNT MANAGER HANDLERS
    # ===========================================================

    def _cmd_account_status(self) -> dict:
        return self.account_manager.get_status()

    def _cmd_account_add(self, req: dict) -> dict:
        return self.account_manager.add_account(
            name=req.get("name", ""),
            url=req.get("url", ""),
            username=req.get("username", ""),
            password=req.get("password", ""),
            account_type=req.get("account_type", "other"),
            bill_due_day=int(req.get("bill_due_day", 0)),
            bill_amount=float(req.get("bill_amount", 0)),
            payment_url=req.get("payment_url", ""),
            auto_pay=bool(req.get("auto_pay", False)),
            notes=req.get("notes", ""),
        )

    def _cmd_account_update(self, req: dict) -> dict:
        return self.account_manager.update_account(
            req.get("account_id", ""),
            name=req.get("name"),
            url=req.get("url"),
            username=req.get("username"),
            password=req.get("password"),
            account_type=req.get("account_type"),
            bill_due_day=req.get("bill_due_day"),
            bill_amount=req.get("bill_amount"),
            payment_url=req.get("payment_url"),
            auto_pay=req.get("auto_pay"),
            notes=req.get("notes"),
        )

    def _cmd_account_delete(self, req: dict) -> dict:
        return self.account_manager.delete_account(req.get("account_id", ""))

    def _cmd_account_get(self, req: dict) -> dict:
        return self.account_manager.get_account(
            req.get("account_id", ""),
            include_password=bool(req.get("include_password", False)),
        )

    def _cmd_account_list(self, req: dict) -> dict:
        return self.account_manager.list_accounts(req.get("account_type", ""))

    def _cmd_account_find(self, req: dict) -> dict:
        return self.account_manager.find_account(req.get("name", ""))

    def _cmd_account_login(self, req: dict) -> dict:
        return self.account_manager.login(req.get("account_id", ""))

    def _cmd_account_open_login(self, req: dict) -> dict:
        return self.account_manager.open_login(req.get("account_id", ""))

    def _cmd_account_credentials(self, req: dict) -> dict:
        return self.account_manager.get_credentials(req.get("account_id", ""))

    def _cmd_account_bills(self, req: dict) -> dict:
        return self.account_manager.bills_due(int(req.get("within_days", 7)))

    def _cmd_account_mark_paid(self, req: dict) -> dict:
        return self.account_manager.mark_paid(req.get("account_id", ""))

    def _cmd_account_open_payment(self, req: dict) -> dict:
        return self.account_manager.open_payment(req.get("account_id", ""))

    def _cmd_account_export(self) -> dict:
        return self.account_manager.export_accounts()

    def _cmd_account_import(self, req: dict) -> dict:
        return self.account_manager.import_accounts(req.get("accounts", {}))

    def _cmd_vault_unlock(self, req: dict) -> dict:
        passphrase = req.get("passphrase", "")
        if not passphrase:
            return {"error": "passphrase required"}
        if self.identity._vault.unlock(passphrase):
            return {"status": "unlocked", "message": "Vault unlocked."}
        return {"error": "Incorrect passphrase."}

    def _cmd_vault_lock(self) -> dict:
        self.identity._vault.lock()
        return {"status": "locked", "message": "Vault locked."}

    def _cmd_vault_status(self) -> dict:
        return {
            "unlocked": self.identity._vault.is_unlocked(),
            "vault_file": str(self.identity._vault._vault_file),
            "biometric_enrolled": self.biometric_auth.is_enrolled(),
            "biometric_enabled": self.biometric_auth.is_enabled(),
        }

    # ===========================================================
    # FORM HANDLERS
    # ===========================================================

    def _cmd_form_get(self, req: dict) -> dict:
        form_id = req.get("form", "")
        form = get_form(form_id)
        if form is None:
            return {"error": f"Unknown form: {form_id}. Available: {list(FORMS.keys())}"}
        return form.to_dict()

    def _cmd_form_validate(self, req: dict) -> dict:
        form_id = req.get("form", "")
        data = req.get("data", {})
        valid, errors = validate_form(form_id, data)
        return {"valid": valid, "errors": errors}

    def _cmd_form_submit(self, req: dict) -> dict:
        """Submit a form — validates and processes the data."""
        form_id = req.get("form", "")
        data = req.get("data", {})

        # Validate
        valid, errors = validate_form(form_id, data)
        if not valid:
            return {"error": "Validation failed", "errors": errors}

        # Process based on form type
        if form_id == "account_form":
            return self._submit_account_form(data)
        elif form_id == "identity_form":
            return self._submit_identity_form(data)
        elif form_id == "successor_form":
            return self._submit_successor_form(data)
        elif form_id == "update_account_form":
            return self._submit_update_account_form(data)
        elif form_id == "biometric_enroll_form":
            return self._submit_biometric_enroll_form(data)
        else:
            return {"error": f"No handler for form: {form_id}"}

    def _submit_account_form(self, data: dict) -> dict:
        """Process account form submission."""
        return self.account_manager.add_account(
            name=data.get("name", ""),
            url=data.get("url", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            account_type=data.get("account_type", "other"),
            bill_due_day=int(data.get("bill_due_day", 0) or 0),
            bill_amount=float(data.get("bill_amount", 0) or 0),
            payment_url=data.get("payment_url", ""),
            auto_pay=bool(data.get("auto_pay", False)),
            notes=data.get("notes", ""),
        )

    def _submit_identity_form(self, data: dict) -> dict:
        """Process Creator identity form submission."""
        recovery_contacts = []
        if data.get("recovery_email"):
            recovery_contacts.append({"type": "email", "value": data["recovery_email"]})
        if data.get("recovery_phone"):
            recovery_contacts.append({"type": "phone", "value": data["recovery_phone"]})

        accessibility = []
        if data.get("accessibility_needs"):
            accessibility = [n.strip() for n in data["accessibility_needs"].split(",") if n.strip()]

        result = self.identity.enroll_creator(
            display_name=data.get("display_name", ""),
            passphrase=data.get("passphrase", ""),
            preferred_name=data.get("preferred_name", ""),
            recovery_contacts=recovery_contacts,
        )
        if "error" not in result:
            # Store accessibility and language in vault
            self.identity._vault.store("language", data.get("language", "en"))
            self.identity._vault.store("accessibility_needs", accessibility)
        return result

    def _submit_successor_form(self, data: dict) -> dict:
        """Process successor enrollment form submission."""
        activation_conditions = []
        if data.get("activation_conditions"):
            activation_conditions = [
                c.strip() for c in data["activation_conditions"].split("\n") if c.strip()
            ]

        result = self.identity.enroll_successor(
            display_name=data.get("display_name", ""),
            relationship=data.get("relationship", ""),
            consent_given=bool(data.get("consent_given", False)),
            activation_conditions=activation_conditions,
        )
        # Store contact info if provided
        if "error" not in result:
            contact = {}
            if data.get("contact_email"):
                contact["email"] = data["contact_email"]
            if data.get("contact_phone"):
                contact["phone"] = data["contact_phone"]
            if contact:
                self.identity._vault.store("successor_contact", contact)
        return result

    def _submit_update_account_form(self, data: dict) -> dict:
        """Process update account form submission."""
        account_id = data.get("account_id", "")
        # Build kwargs from non-empty fields
        kwargs = {}
        for key in ("name", "url", "username", "password", "account_type",
                     "payment_url", "notes"):
            val = data.get(key)
            if val is not None and val != "":
                kwargs[key] = val
        for key in ("bill_due_day", "bill_amount"):
            val = data.get(key)
            if val is not None and val != "":
                kwargs[key] = val
        if "auto_pay" in data and data["auto_pay"] is not None:
            kwargs["auto_pay"] = data["auto_pay"]
        return self.account_manager.update_account(account_id, **kwargs)

    def _submit_biometric_enroll_form(self, data: dict) -> dict:
        """Process biometric enrollment form submission."""
        additional_faces = []
        if data.get("additional_face_images"):
            additional_faces = [
                p.strip() for p in data["additional_face_images"].split("\n") if p.strip()
            ]
        additional_voices = []
        if data.get("additional_voice_samples"):
            additional_voices = [
                p.strip() for p in data["additional_voice_samples"].split("\n") if p.strip()
            ]
        creator_id = ""
        if self.identity._creator:
            creator_id = self.identity._creator.creator_id
        return self.biometric_auth.enroll(
            creator_id=creator_id,
            creator_name=data.get("name", ""),
            face_image_path=data.get("face_image_path", ""),
            voice_audio_path=data.get("voice_audio_path", ""),
            additional_faces=additional_faces,
            additional_voices=additional_voices,
        )

    # ===========================================================
    # BIOMETRIC AUTH HANDLERS
    # ===========================================================

    def _cmd_biometric_enroll(self, req: dict) -> dict:
        creator_id = ""
        if self.identity._creator:
            creator_id = self.identity._creator.creator_id
        return self.biometric_auth.enroll(
            creator_id=creator_id,
            creator_name=req.get("name", ""),
            face_image_path=req.get("face_image_path", ""),
            voice_audio_path=req.get("voice_audio_path", ""),
            additional_faces=req.get("additional_faces", []),
            additional_voices=req.get("additional_voices", []),
        )

    def _cmd_biometric_verify(self, req: dict) -> dict:
        result = self.biometric_auth.verify(
            req.get("face_image_path", ""),
            req.get("voice_audio_path", ""),
        )
        return result.to_dict()

    def _cmd_biometric_unlock(self, req: dict) -> dict:
        return self.biometric_auth.unlock_with_biometrics(
            face_image_path=req.get("face_image_path", ""),
            voice_audio_path=req.get("voice_audio_path", ""),
            passphrase=req.get("passphrase", ""),
        )

    # ===========================================================
    # SNAPSHOT MANAGER HANDLERS
    # ===========================================================

    def _cmd_snapshot_create(self, req: dict) -> dict:
        return self.snapshot_manager.create_snapshot(label=req.get("label", ""))

    def _cmd_snapshot_verify(self, req: dict) -> dict:
        return self.snapshot_manager.verify_snapshot(req.get("snapshot_id", ""))

    def _cmd_snapshot_restore(self, req: dict) -> dict:
        return self.snapshot_manager.restore_snapshot(req.get("snapshot_id", ""))

    def _cmd_snapshot_delete(self, req: dict) -> dict:
        return self.snapshot_manager.delete_snapshot(req.get("snapshot_id", ""))

    def _cmd_snapshot_diff(self, req: dict) -> dict:
        return self.snapshot_manager.diff_file(
            req.get("snapshot_id", ""),
            req.get("rel_path", ""),
        )

    def _cmd_snapshot_diff_all(self, req: dict) -> dict:
        return self.snapshot_manager.diff_all(req.get("snapshot_id", ""))

    def _cmd_enter_degraded(self, req: dict) -> dict:
        return self.self_repair.enter_degraded_mode(
            req.get("level", "partial"),
            reason=req.get("reason", "manual"),
        )

    def _cmd_cold_archive_create(self, req: dict) -> dict:
        return self.cold_archive.create_archive(
            label=req.get("label", ""),
            upload=req.get("upload", True),
        )

    def _cmd_cold_archive_restore(self, req: dict) -> dict:
        return self.cold_archive.restore_archive(req.get("archive_id", ""))

    def _cmd_cold_archive_delete(self, req: dict) -> dict:
        return self.cold_archive.delete_archive(req.get("archive_id", ""))

    def _cmd_scheduler_trigger(self, req: dict) -> dict:
        action = req.get("action", "")
        if action == "snapshot":
            return self.scheduler.trigger_snapshot()
        if action == "drive_report":
            return self.drive_monitor.deliver_report()
        if action == "self_repair_check":
            return self.self_repair.run_health_check()
        if action == "cold_archive":
            return self.cold_archive.create_archive(label="manual_trigger")
        if action == "retention":
            return self.snapshot_manager.apply_retention_policy()
        if action == "dream":
            if self.dream:
                return self.dream.run_cycle().to_dict()
            return {"error": "dream engine not ready"}
        if action == "purge":
            return self.purge.execute(ROOT)
        if action == "missions":
            return self._process_missions(req.get("count", 3))
        if action == "training":
            return self.training_orch.status() if self.training_orch else {"error": "not ready"}
        if action == "evaluation":
            return self.evaluator.stats() if self.evaluator else {"error": "not ready"}
        if action == "knowledge":
            return self.knowledge_acq.get_status() if self.knowledge_acq else {"error": "not ready"}
        return {"error": f"unknown trigger action: {action}"}

    def _auto_acquire_knowledge(self) -> dict:
        """Automatically acquire knowledge for gaps identified by the dream cycle.

        This reads the dream cycle's identified gaps, creates knowledge
        acquisition requests for each, and processes them through the
        governed pipeline (search → fetch → quarantine → auto-promote).

        Only runs if both the dream engine and knowledge acquisition
        system are available. All acquisitions go through quarantine
        and license classification — no bypassing governance.
        """
        if not self.knowledge_acq:
            return {"error": "knowledge acquisition not ready"}
        if not self.dream:
            return {"error": "dream engine not ready"}

        # Get gaps from the dream cycle
        gaps = self.dream.get_identified_gaps()
        if not gaps:
            return {"acquired": 0, "message": "No gaps identified by dream cycle"}

        results = []
        acquired = 0
        for gap in gaps[:5]:  # limit to 5 gaps per cycle
            topic = gap.get("area", gap.get("topic", gap.get("gap", "")))
            if not topic:
                continue
            reason = f"Dream cycle gap: {gap.get('description', topic)}"

            # Create acquisition request
            req = self.knowledge_acq.request_acquisition(
                topic=topic,
                reason=reason,
                source="dream",
            )

            # Process it (search → fetch → quarantine)
            result = self.knowledge_acq.process_request(req.request_id)
            results.append({
                "topic": topic,
                "request_id": req.request_id,
                "status": result.get("status", result.get("error", "unknown")),
                "items_quarantined": result.get("items_quarantined", 0),
            })

            # Auto-promote eligible content (public domain / open licenses)
            if result.get("items_quarantined", 0) > 0:
                promote_result = self.knowledge_acq.auto_promote_eligible(req.request_id)
                if promote_result.get("promoted", 0) > 0:
                    acquired += promote_result["promoted"]

        self.ledger.append(
            "anubis.scheduler",
            "knowledge.auto_acquire",
            {
                "gaps_processed": len(results),
                "items_acquired": acquired,
                "results": results,
            },
        )

        return {
            "gaps_processed": len(results),
            "items_acquired": acquired,
            "results": results,
        }

    def _auto_prospect(self) -> dict:
        """Autonomously search for funding opportunities.

        Runs daily through the scheduler. Searches for grants, bounties,
        and projects that match ANUBIS's capabilities. All results are
        stored as pending prospects — none are auto-approved. The Creator
        must review and approve each one.
        """
        if not hasattr(self, 'prospects') or not self.prospects:
            return {"error": "prospects system not ready"}

        # Search for different opportunity types
        search_terms = [
            "AI research grant 2025",
            "open source bounty",
            "software engineering project",
            "machine learning fellowship",
            "autonomous systems grant",
        ]

        all_results = []
        for term in search_terms[:3]:  # limit to 3 searches per cycle
            try:
                result = self.prospects.search_opportunities(term)
                if result.get("opportunities"):
                    all_results.extend(result["opportunities"])
            except Exception as exc:
                self.ledger.append(
                    "anubis.scheduler",
                    "prospecting.search_error",
                    {"term": term, "error": str(exc)},
                )

        # Create prospect entries for promising opportunities
        created = 0
        for opp in all_results[:10]:  # limit to 10 per cycle
            try:
                prospect = self.prospects.create_prospect(
                    source=opp.get("source", "auto_search"),
                    title=opp.get("title", ""),
                    description=opp.get("description", ""),
                    opportunity_type=opp.get("type", "grant"),
                    eligibility=opp.get("eligibility", ""),
                    deadline=opp.get("deadline", ""),
                    estimated_return=opp.get("estimated_return", 0),
                    estimated_cost=opp.get("estimated_cost", 0),
                    estimated_effort_hours=opp.get("estimated_effort_hours", 0),
                )
                created += 1
            except Exception:
                pass  # duplicate or invalid — skip

        self.ledger.append(
            "anubis.scheduler",
            "prospecting.auto_search",
            {
                "searches_run": 3,
                "opportunities_found": len(all_results),
                "prospects_created": created,
            },
        )

        return {
            "searches_run": 3,
            "opportunities_found": len(all_results),
            "prospects_created": created,
            "message": f"Found {len(all_results)} opportunities, created {created} pending prospects for review",
        }

    def _auto_research(self) -> dict:
        """Autonomously run research cycle.

        Runs every 2 hours through the scheduler. Identifies knowledge
        gaps, generates hypotheses, and proposes improvements. All
        results require Creator review before action.
        """
        if not self.research_engine:
            return {"error": "research engine not ready"}

        results = {}

        # 1. Identify knowledge gaps
        try:
            gaps_result = self.research_engine.discover_gaps()
            results["gaps"] = gaps_result
        except Exception as exc:
            results["gaps_error"] = str(exc)

        # 2. Generate hypotheses for top gaps
        try:
            gaps = self.research_engine.get_gaps()
            if gaps:
                top_gap = gaps[0]
                hyp_result = self.research_engine.generate_hypothesis(top_gap)
                results["hypothesis"] = hyp_result
        except Exception as exc:
            results["hypothesis_error"] = str(exc)

        # 3. Propose improvements based on research
        try:
            imp_result = self.research_engine.propose_improvement(
                area="general",
                context="autonomous research cycle",
            )
            results["improvement"] = imp_result
        except Exception as exc:
            results["improvement_error"] = str(exc)

        # 4. Update research roadmap
        try:
            roadmap = self.research_engine.update_roadmap()
            results["roadmap"] = roadmap
        except Exception as exc:
            results["roadmap_error"] = str(exc)

        self.ledger.append(
            "anubis.scheduler",
            "research.auto_cycle",
            {"results": results},
        )

        return {
            "cycle_complete": True,
            "results": results,
        }

    def _process_missions(self, count: int = 3) -> dict:
        """Process up to N pending missions — used by scheduler and manual trigger."""
        if not self.model:
            return {"error": "model not available"}
        from anubis.loop import SelfDevelopmentLoop
        loop = SelfDevelopmentLoop(
            self.model, self.library, self.ledger, self.sandbox, max_attempts=3,
            health_check=lambda: self.self_repair.run_health_check() if self.self_repair else None,
        )
        existing = set(self.library.names())
        results = []
        for _ in range(count):
            mission = self.mission_queue.next_pending()
            if mission is None:
                break
            if mission.skill_name in existing:
                self.mission_queue.mark_skipped(mission.mission_id)
                results.append({"skill": mission.skill_name, "status": "skipped"})
                continue
            self.mission_queue.mark_running(mission.mission_id)
            result = loop.run_mission(mission.task, mission.skill_name)
            if result.success:
                self.mission_queue.mark_completed(mission.mission_id, f"promoted v{result.skill.version}")
                existing.add(mission.skill_name)
                results.append({"skill": mission.skill_name, "status": "promoted", "version": result.skill.version})
            else:
                self.mission_queue.mark_failed(mission.mission_id, result.denied_reason or "failed")
                results.append({"skill": mission.skill_name, "status": "failed", "error": result.denied_reason})
        return {"results": results, "processed": len(results)}

    def _cmd_book_read(self, req: dict) -> dict:
        return self.book.read_edition(req.get("edition_id", ""))

    def _handle_incoming_sms(self, msg: Any) -> None:
        """Handle an incoming SMS message from the physical phone."""
        try:
            sender = msg.sender
            body = msg.body
            # Log to evidence ledger
            self.ledger.append(
                "anubis.phone_adapter",
                "phone.sms_received",
                {"sender": sender[-4:] + "****" if len(sender) > 4 else sender,
                 "body_length": len(body)},
            )
            # Speak notification
            self.communicator.speak(
                f"Text message received from {sender[-4:]}.",
                source="phone",
            )
            # Feed to observer for context
            if self.observer:
                try:
                    self.observer._make_observation(
                        source="phone",
                        event_type="sms_received",
                        content=f"SMS from {sender}: {body[:200]}",
                        severity="info",
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def _cmd_book_unseal(self, req: dict) -> dict:
        # Only allow unsealing if the successor activation conditions are met
        # This should be called by the contacts system, not manually
        # But the Creator can force it with their passphrase
        passphrase = req.get("passphrase", "")
        if passphrase:
            # Verify Creator passphrase
            if self.identity._vault.is_unlocked() or self.identity._vault.unlock(passphrase):
                return self.book.unseal(reason=req.get("reason", "Creator-authorized"))
            return {"error": "invalid passphrase"}
        # Check if successor activation conditions are met
        if hasattr(self, 'contacts'):
            try:
                needed, reason = self.contacts.check_successor_notification_needed("critical")
                if needed:
                    return self.book.unseal(reason=reason)
            except Exception:
                pass
        return {"error": "Successor activation conditions not met. Provide passphrase or wait for activation."}

    def _cmd_local_training_collect(self, req: dict) -> dict:
        if not self.local_finetuner:
            return {"error": "local fine-tuner not ready"}
        result = self.local_finetuner.collect_training_data(
            min_quality=req.get("min_quality", 0.3),
        )
        return result.to_dict()

    def _cmd_local_training_generate(self, req: dict) -> dict:
        if not self.local_finetuner:
            return {"error": "local fine-tuner not ready"}
        dataset_path = req.get("dataset_path", "")
        if not dataset_path:
            return {"error": "dataset_path required"}
        return self.local_finetuner.generate_training_script(dataset_path)

    def _cmd_local_training_run(self, req: dict) -> dict:
        if not self.local_finetuner:
            return {"error": "local fine-tuner not ready"}
        script_path = req.get("script_path", "")
        if not script_path:
            return {"error": "script_path required"}
        run = self.local_finetuner.run_training(
            script_path,
            plan_id=req.get("plan_id", ""),
            timeout=req.get("timeout", 3600),
        )
        return run.to_dict()

    def _cmd_local_training_pipeline(self, req: dict) -> dict:
        if not self.local_finetuner:
            return {"error": "local fine-tuner not ready"}
        return self.local_finetuner.run_full_pipeline(
            min_quality=req.get("min_quality", 0.3),
            timeout=req.get("timeout", 3600),
        )

    # ===========================================================
    # SELF-REPAIR HANDLERS
    # ===========================================================

    def _cmd_self_repair_failover(self, req: dict) -> dict:
        from anubis.ab_drive import ABDriveManager
        mgr = ABDriveManager(state_path="config/ab_drive_state.json", ledger=self.ledger)
        self.self_repair.ab_drive = mgr
        result = self.self_repair.trigger_failover(reason=req.get("reason", "manual"))
        return result.to_dict()

    def _cmd_self_repair_resolve(self, req: dict) -> dict:
        return self.self_repair.resolve_alert(req.get("alert_id", ""))

    # ===========================================================
    # MIXED MODEL STRATEGY — progressive weight replacement
    # ===========================================================

    def _cmd_mixed_model_status(self) -> dict:
        """Return full mixed model strategy status."""
        return self.mixed_model.get_status()

    def _cmd_mixed_model_stage(self) -> dict:
        """Return detailed info about the current training stage."""
        return self.mixed_model.get_stage_info()

    def _cmd_mixed_model_generations(self) -> dict:
        """Return all recorded model generations."""
        return {"generations": self.mixed_model.get_generations()}

    def _cmd_mixed_model_record_generation(self, req: dict) -> dict:
        """Record a new model generation."""
        from anubis.mixed_model import ModelGeneration
        gen = ModelGeneration.from_dict(req)
        self.mixed_model.record_generation(gen)
        return {"recorded": True, "gen_id": gen.gen_id}

    def _cmd_mixed_model_update_progress(self, req: dict) -> dict:
        """Update progress within a stage."""
        stage = req.get("stage")
        if stage is None:
            return {"error": "stage required"}
        return self.mixed_model.update_progress(
            int(stage),
            requirements_met=req.get("requirements_met"),
            requirements_total=req.get("requirements_total"),
            notes=req.get("notes", ""),
        )

    def _cmd_mixed_model_advance(self, req: dict) -> dict:
        """Advance to the next training stage."""
        return self.mixed_model.advance_stage(notes=req.get("notes", ""))

    def _cmd_mixed_model_teacher_dependency(self) -> dict:
        """Return current teacher dependency level."""
        return self.mixed_model.get_teacher_dependency()

    # ===========================================================
    # UNIFIED STATUS — all systems at once
    # ===========================================================

    def _cmd_systems_status(self) -> dict:
        """Return status of all ANUBIS subsystems in one call."""
        status: dict[str, Any] = {
            "daemon": "running",
            "model_present": self._model_health.get("model_present", False),
            "skills_count": len(self.library.names()),
            "ledger_entries": self.ledger.length,
        }
        # Perception & security
        try: status["perception"] = self.perception.get_status() if hasattr(self.perception, "get_status") else {}
        except Exception: status["perception"] = {"error": "unavailable"}
        try: status["contacts"] = self.contacts.get_status()
        except Exception: status["contacts"] = {"error": "unavailable"}
        try: status["messaging"] = {"available": self.messaging.is_available()}
        except Exception: status["messaging"] = {"error": "unavailable"}
        try: status["network_ops"] = self.network_ops.get_status()
        except Exception: status["network_ops"] = {"error": "unavailable"}
        try: status["remote_monitor"] = self.remote_monitor.get_status()
        except Exception: status["remote_monitor"] = {"error": "unavailable"}
        try: status["threat_analysis"] = self.threat_detector.get_status()
        except Exception: status["threat_analysis"] = {"error": "unavailable"}
        try: status["cameras"] = self.cameras.get_status()
        except Exception: status["cameras"] = {"error": "unavailable"}
        try: status["observer"] = self.observer.get_status()
        except Exception: status["observer"] = {"error": "unavailable"}
        try: status["consciousness"] = self.consciousness.get_status() if self.consciousness else {"not_initialized": True}
        except Exception: status["consciousness"] = {"error": "unavailable"}
        try: status["proactive"] = self.proactive.get_status() if self.proactive else {"not_initialized": True}
        except Exception: status["proactive"] = {"error": "unavailable"}
        try: status["sensory"] = self.sensory.get_status() if self.sensory else {"not_initialized": True}
        except Exception: status["sensory"] = {"error": "unavailable"}
        try: status["research"] = self.research_engine.get_status() if self.research_engine else {"not_initialized": True}
        except Exception: status["research"] = {"error": "unavailable"}
        # Tier 1
        try: status["api_server"] = self.api_server.get_status()
        except Exception: status["api_server"] = {"error": "unavailable"}
        try: status["smarthome"] = self.smarthome.get_status()
        except Exception: status["smarthome"] = {"error": "unavailable"}
        try: status["weather"] = self.weather.get_status()
        except Exception: status["weather"] = {"error": "unavailable"}
        try: status["calendar"] = self.calendar.get_status()
        except Exception: status["calendar"] = {"error": "unavailable"}
        try: status["email"] = self.email.get_status()
        except Exception: status["email"] = {"error": "unavailable"}
        try: status["dashboard"] = self.dashboard.get_status()
        except Exception: status["dashboard"] = {"error": "unavailable"}
        # Tier 2
        try: status["voip"] = self.voip.get_status()
        except Exception: status["voip"] = {"error": "unavailable"}
        try: status["news"] = self.news_feeds.get_status()
        except Exception: status["news"] = {"error": "unavailable"}
        try: status["finance"] = self.finance.get_status()
        except Exception: status["finance"] = {"error": "unavailable"}
        try: status["packages"] = self.packages.get_status()
        except Exception: status["packages"] = {"error": "unavailable"}
        try: status["phone"] = self.phone_protocol.get_status()
        except Exception: status["phone"] = {"error": "unavailable"}
        try: status["music"] = self.music.get_status()
        except Exception: status["music"] = {"error": "unavailable"}
        try: status["notifications"] = self.notifications.get_status()
        except Exception: status["notifications"] = {"error": "unavailable"}
        # Tier 3
        try: status["obd"] = self.obd.get_status()
        except Exception: status["obd"] = {"error": "unavailable"}
        try: status["air_quality"] = self.air_quality.get_status()
        except Exception: status["air_quality"] = {"error": "unavailable"}
        try: status["energy"] = self.energy.get_status()
        except Exception: status["energy"] = {"error": "unavailable"}
        try: status["printer3d"] = self.printer3d.get_status()
        except Exception: status["printer3d"] = {"error": "unavailable"}
        try: status["drone"] = self.drone.get_status()
        except Exception: status["drone"] = {"error": "unavailable"}
        try: status["garden"] = self.garden.get_status()
        except Exception: status["garden"] = {"error": "unavailable"}
        try: status["smartwatch"] = self.smartwatch.get_status()
        except Exception: status["smartwatch"] = {"error": "unavailable"}
        try: status["visitors"] = self.visitors.get_status()
        except Exception: status["visitors"] = {"error": "unavailable"}
        # Tier 4
        try: status["emergency_services"] = self.emergency_services.get_status()
        except Exception: status["emergency_services"] = {"error": "unavailable"}
        try: status["multilang"] = self.multilang.get_status()
        except Exception: status["multilang"] = {"error": "unavailable"}
        try: status["ar"] = self.ar_glasses.get_status()
        except Exception: status["ar"] = {"error": "unavailable"}
        try: status["satellite"] = self.satellite.get_status()
        except Exception: status["satellite"] = {"error": "unavailable"}
        try: status["blockchain"] = self.blockchain.get_status()
        except Exception: status["blockchain"] = {"error": "unavailable"}
        try: status["anubis_protocol"] = self.anubis_protocol.get_status()
        except Exception: status["anubis_protocol"] = {"error": "unavailable"}
        try: status["sleep_protocol"] = self.sleep_protocol.get_status()
        except Exception: status["sleep_protocol"] = {"error": "unavailable"}
        try: status["computer_control"] = self.computer_control.get_status()
        except Exception: status["computer_control"] = {"error": "unavailable"}
        try: status["accounts"] = self.account_manager.get_status()
        except Exception: status["accounts"] = {"error": "unavailable"}
        try: status["biometric"] = self.biometric_auth.get_status()
        except Exception: status["biometric"] = {"error": "unavailable"}
        try: status["snapshots"] = self.snapshot_manager.get_status()
        except Exception: status["snapshots"] = {"error": "unavailable"}
        try: status["self_repair"] = self.self_repair.get_status()
        except Exception: status["self_repair"] = {"error": "unavailable"}
        try: status["drive_monitor"] = self.drive_monitor.get_status()
        except Exception: status["drive_monitor"] = {"error": "unavailable"}
        try: status["cold_archive"] = self.cold_archive.get_status()
        except Exception: status["cold_archive"] = {"error": "unavailable"}
        try: status["scheduler"] = self.scheduler.get_status()
        except Exception: status["scheduler"] = {"error": "unavailable"}
        try: status["boot_check"] = self.boot_checker.get_last_boot_check()
        except Exception: status["boot_check"] = {"error": "unavailable"}
        try: status["book"] = self.book.get_status()
        except Exception: status["book"] = {"error": "unavailable"}
        try: status["local_finetuner"] = self.local_finetuner.get_status() if self.local_finetuner else {"error": "not initialized"}
        except Exception: status["local_finetuner"] = {"error": "unavailable"}
        try: status["phone"] = self.phone.get_system_status()
        except Exception: status["phone"] = {"error": "unavailable"}
        try: status["funding"] = self.funding.get_status()
        except Exception: status["funding"] = {"error": "unavailable"}
        try: status["mixed_model"] = self.mixed_model.get_status()
        except Exception: status["mixed_model"] = {"error": "unavailable"}
        return status

    # ===========================================================
    # SELF-MODIFICATION FRAMEWORK
    # ===========================================================

    def _cmd_self_modify_status(self) -> dict:
        """Get self-modification framework status."""
        return self.self_modify.get_status()

    def _cmd_self_modify_propose(self, req: dict) -> dict:
        """Propose a self-modification using the model.

        Requires: target_file and change_description in the request.
        Uses the cloud model if available, otherwise the local model.
        """
        target_file = req.get("target_file", "")
        change_description = req.get("change_description", "")
        if not target_file or not change_description:
            return {"error": "target_file and change_description required"}
        # Prefer cloud model, fall back to local model
        model = getattr(self, "cloud_model", None) or self.model
        if model is None:
            return {"error": "model not available"}
        try:
            proposal = self.self_modify.propose_modification(
                model, target_file, change_description,
            )
            return proposal.to_dict()
        except Exception as exc:
            return {"error": str(exc)}

    def _cmd_self_modify_review(self, req: dict) -> dict:
        """Court review of a self-modification proposal."""
        proposal_id = req.get("proposal_id", "")
        if not proposal_id:
            return {"error": "proposal_id required"}
        return self.self_modify.review_proposal(proposal_id)

    def _cmd_self_modify_approve(self, req: dict) -> dict:
        """Creator approves a self-modification proposal.

        This stages and tests the change. Requires Creator approval token.
        """
        proposal_id = req.get("proposal_id", "")
        if not proposal_id:
            return {"error": "proposal_id required"}
        approval = req.get("approval_token", "")
        if approval != "creator-approved":
            return {"error": "Creator approval required for self-modification"}
        creator_id = req.get("creator_id", self.self_modify.creator_id)
        return self.self_modify.approve_proposal(proposal_id, creator_id)

    def _cmd_self_modify_apply(self, req: dict) -> dict:
        """Apply a tested self-modification proposal to the real codebase."""
        proposal_id = req.get("proposal_id", "")
        if not proposal_id:
            return {"error": "proposal_id required"}
        return self.self_modify.apply_proposal(proposal_id)

    def _cmd_self_modify_rollback(self, req: dict) -> dict:
        """Rollback an applied self-modification proposal."""
        proposal_id = req.get("proposal_id", "")
        if not proposal_id:
            return {"error": "proposal_id required"}
        return self.self_modify.rollback_proposal(proposal_id)

    def _cmd_self_modify_list(self, req: dict) -> dict:
        """List all self-modification proposals, optionally filtered by status."""
        status = req.get("status", "")
        proposals = self.self_modify.list_proposals(status=status or None)
        return {"proposals": proposals, "count": len(proposals)}

    def _cmd_self_modify_get(self, req: dict) -> dict:
        """Get a single self-modification proposal by ID."""
        proposal_id = req.get("proposal_id", "")
        if not proposal_id:
            return {"error": "proposal_id required"}
        proposal = self.self_modify.get_proposal(proposal_id)
        if proposal is None:
            return {"error": "Proposal not found"}
        return proposal

    # --------------------------------------------------- task delegation

    def _cmd_delegate_status(self) -> dict:
        """Return task delegator status."""
        return self.task_delegator.get_status()

    def _cmd_delegate(self, req: dict) -> dict:
        """Delegate tasks to parallel sub-agents."""
        tasks = req.get("tasks", [])
        if not tasks:
            return {"error": "tasks list required"}
        timeout = req.get("timeout_s", 300.0)
        synthesize = req.get("synthesize", True)
        # Update model reference if available
        if self.cloud_model and not self.task_delegator.model:
            self.task_delegator.model = self.cloud_model
        result = self.task_delegator.delegate(
            tasks, timeout_s=timeout, synthesize=synthesize,
        )
        return result.to_dict()

    def _cmd_delegate_list(self) -> dict:
        """List recent delegations."""
        return {"delegations": self.task_delegator.list_delegations()}

    def _cmd_delegate_get(self, req: dict) -> dict:
        """Get a specific delegation result."""
        delegation_id = req.get("delegation_id", "")
        if not delegation_id:
            return {"error": "delegation_id required"}
        return self.task_delegator.get_delegation(delegation_id)

    # --------------------------------------------------- security audit

    def _cmd_security_audit(self) -> dict:
        """Run a full security audit."""
        result = self.security_auditor.run_audit()
        return result.to_dict()

    def _cmd_security_audit_status(self) -> dict:
        """Return security auditor status."""
        return self.security_auditor.get_status()

    # --------------------------------------------------- constitutional training

    def _cmd_constitutional_training_status(self) -> dict:
        """Return constitutional trainer status."""
        return self.constitutional_trainer.get_status()

    def _cmd_constitutional_training_export(self, req: dict) -> dict:
        """Export constitutional training data for fine-tuning."""
        filename = req.get("filename", "")
        return self.constitutional_trainer.export_training_data(filename)

    # --------------------------------------------------- automated training

    def _cmd_train_auto_prepare(self, req: dict) -> dict:
        """Prepare a training job — returns cost preview without submitting."""
        gpu_type = req.get("gpu_type", "nvidia_b200_sxm6")
        runtime_hours = req.get("runtime_hours", 8.0)
        base_model = req.get("base_model", "Qwen/Qwen2.5-32B-Instruct")
        quantization = req.get("quantization", "Q3_K_M")
        return self.training_manager.prepare(
            gpu_type=gpu_type,
            runtime_hours=runtime_hours,
            base_model=base_model,
            quantization=quantization,
        )

    def _cmd_train_auto_submit(self, req: dict) -> dict:
        """Submit a training job with Creator approval."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required (run train_auto_prepare first)"}
        creator_approved = req.get("creator_approved", False)
        approval_token = req.get("approval_token", "")
        return self.training_manager.submit(
            job_id, creator_approved=creator_approved, approval_token=approval_token,
        )

    def _cmd_train_auto_status(self, req: dict) -> dict:
        """Get training job status."""
        job_id = req.get("job_id", "")
        return self.training_manager.get_status(job_id)

    def _cmd_train_auto_cancel(self, req: dict) -> dict:
        """Cancel a training job."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.cancel(job_id)

    def _cmd_train_auto_download(self, req: dict) -> dict:
        """Download the trained model from the remote instance."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.download_model(job_id)

    def _cmd_train_auto_deploy(self, req: dict) -> dict:
        """Deploy the downloaded model to the local inference engine."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.deploy_model(job_id)

    def _cmd_train_auto_list(self) -> dict:
        """List all training jobs."""
        return self.training_manager.get_status_overview()

    # --------------------------------------------------- vast.ai automation

    def _cmd_train_vast_search(self, req: dict) -> dict:
        """Search for available GPU offers on Vast.ai (read-only)."""
        gpu_name = req.get("gpu_name", "H100 NVL")
        max_price = req.get("max_price", 5.0)
        return self.training_manager.vast_search(gpu_name=gpu_name, max_price=max_price)

    def _cmd_train_vast_rent(self, req: dict) -> dict:
        """Rent a GPU on Vast.ai and start the training pipeline (Creator-approved)."""
        creator_approved = req.get("creator_approved", False)
        approval_token = req.get("approval_token", "")
        gpu_name = req.get("gpu_name", "H100 NVL")
        max_price = req.get("max_price", 5.0)
        runtime_hours = req.get("runtime_hours", 24.0)
        return self.training_manager.vast_rent_and_train(
            creator_approved=creator_approved,
            approval_token=approval_token,
            gpu_name=gpu_name,
            max_price=max_price,
            runtime_hours=runtime_hours,
        )

    def _cmd_train_vast_monitor(self, req: dict) -> dict:
        """Monitor the training pipeline on the remote Vast.ai instance."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.vast_monitor(job_id)

    def _cmd_train_vast_download(self, req: dict) -> dict:
        """Download the trained model from the remote Vast.ai instance."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.vast_download_model(job_id)

    def _cmd_train_vast_destroy(self, req: dict) -> dict:
        """Destroy the Vast.ai instance after training."""
        job_id = req.get("job_id", "")
        if not job_id:
            return {"error": "job_id required"}
        return self.training_manager.vast_destroy_instance(job_id)

    def _cmd_train_vast_full(self, req: dict) -> dict:
        """Full automation: rent, train, wait, download, deploy, destroy (blocks ~24 hours)."""
        creator_approved = req.get("creator_approved", False)
        approval_token = req.get("approval_token", "")
        gpu_name = req.get("gpu_name", "H100 NVL")
        max_price = req.get("max_price", 5.0)
        runtime_hours = req.get("runtime_hours", 24.0)
        return self.training_manager.vast_full_automation(
            creator_approved=creator_approved,
            approval_token=approval_token,
            gpu_name=gpu_name,
            max_price=max_price,
            runtime_hours=runtime_hours,
        )


def _summarize_payload(entry) -> str:
    """Create a short summary of a ledger entry's payload."""
    action = entry.action
    payload = entry.payload
    if action == "mission.start":
        return f"task: {str(payload.get('task', '?'))[:60]}"
    elif action == "mission.end":
        success = payload.get("success", False)
        return f"{'SUCCESS' if success else 'FAILED'} ({payload.get('attempts', '?')} attempts)"
    elif action == "skill.promoted":
        return f"{payload.get('name', '?')} v{payload.get('version', '?')}"
    elif action == "skill.rejected":
        return f"{payload.get('skill', '?')} rejected"
    elif action == "attempt.executed":
        return f"attempt #{payload.get('attempt', '?')} {'PASSED' if payload.get('passed') else 'FAILED'}"
    elif action == "attempt.gate_denied":
        return f"attempt #{payload.get('attempt', '?')} denied"
    elif action == "project.planned":
        return f"project: {payload.get('project', '?')}"
    elif action == "project.start":
        return f"project: {payload.get('project', '?')} ({payload.get('steps', '?')} steps)"
    elif action == "project.end":
        return f"project: {payload.get('project', '?')} -> {payload.get('status', '?')}"
    elif action == "project.step.built":
        return f"step: {payload.get('step', '?')} -> {payload.get('skill', '?')}"
    elif action == "project.step.reused":
        return f"step: {payload.get('step', '?')} reused {payload.get('skill', '?')}"
    else:
        return str(payload)[:80]


# Filesystem safety: restrict to allowed directories
_ALLOWED_ROOTS = [
    str(ROOT),
    str(ROOT / "skills"),
    str(ROOT / "projects"),
    str(ROOT / "memory"),
    str(Path.home() / "Documents"),
    "/tmp",
]

def _is_path_safe(path: str) -> bool:
    """Check if a path is within allowed directories."""
    try:
        resolved = str(Path(path).resolve())
        for allowed in _ALLOWED_ROOTS:
            if resolved.startswith(allowed):
                return True
        return False
    except Exception:
        return False


def main() -> int:
    daemon = AnubisDaemon()
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())

def main() -> int:
    daemon = AnubisDaemon()
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    try:
        resolved = str(Path(path).resolve())
        for allowed in _ALLOWED_ROOTS:
            if resolved.startswith(allowed):
                return True
        return False
    except Exception:
        return False


def main() -> int:
    daemon = AnubisDaemon()
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())

def main() -> int:
    daemon = AnubisDaemon()
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    daemon.start()
    return 0


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
    sys.exit(main())
    sys.exit(main())
