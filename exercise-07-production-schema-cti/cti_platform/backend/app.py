"""
Cyber Threat Intelligence (CTI) Platform - Full Stack Backend
Consolidating Lab 7.1 (Schema Design, $bsonSize, Embedded vs Referenced)
and Lab 7.2 (Working Set, WiredTiger Cache, Random Reads, 10s Real-time Monitoring).
"""

import os
import time
import json
import random
import threading
import datetime
from flask import Flask, jsonify, request, send_from_directory
from bson import json_util, ObjectId
import bson

from database import db_manager
from seed_data import seed_database
from indexing_scripts import setup_indexes
import lab7_1_analysis
import lab7_2_working_set
import monitor_wiredtiger_threats
import chatbot_engine

app = Flask(__name__, static_folder="../frontend", static_url_path="")

# Ensure seed data and indexes on startup
db = db_manager.get_db()
if db.threat_reports.count_documents({}) == 0:
    seed_database()
setup_indexes()

# Background monitoring thread state
monitoring_state = {
    "is_active": True,
    "last_check": None,
    "history": [],
    "recent_discoveries": []
}

def background_monitor_worker():
    """Background worker that runs the 10-second monitoring cycle."""
    while True:
        if monitoring_state["is_active"]:
            try:
                # 1. Crawl for new threats
                new_threats = monitor_wiredtiger_threats.check_for_new_threat_reports()
                if new_threats:
                    db.threat_reports.insert_many(new_threats)
                    for t in new_threats:
                        doc_size = db_manager.calculate_bson_size(t)
                        db_manager.cache_sim.register_document(str(t.get("_id", t["threat_id"])), doc_size, is_new=True)
                        monitoring_state["recent_discoveries"].insert(0, {
                            "title": t["title"],
                            "threat_type": t["threat_type"],
                            "severity": t["severity"],
                            "discovered_at": datetime.datetime.now().strftime("%H:%M:%S")
                        })
                    monitoring_state["recent_discoveries"] = monitoring_state["recent_discoveries"][:10]

                # 2. Get serverStatus
                status = db_manager.get_server_status()
                wt_cache = status.get("wiredTiger", {}).get("cache", {})
                
                entry = {
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                    "hit_ratio": wt_cache.get("calculated cache hit ratio", 100.0),
                    "bytes_in_cache_mb": round(wt_cache.get("bytes currently in the cache", 0) / (1024*1024), 2),
                    "dirty_bytes_mb": round(wt_cache.get("tracked dirty bytes in the cache", 0) / (1024*1024), 2),
                    "pages_requested": wt_cache.get("pages requested from the cache", 0),
                    "pages_read": wt_cache.get("pages read into cache", 0),
                    "total_threats": db.threat_reports.count_documents({})
                }
                monitoring_state["history"].append(entry)
                monitoring_state["history"] = monitoring_state["history"][-30:] # Keep last 30 samples (5 minutes)
                monitoring_state["last_check"] = entry
            except Exception as e:
                print(f"[BackgroundMonitor] Error: {e}")

        time.sleep(10)

# Launch monitoring background daemon thread
monitor_thread = threading.Thread(target=background_monitor_worker, daemon=True)
monitor_thread.start()


# --------------------------------------------------------------------------
# FRONTEND STATIC ROUTES
# --------------------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")

@app.route("/<path:path>")
def static_proxy(path):
    return send_from_directory("../frontend", path)


