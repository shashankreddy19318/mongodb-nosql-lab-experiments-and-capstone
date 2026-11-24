"""
test_app.py
Comprehensive unit and integration test suite covering:
1. Threat database seeding and queries
2. RAG vector retrieval & cosine scoring
3. Conversational chat endpoint and session history persistence
4. Autonomous Vulnerability Bot scan and conversational mitigation
5. Exercises 1 through 18 execution matrix
"""

import unittest
from fastapi.testclient import TestClient

from app.database import get_db, reset_db
from app.threat_service import init_threat_database, get_threats, retrieve_threat_context
from app.bot_service import bot_instance
from app.chat_api import app
import app.exercises_service as exercises

class TestThreatIntelligencePlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_threat_database()
        cls.client = TestClient(app)

    def test_01_database_seeded(self):
        db = get_db()
        threats_count = db["threats"].count_documents({})
        self.assertGreaterEqual(threats_count, 20, "Should have seeded at least 20 threats across platforms")

    def test_02_platform_filtering(self):
        win_threats = get_threats(platform="Windows")
        self.assertGreater(len(win_threats), 0)
        for t in win_threats:
            self.assertEqual(t["platform"], "Windows")

        lnx_threats = get_threats(platform="Linux")
        self.assertGreater(len(lnx_threats), 0)
        for t in lnx_threats:
            self.assertEqual(t["platform"], "Linux")

    def test_03_lifecycle_filtering(self):
        active_threats = get_threats(lifecycle_status="Active")
        self.assertGreater(len(active_threats), 0)
        for t in active_threats:
            self.assertEqual(t["lifecycle_status"], "Active")

        resolved_threats = get_threats(lifecycle_status="Resolved")
        self.assertGreater(len(resolved_threats), 0)
        for t in resolved_threats:
            self.assertEqual(t["lifecycle_status"], "Resolved")

    def test_04_rag_vector_retrieval(self):
        results = retrieve_threat_context("Windows LockBit ransomware", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertGreater(results[0]["score"], 0.5)
        self.assertIn("Windows", [r["platform"] for r in results])

    def test_05_api_health(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "healthy")
        self.assertGreater(data["total_threats"], 0)

    def test_06_api_chat_flow_and_session(self):
        session_id = "test-session-unit-01"
        res = self.client.post("/chat", json={
            "session_id": session_id,
            "message": "How do I mitigate Dirty Pipe on Linux?",
            "platform": "Linux",
            "top_k": 2
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("response", data)
        self.assertGreater(len(data["sources"]), 0)

        # Verify session persistence in MongoDB
        db = get_db()
        session_doc = db["sessions"].find_one({"session_id": session_id})
        self.assertIsNotNone(session_doc)
        self.assertEqual(len(session_doc["history"]), 2)

    def test_07_bot_scan_and_conversational_mitigation(self):
        # 1. Trigger scan
        scan_res = self.client.post("/bot/scan", json={"platform": "Linux", "scope": "system"})
        self.assertEqual(scan_res.status_code, 200)
        scan_data = scan_res.json()
        self.assertGreaterEqual(scan_data["detected_count"], 1)
        vuln = scan_data["vulnerabilities"][0]

        # 2. Conversational confirmation via chat endpoint ("Yes, approve")
        chat_confirm_res = self.client.post("/chat", json={
            "session_id": "test-session-unit-bot",
            "message": "Yes, approve and fix it",
            "platform": "Linux"
        })
        self.assertEqual(chat_confirm_res.status_code, 200)
        chat_data = chat_confirm_res.json()
        self.assertIn("Mitigation Confirmed", chat_data["response"])

        # 3. Verify threat was recorded as Resolved
        db = get_db()
        resolved_doc = db["threats"].find_one({"threat_id": f"THR-{vuln['vuln_id']}"})
        self.assertIsNotNone(resolved_doc)
        self.assertEqual(resolved_doc["lifecycle_status"], "Resolved")

    def test_08_exercises_1_to_18_all_pass(self):
        res = exercises.run_all_exercises()
        self.assertEqual(res["total_exercises"], 18)
        self.assertEqual(res["passed"], 18, "All 18 exercises must pass")

if __name__ == "__main__":
    unittest.main()
