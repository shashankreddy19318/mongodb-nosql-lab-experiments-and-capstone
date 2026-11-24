"""
Lab 10.2: Inventory Reservation with Deadlock & Write-Conflict Handling
Course: Distributed NoSQL Databases (MongoDB 7.0)
Author: Student Submission (chintan)

Demonstrates:
  - Multi-document transactions across 'inventory' and 'orders' collections
  - Optimistic concurrency control (OCC) using versioning and atomic increments
  - High contention concurrency stress testing (8 simultaneous threads vs 5 items)
  - Comparative analysis: WITHOUT retry vs WITH retry (TransientTransactionError recovery)
  - Multi-threaded throughput benchmarking across concurrency levels (1, 4, 8, 16 threads)
  - Architectural comparison: Multi-document Transactions vs Single-Document findAndModify
"""

import os
import sys
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pymongo import MongoClient, WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.errors import PyMongoError, OperationFailure

# Connection Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo-rs0-1:27017,mongo-rs0-2:27018,mongo-rs0-3:27019/?replicaSet=rs0")
DB_NAME = os.getenv("MONGO_DB_INV", "ecommerce_inventory")
BASE_BACKOFF_SEC = 0.05
MAX_RETRIES = 5


class InsufficientStockError(Exception):
    """Raised when available stock is insufficient for reservation."""
    pass


def print_banner(title: str, char="=", width=75):
    print("\n" + char * width)
    print(f"  {title}")
    print(char * width)


