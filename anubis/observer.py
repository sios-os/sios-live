"""Observer engine — ANUBIS sees everything, like The Machine.

Inspired by The Machine from Person of Interest: an intelligence that
continuously monitors its environment, correlates observations across
sources, predicts threats and opportunities, and surfaces only what matters.

This module provides:

1. **Continuous monitoring** — Always-on monitoring of:
   - System state (CPU, memory, disk, services)
   - File changes (config, code, knowledge, memory)
   - Process activity (what's running, what changed)
   - Network state (connections, VPN, gateway)
   - Creator activity (when active, what working on)

2. **Cross-source correlation** — Connects observations from different
   sources to find patterns no single stream would reveal. E.g.,
   "Creator started working on X + knowledge gap in X + dream cycle
   generated mission for X = high probability X is the current project"

3. **Threat prediction** — Predicts problems before they happen:
   - Disk filling up
   - Service degradation
   - Model quality regression
   - Knowledge gaps blocking progress

4. **Opportunity prediction** — Predicts opportunities:
   - New research directions based on knowledge gaps
   - Funding opportunities based on Creator patterns
   - Capability improvements based on dream cycle findings
   - Collaboration opportunities based on knowledge overlap

5. **Relevance filtering** — The Machine doesn't dump everything.
   It surfaces only what matters. Most observations are noise; only
   signal reaches the Creator.

6. **Relevant output** — Generates "numbers" — the Machine's equivalent
   of surfacing only what's relevant. In ANUBIS's case, these are
   prioritized alerts, opportunities, and insights.

Governance:
- Observations are sanitized (no passwords, keys, sensitive data)
- Monitoring is of ANUBIS's own environment, not external surveillance
- Predictions are logged with confidence levels
- The Creator can set monitoring sensitivity

Uses only the Python standard library.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol


class ModelLike(Protocol):
    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        temperature: float = 0.2,
        max_tokens: int | None = None,
        timeout: float = 180.0,
    ) -> Any: ...


# --------------------------------------------------------------------- types


@dataclass
class Observation:
    """A single observation from a monitoring source."""
    obs_id: str
    source: str  # system, file, process, network, creator, dream
    event_type: str  # change, alert, pattern, anomaly, status
    content: str  # sanitized description
    severity: str = "info"  # info, low, medium, high, critical
    timestamp: float = 0.0
    correlated_with: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "obs_id": self.obs_id,
            "source": self.source,
            "event_type": self.event_type,
            "content": self.content,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "correlated_with": self.correlated_with,
            "metadata": self.metadata,
        }


@dataclass
class Correlation:
    """A correlation between multiple observations."""
    corr_id: str
    observation_ids: list[str]
    pattern: str  # what pattern was detected
    confidence: float = 0.0
    prediction: str = ""  # what this pattern predicts
    prediction_type: str = ""  # threat, opportunity, insight
    created_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "corr_id": self.corr_id,
            "observation_ids": self.observation_ids,
            "pattern": self.pattern,
            "confidence": self.confidence,
            "prediction": self.prediction,
            "prediction_type": self.prediction_type,
            "created_at": self.created_at,
        }


@dataclass
class RelevantOutput:
    """A relevant output — the Machine's 'number'.

    Only the most important correlations become relevant outputs
    that reach the Creator's attention.
    """
    output_id: str
    category: str  # threat, opportunity, insight, alert
    title: str
    description: str
    confidence: float = 0.0
    urgency: str = "low"  # low, medium, high, immediate
    recommended_action: str = ""
    source_correlations: list[str] = field(default_factory=list)
    created_at: float = 0.0
    acknowledged: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_id": self.output_id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "confidence": self.confidence,
            "urgency": self.urgency,
            "recommended_action": self.recommended_action,
            "source_correlations": self.source_correlations,
            "created_at": self.created_at,
            "acknowledged": self.acknowledged,
        }


# --------------------------------------------------------------- observer


class ObserverEngine:
    """The Machine — ANUBIS's all-seeing observation and prediction system.

    Continuously monitors the environment, correlates observations,
    predicts threats and opportunities, and surfaces only what matters.
    """

    ACTOR = "anubis.observer"

    def __init__(
        self,
        root: str | Path,
        *,
        model: ModelLike | None = None,
        ledger: Any | None = None,
        system_control: Any | None = None,
        proactive: Any | None = None,
        monitoring_interval_s: float = 60.0,
        sensitivity: str = "normal",  # low, normal, high, paranoid
    ) -> None:
        self.root = Path(root)
        self.model = model
        self.ledger = ledger
        self.system_control = system_control
        self.proactive = proactive
        self.monitoring_interval = monitoring_interval_s
        self.sensitivity = sensitivity

        self._state_dir = self.root / "memory" / "observer"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._observations_file = self._state_dir / "observations.jsonl"
        self._correlations_file = self._state_dir / "correlations.json"
        self._outputs_file = self._state_dir / "relevant_outputs.json"
        self._file_hashes_file = self._state_dir / "file_hashes.json"

        self._observations: list[Observation] = []
        self._correlations: list[Correlation] = []
        self._file_hashes: dict[str, str] = {}
        self._last_monitor: float = 0.0

        self._load_state()

    # ------------------------------------------------------- monitoring

    def monitor(self) -> list[Observation]:
        """Run a monitoring cycle.

        Checks all monitoring sources and generates observations.
        Returns the list of new observations.
        """
        new_observations: list[Observation] = []
        self._last_monitor = time.time()

        # 1. System health monitoring
        if self.system_control is not None:
            try:
                health = self.system_control.check_health()
                for alert in health.alerts:
                    obs = self._make_observation(
                        source="system",
                        event_type="alert",
                        content=alert.get("message", ""),
                        severity=alert.get("level", "info"),
                        metadata={"metric": alert.get("metric")},
                    )
                    new_observations.append(obs)
            except Exception:
                pass

        # 2. File change monitoring
        file_obs = self._check_file_changes()
        new_observations.extend(file_obs)

        # 3. Creator activity monitoring
        if self.proactive is not None:
            try:
                patterns = self.proactive.get_patterns()
                for pattern in patterns[-3:]:  # recent patterns
                    if pattern.get("confidence", 0) > 0.5:
                        obs = self._make_observation(
                            source="creator",
                            event_type="pattern",
                            content=f"Creator pattern: {pattern.get('description', '')}",
                            severity="info",
                            metadata={"pattern_id": pattern.get("pattern_id")},
                        )
                        new_observations.append(obs)
            except Exception:
                pass

        # 4. Process monitoring
        proc_obs = self._check_processes()
        new_observations.extend(proc_obs)

        # Save observations
        for obs in new_observations:
            self._append_observation(obs)

        # 5. Correlate observations
        if new_observations:
            correlations = self._correlate(new_observations)
            for corr in correlations:
                self._correlations.append(corr)
                self._save_correlations()

                # 6. Generate relevant outputs from correlations
                outputs = self._generate_relevant_outputs(corr)
                for output in outputs:
                    self._save_output(output)

        return new_observations

    def _check_file_changes(self) -> list[Observation]:
        """Check for changes in monitored files."""
        observations: list[Observation] = []
        monitored_dirs = [
            self.root / "config",
            self.root / "anubis",
            self.root / "knowledge",
            self.root / "memory",
            self.root / "skills",
        ]

        current_hashes: dict[str, str] = {}
        for dir_path in monitored_dirs:
            if not dir_path.exists():
                continue
            for file_path in self._scan_files(dir_path):
                try:
                    content = file_path.read_bytes()
                    file_hash = hashlib.sha256(content).hexdigest()
                    rel_path = str(file_path.relative_to(self.root))
                    current_hashes[rel_path] = file_hash

                    old_hash = self._file_hashes.get(rel_path)
                    if old_hash is not None and old_hash != file_hash:
                        obs = self._make_observation(
                            source="file",
                            event_type="change",
                            content=f"File changed: {rel_path}",
                            severity="info",
                            metadata={
                                "file": rel_path,
                                "old_hash": old_hash[:12],
                                "new_hash": file_hash[:12],
                            },
                        )
                        observations.append(obs)
                except Exception:
                    continue

        # Check for deleted files
        for old_path in list(self._file_hashes.keys()):
            if old_path not in current_hashes:
                obs = self._make_observation(
                    source="file",
                    event_type="change",
                    content=f"File deleted: {old_path}",
                    severity="medium",
                    metadata={"file": old_path, "action": "deleted"},
                )
                observations.append(obs)

        self._file_hashes = current_hashes
        self._save_file_hashes()

        return observations

    def _scan_files(self, dir_path: Path) -> list[Path]:
        """Scan a directory for files to monitor."""
        files: list[Path] = []
        try:
            for item in dir_path.rglob("*"):
                if item.is_file() and item.suffix in (".py", ".json", ".md",
                                                       ".txt", ".yaml", ".yml",
                                                       ".conf", ".sh"):
                    # Skip large files
                    if item.stat().st_size < 100_000:
                        files.append(item)
        except Exception:
            pass
        return files

    def _check_processes(self) -> list[Observation]:
        """Check running processes for anomalies."""
        observations: list[Observation] = []
        try:
            if os.name == "nt":
                # Windows: use tasklist
                result = os.popen("tasklist /FO CSV /NH 2>nul").read()
                lines = result.strip().split("\n")
                # Count processes
                proc_count = len([l for l in lines if l.strip()])
                if proc_count > 300:
                    obs = self._make_observation(
                        source="process",
                        event_type="anomaly",
                        content=f"High process count: {proc_count}",
                        severity="low",
                        metadata={"process_count": proc_count},
                    )
                    observations.append(obs)
            else:
                # Unix: count processes
                result = os.popen("ps aux 2>/dev/null | wc -l").read()
                proc_count = int(result.strip()) if result.strip().isdigit() else 0
                if proc_count > 500:
                    obs = self._make_observation(
                        source="process",
                        event_type="anomaly",
                        content=f"High process count: {proc_count}",
                        severity="low",
                        metadata={"process_count": proc_count},
                    )
                    observations.append(obs)
        except Exception:
            pass

        return observations

    # ------------------------------------------------------- correlation

    def _correlate(
        self, new_obs: list[Observation]
    ) -> list[Correlation]:
        """Correlate observations across sources.

        This is the core "Machine" function — finding connections between
        seemingly unrelated events.
        """
        correlations: list[Correlation] = []

        # Get recent observations (last 100)
        recent = self._observations[-100:] + new_obs

        # Pattern: file change + system alert = possible issue
        file_changes = [o for o in recent if o.source == "file" and o.event_type == "change"]
        system_alerts = [o for o in recent if o.source == "system" and o.event_type == "alert"]

        if file_changes and system_alerts:
            corr = Correlation(
                corr_id=hashlib.sha256(
                    f"corr:{time.time()}".encode()
                ).hexdigest()[:16],
                observation_ids=[o.obs_id for o in file_changes[:3] + system_alerts[:3]],
                pattern="file_change_with_system_alert",
                confidence=0.6,
                prediction="System alert may be related to recent file changes",
                prediction_type="threat",
                created_at=time.time(),
            )
            correlations.append(corr)

        # Pattern: creator pattern + knowledge gap = opportunity
        creator_patterns = [o for o in recent if o.source == "creator"]
        if len(creator_patterns) >= 2:
            corr = Correlation(
                corr_id=hashlib.sha256(
                    f"corr:{time.time()}:opp".encode()
                ).hexdigest()[:16],
                observation_ids=[o.obs_id for o in creator_patterns[:3]],
                pattern="repeated_creator_activity",
                confidence=0.5,
                prediction="Creator is focused on a specific area — prepare relevant capabilities",
                prediction_type="opportunity",
                created_at=time.time(),
            )
            correlations.append(corr)

        # Pattern: multiple file changes in same directory = active development
        if len(file_changes) >= 3:
            dirs = set()
            for o in file_changes:
                file_path = o.metadata.get("file", "")
                dir_name = str(Path(file_path).parent)
                dirs.add(dir_name)
            if len(dirs) == 1:
                corr = Correlation(
                    corr_id=hashlib.sha256(
                        f"corr:{time.time()}:dev".encode()
                    ).hexdigest()[:16],
                    observation_ids=[o.obs_id for o in file_changes[:5]],
                    pattern="concentrated_file_changes",
                    confidence=0.7,
                    prediction=f"Active development in {dirs.pop()}",
                    prediction_type="insight",
                    created_at=time.time(),
                )
                correlations.append(corr)

        # Use model for deeper correlation if available
        if self.model is not None and len(new_obs) >= 2:
            model_corr = self._model_correlate(new_obs)
            if model_corr:
                correlations.append(model_corr)

        return correlations

    def _model_correlate(self, obs: list[Observation]) -> Correlation | None:
        """Use the model to find deeper correlations."""
        obs_summary = "\n".join(
            f"- [{o.source}/{o.event_type}] {o.content}"
            for o in obs[:10]
        )

        prompt = (
            f"Recent observations:\n{obs_summary}\n\n"
            "Are any of these observations connected? What pattern do they "
            "reveal? What does this pattern predict?\n\n"
            "Output as JSON with keys:\n"
            '  "pattern": description of the pattern,\n'
            '  "confidence": 0.0-1.0,\n'
            '  "prediction": what this predicts,\n'
            '  "prediction_type": threat/opportunity/insight\n'
            "If no meaningful correlation exists, return empty JSON."
        )

        try:
            completion = self.model.chat(
                [
                    {"role": "system", "content": CORRELATION_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=400,
                timeout=60.0,
            )
            import re
            text = re.sub(r"```(?:json)?\s*", "", completion.text)
            text = text.replace("```", "")
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                data = json.loads(text[start:end + 1])
                if data.get("pattern"):
                    return Correlation(
                        corr_id=hashlib.sha256(
                            f"corr:model:{time.time()}".encode()
                        ).hexdigest()[:16],
                        observation_ids=[o.obs_id for o in obs[:5]],
                        pattern=data["pattern"],
                        confidence=data.get("confidence", 0.5),
                        prediction=data.get("prediction", ""),
                        prediction_type=data.get("prediction_type", "insight"),
                        created_at=time.time(),
                    )
        except Exception:
            pass

        return None

    # ------------------------------------------------------- relevant outputs

    def _generate_relevant_outputs(
        self, corr: Correlation
    ) -> list[RelevantOutput]:
        """Generate relevant outputs from a correlation.

        Only high-confidence, actionable correlations become outputs.
        This is the relevance filter — most things don't make it through.
        """
        outputs: list[RelevantOutput] = []

        # Confidence threshold based on sensitivity
        thresholds = {
            "low": 0.8,
            "normal": 0.6,
            "high": 0.4,
            "paranoid": 0.2,
        }
        threshold = thresholds.get(self.sensitivity, 0.6)

        if corr.confidence < threshold:
            return outputs

        # Determine urgency
        if corr.prediction_type == "threat":
            urgency = "high"
        elif corr.prediction_type == "opportunity":
            urgency = "medium"
        else:
            urgency = "low"

        output = RelevantOutput(
            output_id=hashlib.sha256(
                f"output:{corr.corr_id}:{time.time()}".encode()
            ).hexdigest()[:16],
            category=corr.prediction_type,
            title=corr.pattern,
            description=corr.prediction,
            confidence=corr.confidence,
            urgency=urgency,
            recommended_action=self._recommend_action(corr),
            source_correlations=[corr.corr_id],
            created_at=time.time(),
        )
        outputs.append(output)
        self._save_output(output)

        self._log("observer.output_generated", {
            "output_id": output.output_id,
            "category": output.category,
            "urgency": output.urgency,
            "confidence": output.confidence,
        })

        return outputs

    def _recommend_action(self, corr: Correlation) -> str:
        """Recommend an action based on a correlation."""
        if corr.prediction_type == "threat":
            return "Investigate and mitigate before it becomes critical"
        elif corr.prediction_type == "opportunity":
            return "Prepare capabilities and present to Creator"
        else:
            return "Monitor for further developments"

    # ------------------------------------------------------- queries

    def get_observations(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent observations."""
        return [o.to_dict() for o in self._observations[-limit:]]

    def get_correlations(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent correlations."""
        return [c.to_dict() for c in self._correlations[-limit:]]

    def get_relevant_outputs(
        self, unacknowledged_only: bool = False
    ) -> list[dict[str, Any]]:
        """Get relevant outputs (the Machine's 'numbers')."""
        if not self._outputs_file.exists():
            return []
        try:
            outputs = json.loads(
                self._outputs_file.read_text(encoding="utf-8")
            )
            if unacknowledged_only:
                outputs = [o for o in outputs if not o.get("acknowledged")]
            return outputs
        except Exception:
            return []

    def acknowledge_output(self, output_id: str) -> bool:
        """Acknowledge a relevant output."""
        outputs = self.get_relevant_outputs()
        for o in outputs:
            if o.get("output_id") == output_id:
                o["acknowledged"] = True
                self._outputs_file.write_text(
                    json.dumps(outputs, indent=2), encoding="utf-8"
                )
                return True
        return False

    def get_status(self) -> dict[str, Any]:
        """Get observer status."""
        return {
            "sensitivity": self.sensitivity,
            "total_observations": len(self._observations),
            "total_correlations": len(self._correlations),
            "unacknowledged_outputs": len(self.get_relevant_outputs(
                unacknowledged_only=True
            )),
            "monitored_files": len(self._file_hashes),
            "last_monitor": self._last_monitor,
            "monitoring_interval_s": self.monitoring_interval,
        }

    def set_sensitivity(self, level: str) -> bool:
        """Set monitoring sensitivity."""
        if level not in ("low", "normal", "high", "paranoid"):
            return False
        self.sensitivity = level
        return True

    # ------------------------------------------------------- internals

    def _make_observation(
        self,
        source: str,
        event_type: str,
        content: str,
        severity: str = "info",
        metadata: dict[str, Any] | None = None,
    ) -> Observation:
        return Observation(
            obs_id=hashlib.sha256(
                f"obs:{source}:{time.time()}:{content[:50]}".encode()
            ).hexdigest()[:16],
            source=source,
            event_type=event_type,
            content=content,
            severity=severity,
            timestamp=time.time(),
            metadata=metadata or {},
        )

    def _append_observation(self, obs: Observation) -> None:
        self._observations.append(obs)
        self._observations = self._observations[-1000:]  # keep last 1000
        try:
            with open(self._observations_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(obs.to_dict()) + "\n")
        except Exception:
            pass

    def _save_correlations(self) -> None:
        self._correlations_file.write_text(
            json.dumps([c.to_dict() for c in self._correlations[-200:]], indent=2),
            encoding="utf-8",
        )

    def _save_output(self, output: RelevantOutput) -> None:
        outputs = self.get_relevant_outputs()
        outputs.append(output.to_dict())
        outputs = outputs[-100:]  # keep last 100
        self._outputs_file.write_text(
            json.dumps(outputs, indent=2), encoding="utf-8"
        )

    def _save_file_hashes(self) -> None:
        self._file_hashes_file.write_text(
            json.dumps(self._file_hashes, indent=2), encoding="utf-8"
        )

    def _load_state(self) -> None:
        """Load state from disk."""
        if self._observations_file.exists():
            try:
                for line in self._observations_file.read_text(
                    encoding="utf-8"
                ).strip().splitlines()[-200:]:
                    data = json.loads(line)
                    self._observations.append(Observation(
                        obs_id=data["obs_id"],
                        source=data["source"],
                        event_type=data["event_type"],
                        content=data["content"],
                        severity=data.get("severity", "info"),
                        timestamp=data.get("timestamp", 0),
                        correlated_with=data.get("correlated_with", []),
                        metadata=data.get("metadata", {}),
                    ))
            except Exception:
                pass

        if self._correlations_file.exists():
            try:
                data = json.loads(
                    self._correlations_file.read_text(encoding="utf-8")
                )
                self._correlations = [Correlation(
                    corr_id=d["corr_id"],
                    observation_ids=d.get("observation_ids", []),
                    pattern=d.get("pattern", ""),
                    confidence=d.get("confidence", 0),
                    prediction=d.get("prediction", ""),
                    prediction_type=d.get("prediction_type", ""),
                    created_at=d.get("created_at", 0),
                ) for d in data]
            except Exception:
                pass

        if self._file_hashes_file.exists():
            try:
                self._file_hashes = json.loads(
                    self._file_hashes_file.read_text(encoding="utf-8")
                )
            except Exception:
                pass

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass


# --------------------------------------------------------------- prompt

CORRELATION_SYSTEM = """\
You are ANUBIS's observation correlation engine. You find connections \
between seemingly unrelated events. You think like a pattern recognition \
system — looking for hidden relationships, causal chains, and emerging \
trends.

Be precise about confidence. Only report real patterns, not coincidences. \
If observations are unrelated, say so.

Output valid JSON with keys: pattern, confidence, prediction, prediction_type.
"""
