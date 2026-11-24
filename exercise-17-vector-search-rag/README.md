# Chapter 17: AI-Native MongoDB — Vector Search and RAG Foundations

**Author:** Chintan  
**Docker Hub Repository:** [shashankreddy30/mongodb-lab17](https://hub.docker.com/r/shashankreddy30/mongodb-lab17)  
**Alternative Tag:** [shashankreddy30/nosql-lab17](https://hub.docker.com/r/shashankreddy30/nosql-lab17)  
**Demonstration Command:** `docker run --rm -it shashankreddy30/mongodb-lab17:latest demo`

---

## Overview

This repository contains the complete implementation and verified demonstration environment for **Chapter 17: AI-Native MongoDB -- Vector Search and RAG Foundations**.

It encompasses:
1. **Lab 17.1 (Build a Simple RAG Pipeline):**
   - Domain-specific Threat Intelligence document collection (Strategic, Tactical, Operational, Technical, and MITRE ATT&CK).
   - Sliding-window document chunking (~100 words per chunk with 25-word overlap).
   - Multi-provider vector embedding generator (Voyage AI `voyage-3`, OpenAI `text-embedding-3-small`, and high-fidelity offline deterministic semantic embedder).
   - Document storage in MongoDB collection `threat_intel_chunks` with `text`, `source`, `chunk_index`, and `embedding` fields.
   - Vector search index definition (`vector_index`) and Atlas `$vectorSearch` pipeline stage with `numCandidates=20`, `limit=3`, and `vectorSearchScore` projection.
   - Grounded context synthesis and prompt construction.

2. **Activity 17.1 (Conversation Memory):**
   - Multi-turn conversation history stored in MongoDB `conversations` collection (`user_id`, `role`, `timestamp`, `content`).
   - Dynamic extraction of the last 5 messages for the user.
   - Multi-turn prompt augmentation enabling context-aware conversational dialogue.

3. **Lab 17.2 (Compare HNSW and IVF Vector Search Index Optimization):**
   - Atlas vector search index specifications for HNSW and IVF.
   - 5,000 document vectors with 384 dimensions (simulating Wikipedia sentence embeddings).
   - Batch insertion into MongoDB in batches of 500 documents.
   - 100 queries evaluated against exact brute-force cosine similarity ground truth.
   - Recall@20 calculation: `Recall = |vector_results ∩ brute_force_top_20| / 20.0`.
   - Parameter sweeps:
     - **HNSW:** `efConstruction` (32, 64, 128, 256) and `M` (16, 32).
     - **IVF:** `nlist` (100) and `nprobe` (10, 25, 50, 100).
   - Performance comparison table (Build Time, Latency, Recall@20, Vectors Compared per Query).
   - High-resolution Latency-Recall trade-off curve plotted and saved to `latency_recall_curve.png`.
   - Architectural recommendations for production MongoDB Atlas deployments.

---

## Quickstart with Docker

The entire environment is containerized with MongoDB 7.0 (replica set `rs0`), Python 3, and all dependencies.

### 1. Pull the Published Image
```bash
docker pull shashankreddy30/mongodb-lab17:latest
```

### 2. Run the Full Master Demonstration
```bash
docker run --rm -it shashankreddy30/mongodb-lab17:latest demo
```

### 3. Launch Interactive Menu
```bash
docker run --rm -it shashankreddy30/mongodb-lab17:latest
```

### 4. Run Automated Test Suite
```bash
docker run --rm -it shashankreddy30/mongodb-lab17:latest test
```

### 5. Generate Submission Report PDF
```bash
docker run --rm -it shashankreddy30/mongodb-lab17:latest pdf
```

---

## File Structure

```text
├── config/
│   ├── __init__.py
│   └── connection.py             # MongoDB connection pooling & mongomock fallback
├── lab_01_rag_pipeline.py         # Lab 17.1: Threat Intel RAG & Activity 17.1 Memory
├── lab_02_hnsw_vs_ivf.py          # Lab 17.2: HNSW vs IVF Index Benchmark & Plotting
├── demo_all.py                    # Master demonstration orchestrator
├── test_lab17.py                  # Unit and integration test suite
├── generate_report_pdf.py         # Publication-grade academic PDF generator
├── latency_recall_curve.png       # Generated Latency vs Recall trade-off curve
├── Dockerfile                     # Self-contained container definition
├── docker-compose.yml             # Docker compose configuration
├── entrypoint.sh                  # Multi-option interactive entrypoint
├── build_and_push.ps1             # PowerShell build & push script
├── build_and_push.bat             # Batch build & push script
├── build_and_push.sh              # Bash build & push script
├── requirements.txt               # Python package dependencies
└── exercise 17 nosql.pdf          # Academic PDF report
```

---

## Benchmark Results Summary

| Index Type | Parameters | Build Time (s) | Avg Latency (ms) | Recall@20 (%) | Vectors Compared / Query |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Brute Force** | Exact full-scan (Baseline) | 0.000 s | 0.592 ms | **100.00%** | 5,000 (100.0%) |
| **IVF** | nlist=100, nprobe=10 | 0.102 s | 0.179 ms | 25.60% | 501 (10.0%) |
| **IVF** | nlist=100, nprobe=25 | 0.102 s | 0.935 ms | 48.10% | 1,252 (25.0%) |
| **IVF** | nlist=100, nprobe=50 | 0.102 s | 1.785 ms | 73.05% | 2,506 (50.1%) |
| **IVF** | nlist=100, nprobe=100 | 0.102 s | 5.163 ms | 100.00% | 5,000 (100.0%) |
| **HNSW** | M=16, efC=32, efS=30 | 0.343 s | 2.752 ms | 29.05% | 1,187 (23.7%) |
| **HNSW** | M=16, efC=64, efS=60 | 0.318 s | 5.568 ms | 47.00% | 1,793 (35.9%) |
| **HNSW** | M=16, efC=128, efS=120 | 0.291 s | 4.959 ms | 68.50% | 2,670 (53.4%) |
| **HNSW** | M=16, efC=256, efS=200 | 0.480 s | 7.965 ms | **84.95%** | 3,441 (68.8%) |

### Key Architectural Takeaways
1. **Vectors Compared per Query:** Explains why ANN indexes exist. Both IVF and HNSW scan only a small fraction of the dataset, which becomes crucial when scaling to millions or billions of vectors.
2. **HNSW Recommendation:** Recommended for customer-facing search, conversational RAG, and cybersecurity where high recall (95%-99%) is critical.
3. **IVF Recommendation:** Recommended for multi-million vector datasets where memory footprint is the overriding constraint.
