"""
Lab 5.1 - Try It Yourself: Categorize Orders with $bucket Stage
Objective: Add a $bucket stage to categorize orders into:
  - Small (under $50)
  - Medium ($50 - $200)
  - Large (over $200)
based on total order value (quantity * unit_price).
"""

import os
import sys
import json
from bson import json_util
from pymongo import MongoClient

def get_database(db_name="sales_analytics_bucket"):
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

# 24 diverse order records across price tiers
ORDERS_DATA = [
    {"order_id": "ORD-1001", "customer": "Aarav Sharma", "product": "Ultra HD 4K Monitor", "quantity": 1, "unit_price": 380.00, "order_date": "2024-01-12", "status": "completed"},
    {"order_id": "ORD-1002", "customer": "Priya Patel", "product": "Wireless Mechanical Keyboard", "quantity": 2, "unit_price": 85.00, "order_date": "2024-01-15", "status": "completed"},
    {"order_id": "ORD-1003", "customer": "Rohan Mehta", "product": "Ergonomic Gaming Mouse", "quantity": 1, "unit_price": 45.00, "order_date": "2024-01-18", "status": "completed"},
    {"order_id": "ORD-1004", "customer": "Ananya Iyer", "product": "Noise-Cancelling Headphones", "quantity": 1, "unit_price": 220.00, "order_date": "2024-01-24", "status": "shipped"},
    {"order_id": "ORD-1005", "customer": "Vikram Singh", "product": "USB-C Multi-Port Hub", "quantity": 3, "unit_price": 35.00, "order_date": "2024-01-29", "status": "completed"},
    {"order_id": "ORD-1006", "customer": "Aarav Sharma", "product": "High-Speed NVMe SSD 1TB", "quantity": 2, "unit_price": 115.00, "order_date": "2024-02-02", "status": "completed"},
    {"order_id": "ORD-1007", "customer": "Neha Verma", "product": "Adjustable Standing Desk", "quantity": 1, "unit_price": 450.00, "order_date": "2024-02-05", "status": "completed"},
    {"order_id": "ORD-1008", "customer": "Priya Patel", "product": "HD Webcam 1080p", "quantity": 1, "unit_price": 60.00, "order_date": "2024-02-10", "status": "completed"},
    {"order_id": "ORD-1009", "customer": "Siddharth Rao", "product": "Studio Condenser Mic", "quantity": 1, "unit_price": 130.00, "order_date": "2024-02-14", "status": "pending"},
    {"order_id": "ORD-1010", "customer": "Rohan Mehta", "product": "Desk Pad XXL", "quantity": 2, "unit_price": 22.50, "order_date": "2024-02-18", "status": "completed"},
    {"order_id": "ORD-1011", "customer": "Ananya Iyer", "product": "Ultra HD 4K Monitor", "quantity": 2, "unit_price": 380.00, "order_date": "2024-02-22", "status": "completed"},
    {"order_id": "ORD-1012", "customer": "Vikram Singh", "product": "Wireless Mechanical Keyboard", "quantity": 1, "unit_price": 85.00, "order_date": "2024-02-27", "status": "cancelled"},
    {"order_id": "ORD-1013", "customer": "Aarav Sharma", "product": "Noise-Cancelling Headphones", "quantity": 1, "unit_price": 220.00, "order_date": "2024-03-03", "status": "completed"},
    {"order_id": "ORD-1014", "customer": "Neha Verma", "product": "Ergonomic Gaming Mouse", "quantity": 2, "unit_price": 45.00, "order_date": "2024-03-08", "status": "completed"},
    {"order_id": "ORD-1015", "customer": "Siddharth Rao", "product": "High-Speed NVMe SSD 1TB", "quantity": 3, "unit_price": 115.00, "order_date": "2024-03-12", "status": "completed"},
    {"order_id": "ORD-1016", "customer": "Priya Patel", "product": "USB-C Multi-Port Hub", "quantity": 2, "unit_price": 35.00, "order_date": "2024-03-17", "status": "shipped"},
    {"order_id": "ORD-1017", "customer": "Rohan Mehta", "product": "HD Webcam 1080p", "quantity": 1, "unit_price": 60.00, "order_date": "2024-03-21", "status": "pending"},
    {"order_id": "ORD-1018", "customer": "Ananya Iyer", "product": "Adjustable Standing Desk", "quantity": 1, "unit_price": 450.00, "order_date": "2024-03-25", "status": "completed"},
    {"order_id": "ORD-1019", "customer": "Vikram Singh", "product": "High-Speed NVMe SSD 1TB", "quantity": 1, "unit_price": 115.00, "order_date": "2024-04-02", "status": "completed"},
    {"order_id": "ORD-1020", "customer": "Aarav Sharma", "product": "Wireless Mechanical Keyboard", "quantity": 1, "unit_price": 85.00, "order_date": "2024-04-07", "status": "completed"},
    {"order_id": "ORD-1021", "customer": "Neha Verma", "product": "Studio Condenser Mic", "quantity": 1, "unit_price": 130.00, "order_date": "2024-04-12", "status": "shipped"},
    {"order_id": "ORD-1022", "customer": "Siddharth Rao", "product": "Ultra HD 4K Monitor", "quantity": 1, "unit_price": 380.00, "order_date": "2024-04-16", "status": "cancelled"},
    {"order_id": "ORD-1023", "customer": "Priya Patel", "product": "Desk Pad XXL", "quantity": 3, "unit_price": 22.50, "order_date": "2024-04-20", "status": "completed"},
    {"order_id": "ORD-1024", "customer": "Rohan Mehta", "product": "Noise-Cancelling Headphones", "quantity": 1, "unit_price": 220.00, "order_date": "2024-04-25", "status": "completed"}
]

