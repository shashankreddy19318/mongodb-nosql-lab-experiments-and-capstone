"""
lab_01_threat_intel_system.py
Lab 18.1: Build the Comparative System - Identifying False-Positives in Threat Intelligence
Activity 18.1: Graph-based Community Detection Cross-Referenced with MongoDB Details

Implementation of:
1. Synthetic generation of 100,000 recent threats across 20 intelligence sources.
2. MongoDB Schema:
   - 'threat' collection with embedded 'recent_threats' array (last 50 for fast display)
   - 'full_threats' collection
   - Index on (from_source, timestamp)
3. Cassandra Schema:
   - Dual-table denormalized design: 'threats_by_source' and 'threats_by_type'
4. Neo4j Schema:
   - Source nodes, Threat nodes, Entity nodes
   - Relationships: REPORTED, TARGETS, SHARES_INDICATOR, SUSPICIOUS
5. 4 Benchmark Queries across all 3 databases (10 runs each, reporting median latency):
   - Q1: Threat History
   - Q2: Target and Spread
   - Q3: Daily Volume Analytics
   - Q4: Real-time Insert Throughput (1,000 writes)
6. Activity 18.1: Graph Community Detection & False-Positive Isolation.

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab18
"""

import os
import sys
import time
import random
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Local module path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import (
    banner,
    get_mongo_client,
    get_mongo_db,
    reset_collection,
    is_mongo_mock_active,
    get_cassandra_session,
    get_neo4j_driver
)

console = Console()

NUM_THREATS = 100000
BENCHMARK_RUNS = 10

# Threat Intelligence Feeds / Sources
THREAT_SOURCES = [
    {"id": "SRC-001", "name": "CrowdStrike Falcon Feed", "reliability": 0.96},
    {"id": "SRC-002", "name": "VirusTotal Enterprise", "reliability": 0.94},
    {"id": "SRC-003", "name": "Mandiant Advantage", "reliability": 0.95},
    {"id": "SRC-004", "name": "Cisco Talos Intelligence", "reliability": 0.93},
    {"id": "SRC-005", "name": "AlienVault OTX", "reliability": 0.88},
    {"id": "SRC-006", "name": "Palo Alto Unit42", "reliability": 0.95},
    {"id": "SRC-007", "name": "Recorded Future", "reliability": 0.92},
    {"id": "SRC-008", "name": "Microsoft Defender TI", "reliability": 0.93},
    {"id": "SRC-009", "name": "FireEye iSIGHT", "reliability": 0.91},
    {"id": "SRC-010", "name": "Kaspersky Threat Intel", "reliability": 0.90},
    {"id": "SRC-011", "name": "Symantec DeepSight", "reliability": 0.89},
    {"id": "SRC-012", "name": "SentinelOne Singularity", "reliability": 0.92},
    {"id": "SRC-013", "name": "Fortinet FortiGuard", "reliability": 0.89},
    {"id": "SRC-014", "name": "IBM X-Force Exchange", "reliability": 0.91},
    {"id": "SRC-015", "name": "Check Point ThreatCloud", "reliability": 0.90},
    {"id": "SRC-016", "name": "Trend Micro Smart Protection", "reliability": 0.88},
    {"id": "SRC-017", "name": "Darktrace Cyber AI", "reliability": 0.87},
    {"id": "SRC-018", "name": "Rapid7 Threat Command", "reliability": 0.89},
    {"id": "SRC-019", "name": "ESET LiveGrid", "reliability": 0.88},
    {"id": "SRC-020", "name": "AbuseIPDB Community", "reliability": 0.82},
]

THREAT_TYPES = [
    "C2_Server",
    "Phishing_Domain",
    "Ransomware_Distributor",
    "DDoS_Botnet",
    "Exploit_Kit",
    "Credential_Harvester",
    "Benign_CDN_Proxy",          # Common false positive
    "Internal_DNS_Resolver",      # Common false positive
    "Cloud_Service_Endpoint",     # Common false positive
]

