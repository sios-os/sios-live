"""ANUBIS Sleep Protocol — goodnight, wake, and good morning routines.

This module implements the Creator's sleep/wake cycle:

GOODNIGHT:
  - Lock all smart home locks
  - Set sensory mode to sleep (listen only for wake-up commands)
  - Enter sleep monitoring mode
  - Monitor via phone accelerometer and smartwatch health data
  - Only interrupt for emergencies (fall, medical anomaly, intrusion)

WAKE:
  - Sound an alarm (TTS + notification + smart home lights)
  - Monitor accelerometer to confirm the Creator is actually awake
  - If no movement detected within 2 minutes, escalate alarm
  - Repeat until movement confirmed or Creator says "good morning"

GOOD MORNING:
  - Stop alarm monitoring
  - Set sensory mode back to ambient
  - Deliver morning briefing:
    * Calendar events for today
    * To-do list / pending missions
    * Tests run overnight (mission queue stats)
    * Skills promoted overnight
    * Creator approval queue (pending Court reviews)
    * Weather forecast
    * Any alerts that occurred during sleep

The protocol is governed — it does not unlock doors, disable security,
or change sensory mode without Creator command. Emergency interruptions
follow the standard threat escalation path.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Callable


class SleepState(IntEnum):
    AWAKE = 0         # Normal waking state
    SLEEPING = 1      # Goodnight said, monitoring sleep
    WAKING = 2        # Alarm sounding, waiting for confirmation


@dataclass
class SleepSession:
    """A single sleep session record."""
    session_id: str
    started_at: float = 0.0       # goodnight time
    ended_at: float = 0.0         # good morning time
    state: int = int(SleepState.AWAKE)
    # Sleep quality tracking
    restlessness_events: int = 0   # number of significant movements
    heart_rate_avg: float = 0.0
    heart_rate_min: float = 0.0
    heart_rate_max: float = 0.0
    # Wake tracking
    wake_requested_at: float = 0.0
    wake_confirmed_at: float = 0.0
    wake_attempts: int = 0         # how many alarm cycles
    # Alerts during sleep
    alerts_during_sleep: list[dict[str, Any]] = field(default_factory=list)
    # Doors
    doors_locked: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "state": int(self.state),
            "state_name": SleepState(self.state).name,
            "duration_hours": round((self.ended_at or time.time()) - self.started_at, 1) / 3600 if self.started_at else 0,
            "restlessness_events": self.restlessness_events,
            "heart_rate_avg": self.heart_rate_avg,
            "heart_rate_min": self.heart_rate_min,
            "heart_rate_max": self.heart_rate_max,
            "wake_requested_at": self.wake_requested_at,
            "wake_confirmed_at": self.wake_confirmed_at,
            "wake_attempts": self.wake_attempts,
            "alerts_during_sleep": self.alerts_during_sleep,
            "doors_locked": self.doors_locked,
        }


class SleepProtocol:
    """Manages the Creator's sleep/wake cycle.

    Integrates with:
    - SmartHome (lock doors)
    - SensorySystem (mode changes, alarm via TTS)
    - RemoteMonitor (accelerometer for sleep/wake detection)
    - SmartWatch (heart rate during sleep)
    - Calendar (morning briefing)
    - MissionQueue (overnight work stats)
    - SkillLibrary (promotions)
    - Court (pending approvals)
    - WeatherMonitor (morning forecast)
    - NotificationSystem (alerts)
    """

    ACTOR = "anubis.sleep"

    # Wake detection thresholds
    WAKE_MOVEMENT_THRESHOLD = 3.0    # m/s² — significant movement = awake
    WAKE_CONFIRM_WINDOW = 120.0      # seconds to wait for movement after alarm
    WAKE_RETRY_DELAY = 30.0          # seconds between alarm retries
    WAKE_MAX_RETRIES = 5             # max alarm cycles before escalation

    # Sleep restlessness threshold
    RESTLESSNESS_THRESHOLD = 8.0     # m/s² — movement during sleep

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        smarthome: Any | None = None,
        sensory: Any | None = None,
        remote_monitor: Any | None = None,
        smartwatch: Any | None = None,
        calendar: Any | None = None,
        mission_queue: Any | None = None,
        skill_library: Any | None = None,
        court: Any | None = None,
        weather: Any | None = None,
        notifications: Any | None = None,
        communicator: Any | None = None,
        on_alarm: Callable[[], None] | None = None,
        on_briefing: Callable[[str], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.smarthome = smarthome
        self.sensory = sensory
        self.remote_monitor = remote_monitor
        self.smartwatch = smartwatch
        self.calendar = calendar
        self.mission_queue = mission_queue
        self.skill_library = skill_library
        self.court = court
        self.weather = weather
        self.notifications = notifications
        self.communicator = communicator
        self.on_alarm = on_alarm
        self.on_briefing = on_briefing

        self._state_dir = self.root / "memory" / "sleep"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._sessions_file = self._state_dir / "sessions.jsonl"
        self._current_file = self._state_dir / "current.json"

        self._current: SleepSession | None = None
        self._last_accel: tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._last_accel_time: float = 0.0
        self._heart_rate_samples: list[float] = []
        self._wake_check_active: bool = False

        self._load_current()

    def _speak(self, text: str, *, priority: str = "normal") -> None:
        """Speak text through the communicator (DEMON) or sensory fallback."""
        if self.communicator is not None:
            try:
                self.communicator.speak(text, priority=priority, source="sleep")
                return
            except Exception:
                pass
        if self.sensory is not None:
            try:
                self.sensory.speak(text, priority=priority, source="sleep")
            except Exception:
                pass

    # ===========================================================
    # STATE
    # ===========================================================

    @property
    def state(self) -> SleepState:
        if self._current is None:
            return SleepState.AWAKE
        return SleepState(self._current.state)

    @property
    def is_sleeping(self) -> bool:
        return self._current is not None and self._current.state == int(SleepState.SLEEPING)

    @property
    def is_waking(self) -> bool:
        return self._current is not None and self._current.state == int(SleepState.WAKING)

    def get_status(self) -> dict[str, Any]:
        if self._current is None:
            return {
                "state": "awake",
                "session": None,
                "sessions_logged": self._count_sessions(),
            }
        return {
            "state": SleepState(self._current.state).name.lower(),
            "session": self._current.to_dict(),
            "sessions_logged": self._count_sessions(),
        }

    # ===========================================================
    # GOODNIGHT
    # ===========================================================

    def goodnight(self) -> dict[str, Any]:
        """Begin sleep mode.

        - Locks all doors
        - Sets sensory to sleep mode (listens only for wake-up commands)
        - Starts sleep monitoring
        - Only interrupts for emergencies
        """
        if self._current is not None and self._current.state in (int(SleepState.SLEEPING), int(SleepState.WAKING)):
            return {"error": f"Already in {SleepState(self._current.state).name.lower()} state"}

        session = SleepSession(
            session_id=hashlib.sha256(f"sleep:{time.time()}".encode()).hexdigest()[:16],
            started_at=time.time(),
            state=int(SleepState.SLEEPING),
        )

        # Lock all doors
        doors_locked = False
        if self.smarthome:
            try:
                devices = self.smarthome.get_devices()
                locked_count = 0
                for d in devices:
                    if d.get("device_type") == "lock":
                        result = self.smarthome.lock(d["device_id"])
                        if result.get("status") == "locked":
                            locked_count += 1
                doors_locked = locked_count > 0
                session.doors_locked = doors_locked
            except Exception:
                pass

        # Set sensory to sleep mode — listen only for wake-up commands
        # (good morning, wake me up, cancel alarm) but ignore all other audio
        if self.sensory:
            try:
                self.sensory.set_mode("sleep")
            except Exception:
                pass

        # Notify
        if self.notifications:
            try:
                self.notifications.notify(
                    "Goodnight",
                    f"Sleep mode active. Doors {'locked' if doors_locked else 'not locked'}. I will only wake you for emergencies.",
                    priority="normal",
                    category="sleep",
                )
            except Exception:
                pass

        # Speak goodnight
        self._speak(
            f"Goodnight, Creator. Doors {'locked' if doors_locked else 'are not locked'}. "
            "I will watch over you and only wake you if there is an emergency.",
            priority="normal",
        )

        self._current = session
        self._heart_rate_samples = []
        self._save_current()
        self._log("goodnight", {"doors_locked": doors_locked})
        return {
            "state": "sleeping",
            "session_id": session.session_id,
            "doors_locked": doors_locked,
            "message": "Sleep mode active. I will only wake you for emergencies.",
        }

    # ===========================================================
    # WAKE
    # ===========================================================

    def wake(self) -> dict[str, Any]:
        """Sound alarm and monitor until Creator is confirmed awake.

        - Sounds alarm (TTS + notification + lights if available)
        - Monitors accelerometer for movement
        - If no movement within 2 minutes, retries alarm
        - After max retries, escalates (emergency notification)
        - Confirmed awake when significant movement detected
        """
        if self._current is None:
            # Not in a sleep session — just sound alarm
            self._sound_alarm()
            return {"state": "waking", "message": "Alarm sounding. Not in a sleep session."}

        if self._current.state == int(SleepState.WAKING):
            return {"error": "Alarm already sounding"}

        self._current.state = int(SleepState.WAKING)
        self._current.wake_requested_at = time.time()
        self._current.wake_attempts = 1
        self._wake_check_active = True
        self._save_current()

        # Sound the alarm
        self._sound_alarm()

        self._log("wake.requested", {"attempt": self._current.wake_attempts})
        return {
            "state": "waking",
            "attempt": self._current.wake_attempts,
            "message": "Alarm sounding. I will confirm you are awake.",
        }

    def _sound_alarm(self) -> None:
        """Sound the wake alarm via all available channels."""
        # TTS alarm
        if self.sensory:
            try:
                # Set sensory to ambient so the alarm is heard
                self.sensory.set_mode("ambient")
            except Exception:
                pass
            self._speak(
                "Creator, it is time to wake up. Good morning. Please confirm you are awake.",
                priority="urgent",
            )

        # Notification
        if self.notifications:
            try:
                self.notifications.alert("WAKE UP — it is time to get up")
            except Exception:
                pass

        # Turn on lights if smart home available
        if self.smarthome:
            try:
                devices = self.smarthome.get_devices()
                for d in devices:
                    if d.get("device_type") == "light" and "bedroom" in d.get("location", "").lower():
                        self.smarthome.turn_on(d["device_id"])
            except Exception:
                pass

        # Custom alarm callback
        if self.on_alarm:
            try:
                self.on_alarm()
            except Exception:
                pass

    def confirm_awake(self) -> dict[str, Any]:
        """Confirm the Creator is awake (called when movement detected or Creator speaks)."""
        if self._current is None or self._current.state != int(SleepState.WAKING):
            return {"error": "Not in waking state"}

        self._current.wake_confirmed_at = time.time()
        self._current.state = int(SleepState.AWAKE)
        self._wake_check_active = False
        self._save_current()

        # Stop alarm
        self._speak("Good morning. I confirm you are awake.", priority="normal")

        self._log("wake.confirmed", {
            "attempts": self._current.wake_attempts,
            "duration": round(self._current.wake_confirmed_at - self._current.wake_requested_at, 1),
        })
        return {"state": "awake", "message": "Confirmed awake. Say 'good morning' for your briefing."}

    # ===========================================================
    # GOOD MORNING
    # ===========================================================

    def good_morning(self) -> dict[str, Any]:
        """Deliver the morning briefing.

        - Ends the sleep session
        - Restores sensory mode to ambient
        - Reports:
          * Calendar events for today
          * Pending missions / to-do
          * Tests run overnight (mission queue stats)
          * Skills promoted
          * Creator approval queue (pending Court reviews)
          * Weather forecast
          * Alerts during sleep
        """
        if self._current is None:
            # No sleep session — just give briefing
            briefing = self._generate_briefing()
            return {"state": "awake", "briefing": briefing}

        # End the session
        self._current.ended_at = time.time()
        self._current.state = int(SleepState.AWAKE)

        # Calculate sleep stats
        sleep_duration = self._current.ended_at - self._current.started_at
        heart_rate_avg = 0.0
        if self._heart_rate_samples:
            heart_rate_avg = sum(self._heart_rate_samples) / len(self._heart_rate_samples)
            self._current.heart_rate_avg = round(heart_rate_avg, 1)
            self._current.heart_rate_min = round(min(self._heart_rate_samples), 1)
            self._current.heart_rate_max = round(max(self._heart_rate_samples), 1)

        # Restore sensory mode
        if self.sensory:
            try:
                self.sensory.set_mode("ambient")
            except Exception:
                pass

        # Generate briefing
        briefing = self._generate_briefing()

        # Add sleep stats to briefing
        briefing["sleep_stats"] = {
            "duration_hours": round(sleep_duration / 3600, 1),
            "restlessness_events": self._current.restlessness_events,
            "heart_rate_avg": self._current.heart_rate_avg,
            "heart_rate_min": self._current.heart_rate_min,
            "heart_rate_max": self._current.heart_rate_max,
            "wake_attempts": self._current.wake_attempts,
            "alerts_during_sleep": len(self._current.alerts_during_sleep),
        }

        # Save and archive session
        self._archive_session(self._current)
        self._current = None
        self._clear_current()
        self._heart_rate_samples = []

        # Deliver briefing via TTS
        briefing_text = self._format_briefing_text(briefing)
        self._speak(briefing_text, priority="normal")

        # Also send as notification
        if self.notifications:
            try:
                self.notifications.notify(
                    "Good Morning Briefing",
                    briefing_text[:500],
                    priority="normal",
                    category="morning_briefing",
                )
            except Exception:
                pass

        if self.on_briefing:
            try:
                self.on_briefing(briefing_text)
            except Exception:
                pass

        self._log("good_morning", {"duration_hours": round(sleep_duration / 3600, 1)})
        return {"state": "awake", "briefing": briefing, "briefing_text": briefing_text}

    def _generate_briefing(self) -> dict[str, Any]:
        """Generate the morning briefing data."""
        briefing: dict[str, Any] = {}

        # Calendar events today
        if self.calendar:
            try:
                briefing["calendar_today"] = self.calendar.get_today_events()
            except Exception:
                briefing["calendar_today"] = []

        # Pending missions (to-do list)
        if self.mission_queue:
            try:
                stats = self.mission_queue.stats()
                briefing["mission_stats"] = stats
                # Get pending missions
                all_missions = self.mission_queue.all_missions()
                briefing["pending_missions"] = [
                    {"mission_id": m.mission_id, "skill_name": m.skill_name, "task": m.task}
                    for m in all_missions if m.status == "pending"
                ]
            except Exception:
                briefing["mission_stats"] = {}
                briefing["pending_missions"] = []

        # Skills promoted
        if self.skill_library:
            try:
                skills = self.skill_library.names()
                briefing["skills_promoted"] = len(skills)
                briefing["skill_names"] = list(skills)
            except Exception:
                briefing["skills_promoted"] = 0

        # Court — pending approvals
        if self.court:
            try:
                stats = self.court.stats()
                briefing["court_stats"] = stats
                # Get pending reviews (not yet creator-approved)
                reviews = self.court.reviews()
                briefing["pending_approvals"] = [
                    {
                        "review_id": r.review_id,
                        "description": r.description,
                        "artifact_hash": r.artifact_hash,
                        "verdict": r.verdict_name if hasattr(r, "verdict_name") else str(r.verdict),
                        "creator_approved": r.creator_approved,
                    }
                    for r in reviews if not r.creator_approved
                ]
            except Exception:
                briefing["court_stats"] = {}
                briefing["pending_approvals"] = []

        # Weather
        if self.weather:
            try:
                briefing["weather_forecast"] = self.weather.get_forecast()
                briefing["weather_alerts"] = self.weather.get_alerts()
            except Exception:
                briefing["weather_forecast"] = []
                briefing["weather_alerts"] = []

        # Alerts during sleep
        if self._current and self._current.alerts_during_sleep:
            briefing["sleep_alerts"] = self._current.alerts_during_sleep

        return briefing

    def _format_briefing_text(self, briefing: dict[str, Any]) -> str:
        """Format the briefing as spoken text."""
        parts: list[str] = ["Good morning, Creator. Here is your briefing."]

        # Calendar
        events = briefing.get("calendar_today", [])
        if events:
            parts.append(f"You have {len(events)} event{'s' if len(events) != 1 else ''} today:")
            for e in events[:5]:
                title = e.get("title", "untitled")
                start = e.get("start_time", 0)
                if start:
                    from time import localtime, strftime
                    time_str = strftime("%I:%M %p", localtime(start))
                    parts.append(f"  At {time_str}: {title}")
                else:
                    parts.append(f"  {title}")
        else:
            parts.append("Your calendar is clear today.")

        # Pending missions
        pending = briefing.get("pending_missions", [])
        if pending:
            parts.append(f"There {'are' if len(pending) != 1 else 'is'} {len(pending)} pending mission{'s' if len(pending) != 1 else ''} in the queue.")

        # Mission stats (tests run overnight)
        stats = briefing.get("mission_stats", {})
        if stats:
            by_status = stats.get("by_status", {})
            completed = by_status.get("completed", 0)
            failed = by_status.get("failed", 0)
            if completed or failed:
                parts.append(f"Overnight, I completed {completed} mission{'s' if completed != 1 else ''} and {failed} failed.")

        # Skills promoted
        skills_count = briefing.get("skills_promoted", 0)
        parts.append(f"There {'are' if skills_count != 1 else 'is'} {skills_count} promoted skill{'s' if skills_count != 1 else ''} in the library.")

        # Creator approval queue
        approvals = briefing.get("pending_approvals", [])
        if approvals:
            parts.append(f"You have {len(approvals)} item{'s' if len(approvals) != 1 else ''} awaiting your approval:")
            for a in approvals[:5]:
                parts.append(f"  {a.get('description', 'Unknown item')}")

        # Weather
        forecast = briefing.get("weather_forecast", [])
        if forecast:
            today = forecast[0] if isinstance(forecast, list) and forecast else forecast
            if isinstance(today, dict):
                temp = today.get("temperature", today.get("temp", ""))
                cond = today.get("condition", today.get("conditions", ""))
                if temp or cond:
                    parts.append(f"Today's weather: {cond}, {temp} degrees.")

        alerts = briefing.get("weather_alerts", [])
        if alerts:
            parts.append(f"There {'are' if len(alerts) != 1 else 'is'} {len(alerts)} weather alert{'s' if len(alerts) != 1 else ''}.")

        # Sleep alerts
        sleep_alerts = briefing.get("sleep_alerts", [])
        if sleep_alerts:
            parts.append(f"During the night, there {'were' if len(sleep_alerts) != 1 else 'was'} {len(sleep_alerts)} alert{'s' if len(sleep_alerts) != 1 else ''}:")
            for a in sleep_alerts[:3]:
                parts.append(f"  {a.get('title', a.get('type', 'Alert'))}")

        # Sleep stats
        sleep_stats = briefing.get("sleep_stats")
        if sleep_stats:
            hours = sleep_stats.get("duration_hours", 0)
            parts.append(f"You slept for {hours} hours.")
            if sleep_stats.get("restlessness_events", 0) > 10:
                parts.append("You were somewhat restless during the night.")
            hr = sleep_stats.get("heart_rate_avg", 0)
            if hr > 0:
                parts.append(f"Your average heart rate during sleep was {hr} beats per minute.")

        parts.append("That is your briefing. How can I help you today?")
        return " ".join(parts)

    # ===========================================================
    # TELEMETRY PROCESSING — called by remote monitor / smartwatch
    # ===========================================================

    def process_accelerometer(self, x: float, y: float, z: float) -> dict[str, Any]:
        """Process accelerometer data for sleep/wake detection.

        Called when the phone or smartwatch sends accelerometer data.
        """
        magnitude = (x * x + y * y + z * z) ** 0.5
        now = time.time()
        result: dict[str, Any] = {"magnitude": round(magnitude, 2)}

        if self._current is None:
            return result

        # SLEEPING — track restlessness
        if self._current.state == int(SleepState.SLEEPING):
            if magnitude > self.RESTLESSNESS_THRESHOLD:
                self._current.restlessness_events += 1
                self._save_current()
                result["restlessness"] = True

        # WAKING — check for movement = awake
        elif self._current.state == int(SleepState.WAKING):
            if magnitude > self.WAKE_MOVEMENT_THRESHOLD:
                result["wake_movement_detected"] = True
                # Confirm awake
                confirmed = self.confirm_awake()
                result["confirmed_awake"] = True
            else:
                # Check if we need to retry the alarm
                elapsed = now - self._current.wake_requested_at
                retries_elapsed = int(elapsed / self.WAKE_CONFIRM_WINDOW)
                if retries_elapsed >= self._current.wake_attempts and self._current.wake_attempts < self.WAKE_MAX_RETRIES:
                    self._current.wake_attempts += 1
                    self._sound_alarm()
                    self._save_current()
                    result["alarm_retry"] = self._current.wake_attempts
                elif self._current.wake_attempts >= self.WAKE_MAX_RETRIES:
                    # Escalate — send emergency notification
                    if self.notifications:
                        try:
                            self.notifications.alert(
                                "WAKE ESCALATION: Creator has not responded to alarm after multiple attempts."
                            )
                        except Exception:
                            pass
                    result["escalated"] = True

        self._last_accel = (x, y, z)
        self._last_accel_time = now
        return result

    def process_heart_rate(self, heart_rate: float) -> dict[str, Any]:
        """Process heart rate data during sleep.

        Called when the smartwatch sends health data.
        """
        result: dict[str, Any] = {"heart_rate": heart_rate}

        if self._current is None:
            return result

        if self._current.state == int(SleepState.SLEEPING):
            self._heart_rate_samples.append(heart_rate)
            # Check for anomalies
            if heart_rate < 40 or heart_rate > 120:
                # Unusual heart rate during sleep
                alert = {
                    "type": "heart_rate_anomaly",
                    "heart_rate": heart_rate,
                    "timestamp": time.time(),
                    "title": f"Unusual heart rate during sleep: {heart_rate} bpm",
                }
                self._current.alerts_during_sleep.append(alert)
                self._save_current()
                result["anomaly"] = True

        return result

    def record_alert(self, alert_type: str, description: str) -> None:
        """Record an alert that occurred during sleep (e.g., intrusion, fall)."""
        if self._current is None:
            return
        alert = {
            "type": alert_type,
            "description": description,
            "timestamp": time.time(),
            "title": description,
        }
        self._current.alerts_during_sleep.append(alert)
        self._save_current()

    # ===========================================================
    # CANCEL
    # ===========================================================

    def cancel(self) -> dict[str, Any]:
        """Cancel the current sleep session (emergency cancel)."""
        if self._current is None:
            return {"state": "awake", "message": "No active sleep session"}

        # Restore sensory mode
        if self.sensory:
            try:
                self.sensory.set_mode("ambient")
            except Exception:
                pass

        self._current.state = int(SleepState.AWAKE)
        self._current.ended_at = time.time()
        self._archive_session(self._current)
        self._current = None
        self._clear_current()
        self._wake_check_active = False
        self._heart_rate_samples = []

        self._log("cancel", {})
        return {"state": "awake", "message": "Sleep session cancelled"}

    # ===========================================================
    # HISTORY
    # ===========================================================

    def get_history(self, limit: int = 30) -> list[dict[str, Any]]:
        """Get recent sleep session history."""
        sessions: list[dict[str, Any]] = []
        if not self._sessions_file.exists():
            return sessions
        try:
            lines = self._sessions_file.read_text(encoding="utf-8").strip().splitlines()
            for line in reversed(lines[-limit:]):
                sessions.append(json.loads(line))
        except Exception:
            pass
        return sessions

    # ===========================================================
    # PERSISTENCE
    # ===========================================================

    def _load_current(self) -> None:
        if self._current_file.exists():
            try:
                data = json.loads(self._current_file.read_text(encoding="utf-8"))
                self._current = SleepSession(
                    session_id=data.get("session_id", ""),
                    started_at=data.get("started_at", 0),
                    ended_at=data.get("ended_at", 0),
                    state=data.get("state", int(SleepState.AWAKE)),
                    restlessness_events=data.get("restlessness_events", 0),
                    heart_rate_avg=data.get("heart_rate_avg", 0),
                    heart_rate_min=data.get("heart_rate_min", 0),
                    heart_rate_max=data.get("heart_rate_max", 0),
                    wake_requested_at=data.get("wake_requested_at", 0),
                    wake_confirmed_at=data.get("wake_confirmed_at", 0),
                    wake_attempts=data.get("wake_attempts", 0),
                    alerts_during_sleep=data.get("alerts_during_sleep", []),
                    doors_locked=data.get("doors_locked", False),
                )
            except Exception:
                self._current = None

    def _save_current(self) -> None:
        if self._current is None:
            return
        try:
            self._current_file.write_text(
                json.dumps(self._current.to_dict(), indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def _clear_current(self) -> None:
        try:
            if self._current_file.exists():
                self._current_file.unlink()
        except Exception:
            pass

    def _archive_session(self, session: SleepSession) -> None:
        try:
            with open(self._sessions_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(session.to_dict()) + "\n")
        except Exception:
            pass

    def _count_sessions(self) -> int:
        if not self._sessions_file.exists():
            return 0
        try:
            return len(self._sessions_file.read_text(encoding="utf-8").strip().splitlines())
        except Exception:
            return 0

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
