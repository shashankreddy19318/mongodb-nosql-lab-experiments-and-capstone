"""
Activity 7.2: WiredTiger Cache Monitoring & New Threat Discovery Engine
(Reference: Sujeet Jagtap - NoSQL Databases Using MongoDB, Chapter 07)

Key Features:
1. Researches and logs db.serverStatus().wiredTiger.cache metrics every 10 seconds:
   - maximum bytes configured (RAM cache allocation)
   - bytes currently in the cache
   - tracked dirty bytes in the cache (unwritten changes)
   - pages read into cache (cache misses)
   - pages requested from the cache (total memory requests)
   - calculated cache hit ratio: ((requested - read) / requested) * 100
2. Threat Discovery Crawler:
   - Periodically browses for new security reports not yet available in the database
   - Simulates live feeds from CTI Digest and Awesome Annual Security Reports
   - Enriches, classifies, and inserts discovered threat documents into MongoDB
3. Can run continuously or in test mode via CLI arguments.
"""

import sys
import time
import random
import datetime
import argparse
from typing import Dict, Any, List
from database import db_manager
from seed_data import generate_sample_iocs

# Simulated external feeds to crawl for novel threats
FEED_EXTERNAL_CANDIDATES = [
    {
        "title": "Novel Ransomware 'Phobos-Reborn' Deploying Chained Zero-Days Against Hypervisors",
        "threat_type": "Ransomware",
        "severity": "Critical",
        "cvss_score": 9.9,
        "source_id": "SRC-003",
        "actor_id": "ACT-002",
        "cve_ids": ["CVE-2026-5501"]
    },
    {
        "title": "State-Sponsored Supply Chain Compromise in PyPI Cloud Orchestration SDK",
        "threat_type": "APT",
        "severity": "High",
        "cvss_score": 8.9,
        "source_id": "SRC-001",
        "actor_id": "ACT-001",
        "cve_ids": ["CVE-2026-6102"]
    },
    {
        "title": "DarkWeb Actor 'LeakMaster' Auctioning Telecommunications Core Routing Firmware",
        "threat_type": "Zero-Day",
        "severity": "Critical",
        "cvss_score": 9.5,
        "source_id": "SRC-004",
        "actor_id": "ACT-005",
        "cve_ids": ["CVE-2026-7019"]
    },
    {
        "title": "Quantum-Resistant Key Exchange Downgrade Exploit in Legacy TLS Middleboxes",
        "threat_type": "Exploit",
        "severity": "High",
        "cvss_score": 8.6,
        "source_id": "SRC-005",
        "actor_id": "ACT-004",
        "cve_ids": ["CVE-2026-8820"]
    },
    {
        "title": "Distributed Mirai-Descendant IoT Botnet Weaponizing UPnP Vulnerabilities",
        "threat_type": "Botnet",
        "severity": "Medium",
        "cvss_score": 7.4,
        "source_id": "SRC-006",
        "actor_id": "ACT-005",
        "cve_ids": ["CVE-2026-9041"]
    }
]

def check_for_new_threat_reports() -> List[Dict[str, Any]]:
    """
    Browses for newer threat reports not currently stored in the MongoDB database.
    """
    db = db_manager.get_db()
    existing_titles = set(d["title"] for d in db.threat_reports.find({}, {"title": 1}))
    
    new_reports_found = []
    # Pick a candidate from external feed
    candidate = random.choice(FEED_EXTERNAL_CANDIDATES)
    
    # Generate unique title with timestamp
    unique_title = f"{candidate['title']} (Discovered at {datetime.datetime.now().strftime('%H:%M:%S')})"
    if unique_title not in existing_titles:
        new_doc = {
            "threat_id": f"CTI-LIVE-{random.randint(5000, 9999)}",
            "title": unique_title,
            "threat_type": candidate["threat_type"],
            "severity": candidate["severity"],
            "cvss_score": candidate["cvss_score"],
            "confidence": random.randint(85, 99),
            "description": f"Automatically ingested live intelligence report from external OSINT telemetry. High confidence attribution.",
            "published_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "source_id": candidate["source_id"],
            "actor_id": candidate["actor_id"],
            "cve_ids": candidate["cve_ids"],
            "indicators": generate_sample_iocs(count=random.randint(3, 5)),
            "classification": {
                "verdict": "Actual Threat",
                "status": "Active Threat - Ingested by Discovery Crawler",
                "kill_chain_stage": "Exploitation & Delivery",
                "mitre_techniques": ["T1190 - Exploit Public-Facing Application"]
            },
            "tags": ["live-feed", candidate["threat_type"].lower(), candidate["severity"].lower()],
            "discovered_by_crawler": True
        }
        new_reports_found.append(new_doc)
        
    return new_reports_found


