"""
Lab 4.2: Implement Upsert and Bulk Operations
Objective: Use upserts and bulk writes to handle conditional inserts and batch modifications.
Prerequisites: Completion of Lab 4.1.

Instructions Implemented:
1. Function that takes product SKU and price. If SKU exists, updates price.
   If not, inserts a new document with default values using update_one(upsert=True) with $set and $setOnInsert.
2. Bulk write operation that processes 5 simultaneous updates:
   - Increase stock by 10 for products A, B, and C ($inc)
   - Set is_active to False for products D and E ($set)
   - Use UpdateOne operations
   - Verify the bulk write result object (matched_count, modified_count, upserted_count, upserted_ids).
3. Export database states and bulk results to activity_4_2.json.
"""

import os
import sys
import json
from datetime import datetime, timezone
from bson import json_util
from pymongo import MongoClient, UpdateOne

def patch_mongomock_compatibility():
    """
    Ensures mongomock BulkOperationBuilder is fully compatible with PyMongo 4.x
    keyword arguments like sort, collation, etc.
    """
    try:
        import mongomock.collection
        _orig_add_update = mongomock.collection.BulkOperationBuilder.add_update
        def _patched_add_update(self, selector, doc, multi=False, upsert=False, collation=None, array_filters=None, hint=None, **kwargs):
            return _orig_add_update(self, selector, doc, multi=multi, upsert=upsert, collation=collation, array_filters=array_filters, hint=hint)
        mongomock.collection.BulkOperationBuilder.add_update = _patched_add_update
    except Exception:
        pass

def get_database():
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print("[*] Successfully connected to live MongoDB server at localhost:27017")
        return client, client["retail_inventory_db"], False
    except Exception:
        patch_mongomock_compatibility()
        import mongomock
        print("[*] Local MongoDB server offline. Running with mongomock in-memory database.")
        client = mongomock.MongoClient()
        return client, client["retail_inventory_db"], True

