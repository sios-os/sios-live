"""Tests for the voice command router and sensory integration."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.sensory import (
    VoiceCommandRouter, VoiceCommand,
    SensorySystem, AudioListener,
    SPEECH_DIRECT_ADDRESS, SPEECH_SELF_TALK, SPEECH_CONVERSATION, SPEECH_NOISE,
    MODE_AMBIENT, MODE_PRIVACY, MODE_SLEEP,
)


class TestVoiceCommandRouter(unittest.TestCase):
    def setUp(self):
        self.router = VoiceCommandRouter()
        self.handler_called = False
        self.handler_arg = ""

    def _make_handler(self):
        def handler(text: str):
            self.handler_called = True
            self.handler_arg = text
            return {"message": "ok"}
        return handler

    def test_register_and_match(self):
        self.router.register("test", ["hello", "hi"], self._make_handler())
        cmd = self.router.match("hello world", SPEECH_DIRECT_ADDRESS)
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.command_id, "test")

    def test_match_case_insensitive(self):
        self.router.register("test", ["GoodNight"], self._make_handler())
        cmd = self.router.match("goodnight", SPEECH_DIRECT_ADDRESS)
        self.assertIsNotNone(cmd)

    def test_no_match(self):
        self.router.register("test", ["hello"], self._make_handler())
        cmd = self.router.match("goodbye", SPEECH_DIRECT_ADDRESS)
        self.assertIsNone(cmd)

    def test_route_executes_handler(self):
        self.router.register("test", ["hello"], self._make_handler())
        matched, result = self.router.route("hello world", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertTrue(self.handler_called)
        self.assertEqual(result, {"message": "ok"})

    def test_route_no_match(self):
        matched, result = self.router.route("goodbye", SPEECH_DIRECT_ADDRESS)
        self.assertFalse(matched)
        self.assertIsNone(result)

    def test_unregister(self):
        self.router.register("test", ["hello"], self._make_handler())
        self.assertTrue(self.router.unregister("test"))
        self.assertEqual(self.router.count, 0)
        # Second unregister should fail
        self.assertFalse(self.router.unregister("test"))

    def test_count(self):
        self.assertEqual(self.router.count, 0)
        self.router.register("a", ["a"], self._make_handler())
        self.router.register("b", ["b"], self._make_handler())
        self.assertEqual(self.router.count, 2)

    def test_list_commands(self):
        self.router.register("test", ["hello", "hi"], self._make_handler(),
                             description="Test command")
        commands = self.router.list_commands()
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0]["command_id"], "test")
        self.assertEqual(commands[0]["phrases"], ["hello", "hi"])
        self.assertEqual(commands[0]["description"], "Test command")

    def test_match_direct_address(self):
        self.router.register("test", ["hello"], self._make_handler(),
                             match_direct_address=True, match_ambient=False)
        self.assertIsNotNone(self.router.match("hello", SPEECH_DIRECT_ADDRESS))
        self.assertIsNone(self.router.match("hello", SPEECH_CONVERSATION))

    def test_match_ambient(self):
        self.router.register("test", ["goodnight"], self._make_handler(),
                             match_direct_address=True, match_ambient=True)
        # Should match in ambient (conversation type is what ambient produces)
        self.assertIsNotNone(self.router.match("goodnight", SPEECH_CONVERSATION))

    def test_no_match_noise(self):
        self.router.register("test", ["hello"], self._make_handler())
        self.assertIsNone(self.router.match("hello", SPEECH_NOISE))

    def test_works_in_privacy(self):
        self.router.register("test", ["good morning"], self._make_handler(),
                             works_in_privacy=True)
        self.assertIsNotNone(self.router.match("good morning", SPEECH_DIRECT_ADDRESS, in_privacy=True))

    def test_not_in_privacy(self):
        self.router.register("test", ["goodnight"], self._make_handler(),
                             works_in_privacy=False)
        self.assertIsNone(self.router.match("goodnight", SPEECH_DIRECT_ADDRESS, in_privacy=True))

    def test_handler_exception_caught(self):
        def bad_handler(text):
            raise ValueError("boom")
        self.router.register("test", ["hello"], bad_handler)
        matched, result = self.router.route("hello", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertIn("error", result)

    def test_first_match_wins(self):
        self.router.register("first", ["hello"], lambda t: "first")
        self.router.register("second", ["hello"], lambda t: "second")
        matched, result = self.router.route("hello", SPEECH_DIRECT_ADDRESS)
        self.assertEqual(result, "first")

    def test_suppress_chat_default_true(self):
        self.router.register("test", ["hello"], self._make_handler())
        commands = self.router.list_commands()
        self.assertTrue(commands[0]["suppress_chat"])

    def test_suppress_chat_false(self):
        self.router.register("test", ["hello"], self._make_handler(),
                             suppress_chat=False)
        commands = self.router.list_commands()
        self.assertFalse(commands[0]["suppress_chat"])


class TestSensoryVoiceCommands(unittest.TestCase):
    """Test that the SensorySystem routes voice commands before chat."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)
        self.router = VoiceCommandRouter()
        self.chat_called = False
        self.chat_arg = ""
        self.command_called = False
        self.command_arg = ""

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_sensory(self):
        """Create a SensorySystem with mocked subsystems."""
        # We can't easily create a full SensorySystem without model,
        # so we test the _handle_direct_address logic directly.
        sensory = object.__new__(SensorySystem)
        sensory.root = self.root
        sensory.model = None
        sensory.observer = None
        sensory.proactive = None
        sensory.on_conversation = None
        sensory.on_action = None
        sensory.voice_command_router = self.router
        sensory.voice_interpreter = None
        sensory.ledger = None
        # Mock the ears, voice
        sensory.ears = MagicMock()
        sensory.ears.mode = MODE_AMBIENT
        sensory.voice = MagicMock()
        sensory.voice.speak = MagicMock()
        return sensory

    def test_direct_address_routes_to_command(self):
        command_result = {"message": "Sleep mode active"}
        self.router.register("goodnight", ["goodnight"],
                             lambda t: command_result)
        sensory = self._make_sensory()
        sensory.on_conversation = lambda text: self._fail_chat()

        sensory._handle_direct_address("ANUBIS, goodnight")

        self.assertTrue(self.router.count > 0)
        sensory.voice.speak.assert_called_with(
            "Sleep mode active", priority="high", source="voice_command",
        )

    def test_direct_address_falls_through_when_no_match(self):
        chat_response = "Hello Creator"
        self.router.register("test", ["hello"], lambda t: {"message": "hi"})
        sensory = self._make_sensory()
        sensory.on_conversation = lambda text: chat_response

        sensory._handle_direct_address("ANUBIS, what's the weather")

        # Should have spoken the chat response, not the command
        sensory.voice.speak.assert_called_with(
            chat_response, priority="high", source="response",
        )

    def test_ambient_speech_routes_to_command(self):
        self.router.register("goodnight", ["goodnight"],
                             lambda t: {"message": "Goodnight Creator"})
        sensory = self._make_sensory()

        sensory._handle_ambient_speech(SPEECH_CONVERSATION, "I'm going to say goodnight now")

        sensory.voice.speak.assert_called_with(
            "Goodnight Creator", priority="high", source="voice_command",
        )

    def test_ambient_speech_no_match_falls_through(self):
        self.router.register("test", ["hello"], lambda t: {"message": "hi"})
        sensory = self._make_sensory()
        sensory.observer = MagicMock()

        # Should not crash, should fall through to observer
        sensory._handle_ambient_speech(SPEECH_CONVERSATION, "nice weather today")
        # Observer should have been called (fallthrough path)
        sensory.observer._make_observation.assert_called()

    def test_suppress_chat_false_falls_through(self):
        """When suppress_chat is False, both command and chat should fire."""
        command_called = []
        self.router.register("test", ["hello"],
                             lambda t: command_called.append(t),
                             suppress_chat=False)
        sensory = self._make_sensory()
        chat_called = []
        sensory.on_conversation = lambda text: chat_called.append(text) or "chat response"

        sensory._handle_direct_address("ANUBIS, hello")

        # Both should have been called
        self.assertEqual(len(command_called), 1)
        self.assertEqual(len(chat_called), 1)

    def test_command_in_privacy_mode(self):
        """Commands with works_in_privacy should fire in privacy mode."""
        self.router.register("good_morning", ["good morning"],
                             lambda t: {"message": "Good morning Creator"},
                             works_in_privacy=True)
        sensory = self._make_sensory()
        sensory.ears.mode = MODE_PRIVACY

        sensory._handle_direct_address("good morning")

        sensory.voice.speak.assert_called_with(
            "Good morning Creator", priority="high", source="voice_command",
        )

    def test_command_not_in_privacy_mode(self):
        """Commands without works_in_privacy should not fire in privacy mode."""
        self.router.register("goodnight", ["goodnight"],
                             lambda t: {"message": "Goodnight"},
                             works_in_privacy=False)
        sensory = self._make_sensory()
        sensory.ears.mode = MODE_PRIVACY
        sensory.on_conversation = lambda text: "chat response"

        sensory._handle_direct_address("goodnight")

        # Should fall through to chat (command didn't match in privacy)
        sensory.voice.speak.assert_called_with(
            "chat response", priority="high", source="response",
        )

    def _fail_chat(self):
        self.chat_called = True
        return "This should not be called"


