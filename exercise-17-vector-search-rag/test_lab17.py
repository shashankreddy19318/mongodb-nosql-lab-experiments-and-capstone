"""
test_lab17.py
Unit and Integration Test Suite for Chapter 17 Labs:
- Lab 17.1: Build a Simple RAG Pipeline with MongoDB Conversation Memory
- Lab 17.2: Compare HNSW and IVF Vector Search Index Types

Can be run standalone: python test_lab17.py
"""

import unittest
import numpy as np
import os
import sys

# Ensure local imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from lab_01_rag_pipeline import (
    THREAT_INTEL_DOCUMENTS,
    chunk_document_sliding_window,
    EmbeddingEngine,
    ThreatIntelRAGPipeline
)
from lab_02_hnsw_vs_ivf import (
    generate_synthetic_corpus,
    compute_ground_truth,
    compute_recall,
    IVFIndex,
    HNSWIndex,
    HNSW_INDEX_SPEC,
    IVF_INDEX_SPEC
)


class TestLab17RAGPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = EmbeddingEngine(target_dim=384)
        cls.rag = ThreatIntelRAGPipeline(db_name="nosql_test_db")
        cls.rag.ingest_documents(THREAT_INTEL_DOCUMENTS)

    def test_01_document_chunking(self):
        """Test sliding window chunking produces expected segments and word counts."""
        doc = THREAT_INTEL_DOCUMENTS[0]
        chunks = chunk_document_sliding_window(doc, chunk_size=100, step_size=75)
        self.assertGreaterEqual(len(chunks), 1)
        for c in chunks:
            self.assertEqual(c["source"], doc["title"])
            self.assertIn("text", c)
            self.assertGreater(c["word_count"], 0)
            self.assertLessEqual(c["word_count"], 100)

    def test_02_embedding_engine_properties(self):
        """Test embedding generation vectors are normalized to unit length."""
        texts = [
            "MongoDB Atlas Vector Search with HNSW index",
            "Command and Control C2 network telemetry"
        ]
        embeddings = self.engine.embed_texts(texts)
        self.assertEqual(len(embeddings), 2)
        self.assertEqual(len(embeddings[0]), 384)

        # Check L2 norm is approximately 1.0
        norm_0 = sum(x * x for x in embeddings[0]) ** 0.5
        norm_1 = sum(x * x for x in embeddings[1]) ** 0.5
        self.assertAlmostEqual(norm_0, 1.0, places=4)
        self.assertAlmostEqual(norm_1, 1.0, places=4)

        # Check cosine similarity between identical texts is 1.0
        sim_self = self.engine.cosine_similarity(embeddings[0], embeddings[0])
        self.assertAlmostEqual(sim_self, 1.0, places=4)

    def test_03_vector_retrieval(self):
        """Test retrieving top-k chunks returns ranked results with valid scores."""
        query = "What are the common indicators of compromise like IP addresses and hashes?"
        results = self.rag.retrieve(query, top_k=3)
        self.assertEqual(len(results), 3)
        self.assertIn("score", results[0])
        self.assertIn("text", results[0])
        self.assertIn("source", results[0])
        # Verify scores are sorted descending
        self.assertGreaterEqual(results[0]["score"], results[1]["score"])
        self.assertGreaterEqual(results[1]["score"], results[2]["score"])

    def test_04_conversation_memory_persistence(self):
        """Test storing and retrieving last 5 messages for multi-turn conversational context."""
        user_id = "test_analyst_99"
        # Clear any prior messages for this test user
        self.rag.convs_col.delete_many({"user_id": user_id})

        for i in range(1, 8):
            self.rag.store_message(user_id, role="user", content=f"Query {i}")
            self.rag.store_message(user_id, role="assistant", content=f"Response {i}")

        # Fetch last 5 messages
        history = self.rag.get_conversation_history(user_id, limit=5)
        self.assertEqual(len(history), 5)
        # Should contain the most recent messages in chronological order
        self.assertEqual(history[-1]["role"], "assistant")
        self.assertEqual(history[-1]["content"], "Response 7")
        self.assertEqual(history[-2]["role"], "user")
        self.assertEqual(history[-2]["content"], "Query 7")

    def test_05_multi_turn_chat_synthesis(self):
        """Test full chat execution: retrieves chunks, injects history, and persists dialogue."""
        user_id = "test_analyst_flow"
        self.rag.convs_col.delete_many({"user_id": user_id})

        res1 = self.rag.chat(user_id, "Explain Strategic Threat Intelligence", top_k=2)
        self.assertIn("Strategic Threat Intelligence", res1["response"])

        res2 = self.rag.chat(user_id, "How does it differ from Tactical IoCs?", top_k=2)
        self.assertGreater(res2["history_count"], 0)
        self.assertIn("Tactical Threat Intelligence", res2["response"])


class TestLab17IndexOptimization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        np.random.seed(42)
        cls.data, cls.queries, _ = generate_synthetic_corpus(n_docs=500, dim=64, n_queries=10)
        cls.k = 10
        cls.ground_truths, _ = compute_ground_truth(cls.data, cls.queries, k=cls.k)

    def test_06_atlas_index_specifications(self):
        """Verify HNSW and IVF index specifications conform to Atlas Search syntax."""
        self.assertEqual(HNSW_INDEX_SPEC["type"], "vectorSearch")
        self.assertEqual(HNSW_INDEX_SPEC["definition"]["fields"][0]["indexOption"]["type"], "hnsw")
        self.assertEqual(HNSW_INDEX_SPEC["definition"]["fields"][0]["indexOption"]["M"], 16)

        self.assertEqual(IVF_INDEX_SPEC["type"], "vectorSearch")
        self.assertEqual(IVF_INDEX_SPEC["definition"]["fields"][0]["indexOption"]["type"], "ivf")
        self.assertEqual(IVF_INDEX_SPEC["definition"]["fields"][0]["indexOption"]["nlist"], 100)

    def test_07_ivf_index_build_and_search(self):
        """Verify IVF index partitions dataset and returns top-k with valid recall."""
        ivf = IVFIndex(nlist=20)
        ivf.build(self.data, iterations=5)
        self.assertEqual(len(ivf.buckets), 20)

        # Search with nprobe=5
        pred, comp, lat = ivf.search(self.queries[0], k=self.k, nprobe=5)
        self.assertEqual(len(pred), self.k)
        self.assertGreater(comp, 0)
        self.assertLessEqual(comp, len(self.data))

        recall = compute_recall(pred, self.ground_truths[0])
        self.assertGreaterEqual(recall, 0.0)
        self.assertLessEqual(recall, 1.0)

    def test_08_hnsw_index_build_and_search(self):
        """Verify HNSW index builds small-world proximity graph and performs greedy search."""
        hnsw = HNSWIndex(m=16, ef_construction=32)
        hnsw.build(self.data)
        self.assertEqual(len(hnsw.graph), len(self.data))

        # Search with ef_search=40
        pred, comp, lat = hnsw.search(self.queries[0], k=self.k, ef_search=40)
        self.assertEqual(len(pred), self.k)
        self.assertGreater(comp, 0)

        recall = compute_recall(pred, self.ground_truths[0])
        self.assertGreaterEqual(recall, 0.0)
        self.assertLessEqual(recall, 1.0)

    def test_09_recall_calculation(self):
        """Verify Recall@K mathematical computation."""
        pred = np.array([0, 1, 2, 3, 4])
        gt = np.array([0, 1, 2, 8, 9])
        # 3 matching items out of 5 -> 60%
        rec = compute_recall(pred, gt)
        self.assertAlmostEqual(rec, 0.60, places=4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