def upsert_product_price(collection, sku, new_price, default_name=None, default_stock=10, default_tags=None, default_is_active=True):
    """
    Conditionally updates price if SKU exists, or inserts a new document
    with default inventory values if the SKU is not found.
    Uses update_one with upsert=True, $set for price, and $setOnInsert for default fields.
    """
    filter_query = {"sku": sku}
    
    update_doc = {
        "$set": {
            "price": float(new_price)
        },
        "$setOnInsert": {
            "sku": sku,
            "name": default_name if default_name else f"Product {sku}",
            "stock": int(default_stock),
            "tags": default_tags if default_tags else ["general", "standard"],
            "is_active": default_is_active,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    }

    result = collection.update_one(filter_query, update_doc, upsert=True)
    return result

def main():
    client, db, is_mock = get_database()

    print("=" * 80)
    print("LAB 4.2: IMPLEMENT UPSERT AND BULK OPERATIONS")
    print("=" * 80)

    # Initialize collection
    products_col = db["products"]
    products_col.drop()

    # Initial catalog documents (Products A through E)
    initial_products = [
        {"sku": "PROD-A", "name": "Product A - Mechanical Keyboard", "price": 79.99, "stock": 15, "tags": ["accessories", "gaming"], "is_active": True},
        {"sku": "PROD-B", "name": "Product B - Ergonomic Mouse", "price": 29.99, "stock": 30, "tags": ["accessories", "office"], "is_active": True},
        {"sku": "PROD-C", "name": "Product C - Gaming Headset", "price": 59.99, "stock": 8, "tags": ["audio", "gaming"], "is_active": True},
        {"sku": "PROD-D", "name": "Product D - Legacy Webcam 720p", "price": 19.99, "stock": 5, "tags": ["video", "legacy"], "is_active": True},
        {"sku": "PROD-E", "name": "Product E - Discontinued USB 16GB", "price": 9.99, "stock": 2, "tags": ["storage", "legacy"], "is_active": True}
    ]

    products_col.insert_many(initial_products)
    print(f"[+] Initialized 'products' collection with {len(initial_products)} items (PROD-A through PROD-E).\n")

    # ============================================================
    # Task 1: Conditional Upsert Operations
    # ============================================================
    print("=" * 80)
    print("TASK 1: CONDITIONAL UPSERT VIA update_one(upsert=True)")
    print("=" * 80)

    # Case 1A: Existing SKU -> Should UPDATE price, NOT insert
    target_sku_existing = "PROD-A"
    new_price_existing = 84.99
    print(f"[1A] Testing Upsert on EXISTING product SKU: '{target_sku_existing}'")
    before_doc = products_col.find_one({"sku": target_sku_existing})
    print(f"     Before Update -> Price: ${before_doc['price']:.2f} | Stock: {before_doc['stock']} | Name: '{before_doc['name']}'")

    res_1a = upsert_product_price(products_col, target_sku_existing, new_price_existing)
    after_doc = products_col.find_one({"sku": target_sku_existing})

    print(f"     Execution Result:")
    print(f"       * matched_count : {res_1a.matched_count} (Product document was found)")
    print(f"       * modified_count: {res_1a.modified_count} (Price field modified)")
    print(f"       * upserted_id   : {res_1a.upserted_id} (No new insert performed)")
    print(f"     After Update  -> Price: ${after_doc['price']:.2f} | Stock: {after_doc['stock']} | Name: '{after_doc['name']}'\n")

    # Case 1B: Non-Existing SKU -> Should INSERT new document with defaults
    target_sku_new = "PROD-X99"
    new_price_new = 49.99
    print(f"[1B] Testing Upsert on NON-EXISTENT product SKU: '{target_sku_new}'")
    res_1b = upsert_product_price(
        products_col,
        sku=target_sku_new,
        new_price=new_price_new,
        default_name="Product X99 - Smart Hub",
        default_stock=25,
        default_tags=["smart-home", "iot"]
    )
    inserted_doc = products_col.find_one({"sku": target_sku_new})

    print(f"     Execution Result:")
    print(f"       * matched_count : {res_1b.matched_count} (No existing document matched)")
    print(f"       * modified_count: {res_1b.modified_count}")
    print(f"       * upserted_id   : {res_1b.upserted_id} (New document generated)")
    print(f"     New Document  -> SKU: {inserted_doc['sku']} | Name: '{inserted_doc['name']}'")
    print(f"                      Price: ${inserted_doc['price']:.2f} | Stock: {inserted_doc['stock']} | Tags: {inserted_doc['tags']}\n")

    # ============================================================
    # Task 2: Bulk Write with 5 Simultaneous Updates
    # - Increase stock by 10 for products A, B, and C ($inc)
    # - Set is_active to False for products D and E ($set)
    # ============================================================
    print("=" * 80)
    print("TASK 2: BATCH BULK WRITE OPERATIONS (5 SIMULTANEOUS UPDATES)")
    print("=" * 80)

    print("Initial State of Target Products:")
    for target in ["PROD-A", "PROD-B", "PROD-C", "PROD-D", "PROD-E"]:
        d = products_col.find_one({"sku": target})
        print(f"  * [{d['sku']}] {d['name']:<38} | Stock: {d['stock']:>2} | Active: {d['is_active']}")
    print()

    # Define bulk operations list using UpdateOne
    bulk_operations = [
        # 1. Increase stock by 10 for Product A
        UpdateOne(
            filter={"sku": "PROD-A"},
            update={"$inc": {"stock": 10}}
        ),
        # 2. Increase stock by 10 for Product B
        UpdateOne(
            filter={"sku": "PROD-B"},
            update={"$inc": {"stock": 10}}
        ),
        # 3. Increase stock by 10 for Product C
        UpdateOne(
            filter={"sku": "PROD-C"},
            update={"$inc": {"stock": 10}}
        ),
        # 4. Set is_active to False for Product D
        UpdateOne(
            filter={"sku": "PROD-D"},
            update={"$set": {"is_active": False}}
        ),
        # 5. Set is_active to False for Product E
        UpdateOne(
            filter={"sku": "PROD-E"},
            update={"$set": {"is_active": False}}
        )
    ]

    print(f"[+] Executing bulk_write with {len(bulk_operations)} UpdateOne operations...")
    bulk_result = products_col.bulk_write(bulk_operations)

    print("\n[+] Bulk Write Execution Result Object Verification:")
    print(f"    * matched_count  : {bulk_result.matched_count} (All 5 target products matched)")
    print(f"    * modified_count : {bulk_result.modified_count} (All 5 target products modified)")
    print(f"    * upserted_count : {bulk_result.upserted_count} (0 new documents upserted)")
    print(f"    * upserted_ids   : {bulk_result.upserted_ids}")
    print(f"    * acknowledged   : {bulk_result.acknowledged}\n")

    print("Final State of Target Products After Bulk Write:")
    for target in ["PROD-A", "PROD-B", "PROD-C", "PROD-D", "PROD-E"]:
        d = products_col.find_one({"sku": target})
        status_note = ""
        if target in ["PROD-A", "PROD-B", "PROD-C"]:
            status_note = "(Stock increased by +10)"
        elif target in ["PROD-D", "PROD-E"]:
            status_note = "(is_active changed to False)"
        print(f"  * [{d['sku']}] {d['name']:<38} | Stock: {d['stock']:>2} | Active: {str(d['is_active']):<5} {status_note}")
    print()

    # ============================================================
    # Export Results to JSON File
    # ============================================================
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, "activity_4_2.json")

    all_products_final = list(products_col.find().sort("sku", 1))

    export_data = {
        "lab": "Lab 4.2: Implement Upsert and Bulk Operations",
        "task_1_upsert_verification": {
            "case_1a_existing_sku": {
                "sku": target_sku_existing,
                "matched_count": res_1a.matched_count,
                "modified_count": res_1a.modified_count,
                "upserted_id": str(res_1a.upserted_id) if res_1a.upserted_id else None,
                "updated_document": json.loads(json_util.dumps(after_doc))
            },
            "case_1b_new_sku": {
                "sku": target_sku_new,
                "matched_count": res_1b.matched_count,
                "modified_count": res_1b.modified_count,
                "upserted_id": str(res_1b.upserted_id),
                "inserted_document": json.loads(json_util.dumps(inserted_doc))
            }
        },
        "task_2_bulk_write_verification": {
            "operations_count": len(bulk_operations),
            "matched_count": bulk_result.matched_count,
            "modified_count": bulk_result.modified_count,
            "upserted_count": bulk_result.upserted_count,
            "upserted_ids": bulk_result.upserted_ids,
            "acknowledged": bulk_result.acknowledged
        },
        "all_products_after_operations": json.loads(json_util.dumps(all_products_final))
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2)

    print("-" * 80)
    print(f"[+] Output JSON successfully saved to: {json_path}")
    print("=" * 80)

    client.close()

if __name__ == "__main__":
    main()
