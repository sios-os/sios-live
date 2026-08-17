"""Tests for Tier 2 modules: news, finance, packages, phone, music, notifications."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.news_feeds import NewsFeeds, NewsItem
from anubis.finance import FinanceTracker, Transaction, Bill, CAT_FOOD, CAT_TRANSPORT
from anubis.packages import PackageTracker, Package, CARRIER_UPS, CARRIER_FEDEX, STATUS_DELIVERED, STATUS_SHIPPED
from anubis.phone_protocol import PhoneProtocol, PhoneDevice, Notification, DEVICE_ACTIVE
from anubis.music import MusicController, Playlist, MOOD_CALM, MOOD_FOCUS, PLAYBACK_STOPPED
from anubis.notifications import NotificationSystem, Notification, PRIORITY_URGENT, CAT_SECURITY


class TestNewsFeeds(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.news = NewsFeeds(Path(self.tmpdir), interests=["AI", "space"])

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_interest(self):
        self.news.add_interest("quantum")
        self.assertIn("quantum", self.news.interests)

    def test_add_feed(self):
        self.news.add_feed("https://example.com/feed.xml")
        self.assertIn("https://example.com/feed.xml", self.news.feeds)

    def test_score_relevance(self):
        item = NewsItem(item_id="n1", title="New AI breakthrough", summary="AI advances")
        score = self.news._score_relevance(item)
        self.assertGreater(score, 0)

    def test_score_relevance_no_match(self):
        item = NewsItem(item_id="n1", title="Cooking recipe", summary="How to bake")
        score = self.news._score_relevance(item)
        self.assertEqual(score, 0)

    def test_get_items_empty(self):
        self.assertEqual(self.news.get_items(), [])

    def test_get_relevant_items(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="AI news", relevance_score=0.6)
        self.news._items["n2"] = NewsItem(item_id="n2", title="Cooking", relevance_score=0.0)
        relevant = self.news.get_relevant_items(min_score=0.4)
        self.assertEqual(len(relevant), 1)

    def test_mark_read(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="Test")
        self.assertTrue(self.news.mark_read("n1"))
        self.assertTrue(self.news._items["n1"].read)

    def test_save_item(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="Test")
        self.assertTrue(self.news.save_item("n1"))
        self.assertTrue(self.news._items["n1"].saved)

    def test_get_saved_items(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="Test", saved=True)
        saved = self.news.get_saved_items()
        self.assertEqual(len(saved), 1)

    def test_daily_briefing_empty(self):
        briefing = self.news.get_daily_briefing()
        self.assertIn("No relevant", briefing)

    def test_daily_briefing_with_items(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="AI breakthrough", relevance_score=0.6)
        briefing = self.news.get_daily_briefing()
        self.assertIn("AI breakthrough", briefing)

    def test_get_status(self):
        status = self.news.get_status()
        self.assertIn("total_items", status)
        self.assertIn("feeds", status)

    def test_persist(self):
        self.news._items["n1"] = NewsItem(item_id="n1", title="Test")
        self.news._save()
        news2 = NewsFeeds(Path(self.tmpdir))
        self.assertEqual(len(news2.get_items()), 1)


class TestFinanceTracker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.finance = FinanceTracker(Path(self.tmpdir), monthly_budget=5000)

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_transaction(self):
        txn = self.finance.add_transaction(-50, "Grocery shopping", merchant="Whole Foods")
        self.assertEqual(txn.amount, -50)
        self.assertEqual(txn.category, CAT_FOOD)

    def test_categorize_food(self):
        txn = self.finance.add_transaction(-30, "McDonalds")
        self.assertEqual(txn.category, CAT_FOOD)

    def test_categorize_transport(self):
        txn = self.finance.add_transaction(-40, "Shell gas station")
        self.assertEqual(txn.category, CAT_TRANSPORT)

    def test_categorize_unknown(self):
        txn = self.finance.add_transaction(-100, "Random purchase")
        self.assertEqual(txn.category, "unknown")

    def test_flag_large_transaction(self):
        txn = self.finance.add_transaction(-600, "Big purchase")
        self.assertTrue(txn.flagged)
        self.assertIn("Large", txn.flag_reason)

    def test_flag_new_merchant(self):
        txn = self.finance.add_transaction(-150, "Purchase", merchant="NewStore")
        self.assertTrue(txn.flagged)
        self.assertIn("New merchant", txn.flag_reason)

    def test_no_flag_small(self):
        txn = self.finance.add_transaction(-20, "Coffee")
        self.assertFalse(txn.flagged)

    def test_add_bill(self):
        bill = self.finance.add_bill("Electric", 150, due_day=15)
        self.assertEqual(bill.name, "Electric")
        self.assertEqual(bill.amount, 150)

    def test_mark_bill_paid(self):
        bill = self.finance.add_bill("Electric", 150)
        self.assertTrue(self.finance.mark_bill_paid(bill.bill_id))
        self.assertTrue(self.finance._bills[bill.bill_id].paid)

    def test_spending_by_category(self):
        self.finance.add_transaction(-50, "Grocery")
        self.finance.add_transaction(-30, "Gas")
        spending = self.finance.get_spending_by_category()
        self.assertIn(CAT_FOOD, spending)

    def test_monthly_spending(self):
        self.finance.add_transaction(-100, "Shopping")
        self.assertGreater(self.finance.get_monthly_spending(), 0)

    def test_income(self):
        self.finance.add_transaction(3000, "Salary deposit")
        self.assertGreater(self.finance.get_income(), 0)

    def test_import_csv(self):
        csv = "12/01/2026,Grocery Store,-50.00\n12/02/2026,Gas Station,-40.00"
        count = self.finance.import_csv(csv)
        self.assertEqual(count, 2)

    def test_get_status(self):
        status = self.finance.get_status()
        self.assertEqual(status["monthly_budget"], 5000)

    def test_persist(self):
        self.finance.add_transaction(-50, "Test")
        finance2 = FinanceTracker(Path(self.tmpdir))
        self.assertEqual(len(finance2.get_transactions()), 1)

    def test_on_flagged_callback(self):
        called = []
        ft = FinanceTracker(Path(self.tmpdir), on_flagged=lambda t: called.append(t))
        ft.add_transaction(-600, "Big purchase")
        self.assertEqual(len(called), 1)


class TestPackageTracker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.tracker = PackageTracker(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_add_package(self):
        pkg = self.tracker.add_package("1Z1234567890123456", CARRIER_UPS, "Widget")
        self.assertEqual(pkg.carrier, CARRIER_UPS)

    def test_detect_carrier_ups(self):
        self.assertEqual(self.tracker.detect_carrier("1Z1234567890123456"), CARRIER_UPS)

    def test_detect_carrier_fedex(self):
        self.assertEqual(self.tracker.detect_carrier("123456789012345"), CARRIER_FEDEX)

    def test_detect_carrier_unknown(self):
        self.assertEqual(self.tracker.detect_carrier("ABC123"), "Unknown")

    def test_update_status(self):
        pkg = self.tracker.add_package("123", CARRIER_FEDEX, "Test")
        self.assertTrue(self.tracker.update_status(pkg.package_id, STATUS_SHIPPED))
        self.assertEqual(pkg.status, STATUS_SHIPPED)

    def test_delivered_callback(self):
        called = []
        tracker = PackageTracker(Path(self.tmpdir), on_delivered=lambda p: called.append(p))
        pkg = tracker.add_package("123", CARRIER_FEDEX)
        tracker.update_status(pkg.package_id, STATUS_DELIVERED)
        self.assertEqual(len(called), 1)

    def test_get_active_packages(self):
        pkg = self.tracker.add_package("123", CARRIER_FEDEX)
        self.tracker.update_status(pkg.package_id, STATUS_DELIVERED)
        active = self.tracker.get_active_packages()
        self.assertEqual(len(active), 0)

    def test_get_delivered(self):
        pkg = self.tracker.add_package("123", CARRIER_FEDEX)
        self.tracker.update_status(pkg.package_id, STATUS_DELIVERED)
        delivered = self.tracker.get_delivered_packages()
        self.assertEqual(len(delivered), 1)

    def test_remove_package(self):
        pkg = self.tracker.add_package("123", CARRIER_FEDEX)
        self.assertTrue(self.tracker.remove_package(pkg.package_id))

    def test_persist(self):
        self.tracker.add_package("123", CARRIER_FEDEX, "Test")
        tracker2 = PackageTracker(Path(self.tmpdir))
        self.assertEqual(len(tracker2.get_packages()), 1)


class TestPhoneProtocol(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.proto = PhoneProtocol(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_device(self):
        device, token = self.proto.register_device("My Phone", "creator", "android")
        self.assertEqual(device.name, "My Phone")
        self.assertTrue(token)

    def test_authenticate(self):
        device, token = self.proto.register_device("Phone", "creator")
        self.assertTrue(self.proto.authenticate(device.device_id, token))
        self.assertFalse(self.proto.authenticate(device.device_id, "wrong"))

    def test_revoke_device(self):
        device, _ = self.proto.register_device("Phone", "creator")
        self.assertTrue(self.proto.revoke_device(device.device_id))
        self.assertFalse(self.proto.authenticate(device.device_id, device.token))

    def test_heartbeat(self):
        device, _ = self.proto.register_device("Phone", "creator")
        self.assertTrue(self.proto.heartbeat(device.device_id, battery=80, charging=True))
        self.assertEqual(self.proto._devices[device.device_id].battery_level, 80)

    def test_send_notification(self):
        device, _ = self.proto.register_device("Phone", "creator")
        notif = self.proto.send_notification(device.device_id, "Alert", "Test message")
        self.assertEqual(notif.title, "Alert")

    def test_get_pending_notifications(self):
        device, _ = self.proto.register_device("Phone", "creator")
        self.proto.send_notification(device.device_id, "Alert", "Test")
        pending = self.proto.get_pending_notifications(device.device_id)
        self.assertEqual(len(pending), 1)

    def test_mark_delivered(self):
        device, _ = self.proto.register_device("Phone", "creator")
        notif = self.proto.send_notification(device.device_id, "Alert", "Test")
        self.assertTrue(self.proto.mark_notification_delivered(notif.notif_id))
        pending = self.proto.get_pending_notifications(device.device_id)
        self.assertEqual(len(pending), 0)

    def test_receive_telemetry(self):
        device, _ = self.proto.register_device("Phone", "creator")
        self.assertTrue(self.proto.receive_telemetry(device.device_id, {"type": "gps", "lat": 40}))

    def test_telemetry_callback(self):
        called = []
        proto = PhoneProtocol(Path(self.tmpdir), on_telemetry=lambda d, data: called.append(data))
        device, _ = proto.register_device("Phone", "creator")
        proto.receive_telemetry(device.device_id, {"type": "gps"})
        self.assertEqual(len(called), 1)

    def test_get_active_devices(self):
        device, _ = self.proto.register_device("Phone", "creator")
        self.proto.heartbeat(device.device_id)
        active = self.proto.get_active_devices()
        self.assertEqual(len(active), 1)

    def test_persist(self):
        device, _ = self.proto.register_device("Phone", "creator")
        proto2 = PhoneProtocol(Path(self.tmpdir))
        self.assertEqual(len(proto2.get_devices()), 1)


class TestMusicController(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.music = MusicController(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_playlist(self):
        pl = self.music.create_playlist("Chill", MOOD_CALM)
        self.assertEqual(pl.name, "Chill")
        self.assertEqual(pl.mood, MOOD_CALM)

    def test_add_track_to_playlist(self):
        pl = self.music.create_playlist("Chill", MOOD_CALM)
        self.assertTrue(self.music.add_track_to_playlist(pl.playlist_id, "Song", "Artist"))
        self.assertEqual(len(pl.tracks), 1)

    def test_get_playlists(self):
        self.music.create_playlist("Test", MOOD_FOCUS)
        playlists = self.music.get_playlists()
        self.assertEqual(len(playlists), 1)

    def test_set_mood(self):
        result = self.music.set_mood(MOOD_CALM)
        self.assertTrue(result["success"])
        self.assertEqual(result["mood"], MOOD_CALM)

    def test_set_mood_unknown(self):
        result = self.music.set_mood("nonexistent")
        self.assertFalse(result["success"])

    def test_mood_recommendation(self):
        self.assertEqual(self.music.get_mood_recommendation("happy"), "happy")
        self.assertEqual(self.music.get_mood_recommendation("stressed"), "stressed")

    def test_set_volume_valid(self):
        result = self.music.set_volume(50)
        self.assertEqual(self.music.get_volume(), 50)

    def test_set_volume_invalid(self):
        result = self.music.set_volume(150)
        self.assertFalse(result["success"])

    def test_play_no_controller(self):
        result = self.music.play()
        self.assertFalse(result["success"])

    def test_get_status(self):
        status = self.music.get_status()
        self.assertEqual(status["playback_state"], PLAYBACK_STOPPED)

    def test_persist(self):
        self.music.create_playlist("Test", MOOD_CALM)
        music2 = MusicController(Path(self.tmpdir))
        self.assertEqual(len(music2.get_playlists()), 1)


class TestNotificationSystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.notifs = NotificationSystem(Path(self.tmpdir))

    def tearDown(self):
        import shutil; shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_notify(self):
        n = self.notifs.notify("Test", "Hello world")
        self.assertEqual(n.title, "Test")
        self.assertEqual(n.body, "Hello world")

    def test_alert(self):
        n = self.notifs.alert("Emergency!")
        self.assertEqual(n.priority, PRIORITY_URGENT)
        self.assertEqual(n.category, CAT_SECURITY)

    def test_remind(self):
        n = self.notifs.remind("Meeting", "In 10 minutes")
        self.assertEqual(n.category, "reminder")

    def test_info(self):
        n = self.notifs.info("Update", "System updated")
        self.assertEqual(n.priority, "low")

    def test_get_history(self):
        self.notifs.notify("Test1")
        self.notifs.notify("Test2")
        history = self.notifs.get_history()
        self.assertEqual(len(history), 2)

    def test_get_urgent(self):
        self.notifs.notify("Normal")
        self.notifs.alert("Urgent!")
        urgent = self.notifs.get_urgent()
        self.assertEqual(len(urgent), 1)

    def test_dismiss(self):
        n = self.notifs.notify("Test")
        self.assertTrue(self.notifs.dismiss(n.notif_id))
        self.assertTrue(self.notifs._history[-1].dismissed)

    def test_get_status(self):
        status = self.notifs.get_status()
        self.assertIn("platform", status)
        self.assertIn("total_notifications", status)

    def test_on_notification_callback(self):
        called = []
        sys = NotificationSystem(Path(self.tmpdir), on_notification=lambda n: called.append(n))
        sys.notify("Test")
        self.assertEqual(len(called), 1)

    def test_display_fallback(self):
        # Should always succeed via terminal fallback
        n = Notification(notif_id="n1", title="Test", body="Body")
        result = self.notifs._display_terminal(n)
        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
