"""Tests for the ANUBIS communicator layer (DEMON/ANUBIS persona switching)."""
from __future__ import annotations

import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.communicator import (
    Communicator, Persona, DEMON_PERSONA, ANUBIS_PERSONA,
    COMM_MODE_NORMAL, COMM_MODE_TOMB,
)


class TestCommunicator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_communicator(self, name="DEMON"):
        return Communicator(self.root, name=name, ledger=MagicMock())

    # ===========================================================
    # INITIAL STATE
    # ===========================================================

    def test_initial_mode_is_normal(self):
        comm = self._make_communicator()
        self.assertEqual(comm.mode, COMM_MODE_NORMAL)
        self.assertFalse(comm.is_tomb_mode)

    def test_initial_name(self):
        comm = self._make_communicator()
        self.assertEqual(comm.name, "DEMON")

    def test_custom_name(self):
        comm = self._make_communicator(name="JARVIS")
        self.assertEqual(comm.name, "JARVIS")

    def test_wake_word_normal_mode(self):
        comm = self._make_communicator()
        self.assertEqual(comm.wake_word, "demon")

    def test_wake_word_tomb_mode(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        self.assertEqual(comm.wake_word, "anubis")

    def test_wake_word_custom_name(self):
        comm = self._make_communicator(name="JARVIS")
        self.assertEqual(comm.wake_word, "jarvis")

    # ===========================================================
    # TOMB MODE
    # ===========================================================

    def test_enter_tomb(self):
        comm = self._make_communicator()
        result = comm.enter_tomb(reason="reviewing tests")
        self.assertEqual(result["mode"], "tomb")
        self.assertTrue(comm.is_tomb_mode)

    def test_enter_tomb_when_already_in_tomb(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        result = comm.enter_tomb()
        self.assertIn("Already in tomb mode", result["message"])

    def test_exit_tomb(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        result = comm.exit_tomb()
        self.assertEqual(result["mode"], "normal")
        self.assertFalse(comm.is_tomb_mode)
        self.assertIn("DEMON", result["message"])

    def test_exit_tomb_when_not_in_tomb(self):
        comm = self._make_communicator()
        result = comm.exit_tomb()
        self.assertIn("Not in tomb mode", result["message"])

    def test_tomb_mode_persists(self):
        comm = self._make_communicator()
        comm.enter_tomb(reason="test")
        # Create new instance — should load tomb state
        comm2 = Communicator(self.root)
        self.assertTrue(comm2.is_tomb_mode)

    def test_exit_tomb_restores_normal(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        comm.exit_tomb()
        # State should persist as normal
        comm2 = Communicator(self.root)
        self.assertFalse(comm2.is_tomb_mode)

    # ===========================================================
    # RENAME
    # ===========================================================

    def test_rename(self):
        comm = self._make_communicator()
        result = comm.set_name("HERMES")
        self.assertEqual(result["name"], "HERMES")
        self.assertEqual(comm.name, "HERMES")
        self.assertEqual(comm.wake_word, "hermes")

    def test_rename_empty(self):
        comm = self._make_communicator()
        result = comm.set_name("")
        self.assertIn("error", result)

    def test_rename_persists(self):
        comm = self._make_communicator()
        comm.set_name("HERMES")
        comm2 = Communicator(self.root)
        self.assertEqual(comm2.name, "HERMES")

    # ===========================================================
    # SPEAKING
    # ===========================================================

    def test_speak_normal_mode(self):
        spoken = []
        comm = self._make_communicator()
        comm.on_speak = lambda text, source: spoken.append((text, source))
        comm.speak("Hello Creator", source="test")
        self.assertEqual(len(spoken), 1)
        self.assertEqual(spoken[0][0], "Hello Creator")
        self.assertEqual(spoken[0][1], "test")

    def test_speak_tomb_mode(self):
        spoken = []
        comm = self._make_communicator()
        comm.on_speak = lambda text, source: spoken.append((text, source))
        comm.enter_tomb()
        comm.speak("Test results: 5 passed", source="review")
        self.assertEqual(len(spoken), 1)
        self.assertEqual(spoken[0][0], "Test results: 5 passed")

    def test_frame_response_normal_mode(self):
        comm = self._make_communicator()
        framed = comm.frame_response("Processing complete. 3 skills promoted.")
        # In normal mode, the response is passed through (light framing)
        self.assertIn("3 skills promoted", framed)

    def test_frame_response_tomb_mode(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        framed = comm.frame_response("Test results: 5 passed, 1 failed.")
        # In tomb mode, raw response is returned as-is
        self.assertEqual(framed, "Test results: 5 passed, 1 failed.")

    # ===========================================================
    # STYLE PROMPTS
    # ===========================================================

    def test_style_prompt_normal_mode(self):
        comm = self._make_communicator()
        prompt = comm.get_style_prompt()
        self.assertIn("DEMON", prompt)
        self.assertIn("communicator", prompt.lower())

    def test_style_prompt_tomb_mode(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        prompt = comm.get_style_prompt()
        self.assertIn("ANUBIS", prompt)
        self.assertIn("tomb", prompt.lower())

    def test_style_prompt_custom_name(self):
        comm = self._make_communicator(name="JARVIS")
        prompt = comm.get_style_prompt()
        self.assertIn("JARVIS", prompt)

    # ===========================================================
    # ROUTING DETECTION
    # ===========================================================

    def test_should_route_to_anubis(self):
        comm = self._make_communicator()
        self.assertTrue(comm.should_route_to_anubis("speak to anubis"))
        self.assertTrue(comm.should_route_to_anubis("I want to talk to ANUBIS directly"))
        self.assertTrue(comm.should_route_to_anubis("enter tomb"))
        self.assertTrue(comm.should_route_to_anubis("tomb mode"))

    def test_should_not_route_to_anubis(self):
        comm = self._make_communicator()
        self.assertFalse(comm.should_route_to_anubis("what's the weather"))
        self.assertFalse(comm.should_route_to_anubis("hello demon"))

    def test_should_exit_tomb(self):
        comm = self._make_communicator()
        self.assertTrue(comm.should_exit_tomb("back to DEMON"))
        self.assertTrue(comm.should_exit_tomb("exit tomb"))
        self.assertTrue(comm.should_exit_tomb("leave tomb"))

    def test_should_exit_tomb_custom_name(self):
        comm = self._make_communicator(name="JARVIS")
        self.assertTrue(comm.should_exit_tomb("back to JARVIS"))

    def test_should_not_exit_tomb(self):
        comm = self._make_communicator()
        self.assertFalse(comm.should_exit_tomb("what's the weather"))
        self.assertFalse(comm.should_exit_tomb("hello demon"))

    # ===========================================================
    # STATUS
    # ===========================================================

    def test_status_normal(self):
        comm = self._make_communicator()
        status = comm.get_status()
        self.assertEqual(status["name"], "DEMON")
        self.assertEqual(status["mode"], "normal")
        self.assertFalse(status["is_tomb"])
        self.assertEqual(status["wake_word"], "demon")

    def test_status_tomb(self):
        comm = self._make_communicator()
        comm.enter_tomb(reason="reviewing tests")
        time.sleep(0.01)  # ensure duration > 0
        status = comm.get_status()
        self.assertTrue(status["is_tomb"])
        self.assertEqual(status["wake_word"], "anubis")
        self.assertEqual(status["tomb_reason"], "reviewing tests")
        self.assertGreaterEqual(status["tomb_duration"], 0)

    # ===========================================================
    # ACTIVE PERSONA
    # ===========================================================

    def test_active_persona_normal(self):
        comm = self._make_communicator()
        persona = comm.active_persona
        self.assertTrue(persona.is_communicator)
        self.assertEqual(persona.name, "DEMON")

    def test_active_persona_tomb(self):
        comm = self._make_communicator()
        comm.enter_tomb()
        persona = comm.active_persona
        self.assertFalse(persona.is_communicator)
        self.assertEqual(persona.name, "ANUBIS")


class TestPersona(unittest.TestCase):
    def test_demon_persona_is_communicator(self):
        self.assertTrue(DEMON_PERSONA.is_communicator)

    def test_anubis_persona_is_not_communicator(self):
        self.assertFalse(ANUBIS_PERSONA.is_communicator)

    def test_frame_response_communicator(self):
        persona = Persona(name="DEMON", is_communicator=True)
        framed = persona.frame_response("Hello")
        self.assertEqual(framed, "Hello")

    def test_frame_response_anubis_raw(self):
        persona = Persona(name="ANUBIS", is_communicator=False)
        framed = persona.frame_response("Test results: 5 passed")
        self.assertEqual(framed, "Test results: 5 passed")

    def test_frame_response_no_double_frame(self):
        persona = Persona(name="DEMON", is_communicator=True)
        framed = persona.frame_response("DEMON, how are you?")
        self.assertEqual(framed, "DEMON, how are you?")


if __name__ == "__main__":
    unittest.main()