TIER_NAMES = {
    0: "Small (Under $50)",
    50: "Medium ($50 - $200)",
    "large": "Large (Over $200)"
}

def main():
    print("=" * 85)
    print("LAB 5.1 - TRY IT YOURSELF: ORDER VALUE BUCKET CATEGORIZATION ($bucket)")
    print("=" * 85)

    client, db, is_mock = get_database("sales_analytics_bucket")

    # Step 1: Re-seed orders
    db.drop_collection("orders")
    orders_col = db["orders"]
    orders_col.insert_many(ORDERS_DATA)
    total_orders = orders_col.count_documents({})
    print(f"\n[+] Seeded 'orders' collection with {total_orders} documents.")

    # -------------------------------------------------------------------------
    # $bucket Aggregation Pipeline
    # -------------------------------------------------------------------------
    # Stage 1: $addFields to compute order_total = quantity * unit_price
    # Stage 2: $bucket with boundaries [0, 50, 200] and default 'large'
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print("EXECUTING AGGREGATION PIPELINE WITH $bucket STAGE")
    print("-" * 85)

    pipeline_bucket = [
        {
            "$addFields": {
                "order_total": {"$multiply": ["$quantity", "$unit_price"]}
            }
        },
        {
            "$bucket": {
                "groupBy": "$order_total",
                "boundaries": [0, 50, 200],
                "default": "large",
                "output": {
                    "count": {"$sum": 1},
                    "total_revenue": {"$sum": "$order_total"},
                    "avg_order_value": {"$avg": "$order_total"},
                    "min_order_value": {"$min": "$order_total"},
                    "max_order_value": {"$max": "$order_total"},
                    "customers": {"$addToSet": "$customer"},
                    "sample_orders": {
                        "$push": {
                            "order_id": "$order_id",
                            "customer": "$customer",
                            "product": "$product",
                            "order_total": "$order_total"
                        }
                    }
                }
            }
        }
    ]

    raw_bucket_results = list(orders_col.aggregate(pipeline_bucket))

    # Calculate overall total revenue for revenue share computation
    grand_total_revenue = sum(b["total_revenue"] for b in raw_bucket_results)

    # Format and present results
    annotated_results = []
    print(f"\n{'Bucket Range':<22} | {'Category Name':<22} | {'Orders':<8} | {'Revenue ($)':<14} | {'Avg Value ($)':<14} | {'Revenue Share':<12}")
    print("-" * 105)

    for b in raw_bucket_results:
        bucket_id = b["_id"]
        tier_label = TIER_NAMES.get(bucket_id, str(bucket_id))
        
        if bucket_id == 0:
            range_str = "$0.00 <= total < $50"
        elif bucket_id == 50:
            range_str = "$50.00 <= total < $200"
        else:
            range_str = "total >= $200.00"
            
        rev_share = (b["total_revenue"] / grand_total_revenue * 100) if grand_total_revenue > 0 else 0
        
        annotated_item = {
            "bucket_id": bucket_id,
            "range": range_str,
            "tier_category": tier_label,
            "order_count": b["count"],
            "total_revenue": round(b["total_revenue"], 2),
            "avg_order_value": round(b["avg_order_value"], 2),
            "min_order_value": round(b["min_order_value"], 2),
            "max_order_value": round(b["max_order_value"], 2),
            "revenue_share_pct": round(rev_share, 2),
            "unique_customers_count": len(b["customers"]),
            "customers": b["customers"],
            "orders": b["sample_orders"]
        }
        annotated_results.append(annotated_item)

        print(f"{range_str:<22} | {tier_label:<22} | {b['count']:>8} | ${b['total_revenue']:>12,.2f} | ${b['avg_order_value']:>12,.2f} | {rev_share:>11.1f}%")

    # Detailed Itemization by Tier
    print("\n" + "=" * 85)
    print("DETAILED BREAKDOWN BY BUCKET TIER")
    print("=" * 85)

    for item in annotated_results:
        print(f"\n>>> [{item['tier_category'].upper()}] - {item['range']}")
        print(f"    * Orders Count    : {item['order_count']} orders ({item['revenue_share_pct']}% of gross revenue)")
        print(f"    * Revenue Metrics : Total = ${item['total_revenue']:,.2f} | Avg = ${item['avg_order_value']:,.2f} | Range = [${item['min_order_value']:,.2f} - ${item['max_order_value']:,.2f}]")
        print(f"    * Customer Reach  : {item['unique_customers_count']} distinct customers ({', '.join(item['customers'])})")
        print("    * Sample Orders in Tier:")
        for o in item["orders"][:3]:
            print(f"      - {o['order_id']}: {o['customer']} bought '{o['product']}' = ${o['order_total']:,.2f}")
        if len(item["orders"]) > 3:
            print(f"      ... and {len(item['orders']) - 3} more order(s).")

    # -------------------------------------------------------------------------
    # Export to JSON
    # -------------------------------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_5_1_try_it_yourself.json")

    export_payload = {
        "metadata": {
            "activity": "Lab 5.1 - Try It Yourself: $bucket Stage",
            "objective": "Categorize orders into small (<$50), medium ($50-$200), and large (>$200)",
            "grand_total_revenue": round(grand_total_revenue, 2),
            "total_orders": total_orders
        },
        "bucket_analytics": annotated_results
    }

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 85)
    print(f"[+] Successfully exported $bucket analytics to:\n    {json_path}")
    print("=" * 85)

if __name__ == "__main__":
    main()
