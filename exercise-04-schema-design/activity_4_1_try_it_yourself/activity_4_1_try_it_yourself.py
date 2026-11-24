"""
Activity for 4.1: Try It Yourself
Objective: Add a text search capability using the $regex operator to find products whose
name contains a search string (case-insensitive).

Features Implemented:
1. Reusable text search engine supporting:
   - Case-insensitive substring matching ($regex with $options: 'i')
   - Anchored prefix matching (starts with ^)
   - Anchored suffix matching (ends with $)
   - Alternation / Multi-keyword OR search (pattern1|pattern2)
   - Compound searching: Regex text search combined with price and inventory stock filters
2. Benchmark analysis and comparison between $regex queries and MongoDB $text index search.
3. Export search test results to activity_4_1_try_it_yourself.json.
"""

import os
import sys
import json
import re
from bson import json_util
from pymongo import MongoClient

def get_database():
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["inventory_search_db"], False
    except Exception:
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["inventory_search_db"], True

def search_products(collection, query_str, search_mode="contains", case_insensitive=True, additional_filters=None):
    """
    Executes a flexible text search query using the $regex operator.
    
    Modes:
      - 'contains': matches if string appears anywhere in name
      - 'starts_with': matches prefix anchored at start (^)
      - 'ends_with': matches suffix anchored at end ($)
      - 'exact': exact full match (^pattern$)
      - 'raw': uses custom regex expression as-is (e.g., alternation 'mouse|keyboard')
    """
    escaped_query = re.escape(query_str) if search_mode != "raw" else query_str

    if search_mode == "contains":
        pattern = escaped_query
    elif search_mode == "starts_with":
        pattern = f"^{escaped_query}"
    elif search_mode == "ends_with":
        pattern = f"{escaped_query}$"
    elif search_mode == "exact":
        pattern = f"^{escaped_query}$"
    elif search_mode == "raw":
        pattern = query_str
    else:
        pattern = escaped_query

    regex_clause = {"$regex": pattern}
    if case_insensitive:
        regex_clause["$options"] = "i"

    mongo_query = {"name": regex_clause}
    if additional_filters:
        mongo_query.update(additional_filters)

    cursor = collection.find(mongo_query).sort("price", 1)
    results = list(cursor)
    return pattern, mongo_query, results

