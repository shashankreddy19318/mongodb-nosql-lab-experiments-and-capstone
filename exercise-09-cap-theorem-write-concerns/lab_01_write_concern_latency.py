"""
================================================================================
Lab 9.1: Measure Write Concern Latency
Chapter 09 - NoSQL Databases (MongoDB)
================================================================================
Objective:
  Measure the impact of different write concerns (w:1, w:majority, w:all)
  and journaling options (j:true vs j:false) on write latency and throughput.
  Inserts 1,000 documents per configuration and calculates average, P50, and P99 latency.
================================================================================
"""

import os
import sys
import time
from pymongo import MongoClient, WriteConcern

# Default URI: connects directly to primary on localhost:27017 or replica set URI
MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017/?directConnection=true"
)
DOC_COUNT = int(os.getenv("DOC_COUNT", "1000"))


def benchmark_configuration(client, w_val, j_val, label):
    """
    Inserts DOC_COUNT documents sequentially with the specified write concern.
    Measures total time, average latency, P50, and P99.
    """
    db = client["lab09_latency_benchmark"]
    col_name = f"data_{label.replace(':', '_').replace(' ', '_').replace(',', '')}"
    db.drop_collection(col_name)
    
    wc = WriteConcern(w=w_val, j=j_val, wtimeout=20000)
    col = db[col_name].with_options(write_concern=wc)

    latencies = []
    print(f"  [+] Testing {label:<22} ({DOC_COUNT:,} docs)...", end="", flush=True)
    
    start_total = time.perf_counter()
    for seq in range(DOC_COUNT):
        doc = {
            "seq": seq,
            "timestamp_ns": time.time_ns(),
            "label": label,
            "payload": "Distributed database write concern latency benchmark test record"
        }
        t0 = time.perf_counter()
        col.insert_one(doc)
        latencies.append(time.perf_counter() - t0)
    total_sec = time.perf_counter() - start_total
    
    avg_ms = (sum(latencies) / len(latencies)) * 1000.0
    sorted_lats = sorted(latencies)
    p50_ms = sorted_lats[len(sorted_lats) // 2] * 1000.0
    p99_ms = sorted_lats[int(len(sorted_lats) * 0.99)] * 1000.0
    ops_per_sec = DOC_COUNT / total_sec
    
    print(f" Done in {total_sec:>6.3f}s | Avg: {avg_ms:>6.2f} ms | P50: {p50_ms:>6.2f} ms | P99: {p99_ms:>6.2f} ms")
    
    return {
        "label": label,
        "w": str(w_val),
        "j": str(j_val),
        "total_sec": total_sec,
        "avg_ms": avg_ms,
        "p50_ms": p50_ms,
        "p99_ms": p99_ms,
        "ops_sec": ops_per_sec
    }


def main():
    print("=" * 82)
    print("      LAB 9.1: WRITE CONCERN LATENCY & JOURNALING EMPIRICAL BENCHMARK")
    print("=" * 82)
    print(f"Target Connection URI: {MONGO_URI}")
    print(f"Documents per Test:    {DOC_COUNT:,}")
    
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    try:
        status = client.admin.command("replSetGetStatus")
        print(f"Replica Set Name:      {status.get('set', 'N/A')}")
        print("Cluster Topology:")
        for m in status.get("members", []):
            print(f"  * {m['name']:<24} State: {m['stateStr']:<12} Health: {m['health']}")
    except Exception as e:
        print(f"[!] Note on replSetGetStatus: {e}")
    print("-" * 82)

    # 6 test configurations: 3 write concerns x 2 journaling modes
    test_suite = [
        (1, False, "w:1, j:false"),
        (1, True,  "w:1, j:true"),
        ("majority", False, "w:majority, j:false"),
        ("majority", True,  "w:majority, j:true"),
        (3, False, "w:all (w:3), j:false"),
        (3, True,  "w:all (w:3), j:true")
    ]

    results = []
    for w_val, j_val, label in test_suite:
        res = benchmark_configuration(client, w_val, j_val, label)
        results.append(res)

    print("\n" + "=" * 82)
    print("                     EMPIRICAL BENCHMARK RESULTS TABLE")
    print("=" * 82)
    header = f"{'Configuration':<24} | {'Total Time':>11} | {'Avg (ms)':>9} | {'P50 (ms)':>9} | {'P99 (ms)':>9} | {'Throughput':>12}"
    print(header)
    print("-" * 82)
    for r in results:
        row = (
            f"{r['label']:<24} | "
            f"{r['total_sec']:>10.3f}s | "
            f"{r['avg_ms']:>9.2f} | "
            f"{r['p50_ms']:>9.2f} | "
            f"{r['p99_ms']:>9.2f} | "
            f"{r['ops_sec']:>9.1f} ops/s"
        )
        print(row)
    print("=" * 82)

    # Analysis
    base_avg = results[0]["avg_ms"]
    print("\n>>> Analysis 1: Relative Latency Multipliers (vs w:1, j:false Baseline)")
    for r in results:
        mult = r["avg_ms"] / base_avg
        print(f"  * {r['label']:<24} : {mult:>5.2f}x baseline latency")

    print("\n>>> Analysis 2: Journaling Overhead (j:true vs j:false)")
    diff_w1 = results[1]["avg_ms"] - results[0]["avg_ms"]
    diff_wmaj = results[3]["avg_ms"] - results[2]["avg_ms"]
    diff_wall = results[5]["avg_ms"] - results[4]["avg_ms"]
    print(f"  * w:1         : Journal flush adds {diff_w1:+.2f} ms ({((results[1]['avg_ms']/results[0]['avg_ms'])-1)*100:+.1f}%)")
    print(f"  * w:majority  : Journal flush adds {diff_wmaj:+.2f} ms ({((results[3]['avg_ms']/results[2]['avg_ms'])-1)*100:+.1f}%)")
    print(f"  * w:all (w:3) : Journal flush adds {diff_wall:+.2f} ms ({((results[5]['avg_ms']/results[4]['avg_ms'])-1)*100:+.1f}%)")

    print("\n>>> Analysis 3: Architectural Findings")
    print("  1. w:1 is the fastest because the primary acknowledges as soon as the write")
    print("     is applied in memory (or local journal). No network replication wait is required.")
    print("  2. w:majority waits for at least 1 secondary node to acknowledge replication.")
    print("     This introduces inter-node network round-trip latency (~2-4x higher than w:1).")
    print("  3. w:all waits for ALL replica set members (3 nodes) to confirm receipt.")
    print("     Latency is bounded by the slowest member in the cluster.")
    print("  4. Journaling (j:true) enforces synchronous disk synchronization (fsync) before")
    print("     acknowledgment, trading raw throughput for crash durability.")

    client.close()
    print("\n[OK] Lab 9.1 completed successfully.")


if __name__ == "__main__":
    main()
