"""Calendar & scheduling — appointments, reminders, time management.

ANUBIS manages your calendar to:
- Track appointments and remind you before they happen
- Suggest optimal times for tasks
- Detect scheduling conflicts
- Factor your patterns into scheduling
- Integrate with proactive reminders ("you have a meeting in 30 minutes")

SOURCES:
- ICS files (iCalendar format — standard, works with Google/Apple/Outlook export)
- CalDAV (for live calendar sync — requires caldav library)
- Local calendar (ANUBIS's own event store)

Uses stdlib only for ICS parsing. CalDAV is optional.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable


# Event types
EVENT_APPOINTMENT = "appointment"
EVENT_MEETING = "meeting"
EVENT_REMINDER = "reminder"
EVENT_TASK = "task"
EVENT_RECURRING = "recurring"
EVENT_DEADLINE = "deadline"
EVENT_PERSONAL = "personal"

# Reminder timing
REMIND_15_MIN = 15 * 60
REMIND_30_MIN = 30 * 60
REMIND_1_HOUR = 60 * 60
REMIND_1_DAY = 24 * 60 * 60
REMIND_1_WEEK = 7 * 24 * 60 * 60


@dataclass
class CalendarEvent:
    """A calendar event/appointment."""
    event_id: str
    title: str = ""
    description: str = ""
    event_type: str = EVENT_APPOINTMENT
    start_time: float = 0.0  # Unix timestamp
    end_time: float = 0.0
    all_day: bool = False
    location: str = ""
    attendees: list[str] = field(default_factory=list)  # names or emails
    reminder_seconds: int = REMIND_30_MIN  # remind N seconds before
    reminded: bool = False
    completed: bool = False
    recurring: bool = False
    recurrence_rule: str = ""  # RRULE format (e.g., "FREQ=WEEKLY;BYDAY=MO")
    priority: int = 5  # 1=high, 5=normal, 9=low
    tags: list[str] = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "title": self.title,
            "description": self.description,
            "event_type": self.event_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "all_day": self.all_day,
            "location": self.location,
            "attendees": self.attendees,
            "reminder_seconds": self.reminder_seconds,
            "reminded": self.reminded,
            "completed": self.completed,
            "recurring": self.recurring,
            "recurrence_rule": self.recurrence_rule,
            "priority": self.priority,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def is_upcoming(self, within_seconds: float = 86400) -> bool:
        """Check if event is within the next N seconds."""
        now = time.time()
        return now <= self.start_time <= now + within_seconds

    def is_past(self) -> bool:
        return time.time() > self.end_time

    def is_now(self) -> bool:
        now = time.time()
        return self.start_time <= now <= self.end_time

    def needs_reminder(self) -> bool:
        """Check if it's time to send a reminder."""
        if self.reminded or self.completed:
            return False
        now = time.time()
        return now >= self.start_time - self.reminder_seconds and now <= self.start_time

    def time_until(self) -> float:
        """Seconds until event starts."""
        return self.start_time - time.time()


@dataclass
class ScheduleSlot:
    """A free time slot in the schedule."""
    start_time: float
    end_time: float
    duration_minutes: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration_minutes,
        }