def main():
    client, db, is_mock = get_database()

    print("=" * 80)
    print("ACTIVITY 4.1: TRY IT YOURSELF - TEXT SEARCH ENGINE USING $regex")
    print("=" * 80)

    # Initialize collection
    products_col = db["products"]
    products_col.drop()

    catalog_data = [
        {"sku": "SKU-201", "name": "Noise-Cancelling Wireless Headphones", "price": 149.99, "stock": 25, "tags": ["electronics", "wireless", "audio"]},
        {"sku": "SKU-202", "name": "Ultra-Slim Wireless Mouse", "price": 29.99, "stock": 45, "tags": ["accessories", "wireless"]},
        {"sku": "SKU-203", "name": "Mechanical Gaming Keyboard RGB", "price": 89.99, "stock": 15, "tags": ["gaming", "peripherals"]},
        {"sku": "SKU-204", "name": "Braided USB-C Fast Charging Cable", "price": 14.50, "stock": 120, "tags": ["cables", "accessories"]},
        {"sku": "SKU-205", "name": "4K Ultra HD Gaming Monitor", "price": 349.99, "stock": 8, "tags": ["displays", "gaming"]},
        {"sku": "SKU-206", "name": "Ergonomic Memory Foam Mousepad", "price": 24.99, "stock": 0, "tags": ["office", "accessories"]},
        {"sku": "SKU-207", "name": "Portable Bluetooth Speaker", "price": 45.00, "stock": 30, "tags": ["wireless", "audio"]},
        {"sku": "SKU-208", "name": "Smart Fitness Tracker Band", "price": 49.99, "stock": 0, "tags": ["fitness", "wearables"]},
        {"sku": "SKU-209", "name": "Leather Laptop Sleeve Case", "price": 39.50, "stock": 18, "tags": ["leather", "accessories"]},
        {"sku": "SKU-210", "name": "Professional Studio Microphone", "price": 129.99, "stock": 12, "tags": ["audio", "recording"]},
        {"sku": "SKU-211", "name": "Compact True Wireless Earbuds", "price": 79.99, "stock": 0, "tags": ["wireless", "audio"]},
        {"sku": "SKU-212", "name": "High-Speed Wi-Fi 6 Router", "price": 119.99, "stock": 20, "tags": ["networking", "wireless"]}
    ]

    products_col.insert_many(catalog_data)
    print(f"[+] Populated product catalog with {len(catalog_data)} items for search indexing.\n")

    # Dictionary to collect results for export
    test_results_export = {}

    # ============================================================
    # Test Case 1: Case-Insensitive Substring Search for 'wireless'
    # ============================================================
    print("-" * 80)
    print("TEST CASE 1: Case-Insensitive Substring Search ('wireless')")
    print("Objective: Find all products containing 'wireless' in any letter case")
    print("-" * 80)
    pat1, q1, r1 = search_products(products_col, "wireless", search_mode="contains", case_insensitive=True)
    print(f"  Regex Pattern : /{pat1}/i")
    print(f"  MongoDB Filter: {json.dumps(q1)}")
    print(f"  Matches Found : {len(r1)}")
    for doc in r1:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_1_substring_wireless"] = {"query": q1, "results": json.loads(json_util.dumps(r1))}

    # ============================================================
    # Test Case 2: Substring Search for 'pro' (Testing partial stems)
    # ============================================================
    print("-" * 80)
    print("TEST CASE 2: Substring Search for 'pro' (Matches 'Professional', etc.)")
    print("-" * 80)
    pat2, q2, r2 = search_products(products_col, "pro", search_mode="contains", case_insensitive=True)
    print(f"  Regex Pattern : /{pat2}/i")
    print(f"  MongoDB Filter: {json.dumps(q2)}")
    print(f"  Matches Found : {len(r2)}")
    for doc in r2:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_2_substring_pro"] = {"query": q2, "results": json.loads(json_util.dumps(r2))}

    # ============================================================
    # Test Case 3: Prefix Anchored Search (Starts With '^Smart')
    # ============================================================
    print("-" * 80)
    print("TEST CASE 3: Prefix Search (Products starting with 'Smart')")
    print("Efficiency Note: Anchored prefix regexes can leverage index bounds in MongoDB")
    print("-" * 80)
    pat3, q3, r3 = search_products(products_col, "Smart", search_mode="starts_with", case_insensitive=True)
    print(f"  Regex Pattern : /{pat3}/i")
    print(f"  MongoDB Filter: {json.dumps(q3)}")
    print(f"  Matches Found : {len(r3)}")
    for doc in r3:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_3_prefix_smart"] = {"query": q3, "results": json.loads(json_util.dumps(r3))}

    # ============================================================
    # Test Case 4: Suffix Anchored Search (Ends With 'Router$')
    # ============================================================
    print("-" * 80)
    print("TEST CASE 4: Suffix Search (Products ending with 'Router')")
    print("-" * 80)
    pat4, q4, r4 = search_products(products_col, "Router", search_mode="ends_with", case_insensitive=True)
    print(f"  Regex Pattern : /{pat4}/i")
    print(f"  MongoDB Filter: {json.dumps(q4)}")
    print(f"  Matches Found : {len(r4)}")
    for doc in r4:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_4_suffix_router"] = {"query": q4, "results": json.loads(json_util.dumps(r4))}

    # ============================================================
    # Test Case 5: Multi-Keyword Disjunction Search ('mouse|keyboard')
    # ============================================================
    print("-" * 80)
    print("TEST CASE 5: Multi-Keyword Regex Alternation ('mouse|keyboard')")
    print("-" * 80)
    pat5, q5, r5 = search_products(products_col, "mouse|keyboard", search_mode="raw", case_insensitive=True)
    print(f"  Regex Pattern : /{pat5}/i")
    print(f"  MongoDB Filter: {json.dumps(q5)}")
    print(f"  Matches Found : {len(r5)}")
    for doc in r5:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_5_alternation_mouse_keyboard"] = {"query": q5, "results": json.loads(json_util.dumps(r5))}

    # ============================================================
    # Test Case 6: Compound Query (Regex Search + Filter Conditions)
    # Search for 'wireless' AND in-stock (stock > 0) AND price <= 100
    # ============================================================
    print("-" * 80)
    print("TEST CASE 6: Compound Query (Regex + Stock Filter + Price Filter)")
    print("Criteria: Name contains 'wireless', Stock > 0, Price <= $100")
    print("-" * 80)
    filters = {"stock": {"$gt": 0}, "price": {"$lte": 100.0}}
    pat6, q6, r6 = search_products(products_col, "wireless", search_mode="contains", case_insensitive=True, additional_filters=filters)
    print(f"  Regex Pattern : /{pat6}/i")
    print(f"  MongoDB Filter: {json.dumps(q6)}")
    print(f"  Matches Found : {len(r6)}")
    for doc in r6:
        print(f"    * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()
    test_results_export["test_case_6_compound_query"] = {"query": q6, "results": json.loads(json_util.dumps(r6))}

    # ============================================================
    # Technical Architectural Comparison: $regex vs $text Index
    # ============================================================
    print("=" * 80)
    print("TECHNICAL COMPARISON: MongoDB $regex Operator vs $text Full-Text Index")
    print("=" * 80)
    comparison_text = """
+------------------------+---------------------------------------+---------------------------------------+
| FEATURE / CRITERION    | $regex OPERATOR SEARCH                | $text INDEX SEARCH (FULL-TEXT)        |
+------------------------+---------------------------------------+---------------------------------------+
| Matching Type          | Pattern & substring matching          | Word tokenization & stemming          |
| Partial Word / Stems   | Supported anywhere in string          | Exact word roots only (no substrings) |
| Index Utilization      | Only prefix searches (^abc) use index | Highly optimized dedicated text index |
| Unanchored Performance | Forces O(N) Collection Scan           | Fast O(log N) inverted index lookups  |
| Relevance Scoring      | None (Boolean match only)             | Supported via textScore metadata      |
| Language Stopwords     | Not filtered                          | Automatically removes common words    |
| Best Use Case          | Product SKUs, codes, partial names    | Long descriptions, articles, reviews  |
+------------------------+---------------------------------------+---------------------------------------+
"""
    print(comparison_text.strip())
    print()

    # ============================================================
    # Export Results to JSON File
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_4_1_try_it_yourself.json")

    export_data = {
        "lab": "Activity 4.1: Try It Yourself - Text Search with $regex",
        "total_catalog_size": len(catalog_data),
        "test_cases": test_results_export,
        "regex_vs_text_comparison": {
            "regex_advantages": [
                "Supports arbitrary substring and character-level matching anywhere in text",
                "Supports exact prefix/suffix boundary anchoring (^ and $)",
                "No need to create or maintain heavy text indexes for small/medium collections",
                "Case-insensitive option 'i' works across all character sets without language stemming"
            ],
            "regex_tradeoffs": [
                "Unanchored queries (.*pattern.*) cannot use standard B-tree index, scanning entire collection",
                "CPU-intensive on massive multi-gigabyte datasets without prefix anchoring",
                "Lacks relevance scoring and linguistic tokenization"
            ]
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    print("-" * 80)
    print(f"[+] Output JSON successfully saved to: {json_path}")
    print("=" * 80)

    client.close()

if __name__ == "__main__":
    main()
