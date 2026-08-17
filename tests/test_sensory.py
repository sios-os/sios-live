"""Tests for the sensory system — ears, eyes, and voice."""
from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.sensory import (
    AudioListener,
    ScreenWatcher,
    VoiceSpeaker,
    SensorySystem,
    AudioEvent,
    AmbientAction,
    ScreenObservation,
    SpeechRequest,
    MODE_AMBIENT,
    MODE_WAKE_WORD,
    MODE_CONVERSATION,
    MODE_PRIVACY,
    SPEECH_DIRECT_ADDRESS,
    SPEECH_SELF_TALK,
    SPEECH_CONVERSATION,
    SPEECH_NOISE,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = "direct_address"):
        self.response = response
        self.model = "mock:test"

    def chat(self, messages, *, temperature=0.2, max_tokens=None, timeout=180.0):
        return Completion(
            text=self.response,
            thinking="",
            tool_calls=[],
            model="mock:test",
            prompt_tokens=10,
            completion_tokens=20,
            duration_s=0.01,
        )


class TestAudioEvent(unittest.TestCase):
    def test_to_dict(self):
        e = AudioEvent(event_id="a1", event_type=SPEECH_DIRECT_ADDRESS,
                       transcript="hello")
        d = e.to_dict()
        self.assertEqual(d["event_id"], "a1")
        self.assertEqual(d["event_type"], "direct_address")


class TestAmbientAction(unittest.TestCase):
    def test_to_dict(self):
        a = AmbientAction(
            action_id="act1",
            action_type="add_to_list",
            trigger_text="I need milk",
            content="milk",
        )
        d = a.to_dict()
        self.assertEqual(d["action_id"], "act1")
        self.assertEqual(d["action_type"], "add_to_list")
        self.assertEqual(d["content"], "milk")


class TestScreenObservation(unittest.TestCase):
    def test_to_dict(self):
        o = ScreenObservation(obs_id="s1", description="test screen")
        d = o.to_dict()
        self.assertEqual(d["obs_id"], "s1")
        self.assertEqual(d["description"], "test screen")


class TestSpeechRequest(unittest.TestCase):
    def test_to_dict(self):
        r = SpeechRequest(req_id="r1", text="hello world")
        d = r.to_dict()
        self.assertEqual(d["req_id"], "r1")
        self.assertEqual(d["text"], "hello world")
        self.assertFalse(d["spoken"])


