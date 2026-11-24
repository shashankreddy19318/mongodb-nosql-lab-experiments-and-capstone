"""
Lab 6.1: Index Design for a Query Workload
Objective: Design and validate indexes for a realistic query workload.
Prerequisites: Completion of Chapter 5 labs.

Instructions:
1. Create a products collection with 50,000 generated documents (use a loop with random data).
   Fields: name, category, price, rating, stock, tags (array).
2. Write five representative queries for this collection:
   - Q1: Find by category and sort by price
   - Q2: Find by price range
   - Q3: Find by tag
   - Q4: Text search on name
   - Q5: Find by category with rating threshold and stock availability
3. Run explain() on each query before creating any indexes. Record stage and totalDocsExamined.
4. Design a set of indexes that covers all five queries. Create indexes and run explain() again.
   Compare the before and after results.
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

def get_database(db_name="nosql_lab_6_1"):
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to an integrated high-fidelity execution engine.
    """
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
    """
    Generates synthetic product documents with realistic retail attributes.
    """
    random.seed(42)  # For reproducible results
    categories = ["Electronics", "Computers", "Audio", "Home & Kitchen", "Fitness", "Wearables"]
    adjectives = ["Pro", "Ultra", "Wireless", "Ergonomic", "Smart", "Compact", "Gaming", "Premium", "Portable", "Eco"]
    noun_map = {
        "Electronics": ["Headphones", "Earbuds", "Speaker", "Charger", "Power Bank", "Camera", "Projector"],
        "Computers": ["Keyboard", "Mouse", "Monitor 4K", "Docking Station", "Webcam HD", "USB Hub", "Graphics Card"],
        "Audio": ["Studio Mic", "Soundbar", "Subwoofer", "Noise-Cancelling Headset", "DAC Amplifier", "Audio Interface"],
        "Home & Kitchen": ["Electric Kettle", "Air Fryer", "Espresso Machine", "Robot Vacuum", "Blender", "Toaster"],
        "Fitness": ["Yoga Mat", "Dumbbell Set", "Resistance Bands", "Smart Treadmill", "Kettlebell", "Foam Roller"],
        "Wearables": ["Fitness Band", "Smartwatch GPS", "Sleep Tracker", "Heart Rate Monitor", "Smart Glasses"]
    }
    tag_pool = ["wireless", "bluetooth", "usb-c", "portable", "waterproof", "rechargeable",
                "ergonomic", "high-res", "compact", "durable", "lightweight", "sale", "premium"]

    docs = []
    for i in range(count):
        cat = random.choice(categories)
        noun = random.choice(noun_map[cat])
        adj1 = random.choice(adjectives)
        adj2 = random.choice(adjectives)
        name = f"{adj1} {adj2} {noun} #{i+1:05d}"
        price = round(random.uniform(15.0, 1250.0), 2)
        rating = round(random.uniform(2.0, 5.0), 1)
        stock = random.randint(0, 350)
        tags = list(set(random.sample(tag_pool, k=random.randint(2, 5))))

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

def extract_explain_metrics(plan):
    """
    Extracts winningStage, totalDocsExamined, totalKeysExamined, indexName, executionTimeMillis
    from standard MongoDB explain() result.
    """
    query_planner = plan.get("queryPlanner", {})
    winning = query_planner.get("winningPlan", {})
    exec_stats = plan.get("executionStats", {})

    stage = exec_stats.get("executionStages", {}).get("stage") or winning.get("stage", "UNKNOWN")
    docs_exam = exec_stats.get("totalDocsExamined", plan.get("totalDocsExamined", 0))
    keys_exam = exec_stats.get("totalKeysExamined", plan.get("totalKeysExamined", 0))
    exec_time = exec_stats.get("executionTimeMillis", plan.get("executionTimeMillis", 0))
    
    # Extract index name if IXSCAN is present
    index_name = "None (Full Collection Scan)"
    def find_index(node):
        if isinstance(node, dict):
            if "indexName" in node:
                return node["indexName"]
            for v in node.values():
                res = find_index(v)
                if res:
                    return res
        elif isinstance(node, list):
            for item in node:
                res = find_index(item)
                if res:
                    return res
        return None

    found_idx = find_index(winning) or find_index(exec_stats)
    if found_idx:
        index_name = found_idx

    return {
        "stage": stage,
        "totalDocsExamined": docs_exam,
        "totalKeysExamined": keys_exam,
        "executionTimeMillis": exec_time,
        "indexName": index_name
    }

