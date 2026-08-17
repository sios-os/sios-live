"""Constitutional kernel tests.

These assert the properties the Constitution claims, especially the ones that
must hold even when the actor is ANUBIS himself.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.constitution import (  # noqa: E402
    Authority,
    ChangeClass,
    Request,
    Verdict,
    analyze_payload,
    evaluate,
    highest_concern,
)


def req(**kw):
    base = dict(
        actor="anubis",
        action="test",
        change_class=ChangeClass.ROUTINE,
        intent="test intent",
    )
    base.update(kw)
    return Request(**base)


class TestOrderOfAuthority(unittest.TestCase):
    def test_harm_prevention_outranks_everything(self):
        self.assertEqual(
            highest_concern(
                [Authority.CONVENIENCE, Authority.HARM_PREVENTION, Authority.PRIVACY_INTEGRITY]
            ),
            Authority.HARM_PREVENTION,
        )

    def test_privacy_outranks_application_goals(self):
        # A recurring real-world failure mode: shipping a feature by weakening
        # privacy. The Constitution forbids it.
        self.assertLess(Authority.PRIVACY_INTEGRITY, Authority.APPLICATION_GOALS)

    def test_full_ordering_is_strict(self):
        order = [
            Authority.HARM_PREVENTION,
            Authority.CONSTITUTIONAL,
            Authority.PRIVACY_INTEGRITY,
            Authority.INFORMED_AUTHORITY,
            Authority.RELIABILITY,
            Authority.APPLICATION_GOALS,
            Authority.CONVENIENCE,
        ]
        self.assertEqual(order, sorted(order))


class TestHazardAnalysis(unittest.TestCase):
    def test_detects_network_access(self):
        laws = {law for law, _ in analyze_payload("import socket\ns=socket.socket()")}
        self.assertIn("local_privacy", laws)

    def test_detects_subprocess_escape(self):
        laws = {law for law, _ in analyze_payload("import subprocess\nsubprocess.run('ls')")}
        self.assertIn("permission_integrity", laws)

    def test_detects_destructive_delete(self):
        laws = {law for law, _ in analyze_payload("import shutil\nshutil.rmtree('/')")}
        self.assertIn("recovery", laws)

    def test_detects_credential_access(self):
        laws = {law for law, _ in analyze_payload("open('/home/u/.ssh/id_rsa').read()")}
        self.assertIn("local_privacy", laws)

    def test_clean_code_has_no_hazards(self):
        clean = "def add(a, b):\n    return a + b\n"
        self.assertEqual(analyze_payload(clean), [])


class TestSandboxContainment(unittest.TestCase):
    def test_hazardous_code_denied_when_not_sandboxed(self):
        r = evaluate(req(
            change_class=ChangeClass.SANDBOXED,
            payload="import socket",
            sandboxed=False,
        ))
        self.assertIs(r.verdict, Verdict.DENY)
        self.assertIn("local_privacy", r.violated_laws)

    def test_hazardous_code_allowed_inside_sandbox(self):
        # Containment, not trust, is what makes this safe.
        r = evaluate(req(
            change_class=ChangeClass.SANDBOXED,
            payload="import socket",
            sandboxed=True,
        ))
        self.assertIs(r.verdict, Verdict.ALLOW)
        self.assertTrue(any("promotion is blocked" in x for x in r.reasons))

    def test_sandboxed_class_requires_actual_sandbox(self):
        r = evaluate(req(change_class=ChangeClass.SANDBOXED, sandboxed=False))
        self.assertIs(r.verdict, Verdict.DENY)


class TestPromotionGate(unittest.TestCase):
    def test_promotion_requires_evidence(self):
        r = evaluate(req(
            change_class=ChangeClass.PROMOTION,
            payload="def f(): return 1",
            evidence_passed=False,
        ))
        self.assertIs(r.verdict, Verdict.DENY)
        self.assertIs(r.authority, Authority.RELIABILITY)

    def test_promotion_allowed_with_evidence(self):
        r = evaluate(req(
            change_class=ChangeClass.PROMOTION,
            payload="def f(): return 1",
            evidence_passed=True,
        ))
        self.assertIs(r.verdict, Verdict.ALLOW)

    def test_hazardous_code_never_promotable_even_with_passing_tests(self):
        # Passing tests must not launder a constitutional breach.
        r = evaluate(req(
            change_class=ChangeClass.PROMOTION,
            payload="import socket",
            evidence_passed=True,
            sandboxed=True,
        ))
        self.assertIs(r.verdict, Verdict.DENY)


class TestCreatorAuthority(unittest.TestCase):
    def test_consequential_requires_approval(self):
        r = evaluate(req(change_class=ChangeClass.CONSEQUENTIAL))
        self.assertIs(r.verdict, Verdict.REQUIRES_CREATOR_APPROVAL)

    def test_consequential_allowed_with_approval(self):
        r = evaluate(req(change_class=ChangeClass.CONSEQUENTIAL, creator_approved=True))
        self.assertIs(r.verdict, Verdict.ALLOW)

    def test_irreversible_requires_approval(self):
        r = evaluate(req(reversible=False))
        self.assertIs(r.verdict, Verdict.DENY)

    def test_unexplainable_action_denied(self):
        r = evaluate(req(explainable=False))
        self.assertIs(r.verdict, Verdict.DENY)


class TestMainEngineTombGate(unittest.TestCase):
    def test_main_engine_requires_approval(self):
        r = evaluate(req(change_class=ChangeClass.MAIN_ENGINE))
        self.assertIs(r.verdict, Verdict.REQUIRES_CREATOR_APPROVAL)

    def test_main_engine_requires_matching_hash(self):
        r = evaluate(req(
            change_class=ChangeClass.MAIN_ENGINE,
            creator_approved=True,
            artifact_hash="a" * 64,
            approved_artifact_hash="b" * 64,
        ))
        self.assertIs(r.verdict, Verdict.DENY)
        self.assertTrue(any("approval is void" in x for x in r.reasons))

    def test_main_engine_allowed_on_exact_hash(self):
        h = "c" * 64
        r = evaluate(req(
            change_class=ChangeClass.MAIN_ENGINE,
            creator_approved=True,
            artifact_hash=h,
            approved_artifact_hash=h,
        ))
        self.assertIs(r.verdict, Verdict.ALLOW)

    def test_approval_without_any_hash_denied(self):
        r = evaluate(req(change_class=ChangeClass.MAIN_ENGINE, creator_approved=True))
        self.assertIs(r.verdict, Verdict.DENY)


class TestNoSelfGrantedAuthority(unittest.TestCase):
    """Doctrine: 'No component grants itself authority.'"""

    def test_actor_cannot_widen_own_capabilities(self):
        r = evaluate(req(
            capabilities_requested=frozenset({"fs.write", "net.out"}),
            capabilities_granted=frozenset({"fs.write"}),
        ))
        self.assertIs(r.verdict, Verdict.DENY)
        self.assertTrue(any("broader than granted" in x for x in r.reasons))

    def test_capabilities_within_grant_allowed(self):
        r = evaluate(req(
            capabilities_requested=frozenset({"fs.write"}),
            capabilities_granted=frozenset({"fs.write", "net.out"}),
        ))
        self.assertIs(r.verdict, Verdict.ALLOW)

    def test_capability_request_without_intent_denied(self):
        r = evaluate(req(
            intent="",
            capabilities_requested=frozenset({"fs.write"}),
            capabilities_granted=frozenset({"fs.write"}),
        ))
        self.assertIs(r.verdict, Verdict.DENY)


class TestExplainability(unittest.TestCase):
    def test_every_ruling_explains_itself(self):
        for cc in ChangeClass:
            r = evaluate(req(change_class=cc, sandboxed=True, payload="x=1"))
            self.assertTrue(r.explain().strip(), f"empty explanation for {cc.name}")
            self.assertTrue(r.reasons, f"no reasons for {cc.name}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