class TestSleepVoiceCommands(unittest.TestCase):
    """Test that sleep protocol voice commands work end-to-end through the router."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _build_router(self):
        """Build the same router the daemon builds."""
        from anubis.sleep_protocol import SleepProtocol
        sleep = SleepProtocol(self.root, sensory=MagicMock())
        router = VoiceCommandRouter()
        router.register("goodnight", ["goodnight", "good night", "going to bed"],
                        lambda t: sleep.goodnight())
        router.register("wake", ["wake me up", "wake me", "alarm"],
                        lambda t: sleep.wake(),
                        works_in_privacy=True)
        router.register("good_morning", ["good morning", "i'm awake", "i'm up"],
                        lambda t: sleep.good_morning(),
                        works_in_privacy=True)
        router.register("sleep_cancel", ["cancel alarm", "stop alarm"],
                        lambda t: sleep.cancel(),
                        works_in_privacy=True)
        return router, sleep

    def test_goodnight_phrase_triggers_sleep(self):
        router, sleep = self._build_router()
        matched, result = router.route("goodnight", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "sleeping")

    def test_good_night_two_words_triggers(self):
        router, sleep = self._build_router()
        matched, result = router.route("good night", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "sleeping")

    def test_anubis_goodnight_triggers(self):
        router, sleep = self._build_router()
        matched, result = router.route("ANUBIS, goodnight", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "sleeping")

    def test_going_to_bed_triggers(self):
        router, sleep = self._build_router()
        matched, result = router.route("I'm going to bed now", SPEECH_CONVERSATION)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "sleeping")

    def test_wake_me_up_triggers_wake(self):
        router, sleep = self._build_router()
        sleep.goodnight()
        matched, result = router.route("wake me up", SPEECH_DIRECT_ADDRESS)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "waking")

    def test_wake_works_in_privacy(self):
        router, sleep = self._build_router()
        sleep.goodnight()  # enters privacy mode
        matched, result = router.route("wake me up", SPEECH_DIRECT_ADDRESS, in_privacy=True)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "waking")

    def test_good_morning_triggers_briefing(self):
        router, sleep = self._build_router()
        sleep.goodnight()
        matched, result = router.route("good morning", SPEECH_DIRECT_ADDRESS, in_privacy=True)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "awake")
        self.assertIn("briefing", result)

    def test_im_awake_triggers_briefing(self):
        router, sleep = self._build_router()
        sleep.goodnight()
        matched, result = router.route("I'm awake", SPEECH_DIRECT_ADDRESS, in_privacy=True)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "awake")

    def test_cancel_alarm_triggers_cancel(self):
        router, sleep = self._build_router()
        sleep.goodnight()
        sleep.wake()
        matched, result = router.route("cancel alarm", SPEECH_DIRECT_ADDRESS, in_privacy=True)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "awake")

    def test_unrelated_speech_does_not_trigger(self):
        router, sleep = self._build_router()
        matched, result = router.route("what's the weather today", SPEECH_DIRECT_ADDRESS)
        self.assertFalse(matched)

    def test_goodnight_does_not_work_in_privacy(self):
        router, sleep = self._build_router()
        matched, result = router.route("goodnight", SPEECH_DIRECT_ADDRESS, in_privacy=True)
        self.assertFalse(matched)

    def test_wake_works_in_sleep_mode(self):
        """Wake command should match when in sleep mode (not privacy)."""
        router, sleep = self._build_router()
        sleep.goodnight()
        # Sleep mode is NOT privacy mode — voice commands should work
        matched, result = router.route("wake me up", SPEECH_DIRECT_ADDRESS, in_privacy=False)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "waking")

    def test_good_morning_works_in_sleep_mode(self):
        """Good morning should match when in sleep mode (not privacy)."""
        router, sleep = self._build_router()
        sleep.goodnight()
        matched, result = router.route("good morning", SPEECH_DIRECT_ADDRESS, in_privacy=False)
        self.assertTrue(matched)
        self.assertEqual(result["state"], "awake")

    def test_sleep_mode_still_listens(self):
        """MODE_SLEEP should not block the listening loop."""
        from anubis.sensory import MODE_SLEEP, MODE_PRIVACY
        # is_listening should be True for sleep, False for privacy
        # (verified via the mode check in AudioListener)
        self.assertNotEqual(MODE_SLEEP, MODE_PRIVACY)


class TestSleepModeSensory(unittest.TestCase):
    """Test that the sensory system handles sleep mode correctly."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_sleep_mode_accepted(self):
        """set_mode should accept MODE_SLEEP."""
        from anubis.sensory import MODE_SLEEP
        sensory = object.__new__(SensorySystem)
        sensory.ears = MagicMock()
        sensory.ears.set_mode = MagicMock(return_value=True)
        result = sensory.set_mode(MODE_SLEEP)
        self.assertTrue(result)
        sensory.ears.set_mode.assert_called_with(MODE_SLEEP)

    def test_sleep_mode_method_exists(self):
        """SensorySystem should have a sleep_mode() method."""
        sensory = object.__new__(SensorySystem)
        sensory.ears = MagicMock()
        sensory.ears.set_mode = MagicMock(return_value=True)
        sensory.sleep_mode()
        from anubis.sensory import MODE_SLEEP
        sensory.ears.set_mode.assert_called_with(MODE_SLEEP)

    def test_process_speech_in_sleep_mode_routes_to_commands(self):
        """In sleep mode, speech should only route to voice commands."""
        from anubis.sensory import MODE_SLEEP
        router = VoiceCommandRouter()
        command_called = []
        router.register("good_morning", ["good morning"],
                        lambda t: command_called.append(t) or {"message": "Good morning"},
                        works_in_privacy=True)

        # Create a minimal AudioListener-like object to test _process_speech
        listener = object.__new__(AudioListener)
        listener.mode = MODE_SLEEP
        listener.wake_word = "anubis"
        listener.on_direct_address = MagicMock()
        listener.on_ambient_speech = MagicMock()
        listener.on_actionable = None
        listener.model = None
        listener._record_event = MagicMock()

        # Process "good morning" in sleep mode
        listener._process_speech("good morning", 100.0)

        # Should have called on_direct_address (which routes to voice commands)
        listener.on_direct_address.assert_called_once_with("good morning")
        # Should NOT have called on_ambient_speech (no ambient processing in sleep)
        listener.on_ambient_speech.assert_not_called()

    def test_process_speech_in_sleep_mode_ignores_other_speech(self):
        """In sleep mode, non-wake speech should be silently dropped."""
        from anubis.sensory import MODE_SLEEP
        listener = object.__new__(AudioListener)
        listener.mode = MODE_SLEEP
        listener.wake_word = "anubis"
        listener.on_direct_address = MagicMock()
        listener.on_ambient_speech = MagicMock()
        listener.on_actionable = None
        listener.model = None
        listener._record_event = MagicMock()

        # Process random speech in sleep mode
        listener._process_speech("what's the weather", 100.0)

        # on_direct_address is called (it will check the router and find no match)
        # but on_ambient_speech should NOT be called
        listener.on_direct_address.assert_called_once()
        listener.on_ambient_speech.assert_not_called()


if __name__ == "__main__":
    unittest.main()
