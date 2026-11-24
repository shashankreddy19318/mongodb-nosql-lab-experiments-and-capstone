"""
demo_all.py
Master Demonstration Script for Chapter 18:
Comparative Capstone: Identifying False-Positives in Threat Intelligence Services

Executes the entire end-to-end pipeline:
1. Data generation of 100,000 threats across 20 global feeds.
2. MongoDB, Cassandra, and Neo4j schema provisioning and ingestion.
3. 4-Query Benchmarking Suite (10 runs each, reporting median latency).
4. Activity 18.1: Graph Community Detection & False-Positive Isolation.
5. Markdown Report Generation (reports/comparative_analysis_report.md).
6. Publication-grade PDF Report Generation (exercise 18 nosql.pdf).

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab18
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import banner, is_mongo_mock_active
from lab_01_threat_intel_system import run_lab18_1_complete
from lab_02_comparative_report import generate_markdown_report, REPORT_DIR
from generate_report_pdf import build_pdf_report
import shutil


def main():
    start_total = time.perf_counter()

    banner("CHAPTER 18: COMPARATIVE CAPSTONE - THREAT INTELLIGENCE MASTER DEMO", char="#", width=78)
    print("  Author:                  Chintan")
    print("  Docker Hub:              https://hub.docker.com/r/shashankreddy30/mongodb-lab18")
    print("  Course / Scope:          Distributed NoSQL Databases (Chapter 18)")
    print("  Use Case:                Identifying False-Positives from Threat Intelligence Feeds")
    print("  Databases Compared:      MongoDB (Document), Apache Cassandra (Wide-Column), Neo4j (Graph)")
    print("#" * 78)

    # 1. Check Engine
    print("\n[PHASE 0] Checking Database Engine Status...")
    if is_mongo_mock_active():
        print("  -> Status: In-Memory High-Fidelity Engine Active (Sandboxed Container).")
    else:
        print("  -> Status: Connected to Live Database Engine.")

    # 2. Phase 1: Lab 18.1
    print("\n" + "#" * 78)
    print("  [PHASE 1] Executing Lab 18.1: Comparative System & 4-Query Benchmarking")
    print("#" * 78)
    results = run_lab18_1_complete()
    benchmarks = results["benchmarks"]
    fp_communities = results["fp_communities"]

    # 3. Phase 2: Lab 18.2 Markdown Report
    print("\n" + "#" * 78)
    print("  [PHASE 2] Executing Lab 18.2: Synthesizing Comparative Analysis Report")
    print("#" * 78)
    report_md = generate_markdown_report(benchmarks, fp_communities)
    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, "comparative_analysis_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"  [OK] Generated Markdown Report: {report_path}")

    # 4. Phase 3: PDF Generation
    print("\n" + "#" * 78)
    print("  [PHASE 3] Compiling Publication-Grade Academic PDF Report (ReportLab)")
    print("#" * 78)
    primary_pdf = "exercise 18 nosql.pdf"
    alt_pdf = "exercise_18_nosql.pdf"
    alt_pdf2 = "Lab18_Comparative_Analysis_Report.pdf"
    build_pdf_report(primary_pdf)
    shutil.copyfile(primary_pdf, alt_pdf)
    shutil.copyfile(primary_pdf, alt_pdf2)
    print(f"  [OK] Compiled: {primary_pdf}")

    elapsed = time.perf_counter() - start_total
    print("\n" + "#" * 78)
    print("  CHAPTER 18 MASTER DEMONSTRATION COMPLETE")
    print(f"  Total Demonstration Execution Time: {elapsed:.2f} seconds")
    print("  Generated Artifacts:")
    print("    - exercise 18 nosql.pdf (Academic PDF Submission)")
    print("    - reports/comparative_analysis_report.md (Technical Markdown Report)")
    print("    - MongoDB Collections: 'threat' (embedded last 50) and 'full_threats' (100k docs)")
    print("    - Cassandra Tables: 'threats_by_source' and 'threats_by_type'")
    print("    - Neo4j Graph: Nodes, Relationships, and False-Positive Communities")
    print("  Docker Run Command:")
    print("    docker run --rm -it shashankreddy30/mongodb-lab18:latest demo")
    print("#" * 78 + "\n")


if __name__ == "__main__":
    main()
