"""
ingest_threat_intelligence.py
Appendix A-compatible document ingestion script.
Pushes multi-platform Threat Intelligence bulletins and mitigation playbooks
into the FastAPI backend (/ingest endpoint).
"""

import os
import sys
import requests
from data.threat_dataset import THREAT_DATASET

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

def main():
    print("=" * 70)
    print("  Appendix A: Ingest Threat Intelligence Corpus into RAG Pipeline")
    print("=" * 70)

    # Format documents for ingestion
    documents = []
    for t in THREAT_DATASET:
        content = (
            f"Threat Bulletin {t['threat_id']}: {t['title']}.\n"
            f"Platform: {t['platform']}. Lifecycle Status: {t['lifecycle_status']}. Severity: {t['severity']}.\n"
            f"Associated CVEs: {', '.join(t['cve_ids'])}. CVSS: {t['cvss_score']}, EPSS: {t['epss_score']}.\n"
            f"MITRE Tactics: {', '.join(t['mitre_tactics'])}. Techniques: {', '.join(t['mitre_techniques'])}.\n"
            f"Technical Description: {t['description']}\n"
            f"In-Depth Analysis: {t['technical_analysis']}\n"
            f"Mitigation Procedure: {t['mitigation_procedure']['summary']}\n"
            f"Step-by-step mitigation commands: {' | '.join(t['mitigation_procedure']['steps'])}\n"
            f"Verification: {t['mitigation_procedure']['verification_command']}\n"
            f"Rollback: {t['mitigation_procedure']['rollback_plan']}"
        )
        documents.append({
            "title": f"[{t['platform']}] {t['title']}",
            "content": content,
            "platform": t["platform"],
            "lifecycle_status": t["lifecycle_status"]
        })

    print(f"Submitting {len(documents)} threat intelligence documents to {BACKEND_URL}/ingest...")
    try:
        res = requests.post(
            f"{BACKEND_URL}/ingest",
            json={"documents": documents, "chunk_size": 100},
            timeout=30
        )
        res.raise_for_status()
        data = res.json()
        print(f"[OK] {data['message']}")
    except requests.exceptions.ConnectionError:
        print(f"[WARNING] Backend not currently reachable at {BACKEND_URL}.")
        print("Seeding database directly via local threat_service...")
        from app.threat_service import init_threat_database
        init_threat_database()
        print("[OK] Direct database seeding complete.")
    except Exception as e:
        print(f"[ERROR] Ingest failed: {e}")

    print("=" * 70)
    print("  Ingestion Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
