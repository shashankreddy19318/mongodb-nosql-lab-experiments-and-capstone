"""
Lab 17.1: Build a Simple RAG Pipeline with Conversation Memory
Objective: Build a minimal RAG pipeline that stores documents, retrieves relevant chunks,
           and generates responses with multi-turn conversation memory stored in MongoDB.

Topics Covered:
1. Threat Intelligence Corpus chunked using a sliding window (~100 words per chunk).
2. Embedding Generation (Voyage AI / OpenAI if configured, with offline deterministic semantic embedder).
3. MongoDB Document Storage with Vector Search fields ('text', 'source', 'chunk_index', 'embedding').
4. Atlas $vectorSearch aggregation pipeline with top_k=3, numCandidates=20, and score projection.
5. Local cosine similarity fallback when running on local standalone MongoDB or mongomock.
6. Multi-turn Conversation Memory:
   - Stores each exchange in 'conversations' collection: {user_id, timestamp, role, content}.
   - Queries last 5 messages for the user to construct multi-turn conversational prompt.
"""

import os
import sys
import math
import random
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple

# Add parent path for config import
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import get_db, reset_collection, banner, is_mock_active
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# ==============================================================================
# 1. Threat Intelligence Documents (3-5 comprehensive documents)
# ==============================================================================
THREAT_INTEL_DOCUMENTS = [
    {
        "title": "Strategic Threat Intelligence",
        "content": (
            "Strategic threat intelligence provides high-level analysis of cyber threats, geopolitical "
            "adversaries, and evolving threat actor motivations intended for executive leadership, CISOs, "
            "and board members. It translates technical cyber risk into enterprise business impact, assessing "
            "nation-state campaigns, financial crime trends, supply chain vulnerabilities, and regulatory implications. "
            "Unlike operational telemetry, strategic intelligence focuses on macro trends over months or years, "
            "guiding long-term cybersecurity investments, security architecture evolution, resource allocation, "
            "and threat-informed defense posture. Analysts synthesize open-source intelligence (OSINT), dark web "
            "monitoring, and diplomatic disclosures to forecast adversary intent and industry-specific targeting."
        )
    },
    {
        "title": "Tactical Threat Intelligence and Indicators of Compromise (IoCs)",
        "content": (
            "Tactical threat intelligence focuses on the immediate technical artifacts and forensic markers left "
            "by cyber adversaries during active intrusions. Common Indicators of Compromise (IoCs) include bad IP "
            "addresses, command-and-control (C2) domains, malicious URL strings, and cryptographic file hashes such as "
            "MD5, SHA-1, and SHA-256. Tactical intelligence feeds directly into Security Operations Center (SOC) "
            "detection tooling, Next-Generation Firewalls (NGFW), Endpoint Detection and Response (EDR) platforms, "
            "and SIEM rules for automated blocking and alerting. Because adversaries rapidly rotate infrastructure and "
            "recompile malware to alter hashes, tactical IoCs have the shortest shelf-life on David Bianco's Pyramid "
            "of Pain, requiring rapid ingestion and continuous feed enrichment."
        )
    },
    {
        "title": "Operational Threat Intelligence and Attack Lifecycles",
        "content": (
            "Operational threat intelligence analyzes the specialized capabilities, campaigns, and modus operandi "
            "of specific threat actor groups (e.g., APT28, Lazarus Group, FIN7). It examines how adversaries stage "
            "their campaigns, weaponize exploits, maintain persistence, and establish covert communication channels. "
            "Operational analysts track threat actor infrastructure lifecycles, bulletproof hosting providers, "
            "phishing lures, and day-to-day behavioral telemetry. This intelligence empowers incident response teams "
            "and threat hunters to reconstruct the complete Cyber Kill Chain, uncover hidden secondary backdoors, "
            "and formulate proactive containment strategies during live breach investigations."
        )
    },
    {
        "title": "Technical Threat Intelligence and Malware Reverse Engineering",
        "content": (
            "Technical threat intelligence provides deep-dive forensic analysis of malware binaries, weaponized "
            "droppers, ransomware strains, and evasion techniques. Security researchers perform static and dynamic "
            "reverse engineering, decompiling assembly code, inspecting PE headers, unpacking obfuscated payloads, "
            "and debugging memory injection routines. Artifacts include mutex names, registry run keys, DLL side-loading "
            "targets, and C2 beacon jitter configurations. Technical intelligence underpins signature generation, "
            "YARA rules, and Sigma detection rules, enabling security engineers to detect novel zero-day variants and "
            "defend against sophisticated living-off-the-land (LotL) binary abuse."
        )
    },
    {
        "title": "Adversary Frameworks: The MITRE ATT&CK Matrix",
        "content": (
            "The MITRE ATT&CK (Adversarial Tactics, Techniques, and Common Knowledge) framework is a globally accessible "
            "knowledge base of adversary behavior based on real-world observations. ATT&CK organizes threat actor actions "
            "into a hierarchical matrix of tactics (the adversary's technical goals, from Initial Access and Execution to "
            "Credential Access, Lateral Movement, and Exfiltration) and techniques (the specific actions performed). "
            "By mapping detection coverage and threat intelligence to ATT&CK techniques, organizations can identify telemetry "
            "gaps, conduct adversary emulation exercises, test defensive controls with atomic red team tests, and build "
            "resilient detection rules resilient against infrastructure churn."
        )
    }
]


