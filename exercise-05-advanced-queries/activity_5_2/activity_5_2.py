"""
Lab 5.2: Join Data with $lookup
Objective: Use $lookup to perform cross-collection joins and analyze the results.
Prerequisites: Completion of Lab 5.1.

Instructions:
1. Create a products collection with name, category, and base_price.
   Create an orders collection that references products by product_id (not embedding).
   Insert related data.
2. Write a $lookup pipeline that joins orders with products to produce a result showing:
   order date, product name, quantity, and computed total (quantity * base_price).
3. Write a pipeline that finds products that have never been ordered
   (left outer join using $lookup with a follow-up $match for empty join results).
"""

import os
import sys
import json
from bson import json_util
from pymongo import MongoClient

def get_database(db_name="store_joins_db"):
    """
    Connect to local MongoDB instance if running;
    otherwise fallback to mongomock for seamless offline execution.
    """
    try:
        client = MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=1000)
        client.admin.command("ping")
        print(f"[*] Successfully connected to live MongoDB server at localhost:27017 ({db_name})")
        return client, client[db_name], False
    except Exception:
        import mongomock
        print(f"[*] Local MongoDB server offline. Running with mongomock in-memory database ({db_name}).")
        client = mongomock.MongoClient()
        return client, client[db_name], True

# 10 Products across 5 categories (3 products are intentionally un-ordered for left-join verification)
PRODUCTS_DATA = [
    {"product_id": "P-101", "name": "Ultra 4K Monitor 27-inch", "category": "Electronics", "base_price": 350.00},
    {"product_id": "P-102", "name": "Wireless Mechanical Keyboard", "category": "Electronics", "base_price": 95.00},
    {"product_id": "P-103", "name": "Ergonomic Vertical Mouse", "category": "Accessories", "base_price": 45.00},
    {"product_id": "P-104", "name": "Active Noise-Cancelling Headphones", "category": "Audio", "base_price": 210.00},
    {"product_id": "P-105", "name": "Aluminum USB-C Dock 10-in-1", "category": "Accessories", "base_price": 65.00},
    {"product_id": "P-106", "name": "High-Speed NVMe 2TB SSD", "category": "Storage", "base_price": 160.00},
    {"product_id": "P-107", "name": "FHD Auto-Focus Webcam", "category": "Video", "base_price": 75.00},
    {"product_id": "P-108", "name": "Smart Motorized Standing Desk", "category": "Furniture", "base_price": 480.00},     # Unordered
    {"product_id": "P-109", "name": "Ergonomic Mesh Executive Chair", "category": "Furniture", "base_price": 290.00},   # Unordered
    {"product_id": "P-110", "name": "Studio Condenser Broadcast Mic", "category": "Audio", "base_price": 140.00}       # Unordered
]

# 15 Orders referencing products P-101 through P-107
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
    print("LAB 5.2: JOIN DATA WITH $lookup IN MONGODB")
    print("=" * 90)

    client, db, is_mock = get_database("store_joins_db")

    # Step 1: Initialize collections
    db.drop_collection("products")
    db.drop_collection("orders")
    
    products_col = db["products"]
    orders_col = db["orders"]

    products_col.insert_many(PRODUCTS_DATA)
    orders_col.insert_many(ORDERS_DATA)

    print(f"\n[+] Step 1: Initialized schema and seeded database:")
    print(f"    * 'products' collection : {products_col.count_documents({})} documents (name, category, base_price, product_id)")
    print(f"    * 'orders' collection   : {orders_col.count_documents({})} documents (referencing product_id, non-embedded)")

    # -------------------------------------------------------------------------
    # Step 2: $lookup Pipeline - Orders with Product Details
    # Output: order_date, product_name, quantity, computed_total (quantity * base_price)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("PIPELINE 1: $lookup JOIN (Orders + Products) WITH COMPUTED TOTAL")
    print("-" * 90)

    pipeline_join = [
        {
            "$lookup": {
                "from": "products",
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "product_details"
            }
        },
        {"$unwind": "$product_details"},
        {
            "$project": {
                "_id": 0,
                "order_id": 1,
                "order_date": 1,
                "customer_name": 1,
                "product_name": "$product_details.name",
                "category": "$product_details.category",
                "quantity": 1,
                "base_price": "$product_details.base_price",
                "computed_total": {"$multiply": ["$quantity", "$product_details.base_price"]}
            }
        },
        {"$sort": {"order_date": 1, "order_id": 1}}
    ]

    joined_orders = list(orders_col.aggregate(pipeline_join))

    print(f"{'Order ID':<9} | {'Order Date':<11} | {'Customer':<15} | {'Product Name':<34} | {'Qty':<4} | {'Base Price':<11} | {'Total ($)':<10}")
    print("-" * 110)
    for row in joined_orders:
        print(f"{row['order_id']:<9} | {row['order_date']:<11} | {row['customer_name']:<15} | {row['product_name']:<34} | {row['quantity']:>3}  | ${row['base_price']:>9,.2f} | ${row['computed_total']:>9,.2f}")

    total_joined_revenue = sum(r["computed_total"] for r in joined_orders)
    print("-" * 110)
    print(f"Total Aggregated Orders Processed: {len(joined_orders)} | Cumulative Sales Total: ${total_joined_revenue:,.2f}")

    # -------------------------------------------------------------------------
    # Step 3: $lookup Pipeline - Products that have NEVER been ordered
    # Left outer join using $lookup with follow-up $match for empty join results
    # -------------------------------------------------------------------------
    print("\n" + "-" * 90)
    print("PIPELINE 2: PRODUCTS NEVER ORDERED (Left Outer Join + $match Empty Join Results)")
    print("-" * 90)

    pipeline_never_ordered = [
        {
            "$lookup": {
                "from": "orders",
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "order_records"
            }
        },
        {
            "$match": {
                "order_records": {"$size": 0}
            }
        },
        {
            "$project": {
                "_id": 0,
                "product_id": 1,
                "name": 1,
                "category": 1,
                "base_price": 1,
                "orders_count": {"$size": "$order_records"}
            }
        },
        {"$sort": {"product_id": 1}}
    ]

    never_ordered_products = list(products_col.aggregate(pipeline_never_ordered))

    print(f"\n[!] Identified {len(never_ordered_products)} catalog products with zero customer order history:")
    print(f"{'Product ID':<12} | {'Product Name':<36} | {'Category':<14} | {'Base Price ($)':<15} | {'Orders Logged':<14}")
    print("-" * 102)
    for p in never_ordered_products:
        print(f"{p['product_id']:<12} | {p['name']:<36} | {p['category']:<14} | ${p['base_price']:>13,.2f} | {p['orders_count']:>14}")

    # -------------------------------------------------------------------------
    # Export full dataset & join results to JSON
    # -------------------------------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_5_2.json")

    export_payload = {
        "metadata": {
            "lab": "Lab 5.2: Join Data with $lookup",
            "products_count": products_col.count_documents({}),
            "orders_count": orders_col.count_documents({}),
            "total_computed_revenue": round(total_joined_revenue, 2),
            "never_ordered_count": len(never_ordered_products)
        },
        "products_catalog": list(products_col.find({}, {"_id": 0})),
        "raw_orders": list(orders_col.find({}, {"_id": 0})),
        "pipeline_1_joined_orders": joined_orders,
        "pipeline_2_never_ordered_products": never_ordered_products
    }

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 90)
    print(f"[+] Successfully exported joined data & left outer join results to:\n    {json_path}")
    print("=" * 90)

if __name__ == "__main__":
    main()
