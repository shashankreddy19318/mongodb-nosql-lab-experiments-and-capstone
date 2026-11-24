"""
Lab 7.2: Working Set Analysis & WiredTiger Cache Fit
Dataset context: Awesome Annual Security Reports (https://github.com/jacobdjwilson/awesome-annual-security-reports)

Covers:
1. Ingestion of 100,000 documents (~2 KB each) into test collection 'working_set_reports'
2. Extraction and evaluation of db.serverStatus().wiredTiger.cache metrics
3. Random reads workload across the collection tracking Cache Hit Ratio evolution over time
"""

import sys
import time
import random
import bson
from typing import Dict, Any, List
from database import db_manager

ANNUAL_REPORT_VENDORS = [
    ("CrowdStrike", "Global Threat Report", ["eCrime", "Adversary OverWatch", "Breakout Time"]),
    ("Mandiant / Google Cloud", "M-Trends Special Report", ["Dwell Time", "Global Intrusion Vectors", "Ransomware Operations"]),
    ("Verizon", "Data Breach Investigations Report (DBIR)", ["Phishing", "Stolen Credentials", "Internal Misuse"]),
    ("Microsoft", "Digital Defense Report", ["Nation-State Attacks", "IoT/OT Vulnerabilities", "Cloud Identity Attacks"]),
    ("Cisco Talos", "Year in Review", ["Commodity Loaders", "Zero-Day Exploitation", "Supply Chain Attacks"]),
    ("Sophos", "State of Ransomware Report", ["Mean Ransom Payment", "Backup Compromise", "Recovery Cost"]),
    ("Palo Alto Networks / Unit 42", "Incident Response Report", ["Cloud Ransomware", "Extortion Demands", "BEC"]),
    ("Trend Micro", "Annual Cybersecurity Report", ["Linux Malware", "Container Threats", "API Exploitation"])
]

def generate_2kb_report_doc(doc_index: int) -> Dict[str, Any]:
    """Generates an authentic 2 KB cybersecurity intelligence report document."""
    vendor, report_series, focal_areas = random.choice(ANNUAL_REPORT_VENDORS)
    year = random.randint(2019, 2026)
    
    # Generate realistic telemetry payload sized to meet exact ~2 KB BSON target
    telemetry_samples = []
    for s in range(5):
        telemetry_samples.append({
            "sample_id": f"SMPL-{doc_index}-{s}",
            "c2_domain": f"auth-telemetry-node-{random.randint(100, 999)}.defense-metrics.net",
            "ip_address": f"{random.randint(11, 220)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "observed_hash_sha256": "".join(random.choices("0123456789abcdef", k=64)),
            "beacon_interval_ms": random.randint(1500, 60000),
            "threat_rating": random.choice(["Critical", "High", "Medium", "Elevated"]),
            "geo_asn": f"AS{random.randint(1000, 65000)} - {random.choice(['US', 'DE', 'SG', 'IN', 'JP', 'NL', 'UK'])}"
        })

    doc = {
        "report_id": f"AASR-{year}-{doc_index:06d}",
        "dataset_source": "https://github.com/jacobdjwilson/awesome-annual-security-reports",
        "publisher": vendor,
        "report_title": f"{vendor} {report_series} - Annual Threat Telemetry Case #{doc_index}",
        "edition_year": year,
        "focal_topics": focal_areas,
        "executive_summary": (
            f"Annual intelligence synthesis documenting adversary tradecraft, dwell times, and extortion trends observed by {vendor} "
            f"during global incident response engagements in {year}. Telemetry reflects enterprise deployments across Fortune 500."
        ),
        "metrics_telemetry": {
            "median_dwell_time_days": random.randint(2, 45),
            "ransom_demand_avg_usd": random.randint(250000, 8500000),
            "initial_access_vector": random.choice(["Valid Credentials", "Exploit Public Application", "Spearphishing Attachment"]),
            "multi_factor_bypass_rate": round(random.uniform(0.12, 0.48), 3),
            "samples": telemetry_samples
        },
        "mitre_attack_matrix": {
            "tactic": random.choice(["TA0001 Initial Access", "TA0002 Execution", "TA0006 Credential Access", "TA0040 Impact"]),
            "technique_id": f"T{random.randint(1000, 1599)}.{random.randint(1, 9):03d}",
            "detection_confidence": round(random.uniform(0.75, 0.99), 2)
        },
        "analyst_notes": "Archived security benchmark document for working set and cache residency analysis.",
        "padding_buffer": "A" * 600  # Calibrated buffer to stabilize document size at ~2,048 bytes (2 KB)
    }
    return doc