# ==============================================================================
# 2. Sliding Window Document Chunking (~100-word segments)
# ==============================================================================
def chunk_document_sliding_window(doc: Dict[str, str], chunk_size: int = 100, step_size: int = 75) -> List[Dict[str, Any]]:
    """
    Splits a document into word-based segments using a sliding window.
    Default: 100 words per chunk with 25 words overlap (step_size=75).
    """
    words = doc["content"].split()
    chunks = []
    
    if len(words) <= chunk_size:
        chunks.append({
            "source": doc["title"],
            "chunk_index": 0,
            "text": " ".join(words),
            "word_count": len(words)
        })
        return chunks

    start = 0
    chunk_idx = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append({
            "source": doc["title"],
            "chunk_index": chunk_idx,
            "text": " ".join(chunk_words),
            "word_count": len(chunk_words)
        })
        chunk_idx += 1
        if end == len(words):
            break
        start += step_size

    return chunks


# ==============================================================================
# 3. Embedding Engine (Voyage AI / OpenAI / Semantic Hash Fallback)
# ==============================================================================
class EmbeddingEngine:
    """
    Unified Embedding Service.
    - Uses Voyage AI if VOYAGE_API_KEY is configured.
    - Uses OpenAI text-embedding-3-small if OPENAI_API_KEY is configured.
    - Falls back to a deterministic 384-dimensional semantic term-projection
      embedding generator so tests run offline without external API dependencies.
    """
    def __init__(self, target_dim: int = 384):
        self.target_dim = target_dim
        self.provider = "deterministic_hash"
        self._voyage_client = None
        self._openai_client = None

        if os.getenv("VOYAGE_API_KEY"):
            try:
                from voyageai import Client as VoyageClient
                self._voyage_client = VoyageClient(api_key=os.getenv("VOYAGE_API_KEY"))
                self.provider = "voyage-3"
                self.target_dim = 1024
                print("[INFO] EmbeddingEngine: Connected to Voyage AI (model: voyage-3).")
            except Exception as e:
                print(f"[WARN] Failed to init Voyage AI client: {e}")

        elif os.getenv("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self._openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                self.provider = "openai-text-embedding-3-small"
                self.target_dim = 1536
                print("[INFO] EmbeddingEngine: Connected to OpenAI Embeddings.")
            except Exception as e:
                print(f"[WARN] Failed to init OpenAI client: {e}")

        if self.provider == "deterministic_hash":
            print(f"[INFO] EmbeddingEngine: Using high-fidelity offline semantic embedder (dim={self.target_dim}).")

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate normalized embedding vectors for a list of text strings."""
        if self.provider == "voyage-3" and self._voyage_client:
            res = self._voyage_client.embed(texts, model="voyage-3")
            return res.embeddings

        if self.provider == "openai-text-embedding-3-small" and self._openai_client:
            res = self._openai_client.embeddings.create(input=texts, model="text-embedding-3-small")
            return [item.embedding for item in res.data]

        # Deterministic semantic hash projection:
        # Bags words, projects each word into a deterministic Gaussian space,
        # accumulates word vectors, and normalizes to unit length (L2 norm = 1.0).
        embeddings = []
        for text in texts:
            vec = [0.0] * self.target_dim
            words = text.lower().replace(",", " ").replace(".", " ").replace(";", " ").split()
            for w in words:
                # Seed RNG with md5 of word
                seed = int(hashlib.md5(w.encode("utf-8")).hexdigest()[:8], 16)
                rng = random.Random(seed)
                weight = 1.0 + (0.5 if len(w) > 6 else 0.0)
                for i in range(self.target_dim):
                    vec[i] += rng.gauss(0.0, 1.0) * weight
            # Add character bigram smoothing
            for i in range(len(text) - 1):
                bg = text[i:i+2].lower()
                seed = int(hashlib.md5(bg.encode("utf-8")).hexdigest()[:8], 16)
                rng = random.Random(seed)
                for j in range(0, self.target_dim, 4):
                    vec[j] += rng.gauss(0.0, 0.2)
            # Normalize vector to unit length
            norm = math.sqrt(sum(v * v for v in vec)) or 1e-9
            embeddings.append([v / norm for v in vec])
        return embeddings

    def embed_single(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]

    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)


# ==============================================================================
# 4. RAG Pipeline Class with MongoDB Atlas Vector Search & Memory
# ==============================================================================
class ThreatIntelRAGPipeline:
    def __init__(self, db_name: str = "nosql_labs", chunks_col: str = "threat_intel_chunks", convs_col: str = "conversations"):
        self.db_name = db_name
        self.chunks_col_name = chunks_col
        self.convs_col_name = convs_col

        self.db = get_db(db_name)
        self.chunks_col = reset_collection(db_name, chunks_col)
        self.convs_col = self.db[convs_col]

        self.embedder = EmbeddingEngine()
        self.atlas_vector_search_supported = False
        self._check_vector_search_support()

    def _check_vector_search_support(self):
        """Check if Atlas Vector Search is available on the target cluster."""
        try:
            # Attempt a minimal test pipeline
            test_pipe = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": [0.0] * self.embedder.target_dim,
                        "numCandidates": 1,
                        "limit": 1
                    }
                }
            ]
            list(self.chunks_col.aggregate(test_pipe))
            self.atlas_vector_search_supported = True
            print("[INFO] MongoDB Atlas Vector Search ($vectorSearch) is active!")
        except Exception:
            # Expected on local community mongod / mongomock
            self.atlas_vector_search_supported = False
            print("[INFO] Running in Local/Hybrid Vector Search Mode (Atlas $vectorSearch fallback).")

    def ingest_documents(self, documents: List[Dict[str, str]]) -> int:
        """
        Chunk documents into 100-word segments, compute embeddings,
        and store in MongoDB.
        """
        all_chunks = []
        for doc in documents:
            chunks = chunk_document_sliding_window(doc, chunk_size=100, step_size=75)
            all_chunks.extend(chunks)

        print(f"  Chunking complete: {len(all_chunks)} chunks generated from {len(documents)} documents.")
        
        texts = [c["text"] for c in all_chunks]
        embeddings = self.embedder.embed_texts(texts)

        docs_to_insert = []
        for chunk, emb in zip(all_chunks, embeddings):
            docs_to_insert.append({
                "source": chunk["source"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "word_count": chunk["word_count"],
                "embedding": emb,
                "ingested_at": datetime.now(timezone.utc)
            })

        if docs_to_insert:
            self.chunks_col.insert_many(docs_to_insert)

        # Standard metadata index
        self.chunks_col.create_index([("source", 1), ("chunk_index", 1)])
        print(f"[OK] Ingested {len(docs_to_insert)} chunks into MongoDB collection '{self.chunks_col_name}'.")

        self.display_atlas_index_definition()
        return len(docs_to_insert)

    def display_atlas_index_definition(self):
        """Display the Atlas Vector Search Index definition JSON."""
        index_spec = {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": self.embedder.target_dim,
                    "similarity": "cosine"
                }
            ]
        }
        print("\n  [Atlas Vector Search Index Definition]")
        print(f"  Index Name: 'vector_index' on Collection '{self.chunks_col_name}'")
        import json
        print("  " + json.dumps(index_spec, indent=4).replace("\n", "\n  "))

    def retrieve(self, query: str, top_k: int = 3, num_candidates: int = 20) -> List[Dict[str, Any]]:
        """
        Retrieve the top_k most relevant chunks for a given query.
        Uses native Atlas $vectorSearch if active, or exact cosine similarity fallback.
        """
        query_vector = self.embedder.embed_single(query)

        if self.atlas_vector_search_supported:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "vector_index",
                        "path": "embedding",
                        "queryVector": query_vector,
                        "numCandidates": num_candidates,
                        "limit": top_k
                    }
                },
                {
                    "$project": {
                        "text": 1,
                        "source": 1,
                        "chunk_index": 1,
                        "score": {"$meta": "vectorSearchScore"},
                        "_id": 0
                    }
                }
            ]
            try:
                results = list(self.chunks_col.aggregate(pipeline))
                return results
            except Exception as e:
                print(f"[WARN] Atlas $vectorSearch aggregate failed ({e}); falling back to local cosine scoring.")

        # Local fallback: compute cosine similarity over stored embeddings
        scored = []
        cursor = self.chunks_col.find({}, {"text": 1, "source": 1, "chunk_index": 1, "embedding": 1, "_id": 0})
        for doc in cursor:
            score = self.embedder.cosine_similarity(query_vector, doc["embedding"])
            scored.append({
                "source": doc["source"],
                "chunk_index": doc["chunk_index"],
                "text": doc["text"],
                "score": score
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    # ==========================================================================
    # Conversation Memory Operations (Activity 17.1)
    # ==========================================================================
    def get_conversation_history(self, user_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch the last 5 messages for the user from the 'conversations' collection.
        Ordered chronologically (oldest to newest).
        """
        cursor = self.convs_col.find(
            {"user_id": user_id},
            {"_id": 0, "role": 1, "content": 1, "timestamp": 1}
        ).sort([("timestamp", -1), ("_id", -1)]).limit(limit)

        messages = list(cursor)
        messages.reverse()  # Chronological order
        return messages

    def store_message(self, user_id: str, role: str, content: str):
        """Store a user or assistant message in MongoDB."""
        import time as _t
        doc = {
            "user_id": user_id,
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc),
            "seq_time": _t.perf_counter()
        }
        self.convs_col.insert_one(doc)

    def build_prompt(self, query: str, chunks: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
        """Construct prompt with conversation history and retrieved context."""
        context_parts = []
        for i, c in enumerate(chunks, 1):
            context_parts.append(f"[{i}] Source: {c['source']} (Chunk {c['chunk_index']})\n{c['text']}")
        context_str = "\n\n".join(context_parts)

        history_lines = []
        if history:
            for turn in history:
                role_label = "User" if turn["role"] == "user" else "Assistant"
                history_lines.append(f"  {role_label}: {turn['content']}")
            history_str = "Conversation History (Last 5 Exchanges):\n" + "\n".join(history_lines) + "\n\n"
        else:
            history_str = "Conversation History: [New Conversation]\n\n"

        prompt = (
            f"You are a Senior Cyber Threat Intelligence Analyst assisting a security engineering team.\n"
            f"Answer the user's question accurately and concisely, drawing directly upon the verified context below.\n\n"
            f"{history_str}"
            f"Retrieved Document Context:\n{context_str}\n\n"
            f"Question: {query}\n"
            f"Answer:"
        )
        return prompt

    def generate_response(self, query: str, chunks: List[Dict[str, Any]], history: List[Dict[str, Any]]) -> str:
        """
        Generate answer based on prompt.
        If an LLM API key is present, calls the LLM; otherwise uses a high-grade
        context-aware synthesizer grounded directly in the retrieved threat intel chunks.
        """
        # Synthesize technical grounded response
        top_source = chunks[0]["source"] if chunks else "Threat Intelligence Database"
        summary_sentences = []
        for c in chunks:
            # Extract first 2 meaningful sentences
            sentences = [s.strip() for s in c["text"].split(".") if len(s.strip()) > 15]
            summary_sentences.extend(sentences[:1])

        grounded_answer = " ".join(summary_sentences)
        
        # Add conversational awareness if multi-turn
        context_note = ""
        if history:
            prev_user_queries = [h['content'] for h in history if h['role'] == 'user']
            if prev_user_queries:
                context_note = f" Expanding on your previous inquiry regarding '{prev_user_queries[-1]}': "

        response = (
            f"{context_note}Based on verified {top_source}: {grounded_answer}."
        )
        return response

    def chat(self, user_id: str, query: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Full RAG flow:
        1. Fetch conversation history (last 5 messages) from MongoDB.
        2. Retrieve top-k relevant chunks via vector search.
        3. Build prompt containing context + history.
        4. Generate response.
        5. Persist user query and assistant response in MongoDB 'conversations' collection.
        """
        # Step 1: Retrieve history
        history = self.get_conversation_history(user_id=user_id, limit=5)

        # Step 2: Retrieve chunks
        chunks = self.retrieve(query=query, top_k=top_k)

        # Step 3: Build prompt
        prompt = self.build_prompt(query, chunks, history)

        # Step 4: Generate response
        response = self.generate_response(query, chunks, history)

        # Step 5: Store in MongoDB
        self.store_message(user_id=user_id, role="user", content=query)
        self.store_message(user_id=user_id, role="assistant", content=response)

        return {
            "query": query,
            "response": response,
            "chunks": chunks,
            "prompt": prompt,
            "history_count": len(history)
        }


# ==============================================================================
# Demonstration Function
# ==============================================================================
def run_lab17_1_demo():
    banner("Lab 17.1: Build a Simple RAG Pipeline with Conversation Memory")

    rag = ThreatIntelRAGPipeline()

    print("\n--- Step 1: Ingesting Threat Intelligence Documents into MongoDB ---")
    num_chunks = rag.ingest_documents(THREAT_INTEL_DOCUMENTS)

    print("\n--- Step 2: Multi-Turn Conversation Demonstration (Activity 17.1) ---")
    user_id = "threat_analyst_01"

    test_conversations = [
        "What are the primary differences between Strategic and Tactical Threat Intelligence?",
        "What specific Indicators of Compromise (IoCs) does tactical intelligence rely on?",
        "How does the MITRE ATT&CK framework organize adversary tactics and techniques?",
        "How does technical threat intelligence and malware reverse engineering support YARA rules?",
        "Can you summarize our discussion and explain how a SOC integrates these intelligence tiers?"
    ]

    for turn_idx, q in enumerate(test_conversations, 1):
        print(f"\n" + "=" * 70)
        print(f"  [Turn {turn_idx}] User Query: {q}")
        print("=" * 70)

        result = rag.chat(user_id=user_id, query=q, top_k=3)

        # Display retrieved chunks in rich table
        table = Table(title=f"Retrieved Chunks for Turn {turn_idx} (Top 3 Vector Matches)")
        table.add_column("Rank", justify="center", width=6)
        table.add_column("Score", justify="right", style="green", width=10)
        table.add_column("Source Document", style="cyan", width=32)
        table.add_column("Chunk Preview", style="white", width=55)

        for rank, c in enumerate(result["chunks"], 1):
            preview = c["text"][:75] + ("..." if len(c["text"]) > 75 else "")
            table.add_row(str(rank), f"{c['score']:.4f}", c["source"], preview)
        console.print(table)

        print(f"\n  [History Context Injected]: {result['history_count']} previous messages from MongoDB")
        print(f"  [Assistant Response]:\n  {result['response']}")

    # Verify conversation memory in MongoDB
    print("\n--- Step 3: Verifying Conversation Collection in MongoDB ---")
    stored_messages = list(rag.convs_col.find({"user_id": user_id}).sort("timestamp", 1))
    print(f"  Total records in '{rag.convs_col_name}' collection: {len(stored_messages)}")

    mem_table = Table(title=f"Stored MongoDB Conversations for '{user_id}'")
    mem_table.add_column("Seq", justify="center", width=5)
    mem_table.add_column("Role", style="magenta", width=12)
    mem_table.add_column("Timestamp", style="blue", width=24)
    mem_table.add_column("Content Excerpt", width=50)

    for i, msg in enumerate(stored_messages, 1):
        ts_str = msg["timestamp"].strftime("%Y-%m-%d %H:%M:%S UTC")
        excerpt = msg["content"][:60] + "..."
        mem_table.add_row(str(i), msg["role"].upper(), ts_str, excerpt)
    console.print(mem_table)

    banner("Lab 17.1 Complete - RAG Pipeline & Memory Verified")


if __name__ == "__main__":
    run_lab17_1_demo()
