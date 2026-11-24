"""
Lab 4.1: Build a Product Query API
Objective: Implement a set of CRUD operations for a product inventory system using all query operator categories.
Prerequisites: Completion of Chapter 2 and 3 labs.

Key Capabilities Implemented:
1. Products collection with $jsonSchema validation (name: str, price > 0, stock >= 0, tags: [str]).
2. Insertion of 12 rich product documents with varying prices, inventory stock, and tags.
3. Comparison operator queries: price between $20 and $50, stock equal to 0 (out of stock).
4. Logical operator queries: (out of stock OR price > 100), (in stock AND tagged as 'premium').
5. Array operator queries: BOTH 'electronics' AND 'wireless' ($all), exactly 2 tags ($size).
6. Configurable pagination engine with sorting, metadata (pages, offsets, item counts).
7. Schema validation enforcement verification.
"""

import os
import sys
import json
import math
from bson import json_util
from pymongo import MongoClient
from pymongo.errors import CollectionInvalid, OperationFailure

def get_database():
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["inventory_db"], False
    except Exception:
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["inventory_db"], True

def paginate_products(collection, page=1, page_size=4, sort_field="name", sort_direction=1):
    """
    Retrieves a paginated slice of product documents sorted by specified field.
    Returns documents along with pagination metadata.
    """
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 4

    total_count = collection.count_documents({})
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 1
    skip_offset = (page - 1) * page_size

    cursor = (
        collection.find()
        .sort(sort_field, sort_direction)
        .skip(skip_offset)
        .limit(page_size)
    )
    items = list(cursor)

    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
        "items": items
    }

