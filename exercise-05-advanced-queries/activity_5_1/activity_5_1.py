"""
Lab 5.1: Build a Sales Analytics Pipeline
Objective: Construct aggregation pipelines for a sales analytics system.
Prerequisites: Completion of Chapter 4 labs.

Instructions:
1. Create an orders collection with fields: customer, product, quantity, unit_price, order_date, status.
   Insert at least 20 orders across multiple customers and products.
2. Write a pipeline that computes monthly revenue (group by month, sum quantity * unit_price) sorted by month.
3. Write a pipeline that finds the top 3 customers by total spending, including a list of products they bought.
4. Write a pipeline that computes the average order value per status category.
"""

import os
import sys
import json
from bson import json_util
from pymongo import MongoClient

def get_database(db_name="sales_analytics_pipeline"):
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

# 24 realistic order documents across 7 customers and 10 products spanning Jan - Apr 2024
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

def main():
    print("=" * 85)
    print("LAB 5.1: BUILD A SALES ANALYTICS PIPELINE")
    print("=" * 85)

    client, db, is_mock = get_database("sales_analytics_pipeline")

    # Step 1: Drop & populate orders collection
    db.drop_collection("orders")
    orders_col = db["orders"]
    insert_result = orders_col.insert_many(ORDERS_DATA)
    total_orders = len(insert_result.inserted_ids)
    print(f"\n[+] Step 1: Created 'orders' collection & seeded {total_orders} order documents.")
    print("    Fields: customer, product, quantity, unit_price, order_date, status.")

    # -------------------------------------------------------------------------
    # Step 2: Pipeline - Monthly Revenue
    # Group by month, sum (quantity * unit_price), sorted by month
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print("PIPELINE 1: MONTHLY REVENUE ANALYSIS (Group by Month, Sort Ascending)")
    print("-" * 85)

    pipeline_monthly = [
        {
            "$group": {
                "_id": {"$substr": ["$order_date", 0, 7]},
                "monthly_revenue": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}},
                "total_orders": {"$sum": 1},
                "total_units_sold": {"$sum": "$quantity"},
                "avg_order_value": {"$avg": {"$multiply": ["$quantity", "$unit_price"]}}
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "month": "$_id",
                "monthly_revenue": 1,
                "total_orders": 1,
                "total_units_sold": 1,
                "avg_order_value": 1,
                "_id": 0
            }
        }
    ]

    monthly_results = list(orders_col.aggregate(pipeline_monthly))
    
    print(f"{'Month':<12} | {'Revenue ($)':<15} | {'Orders':<10} | {'Units Sold':<12} | {'Avg Order ($)':<15}")
    print("-" * 75)
    for row in monthly_results:
        print(f"{row['month']:<12} | ${row['monthly_revenue']:>13,.2f} | {row['total_orders']:>10} | {row['total_units_sold']:>12} | ${row['avg_order_value']:>13,.2f}")

    # -------------------------------------------------------------------------
    # Step 3: Pipeline - Top 3 Customers by Total Spending
    # Group by customer, sum (quantity * unit_price), list of products bought
    # -------------------------------------------------------------------------
    print("\n" + "-" * 85)
    print("PIPELINE 2: TOP 3 CUSTOMERS BY TOTAL SPENDING (With Purchased Products List)")
    print("-" * 85)

    pipeline_top_customers = [
        {
            "$group": {
                "_id": "$customer",
                "total_spending": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}},
                "total_orders": {"$sum": 1},
                "total_items": {"$sum": "$quantity"},
                "products_bought": {"$addToSet": "$product"}
            }
        },
        {"$sort": {"total_spending": -1}},
        {"$limit": 3},
        {
            "$project": {
                "customer": "$_id",
                "total_spending": 1,
                "total_orders": 1,
                "total_items": 1,
                "products_bought": 1,
                "_id": 0
            }
        }
    ]

    top_customers_results = list(orders_col.aggregate(pipeline_top_customers))

    for rank, cust in enumerate(top_customers_results, 1):
        print(f"Rank #{rank}: {cust['customer']}")
        print(f"  * Total Spending : ${cust['total_spending']:,.2f}")
        print(f"  * Orders Placed  : {cust['total_orders']} ({cust['total_items']} total units)")
        print(f"  * Products Bought: {', '.join(cust['products_bought'])}")
        print()

    # -------------------------------------------------------------------------
    # Step 4: Pipeline - Average Order Value per Status Category
    # -------------------------------------------------------------------------
    print("-" * 85)
    print("PIPELINE 3: AVERAGE ORDER VALUE PER STATUS CATEGORY")
    print("-" * 85)

    pipeline_status = [
        {
            "$group": {
                "_id": "$status",
                "avg_order_value": {"$avg": {"$multiply": ["$quantity", "$unit_price"]}},
                "total_revenue": {"$sum": {"$multiply": ["$quantity", "$unit_price"]}},
                "order_count": {"$sum": 1}
            }
        },
        {"$sort": {"avg_order_value": -1}},
        {
            "$project": {
                "status": "$_id",
                "avg_order_value": 1,
                "total_revenue": 1,
                "order_count": 1,
                "_id": 0
            }
        }
    ]

    status_results = list(orders_col.aggregate(pipeline_status))

    print(f"{'Status Category':<18} | {'Avg Order Value ($)':<22} | {'Total Value ($)':<18} | {'Order Count':<12}")
    print("-" * 78)
    for row in status_results:
        print(f"{row['status'].capitalize():<18} | ${row['avg_order_value']:>20,.2f} | ${row['total_revenue']:>16,.2f} | {row['order_count']:>12}")

    # -------------------------------------------------------------------------
    # Export full dataset & pipeline analytics to JSON
    # -------------------------------------------------------------------------
    output_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(output_dir, "activity_5_1.json")
    
    export_payload = {
        "metadata": {
            "lab": "Lab 5.1: Build a Sales Analytics Pipeline",
            "total_orders_inserted": total_orders,
            "database_name": "sales_analytics_pipeline",
            "collection_name": "orders"
        },
        "all_orders": list(orders_col.find()),
        "pipeline_1_monthly_revenue": monthly_results,
        "pipeline_2_top_3_customers": top_customers_results,
        "pipeline_3_avg_value_by_status": status_results
    }

    with open(json_path, "w", encoding="utf-8") as f:
        f.write(json_util.dumps(export_payload, indent=2))

    print("\n" + "=" * 85)
    print(f"[+] Successfully exported MongoDB data & pipeline results to:\n    {json_path}")
    print("=" * 85)

if __name__ == "__main__":
    main()