def insert_100k_documents(total_docs: int = 100000, batch_size: int = 5000):
    """Inserts 100,000 documents (~2 KB each) into the 'working_set_reports' collection."""
    db = db_manager.get_db()
    col = db.working_set_reports
    
    print("\n" + "="*75)
    print(f" LAB 7.2: INSERTING {total_docs:,} DOCUMENTS (~2 KB EACH)")
    print("="*75)

    current_count = col.count_documents({})
    if current_count >= total_docs:
        print(f"Collection 'working_set_reports' already contains {current_count:,} documents. Skipping generation.")
        sample = col.find_one()
        sample_size = len(bson.BSON.encode(sample)) if sample else 2048
        return current_count, sample_size

    # Verify single document size first
    sample_doc = generate_2kb_report_doc(1)
    sample_size = len(bson.BSON.encode(sample_doc))
    print(f"Calibrated Document Size: {sample_size} bytes ({sample_size / 1024:.2f} KB)")
    expected_total_mb = (sample_size * total_docs) / (1024 * 1024)
    print(f"Projected Collection Size: ~{expected_total_mb:.1f} MB (Uncompressed)")

    start_time = time.time()
    inserted_so_far = current_count
    
    # In live Mongo or mock, insert in efficient batches
    while inserted_so_far < total_docs:
        batch = []
        target = min(batch_size, total_docs - inserted_so_far)
        for i in range(target):
            d = generate_2kb_report_doc(inserted_so_far + i + 1)
            batch.append(d)
        
        col.insert_many(batch)
        inserted_so_far += len(batch)
        
        # Register with cache simulator
        for d in batch:
            doc_id = str(d.get("_id", d["report_id"]))
            db_manager.cache_sim.register_document(doc_id, sample_size, is_new=True)

        elapsed = time.time() - start_time
        rate = inserted_so_far / elapsed if elapsed > 0 else 0
        pct = (inserted_so_far / total_docs) * 100.0
        sys.stdout.write(f"\rProgress: {inserted_so_far:,}/{total_docs:,} documents inserted ({pct:.1f}%) - Speed: {rate:.0f} docs/sec")
        sys.stdout.flush()

    total_time = time.time() - start_time
    print(f"\n[Insertion Complete] Successfully inserted {inserted_so_far:,} documents in {total_time:.2f}s.")
    return inserted_so_far, sample_size


def analyze_wiredtiger_server_status():
    """Extracts and explains db.serverStatus() WiredTiger cache metrics."""
    print("\n" + "="*75)
    print(" WIREDTIGER CACHE METRICS VIA db.serverStatus()")
    print("="*75)

    status = db_manager.get_server_status()
    wt_cache = status.get("wiredTiger", {}).get("cache", {})

    max_bytes = wt_cache.get("maximum bytes configured", 0)
    bytes_in_cache = wt_cache.get("bytes currently in the cache", 0)
    dirty_bytes = wt_cache.get("tracked dirty bytes in the cache", 0)
    pages_read = wt_cache.get("pages read into cache", 0)
    pages_requested = wt_cache.get("pages requested from the cache", 0)
    hit_ratio = wt_cache.get("calculated cache hit ratio", 100.0)
    pct_in_cache = wt_cache.get("percentage of data in cache", 0.0)

    print(f"1. Maximum Cache Configured:   {max_bytes / (1024*1024):.1f} MB ({max_bytes:,} bytes)")
    print(f"2. Bytes Currently in Cache:   {bytes_in_cache / (1024*1024):.2f} MB ({bytes_in_cache:,} bytes)")
    print(f"3. Tracked Dirty Bytes:        {dirty_bytes / (1024*1024):.2f} MB ({dirty_bytes:,} bytes)")
    print(f"4. Percentage of Data in Cache:{pct_in_cache:.2f}%")
    print(f"5. Pages Requested from Cache: {pages_requested:,}")
    print(f"6. Pages Read into Cache:      {pages_read:,}")
    print(f"7. Calculated Cache Hit Ratio: {hit_ratio:.2f}%")
    
    print("\nKey Takeaway on Cache Fit:")
    if pct_in_cache >= 100.0:
        print("✓ The entire working set easily fits in WiredTiger RAM cache. Zero disk read churn required.")
    else:
        print(f"⚠ Cache under-provisioned: {100 - pct_in_cache:.1f}% of data resides on disk. Eviction/disk reads will occur on random access.")

    return wt_cache


def run_random_reads_workload(read_cycles: int = 5000):
    """
    Executes random reads across the collection and measures how
    cache hit ratio changes over time.
    """
    print("\n" + "="*75)
    print(f" RUNNING RANDOM READS WORKLOAD ({read_cycles:,} OPERATIONS)")
    print("="*75)

    db = db_manager.get_db()
    col = db.working_set_reports
    total_docs = col.count_documents({})
    if total_docs == 0:
        print("No documents found. Please run insertion first.")
        return []

    checkpoints = [100, 500, 1000, 2000, 3500, 5000]
    results = []

    print(f"{'Read Ops':<12} | {'Cache Hit Ratio':<18} | {'Pages Requested':<16} | {'Pages Read from Disk'}")
    print("-" * 65)

    for i in range(1, read_cycles + 1):
        target_index = random.randint(1, total_docs)
        report_id = f"AASR-2024-{target_index:06d}"
        
        # Read operation
        doc = col.find_one({"report_id": report_id})
        
        # Track in simulator
        db_manager.cache_sim.record_read(report_id, 2048)

        if i in checkpoints or (i % 1000 == 0):
            status = db_manager.get_server_status()
            cache_info = status.get("wiredTiger", {}).get("cache", {})
            hr = cache_info.get("calculated cache hit ratio", 0.0)
            req = cache_info.get("pages requested from the cache", 0)
            read = cache_info.get("pages read into cache", 0)
            
            print(f"{i:<12} | {hr:>16.2f}% | {req:>16,} | {read:>18,}")
            results.append({
                "reads_completed": i,
                "hit_ratio": hr,
                "pages_requested": req,
                "pages_read": read
            })

    print("-" * 65)
    print("Observation on Cache Hit Ratio Behavior:")
    print("• Cold Start: At the beginning of random reads, newly requested pages are not in memory, causing disk reads.")
    print("• Warm Cache: As the active working set stabilizes in memory, Cache Hit Ratio trends towards steady state.")

    return results

def run_lab_7_2():
    insert_100k_documents(total_docs=100000, batch_size=5000)
    analyze_wiredtiger_server_status()
    run_random_reads_workload(read_cycles=3000)

if __name__ == "__main__":
    run_lab_7_2()
