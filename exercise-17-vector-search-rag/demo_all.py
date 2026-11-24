"""
demo_all.py
Master Demonstration Script for Chapter 17:
AI-Native MongoDB - Vector Search and RAG Foundations

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab17

Executes:
1. Lab 17.1: RAG Pipeline with Threat Intelligence Corpus & MongoDB Conversation Memory
2. Lab 17.2: Vector Search Index Optimization (HNSW vs. IVF) Benchmark & Curve Generation
"""

import os
import sys
import time

# Ensure workspace imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import banner, get_client, is_mock_active
from lab_01_rag_pipeline import run_lab17_1_demo
from lab_02_hnsw_vs_ivf import run_lab17_2_benchmark


def main():
    start_total = time.perf_counter()

    banner("CHAPTER 17: AI-NATIVE MONGODB - VECTOR SEARCH & RAG DEMONSTRATION", char="#", width=78)
    print("  Author:                  Chintan")
    print("  Docker Hub:              https://hub.docker.com/r/shashankreddy30/mongodb-lab17")
    print("  Course / Scope:          Distributed NoSQL Databases (Chapter 17)")
    print("  Topics:                  Atlas Vector Search, RAG Pipelines, Conversation Memory,")
    print("                           HNSW vs. IVF Index Performance, Recall@20 & Latency Trade-offs")
    print("#" * 78)

    # Check MongoDB Status
    print("\n[PHASE 0] Checking MongoDB Storage Engine Status...")
    client = get_client()
    if is_mock_active():
        print("  -> Status: In-Memory High-Fidelity Mock Engine Active (Offline Sandbox).")
    else:
        print("  -> Status: Connected to Live MongoDB Instance.")

    # Phase 1: Lab 17.1
    print("\n" + "#" * 78)
    print("  [PHASE 1] Executing Lab 17.1: Simple RAG Pipeline with Conversation Memory")
    print("#" * 78)
    run_lab17_1_demo()

    # Phase 2: Lab 17.2
    print("\n" + "#" * 78)
    print("  [PHASE 2] Executing Lab 17.2: HNSW vs. IVF Index Optimization Benchmark")
    print("#" * 78)
    results = run_lab17_2_benchmark()

    elapsed = time.perf_counter() - start_total
    print("\n" + "#" * 78)
    print("  CHAPTER 17 MASTER DEMONSTRATION COMPLETE")
    print(f"  Total Demonstration Execution Time: {elapsed:.2f} seconds")
    print("  Generated Artifacts:")
    print("    - latency_recall_curve.png (300 DPI Matplotlib Curve)")
    print("    - threat_intel_chunks collection in MongoDB")
    print("    - conversations collection in MongoDB")
    print("    - vector_benchmark collection in MongoDB")
    print("  Docker Run Command:")
    print("    docker run --rm -it shashankreddy30/mongodb-lab17:latest demo")
    print("#" * 78 + "\n")


if __name__ == "__main__":
    main()
