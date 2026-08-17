"""Tests for the knowledge acquisition system."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from anubis.knowledge_acquisition import (
    KnowledgeAcquisition,
    AcquisitionRequest,
    classify_license,
    detect_license,
    LICENSE_CATEGORIES,
)


class TestLicenseClassification(unittest.TestCase):
    def test_public_domain(self):
        result = classify_license("public domain")
        self.assertEqual(result["category"], "public_domain")
        self.assertTrue(result["auto_promotable"])

    def test_cc0(self):
        result = classify_license("CC0 1.0 Universal")
        self.assertEqual(result["category"], "public_domain")
        self.assertTrue(result["auto_promotable"])

    def test_mit(self):
        result = classify_license("MIT License")
        self.assertEqual(result["category"], "open")
        self.assertTrue(result["auto_promotable"])

    def test_apache(self):
        result = classify_license("Apache 2.0")
        self.assertEqual(result["category"], "open")
        self.assertTrue(result["auto_promotable"])

    def test_cc_by_nc(self):
        result = classify_license("CC-BY-NC 4.0")
        self.assertEqual(result["category"], "non_commercial")
        self.assertFalse(result["auto_promotable"])

    def test_proprietary(self):
        result = classify_license("All Rights Reserved")
        self.assertEqual(result["category"], "restricted")
        self.assertFalse(result["auto_promotable"])

    def test_unknown(self):
        result = classify_license("some weird license")
        self.assertEqual(result["category"], "restricted")
        self.assertFalse(result["auto_promotable"])


class TestDetectLicense(unittest.TestCase):
    def test_detect_mit(self):
        text = "Permission is hereby granted, free of charge, to any person"
        self.assertEqual(detect_license(text), "mit")

    def test_detect_apache(self):
        text = "Apache License, Version 2.0\n\nLicensed under the Apache"
        self.assertEqual(detect_license(text), "apache-2.0")

    def test_detect_cc_by(self):
        text = "This work is licensed under cc-by 4.0"
        self.assertEqual(detect_license(text), "cc-by")

    def test_detect_public_domain(self):
        text = "This work is in the public domain."
        self.assertEqual(detect_license(text), "public domain")

    def test_detect_unknown(self):
        text = "This is just some random text without any license info."
        self.assertEqual(detect_license(text), "unknown")


class TestAcquisitionRequest(unittest.TestCase):
    def test_to_dict(self):
        req = AcquisitionRequest(
            request_id="r1",
            topic="quantum computing",
            reason="needed for project",
            source="creator",
        )
        d = req.to_dict()
        self.assertEqual(d["request_id"], "r1")
        self.assertEqual(d["topic"], "quantum computing")
        self.assertEqual(d["status"], "pending")


class MockGateway:
    def __init__(self, search_results=None, fetch_content=None):
        self._search_results = search_results or []
        self._fetch_content = fetch_content or ""

    def search(self, query):
        return {"results": self._search_results}

    def fetch(self, url):
        return {"content": self._fetch_content, "url": url}


class MockKnowledgeBase:
    def __init__(self):
        self.quarantined = []

    def ingest_to_quarantine(self, title, content, source_id="", specialty_id="", license="", tags=None):
        import hashlib, time
        qid = hashlib.sha256(f"q:{title}:{time.time()}".encode()).hexdigest()[:16]
        self.quarantined.append({
            "qid": qid,
            "title": title,
            "content": content,
            "source_id": source_id,
            "license": license,
        })
        return qid


class TestKnowledgeAcquisition(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.root = Path(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_request_acquisition(self):
        acq = KnowledgeAcquisition(self.root)
        req = acq.request_acquisition("python testing", "need for project")
        self.assertEqual(req.topic, "python testing")
        self.assertEqual(req.status, "pending")

    def test_process_no_gateway(self):
        acq = KnowledgeAcquisition(self.root)
        req = acq.request_acquisition("test", "r")
        result = acq.process_request(req.request_id)
        self.assertIn("error", result)

    def test_process_with_gateway(self):
        gateway = MockGateway(
            search_results=[
                {"url": "https://example.com/doc", "title": "Python Testing Guide"},
            ],
            fetch_content="This is documentation about Python testing.\nMIT License\n",
        )
        kb = MockKnowledgeBase()
        acq = KnowledgeAcquisition(
            self.root, gateway=gateway, knowledge=kb
        )
        req = acq.request_acquisition("python testing", "need")
        result = acq.process_request(req.request_id)
        self.assertEqual(result["status"], "quarantined")
        self.assertGreater(len(kb.quarantined), 0)

    def test_process_no_results(self):
        gateway = MockGateway(search_results=[])
        acq = KnowledgeAcquisition(self.root, gateway=gateway)
        req = acq.request_acquisition("nonexistent topic", "r")
        result = acq.process_request(req.request_id)
        self.assertIn("error", result)

    def test_auto_promote_eligible(self):
        gateway = MockGateway(
            search_results=[{"url": "https://example.com", "title": "Doc"}],
            fetch_content="Public domain documentation about testing.",
        )
        kb = MockKnowledgeBase()
        acq = KnowledgeAcquisition(
            self.root, gateway=gateway, knowledge=kb
        )
        req = acq.request_acquisition("testing", "r")
        acq.process_request(req.request_id)
        result = acq.auto_promote_eligible(req.request_id)
        self.assertIn(result["status"], ["promoted", "partially_promoted", "needs_approval"])

    def test_list_requests(self):
        acq = KnowledgeAcquisition(self.root)
        acq.request_acquisition("topic1", "r1")
        acq.request_acquisition("topic2", "r2")
        requests = acq.list_requests()
        self.assertEqual(len(requests), 2)

    def test_list_requests_by_status(self):
        acq = KnowledgeAcquisition(self.root)
        acq.request_acquisition("topic1", "r1")
        pending = acq.list_requests(status="pending")
        self.assertEqual(len(pending), 1)

    def test_get_request(self):
        acq = KnowledgeAcquisition(self.root)
        req = acq.request_acquisition("topic", "r")
        loaded = acq.get_request(req.request_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["topic"], "topic")

    def test_status(self):
        acq = KnowledgeAcquisition(self.root)
        status = acq.get_status()
        self.assertEqual(status["total_requests"], 0)
        self.assertFalse(status["gateway_configured"])

    def test_status_with_gateway(self):
        gateway = MockGateway()
        acq = KnowledgeAcquisition(self.root, gateway=gateway)
        status = acq.get_status()
        self.assertTrue(status["gateway_configured"])

    def test_persistence(self):
        acq = KnowledgeAcquisition(self.root)
        acq.request_acquisition("topic", "r")
        acq2 = KnowledgeAcquisition(self.root)
        self.assertEqual(len(acq2.list_requests()), 1)


if __name__ == "__main__":
    unittest.main()
