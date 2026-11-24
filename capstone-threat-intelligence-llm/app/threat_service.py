"""
app/threat_service.py
Core Threat Intelligence service managing MongoDB persistence, RAG vector retrieval,
platform-specific queries, and lifecycle transitions.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from app.database import get_db
from app.vector_engine import generate_semantic_embedding, cosine_similarity, chunk_text
from data.threat_dataset import THREAT_DATASET

def init_threat_database():
    """Seed MongoDB with curated threat intelligence dataset and compute initial vector chunks."""
    db = get_db()
    threats_col = db["threats"]
    chunks_col = db["threat_chunks"]

    if threats_col.count_documents({}) == 0:
        threats_col.insert_many(THREAT_DATASET)
        print(f"[OK] Seeded {len(THREAT_DATASET)} master threat intelligence records.")

    # Populate vector search chunks if empty
    if chunks_col.count_documents({}) == 0:
        chunks = []
        for threat in threats_col.find():
            content = (
                f"Threat ID: {threat['threat_id']}. Title: {threat['title']}. "
                f"Platform: {threat['platform']}. Lifecycle Status: {threat['lifecycle_status']}. "
                f"Severity: {threat['severity']} (CVSS {threat['cvss_score']}). "
                f"CVEs: {', '.join(threat['cve_ids'])}. "
                f"Description: {threat['description']}. "
                f"Technical Analysis: {threat['technical_analysis']}. "
                f"Mitigation Summary: {threat['mitigation_procedure']['summary']}. "
                f"Mitigation Steps: {' | '.join(threat['mitigation_procedure']['steps'])}. "
                f"Verification: {threat['mitigation_procedure']['verification_command']}."
            )
            raw_chunks = chunk_text(content, chunk_size=120, overlap=20)
            for idx, c in enumerate(raw_chunks):
                emb = generate_semantic_embedding(c)
                chunks.append({
                    "threat_id": threat["threat_id"],
                    "platform": threat["platform"],
                    "lifecycle_status": threat["lifecycle_status"],
                    "severity": threat["severity"],
                    "title": threat["title"],
                    "chunk_index": idx,
                    "text": c,
                    "embedding": emb,
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
        if chunks:
            chunks_col.insert_many(chunks)
            print(f"[OK] Created and indexed {len(chunks)} vector search embeddings.")

def get_threats(platform: Optional[str] = None, lifecycle_status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve threats matching optional filter criteria."""
    db = get_db()
    query = {}
    if platform and platform.lower() != "all":
        query["platform"] = {"$regex": f"^{platform}$", "$options": "i"}
    if lifecycle_status and lifecycle_status.lower() != "all":
        query["lifecycle_status"] = {"$regex": f"^{lifecycle_status}$", "$options": "i"}
    if severity and severity.lower() != "all":
        query["severity"] = {"$regex": f"^{severity}$", "$options": "i"}

    docs = list(db["threats"].find(query, {"_id": 0}))
    return docs

def retrieve_threat_context(query_str: str, top_k: int = 3, platform_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Semantic vector search against threat_chunks."""
    db = get_db()
    chunks_col = db["threat_chunks"]
    query_emb = generate_semantic_embedding(query_str)

    filter_dict = {}
    if platform_filter and platform_filter.lower() != "all":
        filter_dict["platform"] = {"$regex": f"^{platform_filter}$", "$options": "i"}

    candidates = list(chunks_col.find(filter_dict, {"_id": 0}))
    if not candidates:
        # Fallback without platform filter if no results
        candidates = list(chunks_col.find({}, {"_id": 0}))

    scored = []
    for cand in candidates:
        score = cosine_similarity(query_emb, cand["embedding"])
        scored.append((score, cand))

    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, item in scored[:top_k]:
        results.append({
            "score": round(score, 4),
            "threat_id": item["threat_id"],
            "title": item["title"],
            "platform": item["platform"],
            "lifecycle_status": item["lifecycle_status"],
            "text": item["text"]
        })
    return results

def get_platform_threat_summary() -> Dict[str, Any]:
    """Aggregate threat metrics across platforms and lifecycle states."""
    db = get_db()
    threats = list(db["threats"].find({}, {"_id": 0}))
    summary = {
        "total_threats": len(threats),
        "by_platform": {},
        "by_lifecycle": {
            "Anticipated": 0,
            "Active": 0,
            "Evolving": 0,
            "Resolved": 0
        },
        "by_severity": {
            "Critical": 0,
            "High": 0,
            "Medium": 0,
            "Low": 0
        }
    }
    for t in threats:
        p = t.get("platform", "Unknown")
        summary["by_platform"][p] = summary["by_platform"].get(p, 0) + 1
        st = t.get("lifecycle_status", "Active")
        if st in summary["by_lifecycle"]:
            summary["by_lifecycle"][st] += 1
        sev = t.get("severity", "Medium")
        if sev in summary["by_severity"]:
            summary["by_severity"][sev] += 1
    return summary
