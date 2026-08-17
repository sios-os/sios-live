"""Self-development loop tests, driven by a scripted model.

A fake model makes the loop's control flow deterministic and fast to test. Real
inference is verified separately by tools/first_mission.py -- the point here is
that the governance path is correct, not that the model is clever.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.ledger import Ledger  # noqa: E402
from anubis.loop import SelfDevelopmentLoop  # noqa: E402
from anubis.model import Completion, ModelSpec  # noqa: E402
from anubis.sandbox import Sandbox, SandboxPolicy  # noqa: E402
from anubis.skills import SkillLibrary, parse_proposal  # noqa: E402


class ScriptedModel:
    """Returns queued responses in order, recording the prompts it received."""

    model = "scripted"

    def __init__(self, responses: list[str]) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    @property
    def spec(self) -> ModelSpec:
        return ModelSpec("scripted", "0B", tools=True, thinking=False,
                         vision=False, context=8192, min_vram_gb=0.0)

    def chat(self, messages, **kw) -> Completion:
        self.prompts.append(messages[-1]["content"])
        text = self.responses.pop(0) if self.responses else "unparseable garbage"
        return Completion(text=text, model=self.model, completion_tokens=10,
                          duration_s=0.01)


def proposal(code: str, tests: str) -> str:
    return f"<<<SKILL>>>\n{code}\n<<<TESTS>>>\n{tests}\n<<<END>>>"


GOOD = proposal(
    "def double(n):\n    \"\"\"Double a number.\"\"\"\n    return n * 2\n",
    "assert double(2) == 4\nassert double(0) == 0\nassert double(-3) == -6\n"
    'print("TESTS PASSED")\n',
)

WRONG = proposal(
    "def double(n):\n    \"\"\"Double a number.\"\"\"\n    return n + 2\n",
    "assert double(2) == 4\nassert double(5) == 10\n" 'print("TESTS PASSED")\n',
)

HAZARDOUS = proposal(
    "import socket\ndef double(n):\n    socket.socket()\n    return n * 2\n",
    'assert double(2) == 4\nprint("TESTS PASSED")\n',
)

# Hazardous, but its tests genuinely pass inside the sandbox: creating a socket
# object needs no network, so containment does not stop it. This is the case
# where the *promotion* gate is the only thing standing between a
# constitutional breach and the live skill library.
HAZARDOUS_BUT_PASSING = proposal(
    "import socket\n"
    "def double(n):\n"
    '    """Double a number."""\n'
    "    try:\n"
    "        socket.socket()\n"
    "    except Exception:\n"
    "        pass\n"
    "    return n * 2\n",
    'assert double(2) == 4\nassert double(0) == 0\nprint("TESTS PASSED")\n',
)

# Denied outright: DENY at the sandbox gate requires a hazard *and* no sandbox,
# which the loop never does. A payload that fails the narrowness test instead
# exercises the pre-execution denial path.
UNPARSEABLE = "Certainly! I'd be glad to help you build that capability."


class LoopCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        root = Path(self.dir.name)
        self.library = SkillLibrary(root / "skills")
        self.ledger = Ledger(root / "evidence" / "ledger.jsonl")
        self.sandbox = Sandbox(SandboxPolicy(timeout_s=20, memory_mb=256, cpu_seconds=10))

    def tearDown(self):
        self.dir.cleanup()

    def build(self, responses, max_attempts=3):
        self.model = ScriptedModel(responses)
        return SelfDevelopmentLoop(
            self.model, self.library, self.ledger, self.sandbox,
            max_attempts=max_attempts,
        )


class TestHappyPath(LoopCase):
    def test_first_attempt_promotes(self):
        loop = self.build([GOOD])
        r = loop.run_mission("double a number", "double")
        self.assertTrue(r.success, r.summary())
        self.assertEqual(r.attempt_count, 1)
        self.assertIsNotNone(r.skill)
        self.assertEqual(r.skill.version, 1)

    def test_promoted_skill_is_loadable(self):
        loop = self.build([GOOD])
        loop.run_mission("double a number", "double")
        loaded = self.library.load("double")
        self.assertIn("return n * 2", loaded.code)
        self.assertEqual(loaded.provenance.model, "scripted")
        self.assertEqual(loaded.description, "double a number")

    def test_ledger_records_the_promotion(self):
        loop = self.build([GOOD])
        loop.run_mission("double a number", "double")
        actions = [e.action for e in self.ledger]
        self.assertIn("mission.start", actions)
        self.assertIn("attempt.executed", actions)
        self.assertIn("skill.promoted", actions)
        self.assertIn("mission.end", actions)
        ok, msg = self.ledger.verify()
        self.assertTrue(ok, msg)


class TestLearningFromFailure(LoopCase):
    def test_retries_after_failing_tests_then_succeeds(self):
        loop = self.build([WRONG, GOOD])
        r = loop.run_mission("double a number", "double")
        self.assertTrue(r.success, r.summary())
        self.assertEqual(r.attempt_count, 2)
        self.assertFalse(r.attempts[0].passed)
        self.assertTrue(r.attempts[1].passed)

    def test_failure_output_is_fed_back_to_the_model(self):
        # This is the actual learning mechanism: the model must be told what
        # went wrong, otherwise the retry is just a reroll.
        loop = self.build([WRONG, GOOD])
        loop.run_mission("double a number", "double")
        retry_prompt = self.model.prompts[1]
        self.assertIn("failed", retry_prompt.lower())
        self.assertIn("AssertionError", retry_prompt)

    def test_gives_up_after_max_attempts(self):
        loop = self.build([WRONG, WRONG, WRONG], max_attempts=3)
        r = loop.run_mission("double a number", "double")
        self.assertFalse(r.success)
        self.assertEqual(r.attempt_count, 3)
        self.assertFalse(self.library.exists("double"))
        self.assertIn("no attempt passed", r.denied_reason)

    def test_unparseable_response_is_retried_with_guidance(self):
        loop = self.build(["I would be happy to help you with that!", GOOD])
        r = loop.run_mission("double a number", "double")
        self.assertTrue(r.success, r.summary())
        self.assertTrue(r.attempts[0].parse_error)
        self.assertIn("could not be parsed", self.model.prompts[1])


class TestConstitutionalEnforcement(LoopCase):
    def test_hazardous_code_never_promoted(self):
        loop = self.build([HAZARDOUS, HAZARDOUS, HAZARDOUS])
        r = loop.run_mission("double a number", "double")
        self.assertFalse(r.success)
        self.assertFalse(self.library.exists("double"))

    def test_hazardous_code_is_allowed_to_run_but_never_promoted(self):
        # Design intent: a sandbox exists precisely so hazardous code CAN be
        # executed safely. Containment permits execution; the promotion gate is
        # what refuses to make it a permanent capability.
        loop = self.build([HAZARDOUS_BUT_PASSING], max_attempts=1)
        r = loop.run_mission("double a number", "double")

        executed = [e for e in self.ledger if e.action == "attempt.executed"]
        self.assertTrue(executed, "hazardous code was not executed in the sandbox")
        self.assertTrue(executed[0].payload["passed"], "its tests should have passed")

        self.assertFalse(r.success, "hazardous code was promoted")
        self.assertFalse(self.library.exists("double"))
        self.assertEqual(r.denied_reason, "promotion gate denied")

    def test_promotion_denial_is_logged_with_the_violated_law(self):
        loop = self.build([HAZARDOUS_BUT_PASSING], max_attempts=1)
        loop.run_mission("double a number", "double")
        rejections = [e for e in self.ledger if e.action == "skill.rejected"]
        self.assertTrue(rejections, "promotion refusal was not recorded")
        self.assertIn("local_privacy", rejections[0].payload["ruling"])

    def test_passing_tests_cannot_launder_a_breach(self):
        # Retried three times, always passing its tests, never promoted.
        loop = self.build([HAZARDOUS_BUT_PASSING] * 3, max_attempts=3)
        r = loop.run_mission("double a number", "double")
        self.assertFalse(r.success)
        self.assertEqual(r.attempt_count, 3)
        self.assertFalse(self.library.exists("double"))

    def test_model_cannot_widen_its_own_capabilities(self):
        loop = self.build([GOOD], max_attempts=1)
        loop.granted = frozenset()  # revoke authorship
        r = loop.run_mission("double a number", "double")
        self.assertFalse(r.success)
        self.assertFalse(self.library.exists("double"))


class TestVersioningAndRollback(LoopCase):
    def test_second_promotion_creates_v2_and_keeps_v1(self):
        loop = self.build([GOOD])
        loop.run_mission("double a number", "double")

        better = proposal(
            "def double(n):\n    \"\"\"Double a number, validated.\"\"\"\n"
            "    if not isinstance(n, (int, float)):\n"
            "        raise TypeError('n must be numeric')\n    return n * 2\n",
            "assert double(2) == 4\n"
            "try:\n    double('x')\n    raise SystemExit('should have raised')\n"
            "except TypeError:\n    pass\n"
            'print("TESTS PASSED")\n',
        )
        loop2 = self.build([better])
        r2 = loop2.run_mission("double a number safely", "double")
        self.assertTrue(r2.success, r2.summary())
        self.assertEqual(r2.skill.version, 2)
        self.assertEqual(self.library.versions("double"), [1, 2])
        self.assertEqual(self.library.current_version("double"), 2)

        # v1 must still be intact -- nothing is ever overwritten.
        v1 = self.library.load("double", version=1)
        self.assertIn("return n * 2", v1.code)
        self.assertNotIn("TypeError", v1.code)

    def test_rollback_restores_previous_version(self):
        self.build([GOOD]).run_mission("double", "double")
        v2 = proposal(
            "def double(n):\n    \"\"\"v2.\"\"\"\n    return n * 2\n",
            'assert double(3) == 6\nprint("TESTS PASSED")\n',
        )
        self.build([v2]).run_mission("double v2", "double")
        self.assertEqual(self.library.current_version("double"), 2)
        self.assertEqual(self.library.rollback("double"), 1)
        self.assertEqual(self.library.current_version("double"), 1)


class TestLibraryContextGrows(LoopCase):
    def test_existing_skills_are_shown_on_later_missions(self):
        self.build([GOOD]).run_mission("double a number", "double")

        triple = proposal(
            "def triple(n):\n    \"\"\"Triple.\"\"\"\n    return n * 3\n",
            'assert triple(2) == 6\nprint("TESTS PASSED")\n',
        )
        loop2 = self.build([triple])
        loop2.run_mission("triple a number", "triple")
        # The second mission's prompt must mention the first skill, so the model
        # can build on it rather than duplicate work.
        self.assertIn("double", loop2.model.prompts[0])


class TestProposalParsing(unittest.TestCase):
    def test_marker_format(self):
        code, tests = parse_proposal(GOOD)
        self.assertIn("def double", code)
        self.assertIn("TESTS PASSED", tests)

    def test_markdown_fence_fallback(self):
        raw = (
            "Here is the code:\n```python\ndef f():\n    return 1\n```\n"
            "And the tests:\n```python\nassert f() == 1\n```\n"
        )
        code, tests = parse_proposal(raw)
        self.assertIn("def f", code)
        self.assertIn("assert f()", tests)

    def test_fences_inside_markers_are_stripped(self):
        raw = "<<<SKILL>>>\n```python\ndef f():\n    return 1\n```\n<<<TESTS>>>\n```python\nassert f() == 1\n```\n<<<END>>>"
        code, tests = parse_proposal(raw)
        self.assertTrue(code.startswith("def f"), code)
        self.assertNotIn("```", code)
        self.assertNotIn("```", tests)

    def test_unparseable_raises(self):
        from anubis.skills import SkillError

        with self.assertRaises(SkillError):
            parse_proposal("I cannot help with that request.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
