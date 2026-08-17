"""Tests for the research engine."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.research_engine import (
    ResearchEngine,
    KnowledgeGap,
    Hypothesis,
    ThoughtExperiment,
    ImprovementProposal,
    ResearchDirection,
)
from anubis.model import Completion


class MockModel:
    def __init__(self, response: str = '{"statement": "test", "reasoning": "because"}'):
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


class TestKnowledgeGap(unittest.TestCase):
    def test_to_dict(self):
        gap = KnowledgeGap(
            gap_id="g1",
            domain="materials",
            description="test gap",
            current_state="we know X",
            missing="we don't know Y",
        )
        d = gap.to_dict()
        self.assertEqual(d["gap_id"], "g1")
        self.assertEqual(d["domain"], "materials")


class TestHypothesis(unittest.TestCase):
    def test_to_dict(self):
        hyp = Hypothesis(
            hyp_id="h1",
            gap_id="g1",
            statement="test hypothesis",
            reasoning="because",
        )
        d = hyp.to_dict()
        self.assertEqual(d["hyp_id"], "h1")
        self.assertEqual(d["statement"], "test hypothesis")


class TestThoughtExperiment(unittest.TestCase):
    def test_to_dict(self):
        exp = ThoughtExperiment(
            exp_id="e1",
            hyp_id="h1",
            setup="imagine X",
            reasoning="if X then Y",
            predicted_outcome="Y happens",
            implications="this means Z",
            counterarguments="but maybe W",
            conclusion="supported",
        )
        d = exp.to_dict()
        self.assertEqual(d["exp_id"], "e1")
        self.assertEqual(d["conclusion"], "supported")


class TestImprovementProposal(unittest.TestCase):
    def test_to_dict(self):
        prop = ImprovementProposal(
            prop_id="p1",
            title="Better X",
            domain="engineering",
            current_approach="old way",
            proposed_improvement="new way",
            rationale="because better",
            expected_benefit="50% faster",
        )
        d = prop.to_dict()
        self.assertEqual(d["prop_id"], "p1")
        self.assertEqual(d["title"], "Better X")


class TestResearchEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_init(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        self.assertIsNotNone(engine)

    def test_discover_gaps(self):
        model = MockModel(json.dumps([
            {
                "domain": "materials science",
                "description": "gap in nanoscale properties",
                "current_state": "we know bulk properties",
                "missing": "nanoscale behavior",
                "impact": "high",
                "feasibility": "medium",
            }
        ]))
        engine = ResearchEngine(model, self.root)
        gaps = engine.discover_gaps()
        self.assertGreater(len(gaps), 0)
        self.assertEqual(gaps[0].domain, "materials science")

    def test_generate_hypothesis(self):
        model = MockModel(json.dumps({
            "statement": "Nanoscale properties follow different rules",
            "reasoning": "Because surface area to volume ratio changes",
            "testability": "high",
            "novelty": "novel",
            "confidence": 0.6,
        }))
        engine = ResearchEngine(model, self.root)
        gap = KnowledgeGap(
            gap_id="g1",
            domain="materials",
            description="test gap",
            current_state="X",
            missing="Y",
        )
        hyp = engine.generate_hypothesis(gap)
        self.assertIsNotNone(hyp)
        self.assertEqual(hyp.statement, "Nanoscale properties follow different rules")
        self.assertEqual(hyp.novelty, "novel")

    def test_generate_hypothesis_failure(self):
        model = MockModel("invalid response")
        engine = ResearchEngine(model, self.root)
        gap = KnowledgeGap(
            gap_id="g1",
            domain="materials",
            description="test",
            current_state="X",
            missing="Y",
        )
        hyp = engine.generate_hypothesis(gap)
        self.assertIsNone(hyp)

    def test_run_thought_experiment(self):
        model = MockModel(json.dumps({
            "setup": "Imagine testing at nanoscale",
            "reasoning": "If we test, we'd see different behavior",
            "predicted_outcome": "Properties differ from bulk",
            "implications": "Need new models for nanoscale",
            "counterarguments": "Maybe the difference is negligible",
            "conclusion": "supported",
        }))
        engine = ResearchEngine(model, self.root)
        hyp = Hypothesis(
            hyp_id="h1",
            gap_id="g1",
            statement="test",
            reasoning="test",
            confidence=0.5,
        )
        exp = engine.run_thought_experiment(hyp)
        self.assertIsNotNone(exp)
        self.assertEqual(exp.conclusion, "supported")

    def test_thought_experiment_updates_hypothesis(self):
        model = MockModel(json.dumps({
            "setup": "test",
            "reasoning": "test",
            "predicted_outcome": "test",
            "implications": "test",
            "counterarguments": "test",
            "conclusion": "supported",
        }))
        engine = ResearchEngine(model, self.root)
        hyp = Hypothesis(
            hyp_id="h1",
            gap_id="g1",
            statement="test",
            reasoning="test",
            confidence=0.5,
        )
        engine._save_hypothesis(hyp)
        engine.run_thought_experiment(hyp)
        hyps = engine.get_hypotheses()
        self.assertEqual(hyps[0].status, "supported")
        self.assertGreater(hyps[0].confidence, 0.5)

    def test_propose_improvement(self):
        model = MockModel(json.dumps({
            "title": "Use ML for materials discovery",
            "proposed_improvement": "Train models on known properties",
            "rationale": "Faster than trial and error",
            "expected_benefit": "10x faster discovery",
            "implementation_difficulty": "hard",
            "impact_estimate": "high",
            "prerequisites": ["training data", "compute"],
        }))
        engine = ResearchEngine(model, self.root)
        prop = engine.propose_improvement("materials", "trial and error")
        self.assertIsNotNone(prop)
        self.assertEqual(prop.title, "Use ML for materials discovery")

    def test_update_roadmap(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        # Add a gap first
        gap = KnowledgeGap(
            gap_id="g1",
            domain="materials",
            description="test gap",
            current_state="X",
            missing="Y",
            impact="high",
            feasibility="high",
        )
        engine._save_gap(gap)
        directions = engine.update_roadmap()
        self.assertGreater(len(directions), 0)

    def test_get_gaps(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        gap = KnowledgeGap(
            gap_id="g1",
            domain="test",
            description="test",
            current_state="X",
            missing="Y",
        )
        engine._save_gap(gap)
        gaps = engine.get_gaps()
        self.assertEqual(len(gaps), 1)

    def test_get_gaps_by_status(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        gap = KnowledgeGap(
            gap_id="g1",
            domain="test",
            description="test",
            current_state="X",
            missing="Y",
            status="investigating",
        )
        engine._save_gap(gap)
        investigating = engine.get_gaps(status="investigating")
        self.assertEqual(len(investigating), 1)
        open_gaps = engine.get_gaps(status="open")
        self.assertEqual(len(open_gaps), 0)

    def test_persistence(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        gap = KnowledgeGap(
            gap_id="g1",
            domain="test",
            description="test",
            current_state="X",
            missing="Y",
        )
        engine._save_gap(gap)
        engine2 = ResearchEngine(model, self.root)
        self.assertEqual(len(engine2.get_gaps()), 1)

    def test_status(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        status = engine.get_status()
        self.assertEqual(status["total_gaps"], 0)
        self.assertEqual(status["total_hypotheses"], 0)

    def test_parse_json_array(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        result = engine._parse_json_array('```json\n[{"a": 1}]\n```')
        self.assertEqual(len(result), 1)

    def test_parse_json_object(self):
        model = MockModel()
        engine = ResearchEngine(model, self.root)
        result = engine._parse_json_object('```json\n{"a": 1}\n```')
        self.assertEqual(result["a"], 1)


if __name__ == "__main__":
    unittest.main()