class TestAudioListener(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init_default_ambient(self):
        listener = AudioListener(self.root)
        self.assertEqual(listener.mode, MODE_AMBIENT)
        self.assertEqual(listener.wake_word, "demon")

    def test_init_wake_word_mode(self):
        listener = AudioListener(self.root, mode=MODE_WAKE_WORD)
        self.assertEqual(listener.mode, MODE_WAKE_WORD)

    def test_set_mode(self):
        listener = AudioListener(self.root)
        self.assertTrue(listener.set_mode(MODE_PRIVACY))
        self.assertEqual(listener.mode, MODE_PRIVACY)
        self.assertTrue(listener.set_mode(MODE_AMBIENT))
        self.assertTrue(listener.set_mode(MODE_CONVERSATION))
        self.assertTrue(listener.set_mode(MODE_WAKE_WORD))

    def test_set_mode_invalid(self):
        listener = AudioListener(self.root)
        self.assertFalse(listener.set_mode("invalid"))

    def test_set_wake_word(self):
        listener = AudioListener(self.root)
        listener.set_wake_word("computer")
        self.assertEqual(listener.wake_word, "computer")

    def test_is_available(self):
        listener = AudioListener(self.root)
        self.assertIsInstance(listener.is_available(), bool)

    def test_start_without_tools(self):
        listener = AudioListener(self.root)
        if not listener.is_available():
            result = listener.start()
            self.assertFalse(result)

    def test_mute_unmute(self):
        listener = AudioListener(self.root)
        self.assertFalse(listener._muted)
        listener.mute()
        self.assertTrue(listener._muted)
        listener.unmute()
        self.assertFalse(listener._muted)

    def test_privacy_mode_not_listening(self):
        listener = AudioListener(self.root)
        listener.set_mode(MODE_PRIVACY)
        self.assertFalse(listener.is_listening)

    def test_classify_direct_address_with_name(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("ANUBIS, what time is it?")
        self.assertEqual(result, SPEECH_DIRECT_ADDRESS)

    def test_classify_direct_address_with_question(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("what do you think about this?")
        self.assertEqual(result, SPEECH_DIRECT_ADDRESS)

    def test_classify_self_talk_need(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("I need to get milk after work")
        self.assertEqual(result, SPEECH_SELF_TALK)

    def test_classify_self_talk_should(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("I should call mom tomorrow")
        self.assertEqual(result, SPEECH_SELF_TALK)

    def test_classify_self_talk_actionable(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("don't forget to pick up groceries")
        self.assertEqual(result, SPEECH_SELF_TALK)

    def test_classify_noise_short(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("hmm")
        self.assertEqual(result, SPEECH_NOISE)

    def test_classify_conversation(self):
        listener = AudioListener(self.root, wake_word="anubis")
        result = listener._classify_speech("yeah I was at the store yesterday and they had a sale")
        self.assertEqual(result, SPEECH_CONVERSATION)

    def test_classify_with_model(self):
        model = MockModel("self_talk")
        listener = AudioListener(self.root, wake_word="anubis", model=model)
        # "what do you think" triggers direct_address heuristic, then model refines
        result = listener._classify_speech("what do you think about Rust?")
        # Model says self_talk, so should return that
        self.assertEqual(result, SPEECH_SELF_TALK)

    def test_detect_action_add_to_list(self):
        listener = AudioListener(self.root)
        result = listener._detect_action_type("I need to get milk after work")
        self.assertEqual(result, "add_to_list")

    def test_detect_action_reminder(self):
        listener = AudioListener(self.root)
        result = listener._detect_action_type("remind me to call mom tomorrow")
        self.assertEqual(result, "create_reminder")

    def test_detect_action_none(self):
        listener = AudioListener(self.root)
        result = listener._detect_action_type("the weather is nice today")
        self.assertEqual(result, "")

    def test_extract_action_content(self):
        listener = AudioListener(self.root)
        content = listener._extract_action_content(
            "I need to get milk after work", "add_to_list"
        )
        self.assertIn("milk", content)

    def test_handle_direct_address_callback(self):
        called = []
        def on_direct(text):
            called.append(text)
        listener = AudioListener(
            self.root, on_direct_address=on_direct,
        )
        listener._handle_direct_address("DEMON what time is it", 50.0)
        self.assertEqual(called, ["what time is it"])
        self.assertTrue(listener._in_conversation)

    def test_handle_self_talk_with_action(self):
        called = []
        def on_actionable(action_type, content):
            called.append((action_type, content))
        listener = AudioListener(
            self.root, on_actionable=on_actionable,
        )
        listener._handle_self_talk("I need to get milk after work", 50.0)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], "add_to_list")
        self.assertIn("milk", called[0][1])

    def test_handle_self_talk_no_action(self):
        called = []
        def on_ambient(speech_type, text):
            called.append((speech_type, text))
        listener = AudioListener(
            self.root, on_ambient_speech=on_ambient,
        )
        listener._handle_self_talk("I wonder about the universe", 50.0)
        self.assertEqual(len(called), 1)

    def test_handle_ambient_conversation(self):
        called = []
        def on_ambient(speech_type, text):
            called.append((speech_type, text))
        listener = AudioListener(
            self.root, on_ambient_speech=on_ambient,
        )
        listener._handle_ambient_conversation("yeah that was fun", 50.0)
        self.assertEqual(len(called), 1)
        self.assertEqual(called[0][0], SPEECH_CONVERSATION)

    def test_record_event(self):
        listener = AudioListener(self.root)
        listener._record_event(SPEECH_DIRECT_ADDRESS, "anubis hello", 50.0)
        events = listener.get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "direct_address")

    def test_record_action(self):
        listener = AudioListener(self.root)
        action = AmbientAction(
            action_id="a1",
            action_type="add_to_list",
            trigger_text="I need milk",
            content="milk",
        )
        listener._record_action(action)
        actions = listener.get_actions()
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["action_type"], "add_to_list")

    def test_events_persist(self):
        listener = AudioListener(self.root)
        listener._record_event(SPEECH_SELF_TALK, "test", 10.0)
        listener2 = AudioListener(self.root)
        events = listener2.get_events()
        self.assertEqual(len(events), 1)

    def test_get_status(self):
        listener = AudioListener(self.root)
        status = listener.get_status()
        self.assertIn("mode", status)
        self.assertEqual(status["mode"], MODE_AMBIENT)
        self.assertIn("wake_word", status)
        self.assertIn("available", status)

    def test_process_speech_conversation_mode(self):
        called = []
        def on_direct(text):
            called.append(text)
        listener = AudioListener(
            self.root, mode=MODE_CONVERSATION,
            on_direct_address=on_direct,
        )
        listener._process_speech("hello there", 50.0)
        self.assertEqual(called, ["hello there"])

    def test_process_speech_wake_word_mode(self):
        called = []
        def on_direct(text):
            called.append(text)
        listener = AudioListener(
            self.root, mode=MODE_WAKE_WORD, wake_word="anubis",
            on_direct_address=on_direct,
        )
        # Without wake word — should not trigger
        listener._process_speech("I need milk", 50.0)
        self.assertEqual(called, [])
        # With wake word — should trigger
        listener._process_speech("anubis what time is it", 50.0)
        self.assertEqual(len(called), 1)

    def test_process_speech_ambient_mode(self):
        actions = []
        directs = []
        def on_direct(text):
            directs.append(text)
        def on_actionable(action_type, content):
            actions.append((action_type, content))
        listener = AudioListener(
            self.root, mode=MODE_AMBIENT,
            on_direct_address=on_direct,
            on_actionable=on_actionable,
        )
        # Direct address
        listener._process_speech("demon hello", 50.0)
        self.assertEqual(len(directs), 1)
        # Self-talk with action
        listener._process_speech("I need to get milk", 50.0)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "add_to_list")


class TestScreenWatcher(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        watcher = ScreenWatcher(self.root, capture_interval_s=5.0)
        self.assertEqual(watcher.capture_interval, 5.0)

    def test_is_available(self):
        watcher = ScreenWatcher(self.root)
        self.assertIsInstance(watcher.is_available(), bool)

    def test_start_without_tools(self):
        watcher = ScreenWatcher(self.root)
        if not watcher.is_available():
            result = watcher.start()
            self.assertFalse(result)

    def test_record_observation(self):
        watcher = ScreenWatcher(self.root)
        obs = ScreenObservation(
            obs_id="s1",
            description="test screen",
            changes_detected=True,
        )
        watcher._record_observation(obs)
        observations = watcher.get_observations()
        self.assertEqual(len(observations), 1)

    def test_get_observations_empty(self):
        watcher = ScreenWatcher(self.root)
        self.assertEqual(watcher.get_observations(), [])

    def test_get_status(self):
        watcher = ScreenWatcher(self.root)
        status = watcher.get_status()
        self.assertIn("available", status)
        self.assertIn("watching", status)
        self.assertIn("capture_interval_s", status)

    def test_change_callback(self):
        called = []
        def on_change(desc, prev):
            called.append((desc, prev))
        watcher = ScreenWatcher(self.root, on_change=on_change)
        watcher.on_change("new screen", "old screen")
        self.assertEqual(called, [("new screen", "old screen")])

    def test_capture_once_without_tools(self):
        watcher = ScreenWatcher(self.root)
        if not watcher.is_available():
            result = watcher.capture_once()
            self.assertIsNone(result)


class TestVoiceSpeaker(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        speaker = VoiceSpeaker(self.root)
        self.assertTrue(speaker.enabled)

    def test_speak_returns_id(self):
        speaker = VoiceSpeaker(self.root)
        req_id = speaker.speak("hello", priority="normal")
        self.assertIsNotNone(req_id)
        self.assertNotEqual(req_id, "")

    def test_speak_immediate(self):
        speaker = VoiceSpeaker(self.root)
        req_id = speaker.speak("urgent message", priority="immediate")
        self.assertIsNotNone(req_id)

    def test_speak_now(self):
        speaker = VoiceSpeaker(self.root)
        result = speaker.speak_now("test")
        self.assertIsInstance(result, bool)

    def test_mute(self):
        speaker = VoiceSpeaker(self.root)
        speaker.mute()
        self.assertFalse(speaker.enabled)

    def test_unmute(self):
        speaker = VoiceSpeaker(self.root)
        speaker.mute()
        speaker.unmute()
        self.assertTrue(speaker.enabled)

    def test_clear_queue(self):
        speaker = VoiceSpeaker(self.root)
        speaker.speak("msg1")
        speaker.speak("msg2")
        speaker.speak("msg3")
        count = speaker.clear_queue()
        self.assertEqual(count, 3)
        self.assertEqual(len(speaker.get_queue()), 0)

    def test_queue_limit(self):
        speaker = VoiceSpeaker(self.root, max_queue_size=3)
        speaker.speak("msg1")
        speaker.speak("msg2")
        speaker.speak("msg3")
        speaker.speak("msg4")
        queue = speaker.get_queue()
        self.assertLessEqual(len(queue), 3)

    def test_get_queue(self):
        speaker = VoiceSpeaker(self.root)
        speaker.speak("test message")
        queue = speaker.get_queue()
        self.assertEqual(len(queue), 1)
        self.assertEqual(queue[0]["text"], "test message")

    def test_get_status(self):
        speaker = VoiceSpeaker(self.root)
        status = speaker.get_status()
        self.assertIn("enabled", status)
        self.assertIn("queue_size", status)
        self.assertIn("available", status)

    def test_history(self):
        speaker = VoiceSpeaker(self.root)
        speaker.speak_now("test message")
        history = speaker.get_history()
        self.assertIsInstance(history, list)

    def test_disabled_speak(self):
        speaker = VoiceSpeaker(self.root, enabled=False)
        req_id = speaker.speak("test")
        self.assertEqual(req_id, "")


class TestSensorySystem(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        sensory = SensorySystem(self.root)
        self.assertIsNotNone(sensory.ears)
        self.assertIsNotNone(sensory.eyes)
        self.assertIsNotNone(sensory.voice)
        self.assertEqual(sensory.ears.mode, MODE_AMBIENT)

    def test_start_stop(self):
        sensory = SensorySystem(self.root)
        sensory.start()
        sensory.stop()
        self.assertFalse(sensory.is_running)

    def test_set_wake_word(self):
        sensory = SensorySystem(self.root)
        sensory.set_wake_word("computer")
        self.assertEqual(sensory.ears.wake_word, "computer")

    def test_set_mode(self):
        sensory = SensorySystem(self.root)
        self.assertTrue(sensory.set_mode(MODE_PRIVACY))
        self.assertEqual(sensory.get_mode(), MODE_PRIVACY)
        self.assertTrue(sensory.set_mode(MODE_AMBIENT))
        self.assertEqual(sensory.get_mode(), MODE_AMBIENT)

    def test_privacy_ambient_mode(self):
        sensory = SensorySystem(self.root)
        sensory.privacy_mode()
        self.assertEqual(sensory.get_mode(), MODE_PRIVACY)
        sensory.ambient_mode()
        self.assertEqual(sensory.get_mode(), MODE_AMBIENT)

    def test_mute_unmute_audio(self):
        sensory = SensorySystem(self.root)
        sensory.mute_audio()
        self.assertTrue(sensory.ears._muted)
        sensory.unmute_audio()
        self.assertFalse(sensory.ears._muted)

    def test_mute_unmute_voice(self):
        sensory = SensorySystem(self.root)
        sensory.mute_voice()
        self.assertFalse(sensory.voice.enabled)
        sensory.unmute_voice()
        self.assertTrue(sensory.voice.enabled)

    def test_speak(self):
        sensory = SensorySystem(self.root)
        req_id = sensory.speak("hello", priority="normal")
        self.assertIsNotNone(req_id)

    def test_direct_address_handler_with_conversation(self):
        called = []
        def on_conversation(command):
            called.append(command)
            return f"Response to: {command}"
        sensory = SensorySystem(
            self.root, on_conversation=on_conversation,
        )
        sensory._handle_direct_address("what time is it")
        self.assertEqual(called, ["what time is it"])

    def test_ambient_speech_handler(self):
        sensory = SensorySystem(self.root)
        # Should not crash even without observer/proactive
        sensory._handle_ambient_speech(SPEECH_SELF_TALK, "I need milk")

    def test_actionable_handler(self):
        called = []
        def on_action(action_type, content):
            called.append((action_type, content))
            return f"Done: {content}"
        sensory = SensorySystem(self.root, on_action=on_action)
        sensory._handle_actionable("add_to_list", "milk")
        self.assertEqual(called, [("add_to_list", "milk")])

    def test_actionable_default_acknowledgment(self):
        sensory = SensorySystem(self.root)
        ack = sensory._default_action_acknowledgment("add_to_list", "milk")
        self.assertIn("milk", ack)

    def test_actionable_default_reminder(self):
        sensory = SensorySystem(self.root)
        ack = sensory._default_action_acknowledgment("create_reminder", "call mom")
        self.assertIn("call mom", ack)

    def test_screen_change_handler(self):
        sensory = SensorySystem(self.root)
        sensory._handle_screen_change("new screen", "old screen")

    def test_get_status(self):
        sensory = SensorySystem(self.root)
        status = sensory.get_status()
        self.assertIn("ears", status)
        self.assertIn("eyes", status)
        self.assertIn("voice", status)
        self.assertIn("running", status)

    def test_get_actions(self):
        sensory = SensorySystem(self.root)
        actions = sensory.get_actions()
        self.assertIsInstance(actions, list)

    def test_direct_address_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        sensory = SensorySystem(self.root, observer=observer)
        sensory._handle_direct_address("test command")
        observer._make_observation.assert_called_once()

    def test_direct_address_feeds_proactive(self):
        proactive = MagicMock()
        proactive.observe = MagicMock()
        sensory = SensorySystem(self.root, proactive=proactive)
        sensory._handle_direct_address("test command")
        proactive.observe.assert_called_once()

    def test_ambient_speech_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        sensory = SensorySystem(self.root, observer=observer)
        sensory._handle_ambient_speech(SPEECH_SELF_TALK, "I need milk")
        observer._make_observation.assert_called_once()

    def test_screen_change_feeds_observer(self):
        observer = MagicMock()
        observer._make_observation = MagicMock()
        sensory = SensorySystem(self.root, observer=observer)
        sensory._handle_screen_change("new", "old")
        observer._make_observation.assert_called_once()

    def test_actionable_with_handler_speaks(self):
        def on_action(action_type, content):
            return f"Added {content}"
        sensory = SensorySystem(self.root, on_action=on_action)
        # Should not crash, should queue speech
        sensory._handle_actionable("add_to_list", "milk")


if __name__ == "__main__":
    unittest.main()