# --------------------------------------------------------------------------
# CTI PLATFORM: THREAT INTELLIGENCE & CLASSIFICATION APIS
# --------------------------------------------------------------------------
@app.route("/api/threats", methods=["GET"])
def get_threats():
    """
    Search and filter cyber threats.
    Supports: q (keyword search), threat_type, severity, source_id, verdict.
    """
    q = request.args.get("q", "").strip()
    threat_type = request.args.get("threat_type")
    severity = request.args.get("severity")
    source_id = request.args.get("source_id")
    verdict = request.args.get("verdict")
    limit = int(request.args.get("limit", 50))

    query = {}
    if q:
        query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"tags": {"$regex": q, "$options": "i"}},
            {"indicators.value": {"$regex": q, "$options": "i"}},
            {"threat_id": {"$regex": q, "$options": "i"}},
            {"cve_ids": {"$regex": q, "$options": "i"}}
        ]
    if threat_type:
        query["threat_type"] = threat_type
    if severity:
        query["severity"] = severity
    if source_id:
        query["source_id"] = source_id
    if verdict:
        query["classification.verdict"] = verdict

    docs = list(db.threat_reports.find(query).limit(limit))
    
    # Calculate BSON size for each returned document
    for d in docs:
        d["bson_size_bytes"] = db_manager.calculate_bson_size(d)
        d["_id"] = str(d["_id"])

    return jsonify({
        "status": "success",
        "count": len(docs),
        "total_in_db": db.threat_reports.count_documents({}),
        "threats": docs
    })


