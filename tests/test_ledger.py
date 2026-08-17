"""Evidence ledger tests.

The ledger's only real claim is that history cannot be altered undetectably.
These tests attack that claim directly.
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from anubis.ledger import GENESIS_HASH, Ledger  # noqa: E402


class LedgerCase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "evidence.jsonl"
        self.ledger = Ledger(self.path)

    def tearDown(self):
        self.dir.cleanup()


class TestAppendAndVerify(LedgerCase):
    def test_empty_ledger_verifies(self):
        ok, msg = self.ledger.verify()
        self.assertTrue(ok, msg)

    def test_head_starts_at_genesis(self):
        self.assertEqual(self.ledger.head, GENESIS_HASH)

    def test_append_advances_chain(self):
        e1 = self.ledger.append("anubis", "a", {"n": 1})
        e2 = self.ledger.append("anubis", "b", {"n": 2})
        self.assertEqual(e1.prev_hash, GENESIS_HASH)
        self.assertEqual(e2.prev_hash, e1.entry_hash)
        self.assertEqual(self.ledger.head, e2.entry_hash)
        self.assertEqual(self.ledger.length, 2)

    def test_many_entries_verify(self):
        for i in range(200):
            self.ledger.append("anubis", "step", {"i": i})
        ok, msg = self.ledger.verify()
        self.assertTrue(ok, msg)
        self.assertEqual(self.ledger.length, 200)

    def test_survives_reopen(self):
        for i in range(5):
            self.ledger.append("anubis", "step", {"i": i})
        head = self.ledger.head
        reopened = Ledger(self.path)
        self.assertEqual(reopened.head, head)
        self.assertEqual(reopened.length, 5)
        # Chain must continue correctly across the reopen.
        e = reopened.append("anubis", "after-reopen", {})
        self.assertEqual(e.prev_hash, head)
        ok, msg = reopened.verify()
        self.assertTrue(ok, msg)


class TestTamperDetection(LedgerCase):
    def _rows(self):
        return [
            json.loads(l)
            for l in self.path.read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]

    def _write(self, rows):
        self.path.write_text(
            "\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8"
        )

    def _seed(self, n=6):
        for i in range(n):
            self.ledger.append("anubis", "step", {"i": i, "note": f"entry {i}"})
        ok, _ = self.ledger.verify()
        self.assertTrue(ok)

    def test_detects_payload_edit(self):
        self._seed()
        rows = self._rows()
        rows[3]["payload"]["note"] = "silently changed"
        self._write(rows)
        ok, msg = self.ledger.verify()
        self.assertFalse(ok)
        self.assertIn("payload altered at seq 3", msg)

    def test_detects_deleted_entry(self):
        self._seed()
        rows = self._rows()
        del rows[2]
        self._write(rows)
        ok, msg = self.ledger.verify()
        self.assertFalse(ok)
        self.assertIn("sequence break", msg)

    def test_detects_reordering(self):
        self._seed()
        rows = self._rows()
        rows[2], rows[4] = rows[4], rows[2]
        self._write(rows)
        ok, msg = self.ledger.verify()
        self.assertFalse(ok)

    def test_detects_forged_entry_with_recomputed_payload_hash(self):
        # A sophisticated tamper: attacker fixes the payload hash to match the
        # edited payload. The entry hash and chain must still catch it.
        import hashlib

        self._seed()
        rows = self._rows()
        rows[3]["payload"]["note"] = "forged"
        canonical = json.dumps(
            rows[3]["payload"], sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
        rows[3]["payload_hash"] = hashlib.sha256(canonical).hexdigest()
        self._write(rows)
        ok, msg = self.ledger.verify()
        self.assertFalse(ok, "forged payload_hash slipped through")
        self.assertIn("seq 3", msg)

    def test_detects_appended_fake_entry(self):
        self._seed()
        rows = self._rows()
        fake = dict(rows[-1])
        fake["seq"] = len(rows)
        fake["action"] = "skill.promoted"
        fake["payload"] = {"name": "backdoor", "task": "t", "code": "c"}
        rows.append(fake)
        self._write(rows)
        ok, msg = self.ledger.verify()
        self.assertFalse(ok)


class TestTrainingCorpus(LedgerCase):
    def test_only_promoted_skills_become_exemplars(self):
        self.ledger.append(
            "anubis", "skill.promoted",
            {"name": "good", "task": "add numbers", "code": "def f(): ...",
             "reasoning": "because"},
        )
        self.ledger.append(
            "anubis", "skill.rejected",
            {"name": "bad", "task": "t", "code": "c"},
        )
        self.ledger.append("anubis", "loop.start", {"task": "t"})

        records = list(self.ledger.training_records())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["skill"], "good")
        self.assertEqual(records[0]["task"], "add numbers")

    def test_incomplete_records_skipped(self):
        self.ledger.append("anubis", "skill.promoted", {"name": "x"})  # no task/code
        self.assertEqual(list(self.ledger.training_records()), [])

    def test_records_carry_evidence_hash(self):
        self.ledger.append(
            "anubis", "skill.promoted",
            {"name": "s", "task": "t", "code": "c"},
        )
        rec = next(iter(self.ledger.training_records()))
        self.assertEqual(len(rec["evidence_hash"]), 64)


if __name__ == "__main__":
    unittest.main(verbosity=2)
