"""
Lab 5.2 - Try It Yourself: $lookup with Pipeline Sub-Expression
Objective: Implement a $lookup with a pipeline sub-expression (available in MongoDB 3.6+)
           to filter the joined documents on the foreign side before they are returned.
"""

import os
import sys
import copy
import json
from bson import json_util
from pymongo import MongoClient

def get_database(db_name="pipeline_lookup_db"):
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    Includes custom pipeline handler so that $lookup with 'let' and 'pipeline'
    operates identically whether online or offline.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print(f"[*] Successfully connected to live MongoDB server at localhost:27017 ({db_name})")
        return client, client[db_name], False
    except Exception:
        import mongomock
        import mongomock.aggregate as ma
        from mongomock import helpers

        orig_handle_lookup = ma._PIPELINE_HANDLERS.get('$lookup')

        def custom_handle_lookup(in_collection, database, options):
            if 'pipeline' in options:
                foreign_name = options['from']
                local_name = options['as']
                let_spec = options.get('let', {})
                pipeline_template = options['pipeline']
                foreign_collection = database.get_collection(foreign_name)
                
                for doc in in_collection:
                    # Resolve let variables from parent document
                    let_vals = {}
                    for var_name, field_expr in let_spec.items():
                        if isinstance(field_expr, str) and field_expr.startswith('$'):
                            field_name = field_expr[1:]
                            try:
                                let_vals[var_name] = helpers.get_value_by_dot(doc, field_name)
                            except KeyError:
                                let_vals[var_name] = None
                        else:
                            let_vals[var_name] = field_expr
                    
                    # Recursively substitute $$var references inside foreign pipeline
                    def substitute_vars(obj):
                        if isinstance(obj, dict):
                            return {k: substitute_vars(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [substitute_vars(item) for item in obj]
                        elif isinstance(obj, str) and obj.startswith("$$"):
                            var = obj[2:]
                            if var in let_vals:
                                return let_vals[var]
                            return obj
                        return obj
                    
                    resolved_pipeline = substitute_vars(copy.deepcopy(pipeline_template))
                    matches = list(foreign_collection.aggregate(resolved_pipeline))
                    doc[local_name] = matches
                return in_collection

            if orig_handle_lookup:
                return orig_handle_lookup(in_collection, database, options)
            raise NotImplementedError("Lookup handler unavailable")

        ma._PIPELINE_HANDLERS['$lookup'] = custom_handle_lookup

        print(f"[*] Local MongoDB server offline. Running with mongomock in-memory database ({db_name}).")
        client = mongomock.MongoClient()
        return client, client[db_name], True

# Product Catalog
PRODUCTS_DATA = [
    {"product_id": "P-101", "name": "Ultra 4K Monitor 27-inch", "category": "Electronics", "base_price": 350.00, "is_active": True},
    {"product_id": "P-102", "name": "Wireless Mechanical Keyboard", "category": "Electronics", "base_price": 95.00, "is_active": True},
    {"product_id": "P-103", "name": "Ergonomic Vertical Mouse", "category": "Accessories", "base_price": 45.00, "is_active": True},
    {"product_id": "P-104", "name": "Active Noise-Cancelling Headphones", "category": "Audio", "base_price": 210.00, "is_active": True},
    {"product_id": "P-105", "name": "Aluminum USB-C Dock 10-in-1", "category": "Accessories", "base_price": 65.00, "is_active": True},
    {"product_id": "P-106", "name": "High-Speed NVMe 2TB SSD", "category": "Storage", "base_price": 160.00, "is_active": True},
    {"product_id": "P-107", "name": "FHD Auto-Focus Webcam", "category": "Video", "base_price": 75.00, "is_active": True},
    {"product_id": "P-108", "name": "Smart Motorized Standing Desk", "category": "Furniture", "base_price": 480.00, "is_active": True},
    {"product_id": "P-109", "name": "Ergonomic Mesh Executive Chair", "category": "Furniture", "base_price": 290.00, "is_active": True},
    {"product_id": "P-110", "name": "Studio Condenser Broadcast Mic", "category": "Audio", "base_price": 140.00, "is_active": True}
]

# Orders Data
ORDERS_DATA = [
    {"order_id": "ORD-501", "customer_name": "Aarav Sharma", "product_id": "P-101", "quantity": 1, "order_date": "2024-02-01", "status": "completed"},
    {"order_id": "ORD-502", "customer_name": "Priya Patel", "product_id": "P-102", "quantity": 2, "order_date": "2024-02-03", "status": "completed"},
    {"order_id": "ORD-503", "customer_name": "Rohan Mehta", "product_id": "P-103", "quantity": 1, "order_date": "2024-02-07", "status": "completed"},
    {"order_id": "ORD-504", "customer_name": "Ananya Iyer", "product_id": "P-104", "quantity": 1, "order_date": "2024-02-12", "status": "shipped"},
    {"order_id": "ORD-505", "customer_name": "Vikram Singh", "product_id": "P-105", "quantity": 3, "order_date": "2024-02-15", "status": "completed"},
    {"order_id": "ORD-506", "customer_name": "Aarav Sharma", "product_id": "P-106", "quantity": 2, "order_date": "2024-02-20", "status": "completed"},
    {"order_id": "ORD-507", "customer_name": "Neha Verma", "product_id": "P-107", "quantity": 1, "order_date": "2024-02-25", "status": "completed"},
    {"order_id": "ORD-508", "customer_name": "Siddharth Rao", "product_id": "P-101", "quantity": 2, "order_date": "2024-03-02", "status": "completed"},
    {"order_id": "ORD-509", "customer_name": "Priya Patel", "product_id": "P-105", "quantity": 1, "order_date": "2024-03-06", "status": "pending"},
    {"order_id": "ORD-510", "customer_name": "Rohan Mehta", "product_id": "P-102", "quantity": 1, "order_date": "2024-03-10", "status": "completed"},
    {"order_id": "ORD-511", "customer_name": "Ananya Iyer", "product_id": "P-104", "quantity": 2, "order_date": "2024-03-15", "status": "completed"},
    {"order_id": "ORD-512", "customer_name": "Vikram Singh", "product_id": "P-106", "quantity": 1, "order_date": "2024-03-19", "status": "completed"},
    {"order_id": "ORD-513", "customer_name": "Neha Verma", "product_id": "P-103", "quantity": 2, "order_date": "2024-03-24", "status": "cancelled"},
    {"order_id": "ORD-514", "customer_name": "Aarav Sharma", "product_id": "P-107", "quantity": 1, "order_date": "2024-03-28", "status": "completed"},
    {"order_id": "ORD-515", "customer_name": "Siddharth Rao", "product_id": "P-102", "quantity": 3, "order_date": "2024-04-02", "status": "completed"}
]

def main():
    print("=" * 90)
    print("LAB 5.2 - TRY IT YOURSELF: $lookup WITH PIPELINE SUB-EXPRESSION")
    print("=" * 90)

    client, db, is_mock = get_database("pipeline_lookup_db")

    # Step 1: Re-seed collections
    db.drop_collection("products")
    db.drop_collection("orders")

    products_col = db["products"]
    orders_col = db["orders"]

    products_col.insert_many(PRODUCTS_DATA)
    orders_col.insert_many(ORDERS_DATA)

    print(f"\n[+] Seeded 'products' ({products_col.count_documents({})} items) and 'orders' ({orders_col.count_documents({})} records).")

    # -------------------------------------------------------------------------
    # PIPELINE 1: Foreign Side Filtering in $lookup
    # Join orders with products, but on the foreign collection side filter
    # ONLY products in 'Electronics' category with base_price >= $80.
    # Non-qualifying products are excluded from the joined array BEFORE return!
    # -------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("PIPELINE 1: FOREIGN-SIDE FILTERING ($lookup + 'let' + 'pipeline' SUB-EXPRESSION)")
    print("Predicate: Join ONLY if foreign product matches category == 'Electronics' AND price >= $80")
    print("-" * 90)

    pipeline_subexpr_orders = [
        {
            "$lookup": {
                "from": "products",
                "let": {"order_pid": "$product_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$product_id", "$$order_pid"]},
                                    {"$eq": ["$category", "Electronics"]},
                                    {"$gte": ["$base_price", 80.0]}
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "product_id": 1,
                            "name": 1,
                            "category": 1,
                            "base_price": 1
                        }
                    }
                ],
                "as": "electronic_product_match"
            }
        },
        {
            "$project": {
                "_id": 0,
                "order_id": 1,
                "order_date": 1,
                "customer_name": 1,
                "product_id": 1,
                "quantity": 1,
                "status": 1,
                "match_count": {"$size": "$electronic_product_match"},
                "electronic_product_match": 1
            }
        },
        {"$sort": {"order_id": 1}}
    ]

    orders_with_foreign_filter = list(orders_col.aggregate(pipeline_subexpr_orders))

    print(f"{'Order ID':<9} | {'Customer':<15} | {'PID':<6} | {'Status':<10} | {'Foreign Match':<16} | {'Matched Product Details':<38}")
    print("-" * 105)
    for r in orders_with_foreign_filter:
        if r["match_count"] > 0:
            pinfo = r["electronic_product_match"][0]
            match_desc = f"{pinfo['name']} (${pinfo['base_price']:,.2f})"
            match_status = "[YES] Matched"
        else:
            match_desc = "(Foreign Filter Filtered Out - Non-Electronic / Out of Spec)"
            match_status = "[--] Empty Array"

        print(f"{r['order_id']:<9} | {r['customer_name']:<15} | {r['product_id']:<6} | {r['status']:<10} | {match_status:<16} | {match_desc:<38}")

    # -------------------------------------------------------------------------
    # PIPELINE 2: Reverse Foreign Filter
    # Starting from PRODUCTS: Join with ORDERS, but filter foreign orders to
    # ONLY include completed high-volume orders (quantity >= 2).
    # -------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("PIPELINE 2: CATALOG INVENTORY AUDIT WITH FOREIGN ORDER FILTERING")
    print("Predicate: Join products with ORDERS filtered on foreign side by: status == 'completed' AND qty >= 2")
    print("-" * 90)

    pipeline_subexpr_products = [
        {
            "$lookup": {
                "from": "orders",
                "let": {"pid": "$product_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$product_id", "$$pid"]},
                                    {"$eq": ["$status", "completed"]},
                                    {"$gte": ["$quantity", 2]}
                                ]
                            }
                        }
                    },
                    {
                        "$project": {
                            "_id": 0,
                            "order_id": 1,
                            "customer_name": 1,
                            "quantity": 1,
                            "order_date": 1
                        }
                    }
                ],
                "as": "high_volume_completed_orders"
            }
        },
        {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "name": 1,
                "category": 1,
                "base_price": 1,
                "bulk_orders_count": {"$size": "$high_volume_completed_orders"},
                "high_volume_completed_orders": 1
            }
        },
        {"$sort": {"product_id": 1}}
    ]

    products_with_foreign_filter = list(products_col.aggregate(pipeline_subexpr_products))

    print(f"{'Product ID':<11} | {'Product Name':<34} | {'Category':<13} | {'Price ($)':<10} | {'Bulk Orders':<12} | {'Sample Order IDs'}")
    print("-" * 105)
    for p in products_with_foreign_filter:
        sample_ids = ", ".join(o["order_id"] + f" (x{o['quantity']})" for o in p["high_volume_completed_orders"]) if p["bulk_orders_count"] > 0 else "None"
        print(f"{p['product_id']:<11} | {p['name']:<34} | {p['category']:<13} | ${p['base_price']:>8,.2f} | {p['bulk_orders_count']:>11} | {sample_ids}")

    # -------------------------------------------------------------------------
    # Export full dataset & sub-expression results to JSON
    # -------------------------------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_5_2_try_it_yourself.json")

    export_payload = {
        "metadata": {
            "activity": "Lab 5.2 - Try It Yourself: $lookup with Pipeline Sub-Expression",
            "objective": "Filter joined documents on the foreign side using 'let' and 'pipeline'",
            "mongodb_version_requirement": "3.6+"
        },
        "pipeline_1_foreign_filtered_orders": orders_with_foreign_filter,
        "pipeline_2_foreign_filtered_products": products_with_foreign_filter
    }

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 90)
    print(f"[+] Successfully exported pipeline sub-expression results to:\n    {json_path}")
    print("=" * 90)

if __name__ == "__main__":
    main()