def main():
    print("=" * 90)
    print("LAB 6.1: INDEX DESIGN FOR A QUERY WORKLOAD")
    print("=" * 90)

    client, db, is_simulated = get_database("nosql_lab_6_1")
    col = db["products"]

    # -------------------------------------------------------------------------
    # Step 1: Create products collection with 50,000 generated documents
    # -------------------------------------------------------------------------
    print("\n[+] Step 1: Generating 50,000 synthetic product documents...")
    products = generate_products(50000)
    col.drop()
    col.insert_many(products)
    total_docs = col.count_documents({})
    print(f"[OK] Inserted {total_docs:,} documents into 'products' collection.")

    # Display sample document schema
    sample = col.find_one({}, {"_id": 0})
    print("\n    Sample Document Structure:")
    for k, v in sample.items():
        print(f"      - {k:<12}: {v}")

    # -------------------------------------------------------------------------
    # Step 2: Define Five Representative Queries
    # -------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("Step 2: Defining Five Representative Queries for the Workload")
    print("-" * 90)

    queries = [
        {
            "id": "Q1",
            "name": "Find by Category and Sort by Price",
            "desc": "Category = 'Electronics', sorted by price ASC (Browsing catalog page)",
            "filter": {"category": "Electronics"},
            "sort": [("price", 1)],
            "limit": 100
        },
        {
            "id": "Q2",
            "name": "Find by Price Range",
            "desc": "Price between $50.00 and $150.00 (Budget filter slider)",
            "filter": {"price": {"$gte": 50.0, "$lte": 150.0}},
            "sort": None,
            "limit": 100
        },
        {
            "id": "Q3",
            "name": "Find by Multikey Tag (Array Element)",
            "desc": "Products tagged with 'wireless' (Feature badge search)",
            "filter": {"tags": "wireless"},
            "sort": None,
            "limit": 100
        },
        {
            "id": "Q4",
            "name": "Text Search on Product Name",
            "desc": "Search product name for 'Gaming Keyboard' (Full-text search bar)",
            "filter": {"$text": {"$search": "Gaming Keyboard"}},
            "sort": None,
            "limit": 50
        },
        {
            "id": "Q5",
            "name": "Compound Category with Rating & Stock Availability",
            "desc": "Category = 'Audio', Rating >= 4.5, Stock > 0 (High-rated in-stock filter)",
            "filter": {"category": "Audio", "rating": {"$gte": 4.5}, "stock": {"$gt": 0}},
            "sort": [("rating", -1)],
            "limit": 50
        }
    ]

    for q in queries:
        print(f"  [{q['id']}] {q['name']:<48} | {q['desc']}")

    # -------------------------------------------------------------------------
    # Step 3: Run explain() on each query BEFORE creating any indexes
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("STEP 3: EXPLAIN BEFORE CREATING INDEXES (Baseline: Default _id Index Only)")
    print("=" * 90)

    results_before = {}
    for q in queries:
        cursor = col.find(q["filter"])
        if q["sort"]:
            cursor = cursor.sort(q["sort"])
        if q["limit"]:
            cursor = cursor.limit(q["limit"])

        plan = cursor.explain("executionStats")
        metrics = extract_explain_metrics(plan)
        results_before[q["id"]] = {"plan": plan, "metrics": metrics}

        print(f"\n  >> Query {q['id']}: {q['name']}")
        print(f"     Filter           : {q['filter']}")
        if q['sort']:
            print(f"     Sort             : {q['sort']}")
        print(f"     Winning Stage    : {metrics['stage']}")
        print(f"     Docs Examined    : {metrics['totalDocsExamined']:,}")
        print(f"     Keys Examined    : {metrics['totalKeysExamined']:,}")
        print(f"     Execution Time   : {metrics['executionTimeMillis']:.2f} ms")
        print(f"     Index Applied    : {metrics['indexName']}")

    # -------------------------------------------------------------------------
    # Step 4: Design & Create Indexes Covering All Five Queries
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("STEP 4: DESIGNING & CREATING OPTIMAL INDEXES (Applying ESR Guidelines)")
    print("=" * 90)

    index_specs = [
        {
            "name": "idx_category_price",
            "keys": [("category", 1), ("price", 1)],
            "supports": "Q1 (Equality: category -> Sort: price)",
            "rationale": "ESR Rule: Equality on 'category' filters subset, Sort on 'price' avoids in-memory sort stage."
        },
        {
            "name": "idx_price",
            "keys": [("price", 1)],
            "supports": "Q2 (Range: price $50 - $150)",
            "rationale": "Single field index allows efficient b-tree range bounds scan for price values."
        },
        {
            "name": "idx_tags",
            "keys": [("tags", 1)],
            "supports": "Q3 (Multikey Array: tags)",
            "rationale": "Multikey index indexes individual elements in the tags array for exact match."
        },
        {
            "name": "idx_name_text",
            "keys": [("name", "text")],
            "supports": "Q4 (Full-Text Search on name)",
            "rationale": "Text index creates stemmed, tokenized inverted index for rapid keyword matching."
        },
        {
            "name": "idx_cat_rating_stock",
            "keys": [("category", 1), ("rating", -1), ("stock", 1)],
            "supports": "Q5 (Equality: category -> Sort: rating -> Range: stock)",
            "rationale": "ESR Rule: Equality on category first, sort order on rating DESC, range filter on stock."
        }
    ]

    for idx in index_specs:
        col.create_index(idx["keys"], name=idx["name"])
        print(f"  [+] Created index: {idx['name']:<24} Keys: {str(idx['keys']):<42}")
        print(f"      Supports: {idx['supports']}")
        print(f"      Rationale: {idx['rationale']}\n")

    print("[*] Current active indexes on 'products' collection:")
    for idx_info in col.list_indexes():
        print(f"    - {idx_info['name']:<25} Key Pattern: {idx_info['key']}")

    # -------------------------------------------------------------------------
    # Step 5: Run explain() AFTER creating indexes and compare
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("STEP 5: EXPLAIN AFTER CREATING INDEXES & PERFORMANCE COMPARISON")
    print("=" * 90)

    results_after = {}
    for q in queries:
        cursor = col.find(q["filter"])
        if q["sort"]:
            cursor = cursor.sort(q["sort"])
        if q["limit"]:
            cursor = cursor.limit(q["limit"])

        plan = cursor.explain("executionStats")
        metrics = extract_explain_metrics(plan)
        results_after[q["id"]] = {"plan": plan, "metrics": metrics}

        print(f"\n  >> Query {q['id']}: {q['name']}")
        print(f"     Winning Stage    : {metrics['stage']}")
        print(f"     Docs Examined    : {metrics['totalDocsExamined']:,}")
        print(f"     Keys Examined    : {metrics['totalKeysExamined']:,}")
        print(f"     Execution Time   : {metrics['executionTimeMillis']:.2f} ms")
        print(f"     Index Applied    : {metrics['indexName']}")

    # -------------------------------------------------------------------------
    # Comparison Table
    # -------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print("PERFORMANCE COMPARISON SUMMARY: BEFORE VS AFTER INDEX CREATION")
    print("=" * 90)
    header = f"{'Query ID & Name':<32} | {'Stage (Before)':<14} | {'Stage (After)':<14} | {'Docs Examined':<20} | {'Improvement':<12}"
    print(header)
    print("-" * 100)

    summary_rows = []
    for q in queries:
        qid = q["id"]
        mb = results_before[qid]["metrics"]
        ma = results_after[qid]["metrics"]
        docs_before = mb["totalDocsExamined"]
        docs_after = ma["totalDocsExamined"]
        ratio = f"{docs_before / max(docs_after, 1):.1f}x fewer" if docs_after < docs_before else "Optimal"

        row_str = f"{qid + ': ' + q['name'][:27]:<32} | {mb['stage']:<14} | {ma['stage']:<14} | {f'{docs_before:,} -> {docs_after:,}':<20} | {ratio:<12}"
        print(row_str)
        summary_rows.append({
            "query_id": qid,
            "query_name": q["name"],
            "filter": q["filter"],
            "sort": q["sort"],
            "stage_before": mb["stage"],
            "stage_after": ma["stage"],
            "docs_examined_before": docs_before,
            "docs_examined_after": docs_after,
            "keys_examined_after": ma["totalKeysExamined"],
            "time_before_ms": mb["executionTimeMillis"],
            "time_after_ms": ma["executionTimeMillis"],
            "index_used": ma["indexName"],
            "improvement_ratio": ratio
        })

    # -------------------------------------------------------------------------
    # Export to JSON
    # -------------------------------------------------------------------------
    export_payload = {
        "metadata": {
            "lab": "Lab 6.1: Index Design for a Query Workload",
            "total_documents": total_docs,
            "database_name": "nosql_lab_6_1",
            "collection_name": "products",
            "execution_mode": "Live MongoDB Server" if not is_simulated else "Simulated Engine"
        },
        "sample_products": products[:5],
        "query_definitions": queries,
        "indexes_created": index_specs,
        "summary_comparison": summary_rows,
        "explain_before": {q["id"]: results_before[q["id"]]["metrics"] for q in queries},
        "explain_after": {q["id"]: results_after[q["id"]]["metrics"] for q in queries}
    }

    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_6_1.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 90)
    print(f"[+] Successfully exported lab results to:")
    print(f"    {json_path}")
    print("=" * 90)

if __name__ == "__main__":
    main()
