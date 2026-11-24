"""
Lab 6.1 - Try It Yourself: Index Usage Measurement with $indexStats
Objective: Use the $indexStats aggregation stage to measure actual index usage
           after running realistic queries multiple times. Identify which indexes
           are used most frequently and optimize index maintenance.
"""

import os
import sys
import time
import random
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
for p in [CURRENT_DIR, PARENT_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from bson import json_util
from pymongo import MongoClient

def get_database(db_name="nosql_lab_6_1_try_it_yourself"):
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print(f"[*] Successfully connected to live MongoDB server at localhost:27017 ({db_name})")
        return client, client[db_name], False
    except Exception:
        print(f"[*] Local MongoDB server offline. Running with in-memory execution engine ({db_name}).")
        from simulated_engine import SimulatedMongoEngine
        sim_client = SimulatedMongoEngine()
        return sim_client, sim_client[db_name], True

def generate_products(count=50000):
    random.seed(42)
    categories = ["Electronics", "Computers", "Audio", "Home & Kitchen", "Fitness", "Wearables"]
    noun_map = {
        "Electronics": ["Headphones", "Earbuds", "Speaker", "Charger", "Power Bank", "Camera", "Projector"],
        "Computers": ["Keyboard", "Mouse", "Monitor 4K", "Docking Station", "Webcam HD", "USB Hub", "Graphics Card"],
        "Audio": ["Studio Mic", "Soundbar", "Subwoofer", "Noise-Cancelling Headset", "DAC Amplifier", "Audio Interface"],
        "Home & Kitchen": ["Electric Kettle", "Air Fryer", "Espresso Machine", "Robot Vacuum", "Blender", "Toaster"],
        "Fitness": ["Yoga Mat", "Dumbbell Set", "Resistance Bands", "Smart Treadmill", "Kettlebell", "Foam Roller"],
        "Wearables": ["Fitness Band", "Smartwatch GPS", "Sleep Tracker", "Heart Rate Monitor", "Smart Glasses"]
    }
    tag_pool = ["wireless", "bluetooth", "usb-c", "portable", "waterproof", "rechargeable", "ergonomic", "gaming"]

    docs = []
    for i in range(count):
        cat = random.choice(categories)
        noun = random.choice(noun_map[cat])
        name = f"Pro {noun} #{i+1:05d}"
        price = round(random.uniform(15.0, 1200.0), 2)
        rating = round(random.uniform(2.0, 5.0), 1)
        stock = random.randint(0, 300)
        tags = list(set(random.sample(tag_pool, k=random.randint(2, 4))))

        docs.append({
            "product_id": f"PRD-{i+1:05d}",
            "name": name,
            "category": cat,
            "price": price,
            "rating": rating,
            "stock": stock,
            "tags": tags
        })
    return docs

def main():
    print("=" * 90)
    print("LAB 6.1 TRY IT YOURSELF: INDEX USAGE MONITORING VIA $indexStats")
    print("=" * 90)

    client, db, is_simulated = get_database("nosql_lab_6_1_try_it_yourself")
    col = db["products"]

    # Step 1: Initialize collection & indexes
    print("\n[+] Step 1: Initializing 'products' collection with 50,000 documents...")
    products = generate_products(50000)
    col.drop()
    col.insert_many(products)
    print(f"[OK] Seeded {col.count_documents({}):,} documents.")

    print("\n[+] Creating production indexes on 'products' collection:")
    indexes = [
        ("idx_category_price", [("category", 1), ("price", 1)]),
        ("idx_price", [("price", 1)]),
        ("idx_tags", [("tags", 1)]),
        ("idx_name_text", [("name", "text")]),
        ("idx_cat_rating_stock", [("category", 1), ("rating", -1), ("stock", 1)])
    ]
    for name, keys in indexes:
        col.create_index(keys, name=name)
        print(f"    - Index '{name}': {keys}")

    # Step 2: Simulate query workload with realistic distribution
    print("\n" + "-" * 90)
    print("Step 2: Simulating Realistic Production Workload (Running Queries Multiple Times)")
    print("-" * 90)

    workload = [
        {
            "id": "W1",
            "desc": "Category filter + Price Sort (Catalog page browsing)",
            "query": {"category": "Electronics"},
            "sort": [("price", 1)],
            "runs": 150,
            "target_index": "idx_category_price"
        },
        {
            "id": "W2",
            "desc": "Price range filter $50-$150 (Budget filter slider)",
            "query": {"price": {"$gte": 50.0, "$lte": 150.0}},
            "sort": None,
            "runs": 85,
            "target_index": "idx_price"
        },
        {
            "id": "W3",
            "desc": "Tag array filter 'wireless' (High-frequency tag search)",
            "query": {"tags": "wireless"},
            "sort": None,
            "runs": 220,
            "target_index": "idx_tags"
        },
        {
            "id": "W4",
            "desc": "Full-text search for 'Gaming Keyboard'",
            "query": {"$text": {"$search": "Gaming Keyboard"}},
            "sort": None,
            "runs": 40,
            "target_index": "idx_name_text"
        },
        {
            "id": "W5",
            "desc": "Category 'Audio' with Rating >= 4.5 and Stock > 0",
            "query": {"category": "Audio", "rating": {"$gte": 4.5}, "stock": {"$gt": 0}},
            "sort": [("rating", -1)],
            "runs": 110,
            "target_index": "idx_cat_rating_stock"
        }
    ]

    total_query_runs = 0
    for w in workload:
        print(f"  Executing {w['id']} ({w['desc']}): {w['runs']} iterations -> Index: {w['target_index']}")
        for _ in range(w["runs"]):
            cursor = col.find(w["query"])
            if w["sort"]:
                cursor = cursor.sort(w["sort"])
            # In live mode or simulated mode, trigger query execution
            if is_simulated:
                cursor.explain("executionStats")
            else:
                list(cursor.limit(5))
        total_query_runs += w["runs"]

    print(f"\n[OK] Completed simulated workload: {total_query_runs:,} total queries executed.")

    # Step 3: Run $indexStats aggregation pipeline
    print("\n" + "=" * 90)
    print("STEP 3: RUNNING $indexStats AGGREGATION STAGE")
    print("=" * 90)
    print("  Pipeline: [{'$indexStats': {}}]")

    stats_cursor = col.aggregate([{"$indexStats": {}}])
    raw_stats = list(stats_cursor)

    # Sort index stats by operations count descending
    sorted_stats = sorted(raw_stats, key=lambda x: x.get("accesses", {}).get("ops", 0), reverse=True)
    total_index_ops = sum(s.get("accesses", {}).get("ops", 0) for s in sorted_stats)

    print("\n" + "-" * 90)
    print(f"{'Index Name':<26} | {'Keys':<34} | {'Ops (Hits)':<12} | {'Usage %':<10}")
    print("-" * 90)

    stats_summary = []
    for s in sorted_stats:
        idx_name = s.get("name", "unknown")
        keys = s.get("key", {})
        ops = s.get("accesses", {}).get("ops", 0)
        since = s.get("accesses", {}).get("since", "N/A")
        usage_pct = (ops / max(total_index_ops, 1)) * 100.0

        print(f"{idx_name:<26} | {str(keys):<34} | {ops:<12} | {usage_pct:>6.1f}%")
        stats_summary.append({
            "index_name": idx_name,
            "key": keys,
            "operations": ops,
            "usage_percentage": round(usage_pct, 2),
            "tracked_since": since
        })

    # Step 4: Workload Identification and Analysis
    print("\n" + "=" * 90)
    print("STEP 4: IDENTIFYING MOST & LEAST FREQUENTLY USED INDEXES")
    print("=" * 90)

    most_used = sorted_stats[0] if sorted_stats else {}
    least_used = sorted_stats[-1] if sorted_stats else {}

    print(f"\n  [*] Most Frequently Used Index:")
    print(f"      - Name        : {most_used.get('name')}")
    print(f"      - Keys        : {most_used.get('key')}")
    print(f"      - Operations  : {most_used.get('accesses', {}).get('ops')} hits ({most_used.get('accesses', {}).get('ops', 0) / max(total_index_ops, 1) * 100:.1f}% of total workload)")
    print(f"      - Conclusion  : This index is critical for read performance and must remain pinned in memory (RAM).")

    print(f"\n  [!] Underutilized / Unused Index:")
    print(f"      - Name        : {least_used.get('name')}")
    print(f"      - Keys        : {least_used.get('key')}")
    print(f"      - Operations  : {least_used.get('accesses', {}).get('ops')} hits")
    print(f"      - Conclusion  : If an index records 0 or negligible hits in production, it is a candidate for")
    print(f"                      removal (pruning) to save RAM and eliminate write overhead.")

    # Detailed Production Analysis
    analysis_text = (
        "Production Index Monitoring Insights:\n"
        "1. The $indexStats aggregation stage provides real-time telemetry on index utilization since the last mongod restart.\n"
        "2. High-traffic multikey indexes (like 'idx_tags') and compound catalog indexes ('idx_category_price') absorb\n"
        "   over 60% of all read traffic in typical retail environments.\n"
        "3. Zero-hit indexes create pure write overhead without providing query acceleration. Identifying unused indexes\n"
        "   via $indexStats allows database administrators to safely drop them, freeing up WiredTiger cache and\n"
        "   improving write throughput across the cluster."
    )
    print("\n" + "-" * 90)
    print(analysis_text)
    print("-" * 90)

    # Step 5: Export to JSON
    export_payload = {
        "metadata": {
            "lab": "Lab 6.1 Try It Yourself: Index Usage Measurement via $indexStats",
            "total_documents": 50000,
            "total_queries_simulated": total_query_runs,
            "total_index_operations": total_index_ops,
            "database_name": "nosql_lab_6_1_try_it_yourself",
            "collection_name": "products"
        },
        "workload_simulation": workload,
        "index_statistics": stats_summary,
        "most_frequently_used": {
            "name": most_used.get("name"),
            "key": most_used.get("key"),
            "ops": most_used.get("accesses", {}).get("ops")
        },
        "least_frequently_used": {
            "name": least_used.get("name"),
            "key": least_used.get("key"),
            "ops": least_used.get("accesses", {}).get("ops")
        },
        "dba_recommendations": [
            "Pin frequently used compound indexes in WiredTiger memory cache.",
            "Schedule periodic $indexStats audits to detect zombie or unused indexes.",
            "Drop indexes with near-zero access counts to recover memory and reduce write latency."
        ]
    }

    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_6_1_try_it_yourself.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 90)
    print(f"[+] Successfully exported $indexStats results to:")
    print(f"    {json_path}")
    print("=" * 90)

if __name__ == "__main__":
    main()
