"""Tests for calendar and scheduling."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.calendar import (
    Calendar, CalendarEvent, EVENT_APPOINTMENT, EVENT_MEETING,
    REMIND_30_MIN, REMIND_1_HOUR,
)


class TestCalendarEvent(unittest.TestCase):
    def test_to_dict(self):
        e = CalendarEvent(event_id="e1", title="Doctor", start_time=time.time() + 3600)
        d = e.to_dict()
        self.assertEqual(d["event_id"], "e1")
        self.assertEqual(d["title"], "Doctor")

    def test_is_upcoming(self):
        e = CalendarEvent(event_id="e1", start_time=time.time() + 1800)
        self.assertTrue(e.is_upcoming(3600))
        self.assertFalse(e.is_upcoming(900))

    def test_is_past(self):
        e = CalendarEvent(event_id="e1", start_time=time.time() - 3600, end_time=time.time() - 1800)
        self.assertTrue(e.is_past())

    def test_is_now(self):
        now = time.time()
        e = CalendarEvent(event_id="e1", start_time=now - 100, end_time=now + 100)
        self.assertTrue(e.is_now())

    def test_needs_reminder(self):
        now = time.time()
        e = CalendarEvent(
            event_id="e1", start_time=now + 600,
            reminder_seconds=REMIND_30_MIN,
        )
        self.assertTrue(e.needs_reminder())

    def test_does_not_need_reminder_after_reminded(self):
        now = time.time()
        e = CalendarEvent(
            event_id="e1", start_time=now + 600,
            reminder_seconds=REMIND_30_MIN, reminded=True,
        )
        self.assertFalse(e.needs_reminder())

    def test_time_until(self):
        e = CalendarEvent(event_id="e1", start_time=time.time() + 3600)
        self.assertAlmostEqual(e.time_until(), 3600, delta=5)


class TestCalendar(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.cal = Calendar(self.root)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_event(self):
        event = self.cal.add_event("Doctor Appointment", time.time() + 86400)
        self.assertEqual(event.title, "Doctor Appointment")
        self.assertEqual(len(self.cal.get_events()), 1)

    def test_remove_event(self):
        event = self.cal.add_event("Test", time.time() + 86400)
        self.assertTrue(self.cal.remove_event(event.event_id))
        self.assertEqual(len(self.cal.get_events()), 0)

    def test_update_event(self):
        event = self.cal.add_event("Test", time.time() + 86400)
        self.assertTrue(self.cal.update_event(event.event_id, title="Updated"))
        data = self.cal.get_event(event.event_id)
        self.assertEqual(data["title"], "Updated")

    def test_complete_event(self):
        event = self.cal.add_event("Test", time.time() + 86400)
        self.cal.complete_event(event.event_id)
        data = self.cal.get_event(event.event_id)
        self.assertTrue(data["completed"])

    def test_get_upcoming_events(self):
        now = time.time()
        self.cal.add_event("Soon", now + 3600)
        self.cal.add_event("Later", now + 86400 * 3)
        upcoming = self.cal.get_upcoming_events(within_hours=24)
        self.assertEqual(len(upcoming), 1)
        self.assertEqual(upcoming[0]["title"], "Soon")

    def test_get_today_events(self):
        now = time.time()
        self.cal.add_event("Today", now + 3600)
        self.cal.add_event("Tomorrow", now + 86400 + 3600)
        today = self.cal.get_today_events()
        self.assertEqual(len(today), 1)
        self.assertEqual(today[0]["title"], "Today")

    def test_get_events_by_type(self):
        self.cal.add_event("Meeting", time.time() + 86400, event_type=EVENT_MEETING)
        self.cal.add_event("Appt", time.time() + 86400, event_type=EVENT_APPOINTMENT)
        meetings = self.cal.get_events_by_type(EVENT_MEETING)
        self.assertEqual(len(meetings), 1)

    def test_get_events_by_tag(self):
        self.cal.add_event("Work", time.time() + 86400, tags=["work", "important"])
        self.cal.add_event("Personal", time.time() + 86400, tags=["personal"])
        work = self.cal.get_events_by_tag("work")
        self.assertEqual(len(work), 1)

    def test_check_reminders(self):
        now = time.time()
        self.cal.add_event("Soon", now + 600, reminder_seconds=REMIND_30_MIN)
        reminders = self.cal.check_reminders()
        self.assertEqual(len(reminders), 1)
        self.assertTrue(reminders[0].reminded)

    def test_check_reminders_no_duplicates(self):
        now = time.time()
        self.cal.add_event("Soon", now + 600, reminder_seconds=REMIND_30_MIN)
        self.cal.check_reminders()
        reminders = self.cal.check_reminders()
        self.assertEqual(len(reminders), 0)

    def test_on_reminder_callback(self):
        called = []
        cal = Calendar(self.root, on_reminder=lambda e: called.append(e))
        now = time.time()
        cal.add_event("Soon", now + 600, reminder_seconds=REMIND_30_MIN)
        cal.check_reminders()
        self.assertEqual(len(called), 1)

    def test_find_free_slots(self):
        now = time.time()
        # Add an event at 10am
        ten_am = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        self.cal.add_event("Meeting", ten_am.timestamp(), end_time=ten_am.timestamp() + 3600)
        slots = self.cal.find_free_slots(now, duration_minutes=60)
        self.assertTrue(len(slots) > 0)
        # None of the slots should overlap with 10am-11am
        for slot in slots:
            self.assertFalse(
                slot["start_time"] < ten_am.timestamp() + 3600 and
                slot["end_time"] > ten_am.timestamp()
            )

    def test_suggest_time(self):
        slot = self.cal.suggest_time(duration_minutes=60)
        self.assertIsNotNone(slot)
        self.assertIn("start_time", slot)

    def test_detect_conflicts(self):
        now = time.time()
        self.cal.add_event("Existing", now + 3600, end_time=now + 7200)
        conflicts = self.cal.detect_conflicts(now + 4000, now + 5000)
        self.assertEqual(len(conflicts), 1)

    def test_no_conflict(self):
        now = time.time()
        self.cal.add_event("Existing", now + 3600, end_time=now + 7200)
        conflicts = self.cal.detect_conflicts(now + 8000, now + 9000)
        self.assertEqual(len(conflicts), 0)

    def test_import_ics(self):
        ics = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
SUMMARY:Test Meeting
DTSTART:20260101T100000Z
DTEND:20260101T110000Z
DESCRIPTION:A test meeting
LOCATION:Office
END:VEVENT
BEGIN:VEVENT
SUMMARY:Another Meeting
DTSTART:20260102T140000Z
DTEND:20260102T150000Z
END:VEVENT
END:VCALENDAR"""
        count = self.cal.import_ics(ics)
        self.assertEqual(count, 2)
        events = self.cal.get_events()
        self.assertEqual(len(events), 2)

    def test_export_ics(self):
        self.cal.add_event("Test", time.time() + 86400)
        ics = self.cal.export_ics()
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("END:VCALENDAR", ics)
        self.assertIn("Test", ics)

    def test_daily_briefing_empty(self):
        briefing = self.cal.get_daily_briefing()
        self.assertIn("no events", briefing)

    def test_daily_briefing_with_events(self):
        self.cal.add_event("Meeting", time.time() + 3600, location="Office")
        briefing = self.cal.get_daily_briefing()
        self.assertIn("Meeting", briefing)
        self.assertIn("Office", briefing)

    def test_get_status(self):
        self.cal.add_event("Test", time.time() + 3600)
        status = self.cal.get_status()
        self.assertEqual(status["total_events"], 1)
        self.assertEqual(status["today_events"], 1)

    def test_events_persist(self):
        self.cal.add_event("Test", time.time() + 86400)
        cal2 = Calendar(self.root)
        self.assertEqual(len(cal2.get_events()), 1)

    def test_default_end_time(self):
        event = self.cal.add_event("Test", time.time() + 86400)
        self.assertEqual(event.end_time, event.start_time + 3600)

    def test_all_day_event(self):
        event = self.cal.add_event("Vacation", time.time() + 86400, all_day=True)
        self.assertTrue(event.all_day)


if __name__ == "__main__":
    unittest.main()