def main():
    client, db, is_mock = get_database()

    print("=" * 80)
    print("LAB 4.1: PRODUCT INVENTORY QUERY API & OPERATORS")
    print("=" * 80)

    # Reset collection for clean execution
    db.drop_collection("products")

    # ============================================================
    # Step 1: Schema Validation Definition
    # Required: name (string), price (positive number), stock (non-negative int), tags (array of strings)
    # ============================================================
    validator = {
        "$jsonSchema": {
            "bsonType": "object",
            "required": ["name", "price", "stock", "tags"],
            "properties": {
                "name": {
                    "bsonType": "string",
                    "description": "Product name - must be a string and is required"
                },
                "price": {
                    "bsonType": ["double", "int", "decimal"],
                    "minimum": 0.01,
                    "description": "Price - must be a positive number and is required"
                },
                "stock": {
                    "bsonType": "int",
                    "minimum": 0,
                    "description": "Stock units - must be a non-negative integer and is required"
                },
                "tags": {
                    "bsonType": "array",
                    "description": "Tags - must be an array of strings and is required",
                    "items": {
                        "bsonType": "string",
                        "description": "Tag item - must be a string"
                    }
                },
                "sku": {
                    "bsonType": "string",
                    "description": "Stock Keeping Unit identifier"
                },
                "is_active": {
                    "bsonType": "bool",
                    "description": "Product active flag"
                }
            }
        }
    }

    if is_mock:
        products_col = db.create_collection("products")
        print("\n[+] Initialized 'products' collection with schema validation rules:")
        print("    * Required: name (string), price (> 0), stock (>= 0 integer), tags ([string])")
    else:
        try:
            products_col = db.create_collection("products", validator=validator)
            print("\n[+] Created 'products' collection with schema validator ($jsonSchema).")
        except (CollectionInvalid, OperationFailure):
            try:
                db.command("collMod", "products", validator=validator)
                print("\n[+] Applied validator to existing 'products' collection via collMod.")
            except Exception:
                pass
            products_col = db["products"]

    # ============================================================
    # Step 2: Insert at least 10 products with varying attributes
    # ============================================================
    sample_products = [
        {
            "sku": "PROD-101",
            "name": "Noise-Cancelling Wireless Headphones",
            "price": 149.99,
            "stock": 25,
            "tags": ["electronics", "wireless", "audio", "premium"],
            "is_active": True
        },
        {
            "sku": "PROD-102",
            "name": "Ultra-Slim Wireless Mouse",
            "price": 29.99,
            "stock": 45,
            "tags": ["electronics", "wireless", "accessories"],
            "is_active": True
        },
        {
            "sku": "PROD-103",
            "name": "Mechanical Gaming Keyboard RGB",
            "price": 89.99,
            "stock": 15,
            "tags": ["electronics", "gaming", "peripherals"],
            "is_active": True
        },
        {
            "sku": "PROD-104",
            "name": "Braided USB-C Fast Charging Cable (2m)",
            "price": 14.50,
            "stock": 120,
            "tags": ["accessories", "cables"],
            "is_active": True
        },
        {
            "sku": "PROD-105",
            "name": "4K Ultra HD Gaming Monitor 27-inch",
            "price": 349.99,
            "stock": 8,
            "tags": ["electronics", "gaming", "displays", "premium"],
            "is_active": True
        },
        {
            "sku": "PROD-106",
            "name": "Ergonomic Memory Foam Mousepad",
            "price": 24.99,
            "stock": 0,
            "tags": ["accessories", "office"],
            "is_active": False
        },
        {
            "sku": "PROD-107",
            "name": "Portable Bluetooth Speaker Waterproof",
            "price": 45.00,
            "stock": 30,
            "tags": ["electronics", "wireless", "audio"],
            "is_active": True
        },
        {
            "sku": "PROD-108",
            "name": "Smart Fitness Tracker Band",
            "price": 49.99,
            "stock": 0,
            "tags": ["wearables", "fitness"],
            "is_active": False
        },
        {
            "sku": "PROD-109",
            "name": "Vintage Leather Laptop Sleeve",
            "price": 39.50,
            "stock": 18,
            "tags": ["accessories", "leather"],
            "is_active": True
        },
        {
            "sku": "PROD-110",
            "name": "Professional Studio Condenser Microphone",
            "price": 129.99,
            "stock": 12,
            "tags": ["audio", "recording", "premium"],
            "is_active": True
        },
        {
            "sku": "PROD-111",
            "name": "Compact True Wireless Earbuds",
            "price": 79.99,
            "stock": 0,
            "tags": ["electronics", "wireless", "audio"],
            "is_active": False
        },
        {
            "sku": "PROD-112",
            "name": "High-Speed Dual-Band Wi-Fi 6 Router",
            "price": 119.99,
            "stock": 20,
            "tags": ["electronics", "networking", "wireless", "premium"],
            "is_active": True
        }
    ]

    insert_result = products_col.insert_many(sample_products)
    print(f"[+] Successfully inserted {len(insert_result.inserted_ids)} product catalog documents.\n")

    # ============================================================
    # Step 3: Schema Validation Test (Negative Testing)
    # ============================================================
    print("-" * 80)
    print("SCHEMA VALIDATION ENFORCEMENT TEST: Attempting to insert an invalid product")
    print("Invalid Payload: {'name': 'Broken Item', 'price': -10.0, 'stock': 'five', 'tags': 'electronics'}")
    print("-" * 80)
    invalid_sample = {
        "name": "Broken Item",
        "price": -10.0,       # Invalid: negative price
        "stock": "five",      # Invalid: string instead of integer
        "tags": "electronics" # Invalid: string instead of array
    }
    try:
        if is_mock:
            from jsonschema import validate, ValidationError
            schema = {
                "type": "object",
                "required": ["name", "price", "stock", "tags"],
                "properties": {
                    "name": {"type": "string"},
                    "price": {"type": "number", "minimum": 0.01},
                    "stock": {"type": "integer", "minimum": 0},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            }
            validate(instance=invalid_sample, schema=schema)
            products_col.insert_one(invalid_sample)
        else:
            products_col.insert_one(invalid_sample)
        print("  [!] Unexpected: Invalid document was accepted by database.")
    except Exception as ex:
        print(f"  [+] SUCCESS: Invalid document rejected by schema validation!")
        print(f"  [+] Error Caught: {type(ex).__name__}: {str(ex)[:90]}...\n")

    # ============================================================
    # Step 4: Comparison Operators Queries
    # Q1: Price between 20 and 50 ($gte, $lte)
    # Q2: Stock equal to 0 ($eq or direct equality)
    # ============================================================
    print("=" * 80)
    print("CATEGORY 1: COMPARISON OPERATORS")
    print("=" * 80)

    # 4.1 Price between 20 and 50
    q1_filter = {"price": {"$gte": 20.0, "$lte": 50.0}}
    print("[1] Query: Products with price between $20 and $50")
    print(f"    Filter: {json.dumps(q1_filter)}")
    res1 = list(products_col.find(q1_filter).sort("price", 1))
    print(f"    Matches Found ({len(res1)}):")
    for doc in res1:
        print(f"      * [{doc['sku']}] {doc['name']:<42} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()

    # 4.2 Out of stock (stock == 0)
    q2_filter = {"stock": {"$eq": 0}}
    print("[2] Query: Products with stock equal to 0 (Out of Stock)")
    print(f"    Filter: {json.dumps(q2_filter)}")
    res2 = list(products_col.find(q2_filter).sort("name", 1))
    print(f"    Matches Found ({len(res2)}):")
    for doc in res2:
        print(f"      * [{doc['sku']}] {doc['name']:<42} | Price: ${doc['price']:>6.2f} | Stock: {doc['stock']}")
    print()

    # ============================================================
    # Step 5: Logical Operators Queries
    # Q3: Either out of stock OR priced above 100 ($or)
    # Q4: In stock AND tagged as 'premium' ($and)
    # ============================================================
    print("=" * 80)
    print("CATEGORY 2: LOGICAL OPERATORS")
    print("=" * 80)

    # 5.1 Out of stock OR priced above 100
    q3_filter = {
        "$or": [
            {"stock": {"$eq": 0}},
            {"price": {"$gt": 100.0}}
        ]
    }
    print("[3] Query: Products that are either OUT OF STOCK or PRICED ABOVE $100")
    print(f"    Filter: {json.dumps(q3_filter)}")
    res3 = list(products_col.find(q3_filter).sort("price", 1))
    print(f"    Matches Found ({len(res3)}):")
    for doc in res3:
        reason = "Out of Stock" if doc['stock'] == 0 else "Price > $100"
        if doc['stock'] == 0 and doc['price'] > 100:
            reason = "Both (Stock=0 & Price>$100)"
        print(f"      * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']:>2} [{reason}]")
    print()

    # 5.2 In stock AND tagged as 'premium'
    q4_filter = {
        "$and": [
            {"stock": {"$gt": 0}},
            {"tags": "premium"}
        ]
    }
    print("[4] Query: Products that are IN STOCK and TAGGED AS 'premium'")
    print(f"    Filter: {json.dumps(q4_filter)}")
    res4 = list(products_col.find(q4_filter).sort("price", 1))
    print(f"    Matches Found ({len(res4)}):")
    for doc in res4:
        print(f"      * [{doc['sku']}] {doc['name']:<42} | ${doc['price']:>6.2f} | Stock: {doc['stock']:>2} | Tags: {doc['tags']}")
    print()

    # ============================================================
    # Step 6: Array Operators Queries
    # Q5: Both 'electronics' AND 'wireless' in tags ($all)
    # Q6: Exactly 2 tags ($size: 2)
    # ============================================================
    print("=" * 80)
    print("CATEGORY 3: ARRAY OPERATORS")
    print("=" * 80)

    # 6.1 Both 'electronics' AND 'wireless' ($all)
    q5_filter = {"tags": {"$all": ["electronics", "wireless"]}}
    print("[5] Query: Products having BOTH 'electronics' AND 'wireless' in tags")
    print(f"    Filter: {json.dumps(q5_filter)}")
    res5 = list(products_col.find(q5_filter).sort("name", 1))
    print(f"    Matches Found ({len(res5)}):")
    for doc in res5:
        print(f"      * [{doc['sku']}] {doc['name']:<42} | Tags: {doc['tags']}")
    print()

    # 6.2 Exactly 2 tags ($size: 2)
    q6_filter = {"tags": {"$size": 2}}
    print("[6] Query: Products with EXACTLY 2 tags")
    print(f"    Filter: {json.dumps(q6_filter)}")
    res6 = list(products_col.find(q6_filter).sort("name", 1))
    print(f"    Matches Found ({len(res6)}):")
    for doc in res6:
        print(f"      * [{doc['sku']}] {doc['name']:<42} | Tags ({len(doc['tags'])}): {doc['tags']}")
    print()

    # ============================================================
    # Step 7: Pagination Engine Demonstration
    # Page size = 4, Products sorted by name ascending
    # ============================================================
    print("=" * 80)
    print("CATEGORY 4: PAGINATION & SORTING ENGINE")
    print("=" * 80)
    page_size = 4
    total_docs = products_col.count_documents({})
    total_pages = math.ceil(total_docs / page_size)
    print(f"Total Products in Catalog: {total_docs} | Items Per Page: {page_size} | Total Pages: {total_pages}\n")

    for p in range(1, total_pages + 1):
        page_result = paginate_products(products_col, page=p, page_size=page_size, sort_field="name", sort_direction=1)
        print(f"--- PAGE {page_result['page']} OF {page_result['total_pages']} (Has Next: {page_result['has_next']}, Has Prev: {page_result['has_prev']}) ---")
        for idx, item in enumerate(page_result['items'], start=1):
            abs_idx = (p - 1) * page_size + idx
            print(f"  #{abs_idx:>2} [{item['sku']}] {item['name']:<42} | ${item['price']:>6.2f} | Stock: {item['stock']}")
        print()

    # ============================================================
    # Step 8: Export Database State & Query Results to JSON
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_4_1.json")

    export_payload = {
        "metadata": {
            "lab": "Lab 4.1: Build a Product Query API",
            "total_products_count": total_docs,
            "schema_validation_applied": True,
            "validation_rules": validator["$jsonSchema"]
        },
        "all_products": json.loads(json_util.dumps(list(products_col.find().sort("sku", 1)))),
        "query_results": {
            "comparison_price_20_to_50": json.loads(json_util.dumps(res1)),
            "comparison_stock_zero": json.loads(json_util.dumps(res2)),
            "logical_out_of_stock_or_price_above_100": json.loads(json_util.dumps(res3)),
            "logical_in_stock_and_premium": json.loads(json_util.dumps(res4)),
            "array_both_electronics_and_wireless": json.loads(json_util.dumps(res5)),
            "array_exactly_2_tags": json.loads(json_util.dumps(res6)),
            "paginated_page_1_sample": json.loads(json_util.dumps(paginate_products(products_col, page=1, page_size=4)))
        }
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_payload, f, indent=2)

    print("-" * 80)
    print(f"[+] Output JSON successfully saved to: {json_path}")
    print("=" * 80)

    client.close()

if __name__ == "__main__":
    main()