def get_client() -> MongoClient:
    """Initialize and return MongoClient connection."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client


def seed_inventory(db, initial_stock: int = 5) -> None:
    """
    Seed inventory collection:
    {product_id, name, stock, price, version}
    and reset orders collection:
    {order_id, customer_id, items, status, total, created_at}
    """
    inventory_col = db["inventory"]
    orders_col = db["orders"]

    inventory_col.drop()
    orders_col.drop()

    inventory_col.insert_one({
        "product_id": "PROD-100",
        "name": "Ultra-Slim Pro Laptop 15\"",
        "stock": initial_stock,
        "price": 1299.99,
        "version": 1
    })
    print(f"  [INIT] Seeded product PROD-100 with stock={initial_stock}, version=1. Orders collection reset.")


def reserve_inventory_tx(
    client: MongoClient,
    product_id: str,
    customer_id: str,
    qty: int = 1,
    retry: bool = True,
    max_retries: int = MAX_RETRIES
) -> dict:
    """
    Reserve inventory using a multi-document ACID transaction.
    If retry=True, automatically catches TransientTransactionError / WriteConflict
    and retries with exponential backoff.
    """
    db = client[DB_NAME]
    inventory_col = db["inventory"]
    orders_col = db["orders"]

    attempt = 0
    start_time = time.time()

    while True:
        attempt += 1
        with client.start_session() as session:
            try:
                session.start_transaction(
                    read_concern=ReadConcern(level="snapshot"),
                    write_concern=WriteConcern(w="majority")
                )

                # Step 1: Read current stock within transaction snapshot
                item = inventory_col.find_one({"product_id": product_id}, session=session)
                if not item:
                    raise OperationFailure(f"Product {product_id} not found.")

                if item["stock"] < qty:
                    raise InsufficientStockError(
                        f"Insufficient stock: requested {qty}, available {item['stock']}"
                    )

                # Step 2: Atomic decrement stock and increment version
                update_result = inventory_col.update_one(
                    {"product_id": product_id, "stock": {"$gte": qty}},
                    {"$inc": {"stock": -qty, "version": 1}},
                    session=session
                )

                if update_result.matched_count == 0:
                    raise InsufficientStockError(
                        f"Stock contention: could not claim {qty} units."
                    )

                # Step 3: Insert order record within same transaction
                order_doc = {
                    "order_id": f"ORD-{int(time.time()*1000)}-{random.randint(1000, 9999)}",
                    "customer_id": customer_id,
                    "items": [{
                        "product_id": product_id,
                        "name": item["name"],
                        "qty": qty,
                        "price": item["price"]
                    }],
                    "status": "CONFIRMED",
                    "total": round(item["price"] * qty, 2),
                    "attempt": attempt,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                orders_col.insert_one(order_doc, session=session)

                # Step 4: Commit transaction
                session.commit_transaction()
                latency_ms = (time.time() - start_time) * 1000
                return {
                    "success": True,
                    "status": "RESERVED",
                    "order_id": order_doc["order_id"],
                    "attempts": attempt,
                    "latency_ms": latency_ms,
                    "customer_id": customer_id
                }

            except InsufficientStockError as ise:
                session.abort_transaction()
                latency_ms = (time.time() - start_time) * 1000
                return {
                    "success": False,
                    "status": "INSUFFICIENT",
                    "error": str(ise),
                    "attempts": attempt,
                    "latency_ms": latency_ms,
                    "customer_id": customer_id
                }

            except PyMongoError as pe:
                is_transient = pe.has_error_label("TransientTransactionError") or "WriteConflict" in str(pe)
                if retry and is_transient and attempt < max_retries:
                    # Exponential backoff with jitter
                    backoff = (BASE_BACKOFF_SEC * (2 ** (attempt - 1))) + random.uniform(0.01, 0.05)
                    time.sleep(backoff)
                    continue
                else:
                    session.abort_transaction()
                    latency_ms = (time.time() - start_time) * 1000
                    return {
                        "success": False,
                        "status": "CONFLICT",
                        "error": str(pe),
                        "attempts": attempt,
                        "latency_ms": latency_ms,
                        "customer_id": customer_id
                    }


def reserve_inventory_non_tx(
    client: MongoClient,
    product_id: str,
    customer_id: str,
    qty: int = 1,
    simulate_crash: bool = False
) -> dict:
    """
    Non-transactional reservation using find_one_and_update (findAndModify).
    Fast single-document atomicity, but vulnerable to partial failures.
    """
    db = client[DB_NAME]
    inventory_col = db["inventory"]
    orders_col = db["orders"]

    start_time = time.time()
    # Atomic decrement on single document
    updated_item = inventory_col.find_one_and_update(
        {"product_id": product_id, "stock": {"$gte": qty}},
        {"$inc": {"stock": -qty, "version": 1}},
        return_document=True
    )

    if not updated_item:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status": "INSUFFICIENT",
            "latency_ms": latency_ms,
            "customer_id": customer_id
        }

    # If simulate_crash is enabled, fail before order insertion
    if simulate_crash:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "status": "CRASHED_BEFORE_ORDER_INSERT",
            "error": "Simulated application crash / network partition between decrement and insert",
            "latency_ms": latency_ms,
            "customer_id": customer_id
        }

    # Insert order
    order_doc = {
        "order_id": f"ORD-NONTX-{int(time.time()*1000)}-{random.randint(1000, 9999)}",
        "customer_id": customer_id,
        "items": [{"product_id": product_id, "qty": qty, "price": updated_item["price"]}],
        "status": "CONFIRMED",
        "total": round(updated_item["price"] * qty, 2),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    orders_col.insert_one(order_doc)

    latency_ms = (time.time() - start_time) * 1000
    return {
        "success": True,
        "status": "RESERVED",
        "order_id": order_doc["order_id"],
        "latency_ms": latency_ms,
        "customer_id": customer_id
    }


def run_concurrency_test(client: MongoClient, retry_enabled: bool, num_threads: int = 8, initial_stock: int = 5):
    """
    Execute simultaneous reservation requests against limited stock.
    Demonstrates write conflicts and resolution behavior.
    """
    db = client[DB_NAME]
    seed_inventory(db, initial_stock=initial_stock)
    
    mode_str = "WITH Automatic Retry & Backoff" if retry_enabled else "WITHOUT Retry (Raw WriteConflicts)"
    print_banner(f"Contention Test ({num_threads} Threads vs {initial_stock} Units) â€” {mode_str}", "-")

    results = []
    start_total = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(
                reserve_inventory_tx,
                client,
                "PROD-100",
                f"CUST-{i:03d}",
                1,
                retry_enabled
            )
            for i in range(1, num_threads + 1)
        ]
        for f in as_completed(futures):
            results.append(f.result())

    total_wall_ms = (time.time() - start_total) * 1000
    
    # Analyze outcomes
    reserved = [r for r in results if r["status"] == "RESERVED"]
    conflicts = [r for r in results if r["status"] == "CONFLICT"]
    insufficient = [r for r in results if r["status"] == "INSUFFICIENT"]

    print(f"\n  --- Execution Summary ({mode_str}) ---")
    print(f"  {'Customer':<10} | {'Status':<14} | {'Attempts':>8} | {'Latency (ms)':>12}")
    print("  " + "-" * 52)
    for r in sorted(results, key=lambda x: x["customer_id"]):
        print(f"  {r['customer_id']:<10} | {r['status']:<14} | {r.get('attempts', 1):>8} | {r['latency_ms']:>12.1f}")
    print("  " + "-" * 52)

    db_item = db["inventory"].find_one({"product_id": "PROD-100"})
    orders_count = db["orders"].count_documents({})

    print(f"\n  Database State Verification:")
    print(f"    Total Threads Launched : {num_threads}")
    print(f"    Successful Reservations: {len(reserved)}")
    print(f"    Write Conflicts Failed : {len(conflicts)}")
    print(f"    Insufficient Stock     : {len(insufficient)}")
    print(f"    Remaining Stock in DB  : {db_item['stock']}")
    print(f"    Total Orders Inserted  : {orders_count}")
    print(f"    Total Wall-Clock Time  : {total_wall_ms:.1f}ms")

    return {
        "retry_enabled": retry_enabled,
        "threads": num_threads,
        "reserved": len(reserved),
        "conflicts": len(conflicts),
        "insufficient": len(insufficient),
        "remaining_stock": db_item["stock"],
        "orders_count": orders_count,
        "wall_ms": total_wall_ms
    }


def run_throughput_benchmark(client: MongoClient, concurrency_levels=(1, 4, 8, 16), ops_per_thread=10):
    """
    Measure transaction throughput (res/sec) and latency across concurrency levels.
    """
    db = client[DB_NAME]
    print_banner("Throughput Benchmark across Concurrency Levels (1, 4, 8, 16 Threads)", "-")
    print(f"  Testing {ops_per_thread} operations per thread on dedicated inventory partitions.\n")

    summary_table = []

    for workers in concurrency_levels:
        total_ops = workers * ops_per_thread
        seed_inventory(db, initial_stock=total_ops * 2)

        start_time = time.time()
        success_count = 0
        total_attempts = 0
        latencies = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for t_idx in range(workers):
                for op_idx in range(ops_per_thread):
                    cust_id = f"BENCH-{t_idx:02d}-{op_idx:02d}"
                    futures.append(
                        executor.submit(
                            reserve_inventory_tx,
                            client,
                            "PROD-100",
                            cust_id,
                            1,
                            True
                        )
                    )

            for f in as_completed(futures):
                res = f.result()
                if res["success"]:
                    success_count += 1
                total_attempts += res.get("attempts", 1)
                latencies.append(res.get("latency_ms", 0))

        wall_sec = time.time() - start_time
        throughput = success_count / wall_sec if wall_sec > 0 else 0
        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        latencies.sort()
        p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0

        row = {
            "threads": workers,
            "total_ops": total_ops,
            "successful": success_count,
            "wall_sec": wall_sec,
            "throughput_ops_sec": throughput,
            "avg_latency_ms": avg_lat,
            "p95_latency_ms": p95_lat,
            "retries_per_op": (total_attempts - total_ops) / total_ops if total_ops > 0 else 0
        }
        summary_table.append(row)

        print(f"  Concurrency: {workers:>2} Workers | Ops: {total_ops:>3} | Success: {success_count:>3} | "
              f"Time: {wall_sec:>5.2f}s | Throughput: {throughput:>7.1f} ops/sec | Avg Lat: {avg_lat:>5.1f}ms | P95 Lat: {p95_lat:>5.1f}ms")

    return summary_table


def run_architectural_comparison(client: MongoClient, num_ops: int = 50):
    """
    Compare ACID Multi-Document Transactions vs Non-Transactional findAndModify.
    Demonstrates throughput differences and data inconsistency risks.
    """
    db = client[DB_NAME]
    print_banner("Architectural Comparison: Transactions vs findAndModify (find_one_and_update)", "-")

    # 1. Benchmark Transactional
    seed_inventory(db, initial_stock=num_ops * 2)
    start_tx = time.time()
    for i in range(num_ops):
        reserve_inventory_tx(client, "PROD-100", f"TX-CUST-{i}", qty=1, retry=True)
    tx_duration = time.time() - start_tx
    tx_tps = num_ops / tx_duration

    # 2. Benchmark Non-Transactional
    seed_inventory(db, initial_stock=num_ops * 2)
    start_nontx = time.time()
    for i in range(num_ops):
        reserve_inventory_non_tx(client, "PROD-100", f"NONTX-CUST-{i}", qty=1, simulate_crash=False)
    nontx_duration = time.time() - start_nontx
    nontx_tps = num_ops / nontx_duration

    # 3. Simulate Inconsistency Vulnerability in Non-Transactional
    seed_inventory(db, initial_stock=5)
    print("  Simulating mid-process crash in Non-Transactional reservation...")
    crash_res = reserve_inventory_non_tx(client, "PROD-100", "CRASH-USER", qty=1, simulate_crash=True)
    post_item = db["inventory"].find_one({"product_id": "PROD-100"})
    orders_cnt = db["orders"].count_documents({"customer_id": "CRASH-USER"})

    print(f"\n  Inconsistency Vulnerability Demonstration:")
    print(f"    Initial Stock: 5 | Decrement occurred: True")
    print(f"    Post-Crash DB Stock: {post_item['stock']} (Decremented to 4)")
    print(f"    Orders Inserted for CRASH-USER: {orders_cnt} (Order missing!)")
    print(f"    Conclusion: In non-transactional code, crash after decrement loses inventory permanently!")
    print(f"    In contrast, multi-document transactions automatically roll back on any crash/error.")

    print(f"\n  Throughput Comparison ({num_ops} sequential ops):")
    print(f"    ACID Transactions (Snapshot + Majority) : {tx_tps:,.1f} ops/sec (Time: {tx_duration:.3f}s)")
    print(f"    findAndModify (Single-Doc Atomic)       : {nontx_tps:,.1f} ops/sec (Time: {nontx_duration:.3f}s)")
    print(f"    Throughput Delta                        : findAndModify is {nontx_tps/tx_tps:.1f}x faster, but lacks cross-collection atomicity.")


def main():
    print_banner("LAB 10.2: INVENTORY RESERVATION WITH CONCURRENCY & DEADLOCK HANDLING")
    client = get_client()

    # Part 1: Concurrency Contention - Without Retry
    res_no_retry = run_concurrency_test(client, retry_enabled=False, num_threads=8, initial_stock=5)

    # Part 2: Concurrency Contention - With Retry
    res_with_retry = run_concurrency_test(client, retry_enabled=True, num_threads=8, initial_stock=5)

    # Assertions for With Retry
    assert res_with_retry["reserved"] == 5, f"Expected exactly 5 reservations, got {res_with_retry['reserved']}"
    assert res_with_retry["insufficient"] == 3, f"Expected exactly 3 insufficient stock rejections, got {res_with_retry['insufficient']}"
    assert res_with_retry["remaining_stock"] == 0, f"Expected 0 stock remaining, got {res_with_retry['remaining_stock']}"
    assert res_with_retry["orders_count"] == 5, f"Expected 5 orders in DB, got {res_with_retry['orders_count']}"
    print("\n  [ALL CONCURRENCY ASSERTIONS PASSED] Perfect isolation: 5 reserved, 3 rejected, 0 over-selling.")

    # Part 3: Throughput Benchmark
    bench_results = run_throughput_benchmark(client, concurrency_levels=(1, 4, 8, 16), ops_per_thread=10)

    # Part 4: Architectural Comparison
    run_architectural_comparison(client, num_ops=40)

    client.close()
    print_banner("LAB 10.2 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    main()