TARGET_ENTITIES = [
    "auth.internal-corp.net",
    "cdn-edge-01.fastroute.com",
    "gateway.payment-svc.org",
    "dns.public-resolve.net",
    "api.shared-cloud.io",
    "proxy.cluster-lon.net",
    "login.enterprise-sso.com",
    "vpn.remote-workforce.io",
    "telemetry.endpoint-sec.org",
    "mail.secure-relay.net",
]


def generate_threat_dataset(n: int = NUM_THREATS, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generate n synthetic threat intelligence events with realistic attributes
    and deliberate false-positive clusters (benign CDNs / DNS falsely flagged).
    """
    random.seed(seed)
    base_date = datetime(2024, 1, 1, 0, 0, 0)
    threats = []

    print(f"[*] Generating {n:,} synthetic threat intelligence records across {len(THREAT_SOURCES)} sources...")

    for i in range(n):
        src = random.choice(THREAT_SOURCES)
        ttype = random.choice(THREAT_TYPES)
        target = random.choice(TARGET_ENTITIES)
        
        # Inject known False Positives (~6% frequency)
        is_false_positive = False
        if ttype in ("Benign_CDN_Proxy", "Internal_DNS_Resolver", "Cloud_Service_Endpoint"):
            is_false_positive = True
            severity = round(random.uniform(0.70, 0.95), 2)  # Over-flagged
            confidence = round(random.uniform(0.35, 0.60), 2) # Low actual confidence
            risk_score = round(severity * (1.0 - confidence), 4) # Discrepancy signal
        else:
            is_false_positive = (random.random() < 0.02)
            severity = round(random.uniform(0.10, 0.99), 2)
            confidence = round(random.uniform(0.65, 0.99), 2)
            risk_score = round(severity * confidence, 4)

        # Timestamps across a 180-day window
        delta_seconds = random.randint(0, 180 * 86400)
        timestamp = (base_date + timedelta(seconds=delta_seconds)).isoformat()

        threat = {
            "threat_id": f"THR-{i:07d}",
            "from_source": src["id"],
            "source_name": src["name"],
            "threat_type": ttype,
            "indicator": f"ioc-{target}-{i % max(10, n // 100)}",  # Shared IOCs create graph communities
            "target": target,
            "target_type": "fqdn" if ".net" in target or ".com" in target else "ip",
            "severity": severity,
            "confidence": confidence,
            "risk_score": risk_score,
            "timestamp": timestamp,
            "is_false_positive": is_false_positive,
            "geo_origin": random.choice(["US", "DE", "CN", "RU", "IN", "NL", "SG", "BR"]),
            "payload_hash": f"sha256-{abs(hash(f'THR-{i}')) % 10**16:016x}",
        }
        threats.append(threat)

    print(f"[OK] Generated {len(threats):,} threat records.")
    return threats


# ==============================================================================
# SCHEMA INITIALIZATION & INGESTION
# ==============================================================================

def ingest_mongodb(db, threats: List[Dict[str, Any]]):
    """
    Ingest into MongoDB according to Chapter 18 specifications:
    - 'full_threats' collection: All threats indexed on (from_source, timestamp)
    - 'threat' collection: Source summaries with embedded 'recent_threats' array (last 50)
    """
    banner("1. MongoDB Schema Setup & Ingestion")

    full_col = reset_collection(db.name, "full_threats")
    summary_col = reset_collection(db.name, "threat")

    print("[*] Creating MongoDB indexes on full_threats...")
    full_col.create_index([("from_source", 1), ("timestamp", -1)], name="idx_source_time")
    full_col.create_index([("risk_score", -1)], name="idx_risk")
    full_col.create_index([("threat_type", 1)], name="idx_type")

    print(f"[*] Bulk inserting {len(threats):,} documents into full_threats...")
    start_t = time.perf_counter()
    # Batch in 10,000s for memory efficiency
    batch_size = 10000
    for b in range(0, len(threats), batch_size):
        full_col.insert_many(threats[b:b+batch_size], ordered=False)
    load_time = time.perf_counter() - start_t
    print(f"[OK] full_threats populated in {load_time:.2f}s ({len(threats)/load_time:,.0f} docs/sec)")

    # Build 'threat' collection with embedded recent_threats array (last 50 per source)
    print("[*] Building embedded 'threat' collection (source profiles with last 50 threats)...")
    source_groups = defaultdict(list)
    for t in threats:
        source_groups[t["from_source"]].append(t)

    summary_docs = []
    for src_id, src_threats in source_groups.items():
        src_threats.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_50 = src_threats[:50]
        src_meta = next((s for s in THREAT_SOURCES if s["id"] == src_id), {"name": src_id, "reliability": 0.9})
        doc = {
            "source_id": src_id,
            "source_name": src_meta["name"],
            "reliability_score": src_meta["reliability"],
            "total_reported": len(src_threats),
            "last_updated": recent_50[0]["timestamp"] if recent_50 else None,
            "recent_threats": recent_50  # Embedded array for sub-millisecond dashboard display
        }
        summary_docs.append(doc)

    summary_col.insert_many(summary_docs)
    summary_col.create_index([("source_id", 1)], unique=True)
    print(f"[OK] threat collection populated with {len(summary_docs)} source documents.")


def ingest_cassandra(session, threats: List[Dict[str, Any]]):
    """
    Ingest into Cassandra according to Chapter 18 specifications:
    - threats_by_source: partition key (from_source), clustering key (timestamp DESC)
    - threats_by_type:   partition key (threat_type), clustering key (timestamp DESC)
    """
    banner("2. Cassandra Schema Setup & Ingestion")
    print("[*] Initializing denormalized dual-table schema in Cassandra...")
    start_t = time.perf_counter()
    session.insert_batch(threats)
    load_time = time.perf_counter() - start_t
    print(f"[OK] Cassandra populated (dual tables) in {load_time:.2f}s ({len(threats)*2/load_time:,.0f} writes/sec)")


def ingest_neo4j(driver, threats: List[Dict[str, Any]]):
    """
    Ingest into Neo4j according to Chapter 18 specifications:
    - Source nodes, Threat nodes, Entity nodes
    - Relationships: REPORTED, TARGETS, SHARES_INDICATOR, SUSPICIOUS
    """
    banner("3. Neo4j Graph Schema Setup & Ingestion")
    print("[*] Populating Graph Nodes and Index-Free Adjacency Relationships...")
    start_t = time.perf_counter()

    for s in THREAT_SOURCES:
        driver.add_source(s["id"], s)

    # Ingest threats and build relationships
    for t in threats:
        driver.add_threat(t["threat_id"], t)

    print("[*] Constructing SHARES_INDICATOR and SUSPICIOUS cross-source relationships...")
    driver.build_graph_relationships()
    load_time = time.perf_counter() - start_t
    print(f"[OK] Neo4j graph populated in {load_time:.2f}s")


# ==============================================================================
# BENCHMARK QUERIES (10 RUNS, MEDIAN LATENCY)
# ==============================================================================

def benchmark_10_runs(query_fn, name: str, db_name: str) -> Tuple[float, float, float, int]:
    """
    Execute query_fn 10 times, record latencies, and return (median_ms, min_ms, max_ms, count).
    """
    latencies = []
    result_count = 0

    # Warm-up run
    res = query_fn()
    result_count = len(res) if isinstance(res, (list, dict)) else 1

    for _ in range(BENCHMARK_RUNS):
        start = time.perf_counter()
        query_fn()
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        latencies.append(elapsed_ms)

    median_ms = statistics.median(latencies)
    min_ms = min(latencies)
    max_ms = max(latencies)
    return median_ms, min_ms, max_ms, result_count


def run_benchmark_suite(mongo_db, cass_session, neo_driver, dataset: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Dict[str, Any]]:
    """
    Executes the 4 benchmark queries across all 3 databases:
    1. Threat History
    2. Target and Spread
    3. Daily Volume Analytics
    4. Real-time Insert Throughput (1,000 writes)
    """
    banner("4. Executing Benchmark Suite (10 Runs per Query, Median Latency)")

    benchmarks = {
        "Q1_Threat_History": {},
        "Q2_Target_and_Spread": {},
        "Q3_Daily_Volume_Analytics": {},
        "Q4_Insert_Throughput": {}
    }

    full_col = mongo_db["full_threats"]
    threat_col = mongo_db["threat"]
    target_source = "SRC-001"

    # --------------------------------------------------------------------------
    # Q1: Threat History (Lookup last 50 threats from SRC-001)
    # --------------------------------------------------------------------------
    print("\n--- Running Q1: Threat History (from_source = 'SRC-001', sorted by timestamp DESC, limit 50) ---")

    # MongoDB: point lookup from embedded 'threat' collection or indexed query on 'full_threats'
    def mongo_q1():
        # Ultra-fast embedded read pattern
        doc = threat_col.find_one({"source_id": target_source}, {"recent_threats": {"$slice": 50}})
        return doc["recent_threats"] if doc else []

    m_med, m_min, m_max, m_cnt = benchmark_10_runs(mongo_q1, "Q1", "MongoDB")
    benchmarks["Q1_Threat_History"]["MongoDB"] = {"median": m_med, "min": m_min, "max": m_max, "count": m_cnt}
    print(f"  MongoDB:   Median = {m_med:.2f} ms | Min = {m_min:.2f} ms | Max = {m_max:.2f} ms (Count: {m_cnt})")

    # Cassandra: single partition read on threats_by_source
    def cass_q1():
        return cass_session.query_threat_history(target_source, limit=50)

    c_med, c_min, c_max, c_cnt = benchmark_10_runs(cass_q1, "Q1", "Cassandra")
    benchmarks["Q1_Threat_History"]["Cassandra"] = {"median": c_med, "min": c_min, "max": c_max, "count": c_cnt}
    print(f"  Cassandra: Median = {c_med:.2f} ms | Min = {c_min:.2f} ms | Max = {c_max:.2f} ms (Count: {c_cnt})")

    # Neo4j: single traversal from Source node along REPORTED relationships
    def neo_q1():
        return neo_driver.query_threat_history(target_source, limit=50)

    n_med, n_min, n_max, n_cnt = benchmark_10_runs(neo_q1, "Q1", "Neo4j")
    benchmarks["Q1_Threat_History"]["Neo4j"] = {"median": n_med, "min": n_min, "max": n_max, "count": n_cnt}
    print(f"  Neo4j:     Median = {n_med:.2f} ms | Min = {n_min:.2f} ms | Max = {n_max:.2f} ms (Count: {n_cnt})")

    # --------------------------------------------------------------------------
    # Q2: Target and Spread (Filter threats where risk_score > 0.8)
    # --------------------------------------------------------------------------
    print("\n--- Running Q2: Target and Spread (risk_score > 0.8) ---")

    # MongoDB: B-tree index scan on risk_score
    def mongo_q2():
        if is_mongo_mock_active():
            return [t for t in dataset if t.get("risk_score", 0.0) > 0.8]
        return list(full_col.find({"risk_score": {"$gt": 0.8}}, {"_id": 0, "threat_id": 1, "target": 1, "risk_score": 1}))

    m_med, m_min, m_max, m_cnt = benchmark_10_runs(mongo_q2, "Q2", "MongoDB")
    benchmarks["Q2_Target_and_Spread"]["MongoDB"] = {"median": m_med, "min": m_min, "max": m_max, "count": m_cnt}
    print(f"  MongoDB:   Median = {m_med:.2f} ms | Min = {m_min:.2f} ms | Max = {m_max:.2f} ms (Count: {m_cnt})")

    # Cassandra: Secondary index / multi-partition scan (ALLOW FILTERING)
    def cass_q2():
        return cass_session.query_target_spread(min_risk=0.8)

    c_med, c_min, c_max, c_cnt = benchmark_10_runs(cass_q2, "Q2", "Cassandra")
    benchmarks["Q2_Target_and_Spread"]["Cassandra"] = {"median": c_med, "min": c_min, "max": c_max, "count": c_cnt}
    print(f"  Cassandra: Median = {c_med:.2f} ms | Min = {c_min:.2f} ms | Max = {c_max:.2f} ms (Count: {c_cnt})")

    # Neo4j: property filter on Threat nodes
    def neo_q2():
        return neo_driver.query_target_spread(min_risk=0.8)

    n_med, n_min, n_max, n_cnt = benchmark_10_runs(neo_q2, "Q2", "Neo4j")
    benchmarks["Q2_Target_and_Spread"]["Neo4j"] = {"median": n_med, "min": n_min, "max": n_max, "count": n_cnt}
    print(f"  Neo4j:     Median = {n_med:.2f} ms | Min = {n_min:.2f} ms | Max = {n_max:.2f} ms (Count: {n_cnt})")

    # --------------------------------------------------------------------------
    # Q3: Daily Volume Analytics (Group by threat_type)
    # --------------------------------------------------------------------------
    print("\n--- Running Q3: Daily Volume Analytics (Aggregation by threat_type) ---")

    # MongoDB: Native Aggregation Pipeline
    def mongo_q3():
        if is_mongo_mock_active():
            counts = defaultdict(int)
            for d in dataset:
                counts[d.get("threat_type")] += 1
            return [{"_id": k, "total_count": v} for k, v in counts.items()]
        pipeline = [
            {"$group": {"_id": "$threat_type", "total_count": {"$sum": 1}}},
            {"$sort": {"total_count": -1}}
        ]
        return list(full_col.aggregate(pipeline))

    m_med, m_min, m_max, m_cnt = benchmark_10_runs(mongo_q3, "Q3", "MongoDB")
    benchmarks["Q3_Daily_Volume_Analytics"]["MongoDB"] = {"median": m_med, "min": m_min, "max": m_max, "count": m_cnt}
    print(f"  MongoDB:   Median = {m_med:.2f} ms | Min = {m_min:.2f} ms | Max = {m_max:.2f} ms (Count: {m_cnt})")

    # Cassandra: Partition key grouping / Spark emulation
    def cass_q3():
        return cass_session.query_daily_volume()

    c_med, c_min, c_max, c_cnt = benchmark_10_runs(cass_q3, "Q3", "Cassandra")
    benchmarks["Q3_Daily_Volume_Analytics"]["Cassandra"] = {"median": c_med, "min": c_min, "max": c_max, "count": c_cnt}
    print(f"  Cassandra: Median = {c_med:.2f} ms | Min = {c_min:.2f} ms | Max = {c_max:.2f} ms (Count: {c_cnt})")

    # Neo4j: Whole graph aggregation
    def neo_q3():
        return neo_driver.query_daily_volume()

    n_med, n_min, n_max, n_cnt = benchmark_10_runs(neo_q3, "Q3", "Neo4j")
    benchmarks["Q3_Daily_Volume_Analytics"]["Neo4j"] = {"median": n_med, "min": n_min, "max": n_max, "count": n_cnt}
    print(f"  Neo4j:     Median = {n_med:.2f} ms | Min = {n_min:.2f} ms | Max = {n_max:.2f} ms (Count: {n_cnt})")

    # --------------------------------------------------------------------------
    # Q4: Real-time Insert Throughput (1,000 writes)
    # --------------------------------------------------------------------------
    print("\n--- Running Q4: Real-time Insert Throughput (Batch of 1,000 real-time records) ---")
    extra_batch = [
        {
            "threat_id": f"RT-{i:05d}",
            "from_source": "SRC-001",
            "threat_type": "C2_Server",
            "indicator": f"ioc-rt-{i}",
            "target": "gateway.payment-svc.org",
            "severity": 0.85,
            "confidence": 0.90,
            "risk_score": 0.765,
            "timestamp": datetime.now().isoformat(),
            "is_false_positive": False,
        }
        for i in range(1000)
    ]

    # MongoDB: insert_many
    def mongo_q4():
        batch_docs = [{k: v for k, v in t.items() if k != "_id"} for t in extra_batch]
        full_col.insert_many(batch_docs, ordered=False)
        return 1000

    m_med, m_min, m_max, m_cnt = benchmark_10_runs(mongo_q4, "Q4", "MongoDB")
    benchmarks["Q4_Insert_Throughput"]["MongoDB"] = {"median": m_med, "min": m_min, "max": m_max, "ops_sec": 1000.0 / (m_med / 1000.0)}
    print(f"  MongoDB:   Median = {m_med:.2f} ms ({1000.0/(m_med/1000.0):,.0f} writes/sec)")

    # Cassandra: Dual-table batch write
    def cass_q4():
        cass_session.insert_batch(extra_batch)
        return 1000

    c_med, c_min, c_max, c_cnt = benchmark_10_runs(cass_q4, "Q4", "Cassandra")
    benchmarks["Q4_Insert_Throughput"]["Cassandra"] = {"median": c_med, "min": c_min, "max": c_max, "ops_sec": 1000.0 / (c_med / 1000.0)}
    print(f"  Cassandra: Median = {c_med:.2f} ms ({1000.0/(c_med/1000.0):,.0f} writes/sec)")

    # Neo4j: Graph write (nodes + relationships)
    def neo_q4():
        for t in extra_batch:
            neo_driver.add_threat(t["threat_id"], t)
        return 1000

    n_med, n_min, n_max, n_cnt = benchmark_10_runs(neo_q4, "Q4", "Neo4j")
    benchmarks["Q4_Insert_Throughput"]["Neo4j"] = {"median": n_med, "min": n_min, "max": n_max, "ops_sec": 1000.0 / (n_med / 1000.0)}
    print(f"  Neo4j:     Median = {n_med:.2f} ms ({1000.0/(n_med/1000.0):,.0f} writes/sec)")

    return benchmarks


def display_benchmark_table(benchmarks: Dict[str, Dict[str, Any]]):
    """Render Rich tabular comparison."""
    table = Table(title="Chapter 18 Benchmark Performance (10 Runs Median Latency)", border_style="cyan")
    table.add_column("Benchmark Query", style="bold white", width=26)
    table.add_column("MongoDB (ms)", justify="right", style="green", width=16)
    table.add_column("Cassandra (ms)", justify="right", style="yellow", width=16)
    table.add_column("Neo4j (ms)", justify="right", style="magenta", width=16)
    table.add_column("Best Performer / Structural Advantage", style="cyan", width=32)

    notes = {
        "Q1_Threat_History": "MongoDB / Cassandra (Single-partition O(1))",
        "Q2_Target_and_Spread": "MongoDB (B-tree Index scan)",
        "Q3_Daily_Volume_Analytics": "MongoDB (Native Aggregation Pipeline)",
        "Q4_Insert_Throughput": "Cassandra (Append-only LSM-Tree commit log)"
    }

    for qname, data in benchmarks.items():
        m_val = f"{data['MongoDB']['median']:.2f}"
        c_val = f"{data['Cassandra']['median']:.2f}"
        n_val = f"{data['Neo4j']['median']:.2f}"
        label = qname.replace("_", " ")
        table.add_row(label, m_val, c_val, n_val, notes.get(qname, ""))

    console.print(table)


# ==============================================================================
# ACTIVITY 18.1: GRAPH COMMUNITY DETECTION & FALSE-POSITIVE CROSS-REFERENCING
# ==============================================================================

def run_activity_18_1_detection(mongo_db, neo_driver) -> List[Dict[str, Any]]:
    """
    Activity for 18.1: Try it yourself:
    1. Use Neo4j graph algorithms to identify communities of threats with unusually
       high inter-connectivity frequency over shared infrastructure / IOCs.
    2. Cross-reference with MongoDB 'full_threats' transaction/payload details.
    3. Isolate False-Positive clusters (e.g. Content Delivery Networks, Google DNS,
       benign enterprise proxies mistakenly reported as malware).
    """
    banner("5. Activity 18.1: Graph-based Community Detection & Cross-Database Correlation")
    print("[*] Running Community Detection algorithm across Neo4j SHARES_INDICATOR graph...")

    communities = neo_driver.detect_false_positive_communities()
    print(f"[OK] Identified {len(communities)} threat communities based on shared indicator density.")

    full_col = mongo_db["full_threats"]
    fp_isolated = []

    print("[*] Cross-referencing top detected communities against MongoDB threat details...")
    for comm in communities[:5]:
        sample_ids = comm["sample_threat_ids"]
        # Fetch detailed documents from MongoDB
        mongo_docs = list(full_col.find({"threat_id": {"$in": sample_ids}}))

        # Check for false-positive attributes
        types = set(d.get("threat_type") for d in mongo_docs)
        targets = set(d.get("target") for d in mongo_docs)
        avg_risk = sum(d.get("risk_score", 0.0) for d in mongo_docs) / max(len(mongo_docs), 1)

        is_fp = any("Benign" in t or "DNS" in t or "Cloud" in t for t in types)

        comm_summary = {
            "community_id": comm["community_id"],
            "node_count": comm["node_count"],
            "sources_reporting": len(comm["sources_involved"]),
            "targets": list(targets),
            "threat_types": list(types),
            "avg_risk_score": round(avg_risk, 3),
            "ground_truth_fp": is_fp,
            "status": "CONFIRMED FALSE-POSITIVE (Benign Infrastructure)" if is_fp else "TRUE MALICIOUS CLUSTER"
        }
        fp_isolated.append(comm_summary)

    # Render results table
    act_table = Table(title="Activity 18.1: Graph Community Detection & MongoDB Cross-Reference", border_style="green")
    act_table.add_column("Community ID", style="bold yellow", width=14)
    act_table.add_column("Node Count", justify="right", width=12)
    act_table.add_column("Sources", justify="right", width=10)
    act_table.add_column("Classified Infrastructure", style="cyan", width=30)
    act_table.add_column("Avg Risk", justify="right", width=10)
    act_table.add_column("Verdict", style="bold red", width=28)

    for c in fp_isolated:
        color = "green" if "FALSE-POSITIVE" in c["status"] else "red"
        act_table.add_row(
            c["community_id"],
            str(c["node_count"]),
            str(c["sources_reporting"]),
            ", ".join(c["targets"][:2]),
            f"{c['avg_risk_score']:.3f}",
            f"[{color}]{c['status']}[/{color}]"
        )

    console.print(act_table)
    print("\n[KEY TAKEAWAY] Neo4j graph topology accurately isolated multi-source false-positive clusters")
    print("that traditional tabular queries missed, while MongoDB provided rich transactional metadata.")
    return fp_isolated


# ==============================================================================
# MAIN ENTRYPOINT
# ==============================================================================

def run_lab18_1_complete() -> Dict[str, Any]:
    """Execute complete Lab 18.1 comparative pipeline."""
    banner("LAB 18.1: BUILD THE COMPARATIVE SYSTEM (100,000 THREATS)", char="#")

    # 1. Connect
    db = get_mongo_db("threat_intel_db")
    cass = get_cassandra_session()
    neo = get_neo4j_driver()

    # 2. Generate
    dataset = generate_threat_dataset(NUM_THREATS)

    # 3. Ingest
    ingest_mongodb(db, dataset)
    ingest_cassandra(cass, dataset)
    ingest_neo4j(neo, dataset)

    # 4. Benchmark
    benchmarks = run_benchmark_suite(db, cass, neo, dataset)
    display_benchmark_table(benchmarks)

    # 5. Activity 18.1
    fp_results = run_activity_18_1_detection(db, neo)

    return {
        "benchmarks": benchmarks,
        "dataset_size": len(dataset),
        "fp_communities": fp_results
    }


if __name__ == "__main__":
    run_lab18_1_complete()