class Calendar:
    """Calendar and scheduling system.

    Manages events, reminders, and scheduling. Can import ICS files
    and sync with CalDAV servers (optional).
    """

    ACTOR = "anubis.calendar"

    def __init__(
        self,
        root: str | Path,
        *,
        ledger: Any | None = None,
        on_reminder: Callable[[CalendarEvent], None] | None = None,
    ) -> None:
        self.root = Path(root)
        self.ledger = ledger
        self.on_reminder = on_reminder

        self._state_dir = self.root / "memory" / "calendar"
        self._state_dir.mkdir(parents=True, exist_ok=True)
        self._events_file = self._state_dir / "events.json"

        self._events: dict[str, CalendarEvent] = {}
        self._load()

    # --------------------------------------------------- event management

    def add_event(
        self,
        title: str,
        start_time: float,
        *,
        end_time: float = 0,
        description: str = "",
        event_type: str = EVENT_APPOINTMENT,
        all_day: bool = False,
        location: str = "",
        attendees: list[str] | None = None,
        reminder_seconds: int = REMIND_30_MIN,
        priority: int = 5,
        tags: list[str] | None = None,
        recurring: bool = False,
        recurrence_rule: str = "",
    ) -> CalendarEvent:
        """Add a calendar event."""
        if end_time == 0:
            end_time = start_time + 3600  # default 1 hour

        event_id = hashlib.sha256(
            f"event:{title}:{start_time}:{time.time()}".encode()
        ).hexdigest()[:16]

        event = CalendarEvent(
            event_id=event_id,
            title=title,
            description=description,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            location=location,
            attendees=attendees or [],
            reminder_seconds=reminder_seconds,
            priority=priority,
            tags=tags or [],
            recurring=recurring,
            recurrence_rule=recurrence_rule,
            created_at=time.time(),
            updated_at=time.time(),
        )

        self._events[event_id] = event
        self._save()
        self._log("event.added", {"title": title, "start": start_time})
        return event

    def remove_event(self, event_id: str) -> bool:
        if event_id in self._events:
            del self._events[event_id]
            self._save()
            return True
        return False

    def update_event(self, event_id: str, **kwargs: Any) -> bool:
        event = self._events.get(event_id)
        if event is None:
            return False
        for key, value in kwargs.items():
            if hasattr(event, key) and key not in ("event_id", "created_at"):
                setattr(event, key, value)
        event.updated_at = time.time()
        self._save()
        return True

    def complete_event(self, event_id: str) -> bool:
        return self.update_event(event_id, completed=True)

    def get_event(self, event_id: str) -> dict[str, Any] | None:
        e = self._events.get(event_id)
        return e.to_dict() if e else None

    def get_events(self) -> list[dict[str, Any]]:
        return [e.to_dict() for e in sorted(
            self._events.values(), key=lambda x: x.start_time
        )]

    def get_upcoming_events(self, within_hours: float = 24) -> list[dict[str, Any]]:
        """Get events in the next N hours."""
        cutoff = time.time() + within_hours * 3600
        now = time.time()
        return [
            e.to_dict() for e in sorted(self._events.values(), key=lambda x: x.start_time)
            if now <= e.start_time <= cutoff and not e.completed
        ]

    def get_today_events(self) -> list[dict[str, Any]]:
        """Get all events today."""
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day).timestamp()
        end_of_day = (datetime(now.year, now.month, now.day) + timedelta(days=1)).timestamp()
        return [
            e.to_dict() for e in sorted(self._events.values(), key=lambda x: x.start_time)
            if start_of_day <= e.start_time < end_of_day and not e.completed
        ]

    def get_events_by_type(self, event_type: str) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events.values() if e.event_type == event_type]

    def get_events_by_tag(self, tag: str) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events.values() if tag in e.tags]

    # --------------------------------------------------- reminders

    def check_reminders(self) -> list[CalendarEvent]:
        """Check for events that need reminders. Triggers callback."""
        to_remind: list[CalendarEvent] = []
        for event in self._events.values():
            if event.needs_reminder():
                event.reminded = True
                to_remind.append(event)
                if self.on_reminder:
                    try:
                        self.on_reminder(event)
                    except Exception:
                        pass
                self._log("reminder.sent", {"event": event.title})
        if to_remind:
            self._save()
        return to_remind

    def get_pending_reminders(self) -> list[dict[str, Any]]:
        """Get events that will need reminders soon."""
        return [
            e.to_dict() for e in self._events.values()
            if e.needs_reminder() and not e.reminded
        ]

    # --------------------------------------------------- scheduling

    def find_free_slots(
        self, date: float, duration_minutes: float = 60
    ) -> list[dict[str, Any]]:
        """Find free time slots on a given day."""
        day_start = datetime.fromtimestamp(date).replace(
            hour=8, minute=0, second=0, microsecond=0
        )
        day_end = day_start.replace(hour=20, minute=0)

        busy: list[tuple[float, float]] = []
        for event in self._events.values():
            if event.completed:
                continue
            event_date = datetime.fromtimestamp(event.start_time)
            if event_date.date() == day_start.date():
                busy.append((event.start_time, event.end_time))

        busy.sort()
        slots: list[dict[str, Any]] = []
        current = day_start.timestamp()

        for b_start, b_end in busy:
            if b_start > current:
                slot_duration = (b_start - current) / 60
                if slot_duration >= duration_minutes:
                    slots.append({
                        "start_time": current,
                        "end_time": b_start,
                        "duration_minutes": slot_duration,
                    })
            current = max(current, b_end)

        # Final slot
        if current < day_end.timestamp():
            slot_duration = (day_end.timestamp() - current) / 60
            if slot_duration >= duration_minutes:
                slots.append({
                    "start_time": current,
                    "end_time": day_end.timestamp(),
                    "duration_minutes": slot_duration,
                })

        return slots

    def suggest_time(self, duration_minutes: float = 60, days_ahead: int = 7) -> dict[str, Any] | None:
        """Suggest the best time for a new event."""
        for day_offset in range(days_ahead):
            date = time.time() + day_offset * 86400
            slots = self.find_free_slots(date, duration_minutes)
            if slots:
                # Return the first available slot
                return slots[0]
        return None

    def detect_conflicts(self, start_time: float, end_time: float) -> list[dict[str, Any]]:
        """Detect scheduling conflicts for a time range."""
        conflicts = []
        for event in self._events.values():
            if event.completed:
                continue
            # Overlap check
            if start_time < event.end_time and end_time > event.start_time:
                conflicts.append(event.to_dict())
        return conflicts

    # --------------------------------------------------- ICS import/export

    def import_ics(self, ics_content: str) -> int:
        """Import events from ICS (iCalendar) content.

        Basic parser — handles VEVENT blocks with DTSTART, DTEND,
        SUMMARY, DESCRIPTION, LOCATION.
        """
        count = 0
        lines = ics_content.replace("\r\n", "\n").split("\n")
        current_event: dict[str, str] = {}
        in_event = False

        for line in lines:
            line = line.strip()
            if line == "BEGIN:VEVENT":
                in_event = True
                current_event = {}
            elif line == "END:VEVENT":
                in_event = False
                if "SUMMARY" in current_event and "DTSTART" in current_event:
                    start = self._parse_ics_date(current_event["DTSTART"])
                    end = self._parse_ics_date(
                        current_event.get("DTEND", current_event["DTSTART"])
                    )
                    if start:
                        self.add_event(
                            title=current_event["SUMMARY"],
                            start_time=start,
                            end_time=end or start + 3600,
                            description=current_event.get("DESCRIPTION", ""),
                            location=current_event.get("LOCATION", ""),
                            all_day="VALUE=DATE" in current_event.get("DTSTART", ""),
                        )
                        count += 1
            elif in_event and ":" in line:
                key, value = line.split(":", 1)
                current_event[key] = value

        return count

    def export_ics(self) -> str:
        """Export all events as ICS."""
        lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//ANUBIS//Calendar//EN",
        ]
        for event in self._events.values():
            lines.extend([
                "BEGIN:VEVENT",
                f"UID:{event.event_id}@anubis",
                f"DTSTART:{self._format_ics_date(event.start_time)}",
                f"DTEND:{self._format_ics_date(event.end_time)}",
                f"SUMMARY:{event.title}",
                f"DESCRIPTION:{event.description}",
                f"LOCATION:{event.location}",
                "END:VEVENT",
            ])
        lines.append("END:VCALENDAR")
        return "\r\n".join(lines)

    def _parse_ics_date(self, value: str) -> float:
        """Parse ICS date string to Unix timestamp."""
        # Handle VALUE=DATE:YYYYMMDD
        if "VALUE=DATE:" in value:
            value = value.split("VALUE=DATE:")[1]
            dt = datetime.strptime(value, "%Y%m%d")
            return dt.timestamp()
        # Handle YYYYMMDDTHHMMSSZ
        value = value.split(":")[-1].replace("Z", "")
        try:
            dt = datetime.strptime(value, "%Y%m%dT%H%M%S")
            return dt.timestamp()
        except ValueError:
            return 0.0

    def _format_ics_date(self, timestamp: float) -> str:
        """Format Unix timestamp as ICS date string."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y%m%dT%H%M%SZ")

    # --------------------------------------------------- daily briefing

    def get_daily_briefing(self) -> str:
        """Generate a daily schedule briefing."""
        today = self.get_today_events()
        if not today:
            return "You have no events scheduled for today."

        parts = ["Today's schedule:"]
        for event in today:
            time_str = datetime.fromtimestamp(event["start_time"]).strftime("%I:%M %p")
            parts.append(f"  {time_str} — {event['title']}")
            if event.get("location"):
                parts.append(f"    Location: {event['location']}")

        # Check for upcoming reminders
        pending = self.get_pending_reminders()
        if pending:
            parts.append(f"\n  Upcoming reminders: {len(pending)}")

        return "\n".join(parts)

    # --------------------------------------------------- status

    def get_status(self) -> dict[str, Any]:
        now = time.time()
        return {
            "total_events": len(self._events),
            "upcoming_24h": len(self.get_upcoming_events(24)),
            "today_events": len(self.get_today_events()),
            "pending_reminders": len(self.get_pending_reminders()),
            "completed_events": sum(1 for e in self._events.values() if e.completed),
            "recurring_events": sum(1 for e in self._events.values() if e.recurring),
        }

    # --------------------------------------------------- persistence

    def _load(self) -> None:
        if not self._events_file.exists():
            return
        try:
            data = json.loads(self._events_file.read_text(encoding="utf-8"))
            for e_id, e in data.items():
                self._events[e_id] = CalendarEvent(
                    event_id=e_id,
                    title=e.get("title", ""),
                    description=e.get("description", ""),
                    event_type=e.get("event_type", EVENT_APPOINTMENT),
                    start_time=e.get("start_time", 0),
                    end_time=e.get("end_time", 0),
                    all_day=e.get("all_day", False),
                    location=e.get("location", ""),
                    attendees=e.get("attendees", []),
                    reminder_seconds=e.get("reminder_seconds", REMIND_30_MIN),
                    reminded=e.get("reminded", False),
                    completed=e.get("completed", False),
                    recurring=e.get("recurring", False),
                    recurrence_rule=e.get("recurrence_rule", ""),
                    priority=e.get("priority", 5),
                    tags=e.get("tags", []),
                    created_at=e.get("created_at", 0),
                    updated_at=e.get("updated_at", 0),
                )
        except Exception:
            pass

    def _save(self) -> None:
        data = {e_id: e.to_dict() for e_id, e in self._events.items()}
        self._events_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _log(self, action: str, data: dict[str, Any]) -> None:
        if self.ledger is not None:
            try:
                self.ledger.append(self.ACTOR, action, data)
            except Exception:
                pass
