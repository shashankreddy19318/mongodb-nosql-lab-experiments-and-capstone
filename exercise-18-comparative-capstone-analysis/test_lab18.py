"""
test_lab18.py
Unit and Integration Test Suite for Chapter 18 Comparative Capstone:
- Lab 18.1: Comparative System & Benchmarks (MongoDB, Cassandra, Neo4j)
- Activity 18.1: Graph Community Detection & False-Positive Isolation
- Lab 18.2: Comparative Analysis Report & PDF Compilation

Can be executed standalone: python test_lab18.py
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import (
    get_mongo_db,
    reset_collection,
    get_cassandra_session,
    get_neo4j_driver
)
from lab_01_threat_intel_system import (
    generate_threat_dataset,
    ingest_mongodb,
    ingest_cassandra,
    ingest_neo4j,
    run_benchmark_suite,
    run_activity_18_1_detection
)
from lab_02_comparative_report import generate_markdown_report
from generate_report_pdf import build_pdf_report


class TestChapter18Capstone(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Provision a test dataset and initialize databases."""
        cls.test_threats = generate_threat_dataset(n=1000, seed=123)
        cls.db = get_mongo_db("threat_test_db")
        cls.cass = get_cassandra_session()
        cls.neo = get_neo4j_driver()

        ingest_mongodb(cls.db, cls.test_threats)
        ingest_cassandra(cls.cass, cls.test_threats)
        ingest_neo4j(cls.neo, cls.test_threats)

    def test_01_dataset_integrity(self):
        """Verify synthetic dataset has all required schema fields and valid types."""
        self.assertEqual(len(self.test_threats), 1000)
        sample = self.test_threats[0]
        required_fields = [
            "threat_id", "from_source", "threat_type", "indicator",
            "target", "severity", "confidence", "risk_score", "timestamp", "is_false_positive"
        ]
        for field in required_fields:
            self.assertIn(field, sample)
            self.assertIsNotNone(sample[field])

    def test_02_mongodb_embedded_and_full_schema(self):
        """Verify MongoDB has 'full_threats' and embedded 'threat' collection."""
        full_col = self.db["full_threats"]
        threat_col = self.db["threat"]

        self.assertEqual(full_col.count_documents({}), 1000)

        # Check embedded recent_threats array
        source_doc = threat_col.find_one({"source_id": "SRC-001"})
        if source_doc:
            self.assertIn("recent_threats", source_doc)
            self.assertLessEqual(len(source_doc["recent_threats"]), 50)

    def test_03_cassandra_dual_tables(self):
        """Verify Cassandra dual-table writes satisfy partition queries."""
        history = self.cass.query_threat_history("SRC-001", limit=10)
        self.assertIsInstance(history, list)

        # Verify daily volume
        volume = self.cass.query_daily_volume()
        self.assertIsInstance(volume, dict)
        self.assertGreater(len(volume), 0)

    def test_04_neo4j_graph_and_activity_18_1(self):
        """Verify Neo4j graph traversal and false-positive community detection."""
        history = self.neo.query_threat_history("SRC-001", limit=10)
        self.assertIsInstance(history, list)

        # Test Activity 18.1 Community Detection
        fp_communities = run_activity_18_1_detection(self.db, self.neo)
        self.assertIsInstance(fp_communities, list)
        self.assertGreater(len(fp_communities), 0)

    def test_05_benchmark_suite_execution(self):
        """Verify 4 benchmark queries run and produce median latency stats."""
        benchmarks = run_benchmark_suite(self.db, self.cass, self.neo, self.test_threats)
        self.assertIn("Q1_Threat_History", benchmarks)
        self.assertIn("Q2_Target_and_Spread", benchmarks)
        self.assertIn("Q3_Daily_Volume_Analytics", benchmarks)
        self.assertIn("Q4_Insert_Throughput", benchmarks)

        for qname, dbs in benchmarks.items():
            for db_name in ["MongoDB", "Cassandra", "Neo4j"]:
                self.assertIn(db_name, dbs)
                self.assertIn("median", dbs[db_name])
                self.assertGreaterEqual(dbs[db_name]["median"], 0.0)

    def test_06_report_and_pdf_generation(self):
        """Verify report generation produces non-empty Markdown and PDF files."""
        benchmarks = run_benchmark_suite(self.db, self.cass, self.neo, self.test_threats)
        fp_communities = run_activity_18_1_detection(self.db, self.neo)
        report_md = generate_markdown_report(benchmarks, fp_communities)
        self.assertIn("# Comparative Analysis Report", report_md)
        self.assertIn("Executive Summary", report_md)

        test_pdf = "test_output.pdf"
        build_pdf_report(test_pdf)
        self.assertTrue(os.path.exists(test_pdf))
        self.assertGreater(os.path.getsize(test_pdf), 5000)
        if os.path.exists(test_pdf):
            os.remove(test_pdf)


if __name__ == "__main__":
    unittest.main()
