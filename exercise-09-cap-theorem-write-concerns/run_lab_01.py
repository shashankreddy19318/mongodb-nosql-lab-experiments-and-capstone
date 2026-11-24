"""
Lab 9.1: Measure Write Concern Latency
Benchmarks write concerns: w:1, w:majority, w:all (w:3)
With both j:false and j:true.
Measures total time, average latency, P50, and P99 latency.
"""

import sys
import os
import time
from pymongo import MongoClient, WriteConcern

# Connect directly to primary on localhost:27017 or use replicaSet URI if available
PRIMARY_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true")
DOC_COUNT = 1000

def benchmark_wc(client, w_val, j_val, label):
    db = client["cap_latency_benchmark"]
    col_name = f"data_{label.replace(':', '_').replace(' ', '_').replace(',', '')}"
    db.drop_collection(col_name)
    wc = WriteConcern(w=w_val, j=j_val, wtimeout=15000)
    col = db[col_name].with_options(write_concern=wc)

    latencies = []
    print(f"  --> Benchmarking {label} (1,000 documents)...", end="", flush=True)
    t0 = time.perf_counter()
    for i in range(DOC_COUNT):
        doc = {"seq": i, "timestamp_ns": time.time_ns(), "payload": "Lab 9.1 latency measurement document"}
        start = time.perf_counter()
        col.insert_one(doc)
        latencies.append(time.perf_counter() - start)
    total_time = time.perf_counter() - t0
    print(f" Done in {total_time:.3f}s")

    avg_ms = (sum(latencies) / len(latencies)) * 1000
    sorted_lats = sorted(latencies)
    p50_ms = sorted_lats[len(sorted_lats) // 2] * 1000
    p99_ms = sorted_lats[int(len(sorted_lats) * 0.99)] * 1000
    ops_sec = DOC_COUNT / total_time

    return {
        "label": label,
        "w": str(w_val),
        "j": str(j_val),
        "total_time_s": total_time,
        "avg_ms": avg_ms,
        "p50_ms": p50_ms,
        "p99_ms": p99_ms,
        "ops_sec": ops_sec
    }

def main():
    print("=" * 78)
    print("       LAB 9.1: WRITE CONCERN LATENCY & JOURNALING BENCHMARK")
    print("=" * 78)
    print(f"Target URI: {PRIMARY_URI}")
    print(f"Document count per test: {DOC_COUNT:,}")
    
    client = MongoClient(PRIMARY_URI, serverSelectionTimeoutMS=5000)
    # Check connection and replSet status
    status = client.admin.command("replSetGetStatus")
    print(f"Replica Set Name: {status['set']}")
    print("Cluster Members:")
    for m in status['members']:
        print(f"  - {m['name']:<25} State: {m['stateStr']:<15} Health: {m['health']}")
    print("-" * 78)

    configs = [
        (1, False, "w:1, j:false"),
        (1, True,  "w:1, j:true"),
        ("majority", False, "w:majority, j:false"),
        ("majority", True,  "w:majority, j:true"),
        (3, False, "w:all (w:3), j:false"),
        (3, True,  "w:all (w:3), j:true")
    ]

    results = []
    for w_val, j_val, label in configs:
        res = benchmark_wc(client, w_val, j_val, label)
        results.append(res)

    print("\n" + "=" * 78)
    print("                  WRITE CONCERN LATENCY COMPARISON TABLE")
    print("=" * 78)
    header = f"{'Configuration':<24} | {'Total Time':>11} | {'Avg (ms)':>9} | {'P50 (ms)':>9} | {'P99 (ms)':>9} | {'Throughput':>10}"
    print(header)
    print("-" * 78)
    for r in results:
        line = f"{r['label']:<24} | {r['total_time_s']:>10.3f}s | {r['avg_ms']:>9.2f} | {r['p50_ms']:>9.2f} | {r['p99_ms']:>9.2f} | {r['ops_sec']:>7.1f} op/s"
        print(line)
    print("=" * 78)

    # Detailed Analysis
    base_avg = results[0]['avg_ms']
    print("\n--- Comparative Analysis & Relative Slowdown ---")
    for r in results:
        ratio = r['avg_ms'] / base_avg
        print(f"  * {r['label']:<24}: {ratio:>5.2f}x baseline (w:1, j:false)")

    print("\n--- Impact of Journaling (j:true vs j:false) ---")
    j_overhead_w1 = results[1]['avg_ms'] - results[0]['avg_ms']
    j_overhead_wmaj = results[3]['avg_ms'] - results[2]['avg_ms']
    j_overhead_wall = results[5]['avg_ms'] - results[4]['avg_ms']
    print(f"  * w:1        : j:true adds {j_overhead_w1:+.2f} ms ({((results[1]['avg_ms']/results[0]['avg_ms'])-1)*100:+.1f}%)")
    print(f"  * w:majority : j:true adds {j_overhead_wmaj:+.2f} ms ({((results[3]['avg_ms']/results[2]['avg_ms'])-1)*100:+.1f}%)")
    print(f"  * w:all (w:3): j:true adds {j_overhead_wall:+.2f} ms ({((results[5]['avg_ms']/results[4]['avg_ms'])-1)*100:+.1f}%)")

    client.close()
    print("\n[OK] Lab 9.1 benchmark completed successfully.")

if __name__ == "__main__":
    main()