def monitor_loop(interval_seconds: int = 10, max_cycles: int = 0):
    """
    Continuously monitors WiredTiger cache hit ratio every 10 seconds
    and searches for / ingests new threat reports.
    """
    db = db_manager.get_db()
    
    print("\n" + "="*85)
    print(" ACTIVITY 7.2: WIREDTIGER CACHE MONITOR & REAL-TIME THREAT CRAWLER")
    print(" Reporting interval: Every 10 Seconds | Querying: db.serverStatus().wiredTiger.cache")
    print("="*85)

    cycle = 0
    try:
        while True:
            cycle += 1
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 1. Step 1: Browse for newer threat reports not in DB
            new_threats = check_for_new_threat_reports()
            inserted_count = 0
            if new_threats:
                db.threat_reports.insert_many(new_threats)
                inserted_count = len(new_threats)
                for t in new_threats:
                    doc_size = db_manager.calculate_bson_size(t)
                    db_manager.cache_sim.register_document(str(t.get("_id", t["threat_id"])), doc_size, is_new=True)

            # 2. Step 2: Query WiredTiger serverStatus cache metrics
            status = db_manager.get_server_status()
            wt_cache = status.get("wiredTiger", {}).get("cache", {})
            
            max_bytes = wt_cache.get("maximum bytes configured", 0)
            bytes_in_cache = wt_cache.get("bytes currently in the cache", 0)
            dirty_bytes = wt_cache.get("tracked dirty bytes in the cache", 0)
            pages_read = wt_cache.get("pages read into cache", 0)
            pages_requested = wt_cache.get("pages requested from the cache", 0)
            hit_ratio = wt_cache.get("calculated cache hit ratio", 100.0)
            pct_in_cache = wt_cache.get("percentage of data in cache", 0.0)
            total_threats = db.threat_reports.count_documents({})

            # Print formatted monitoring telemetry block
            print(f"\n[TELEMETRY REPORT #{cycle}] {timestamp}")
            print(f"├─ Total Threats in Database:    {total_threats:,} (+{inserted_count} newly crawled)")
            if inserted_count > 0:
                print(f"│  └─ Ingested: '{new_threats[0]['title'][:50]}...'")
            print(f"├─ WiredTiger Configured Cache:  {max_bytes / (1024*1024):.1f} MB")
            print(f"├─ Memory Used by Cache:         {bytes_in_cache / (1024*1024):.2f} MB ({pct_in_cache:.1f}% resident)")
            print(f"├─ Tracked Dirty Bytes:          {dirty_bytes / (1024*1024):.2f} MB (pending writeback)")
            print(f"├─ Pages Requested (RAM hits):   {pages_requested:,}")
            print(f"├─ Pages Read (Disk misses):     {pages_read:,}")
            print(f"└─ WIREDTIGER CACHE HIT RATIO:   {hit_ratio:.2f}%")

            if max_cycles > 0 and cycle >= max_cycles:
                print(f"\n[Monitor] Completed {cycle} cycles. Exiting.")
                break

            time.sleep(interval_seconds)

    except KeyboardInterrupt:
        print("\n[Monitor] User interrupted monitoring loop. Shutdown clean.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WiredTiger 10s Monitoring & Threat Ingestion Script")
    parser.add_argument("--interval", type=int, default=10, help="Interval in seconds (default: 10)")
    parser.add_argument("--cycles", type=int, default=0, help="Maximum reporting cycles (0 for infinite)")
    args = parser.parse_args()

    monitor_loop(interval_seconds=args.interval, max_cycles=args.cycles)