@app.route("/api/threats/<threat_id>/classify", methods=["POST", "PUT"])
def classify_threat(threat_id):
    """
    Classify a threat: Update analyst verdict (Actual Threat vs Benign),
    severity, risk score, and MITRE techniques.
    """
    data = request.json or {}
    verdict = data.get("verdict", "Actual Threat")
    severity = data.get("severity")
    status = data.get("status", "Verified Active Threat" if verdict == "Actual Threat" else "Benign / False Positive")
    mitre_techniques = data.get("mitre_techniques", [])

    update_fields = {
        "classification.verdict": verdict,
        "classification.status": status,
        "classification.last_reviewed_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }
    if severity:
        update_fields["severity"] = severity
    if mitre_techniques:
        update_fields["classification.mitre_techniques"] = mitre_techniques

    res = db.threat_reports.update_one(
        {"$or": [{"threat_id": threat_id}, {"_id": ObjectId(threat_id) if ObjectId.is_valid(threat_id) else None}]},
        {"$set": update_fields}
    )

    return jsonify({
        "status": "success",
        "modified_count": res.modified_count,
        "message": f"Threat {threat_id} successfully classified as '{verdict}'"
    })


@app.route("/api/sources", methods=["GET"])
def get_sources():
    """Returns list of intelligence sources with threat counts and threat status."""
    sources = list(db.sources.find())
    for s in sources:
        s["_id"] = str(s["_id"])
        s["threats_count"] = db.threat_reports.count_documents({"source_id": s["source_id"]})
        # Check actual threat count from this source
        s["actual_threats_count"] = db.threat_reports.count_documents({
            "source_id": s["source_id"],
            "classification.verdict": "Actual Threat"
        })
    return jsonify({"status": "success", "sources": sources})


@app.route("/api/sources/<source_id>/verdict", methods=["POST"])
def toggle_source_verdict(source_id):
    """
    Activity 7.1: Decide whether a source is an Actual Threat vector or Benign feed.
    """
    data = request.json or {}
    is_threat = bool(data.get("is_verified_threat", True))
    
    db.sources.update_one(
        {"source_id": source_id},
        {"$set": {
            "is_verified_threat": is_threat,
            "is_attacker_source": is_threat,
            "classification": "Direct Threat Origin" if is_threat else "Trusted Intelligence Feed"
        }}
    )
    # Also update embedded redesign collection
    db.sources_embedded_threats.update_one(
        {"source_id": source_id},
        {"$set": {"is_actual_threat_source": is_threat}}
    )

    return jsonify({
        "status": "success",
        "source_id": source_id,
        "is_verified_threat": is_threat,
        "message": f"Source {source_id} verdict updated to: {'ACTUAL THREAT' if is_threat else 'BENIGN FEED'}"
    })


@app.route("/api/overview-stats", methods=["GET"])
def get_overview_stats():
    """Returns aggregated high-level statistics."""
    total_threats = db.threat_reports.count_documents({})
    critical_threats = db.threat_reports.count_documents({"severity": "Critical"})
    actual_threats = db.threat_reports.count_documents({"classification.verdict": "Actual Threat"})
    total_sources = db.sources.count_documents({})
    malicious_sources = db.sources.count_documents({"is_verified_threat": True})
    
    return jsonify({
        "total_threats": total_threats,
        "critical_threats": critical_threats,
        "actual_threats": actual_threats,
        "benign_or_fp": total_threats - actual_threats,
        "total_sources": total_sources,
        "malicious_sources": malicious_sources
    })


# --------------------------------------------------------------------------
# LAB 7.1 APIS: SCHEMA ANALYSIS, $bsonSize, & EMBEDDED REDESIGN
# --------------------------------------------------------------------------
@app.route("/api/lab71/schema-analysis", methods=["GET"])
def get_schema_analysis():
    """Returns detailed schema analysis identifying embedding vs referencing."""
    return jsonify({
        "status": "success",
        "platform_url": "https://ctidigest.com/",
        "relationships": [
            {
                "relationship": "ThreatReport -> Indicators of Compromise (IOCs)",
                "pattern": "EMBEDDING (1-to-Few)",
                "fields": "threat_reports.indicators",
                "is_embedded": True,
                "why_used": "IOCs (IPs, hashes, domains) are tightly coupled to the specific threat incident. They are always queried and displayed together during threat hunting. No document size risk because a report rarely has more than 50 IOCs."
            },
            {
                "relationship": "ThreatReport -> Classification & MITRE Tactics",
                "pattern": "EMBEDDING (1-to-One Subdocument)",
                "fields": "threat_reports.classification",
                "is_embedded": True,
                "why_used": "Classification verdicts (Actual Threat vs Benign) and MITRE tactics are intrinsic attributes of the report document. Embedded subdocuments provide atomic updates and zero join overhead."
            },
            {
                "relationship": "ThreatReport -> Intelligence Feed / Source",
                "pattern": "REFERENCING (N-to-1)",
                "fields": "threat_reports.source_id -> sources.source_id",
                "is_embedded": False,
                "why_referencing": "A single source (e.g. CISA or Mandiant) produces thousands of alerts over months. Embedding all alerts into the source would rapidly breach MongoDB's 16 MB document limit. Sources also have independent update cycles (reputation, URL changes).",
                "embedded_alternative": {
                    "source_id": "SRC-001",
                    "name": "CISA AIS",
                    "threat_reports": [
                        {"threat_id": "CTI-2026-1001", "title": "LockBit 4.0...", "severity": "Critical"},
                        {"threat_id": "CTI-2026-1002", "title": "Volt Typhoon...", "severity": "High"}
                    ]
                }
            },
            {
                "relationship": "ThreatReport -> Threat Actor (APT)",
                "pattern": "REFERENCING (N-to-1 / M-to-N)",
                "fields": "threat_reports.actor_id -> threat_actors.actor_id",
                "is_embedded": False,
                "why_referencing": "APTs (e.g. APT29, Lazarus) are long-lived entities responsible for hundreds of campaigns across multiple years. Storing them independently avoids massive duplicate copies of actor profiles across every incident alert.",
                "embedded_alternative": {
                    "threat_id": "CTI-2026-1001",
                    "actor_profile": {
                        "name": "APT29 (Cozy Bear)",
                        "origin": "Russian Federation",
                        "motivation": "Cyber Espionage"
                    }
                }
            },
            {
                "relationship": "ThreatReport -> CVE Vulnerabilities",
                "pattern": "REFERENCING (M-to-N)",
                "fields": "threat_reports.cve_ids -> cves.cve_id",
                "is_embedded": False,
                "why_referencing": "CVEs are industry-standard dictionary records with EPSS and CVSS metrics updated dynamically by NVD. Referencing prevents stale vulnerability scores.",
                "embedded_alternative": {
                    "threat_id": "CTI-2026-1001",
                    "cve_records": [
                        {"cve_id": "CVE-2026-3021", "cvss": 9.8, "epss": 0.89}
                    ]
                }
            }
        ]
    })


@app.route("/api/lab71/bson-size", methods=["GET"])
def get_bson_size_analysis():
    """
    Calculates document sizes using $bsonSize logic and verifies 16 MB limit safety.
    """
    docs = list(db.threat_reports.find())
    sizes = [db_manager.calculate_bson_size(d) for d in docs]
    
    limit_bytes = 16 * 1024 * 1024  # 16 MB
    if sizes:
        avg_size = sum(sizes) / len(sizes)
        min_size = min(sizes)
        max_size = max(sizes)
    else:
        avg_size = min_size = max_size = 0

    pct_of_limit = (max_size / limit_bytes) * 100.0 if limit_bytes > 0 else 0
    headroom = limit_bytes - max_size

    # Distribution histogram
    distribution = {
        "< 1 KB": sum(1 for s in sizes if s < 1024),
        "1 KB - 2 KB": sum(1 for s in sizes if 1024 <= s < 2048),
        "2 KB - 5 KB": sum(1 for s in sizes if 2048 <= s < 5120),
        "> 5 KB": sum(1 for s in sizes if s >= 5120)
    }

    return jsonify({
        "status": "success",
        "total_documents": len(sizes),
        "avg_document_size_bytes": round(avg_size, 2),
        "avg_document_size_kb": round(avg_size / 1024, 2),
        "min_document_size_bytes": min_size,
        "max_document_size_bytes": max_size,
        "max_document_size_kb": round(max_size / 1024, 2),
        "mongodb_16mb_limit_bytes": limit_bytes,
        "max_pct_of_limit": round(pct_of_limit, 5),
        "headroom_bytes_remaining": headroom,
        "headroom_mb_remaining": round(headroom / (1024*1024), 2),
        "is_safe_from_16mb_limit": max_size < limit_bytes,
        "size_distribution": distribution
    })


@app.route("/api/lab71/redesign-benchmark", methods=["GET"])
def get_redesign_benchmark():
    """
    Activity 7.1: Try It Yourself Benchmark.
    Compares Referencing ($lookup) vs Embedded design for deciding which source is an actual threat.
    """
    # 1. Referenced Design ($lookup)
    t0 = time.perf_counter()
    for _ in range(15):
        _ = list(db.sources.aggregate([
            {
                "$lookup": {
                    "from": "threat_reports",
                    "localField": "source_id",
                    "foreignField": "source_id",
                    "as": "reports"
                }
            },
            {
                "$project": {
                    "name": 1,
                    "reliability_score": 1,
                    "is_verified_threat": 1,
                    "actual_threats": {
                        "$filter": {
                            "input": "$reports",
                            "as": "r",
                            "cond": {"$eq": ["$$r.classification.verdict", "Actual Threat"]}
                        }
                    }
                }
            }
        ]))
    t_ref_ms = (time.perf_counter() - t0) * 1000.0 / 15.0

    # 2. Embedded Design (Single Seek)
    t0 = time.perf_counter()
    for _ in range(15):
        _ = list(db.sources_embedded_threats.find(
            {},
            {"name": 1, "is_actual_threat_source": 1, "threat_summary": 1}
        ))
    t_emb_ms = (time.perf_counter() - t0) * 1000.0 / 15.0

    speedup = round(t_ref_ms / t_emb_ms, 2) if t_emb_ms > 0 else 1.0

    return jsonify({
        "status": "success",
        "scenario": "Deciding which intelligence source represents an actual threat",
        "referenced_design_time_ms": round(t_ref_ms, 3),
        "embedded_design_time_ms": round(t_emb_ms, 3),
        "speedup_factor": speedup,
        "what_becomes_faster": [
            "Source Threat Verdicts: Instant O(1) single-document retrieval without pipeline joins.",
            "Complete Dossier Fetch: Getting the source and all its associated threat payloads in a single disk seek.",
            "Atomic Updates: Flipping a source's threat verdict updates metadata and payload status in one write."
        ],
        "what_becomes_harder": [
            "Document Size Bloat: As an adversary source issues hundreds of payloads, the source document risks breaching the 16 MB limit.",
            "Update Contention: Multiple background ingestion crawlers attempting to append threats to the same source document cause write locking.",
            "Cross-Source Analysis: Correlating an IP indicator across multiple sources requires unrolling deeply nested subdocuments ($unwind)."
        ]
    })


# --------------------------------------------------------------------------
# LAB 7.2 APIS: WORKING SET ANALYSIS & WIREDTIGER METRICS
# --------------------------------------------------------------------------
@app.route("/api/lab72/working-set", methods=["GET"])
def get_working_set_analysis():
    """Calculates dataset size, working set size, and WiredTiger cache fit."""
    db = db_manager.get_db()
    total_docs = db.working_set_reports.count_documents({})
    
    # Calculate sample size
    sample = db.working_set_reports.find_one()
    sample_size = db_manager.calculate_bson_size(sample) if sample else 2048
    
    total_data_size_bytes = total_docs * sample_size
    index_size_bytes = int(total_data_size_bytes * 0.15) # Standard index overhead ~15%
    working_set_bytes = total_data_size_bytes + index_size_bytes

    status = db_manager.get_server_status()
    wt_cache = status.get("wiredTiger", {}).get("cache", {})
    max_cache_bytes = wt_cache.get("maximum bytes configured", 512 * 1024 * 1024)
    cache_fit_pct = (max_cache_bytes / working_set_bytes * 100.0) if working_set_bytes > 0 else 100.0

    return jsonify({
        "total_documents": total_docs,
        "sample_doc_size_bytes": sample_size,
        "total_data_size_mb": round(total_data_size_bytes / (1024*1024), 2),
        "index_overhead_mb": round(index_size_bytes / (1024*1024), 2),
        "total_working_set_mb": round(working_set_bytes / (1024*1024), 2),
        "wiredtiger_cache_mb": round(max_cache_bytes / (1024*1024), 2),
        "cache_fit_percentage": round(min(100.0, cache_fit_pct), 2),
        "cache_status": "Cache Fit - Entire working set resides in RAM" if cache_fit_pct >= 100 else "Cache Pressure - Working set exceeds RAM, disk I/O required"
    })


@app.route("/api/lab72/insert-100k", methods=["POST"])
def trigger_insert_100k():
    """
    Inserts 100,000 documents (~2 KB each) based on awesome-annual-security-reports.
    Fast batch insertion.
    """
    target = int(request.json.get("count", 100000)) if request.json else 100000
    # In web request, if target is large, do quick generate or batch
    count, size = lab7_2_working_set.insert_100k_documents(total_docs=target, batch_size=5000)
    return jsonify({
        "status": "success",
        "documents_inserted": count,
        "average_doc_size_bytes": size,
        "total_size_mb": round((count * size) / (1024*1024), 2)
    })


@app.route("/api/lab72/server-status", methods=["GET"])
def get_server_status():
    """Returns raw WiredTiger server status metrics."""
    status = db_manager.get_server_status()
    return jsonify(status)


@app.route("/api/lab72/random-reads", methods=["POST"])
def trigger_random_reads():
    """
    Runs random reads across the collection and returns cache hit ratio timeline.
    """
    cycles = int(request.json.get("cycles", 2000)) if request.json else 2000
    timeline = lab7_2_working_set.run_random_reads_workload(read_cycles=cycles)
    return jsonify({
        "status": "success",
        "cycles_executed": cycles,
        "timeline": timeline
    })


@app.route("/api/lab72/monitoring-stream", methods=["GET"])
def get_monitoring_stream():
    """Returns real-time 10-second monitoring timeline and crawler discoveries."""
    return jsonify({
        "status": "success",
        "is_active": monitoring_state["is_active"],
        "last_check": monitoring_state["last_check"],
        "history": monitoring_state["history"],
        "recent_discoveries": monitoring_state["recent_discoveries"]
    })


@app.route("/api/chat", methods=["POST"])
def chat():
    """Chatbot conversational endpoint for Sentinel AI Copilot."""
    data = request.json or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"status": "error", "message": "Empty message"}), 400

    response = chatbot_engine.process_chat_message(message)
    return jsonify({
        "status": "success",
        "reply": response.get("reply", ""),
        "suggested_actions": response.get("suggested_actions", [])
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n==================================================================")
    print(f" CYBER THREAT INTELLIGENCE (CTI) PLATFORM - LAB 7.1 & 7.2 READY")
    print(f" Access Platform in Browser: http://localhost:{port}")
    print(f"==================================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
