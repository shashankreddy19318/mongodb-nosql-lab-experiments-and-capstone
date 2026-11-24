"""
Lab 10.1: Multi-Document ACID Transactions & Bank Transfer System
Course: Distributed NoSQL Databases (MongoDB 7.0)
Author: Student Submission (chintan)

Demonstrates:
  - Multi-document ACID transactions using ClientSession
  - Read Concern 'snapshot' for Point-In-Time consistency
  - Write Concern 'majority' for durability across replica set members
  - Insufficient funds validation with atomic filter matching
  - Transaction rollback guarantee (atomicity verification)
  - Automatic retry logic with exponential backoff for TransientTransactionError
"""

import os
import sys
import time
import random
import threading
from datetime import datetime, timezone
from pymongo import MongoClient, WriteConcern
from pymongo.read_concern import ReadConcern
from pymongo.errors import PyMongoError, OperationFailure

# Connection Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo-rs0-1:27017,mongo-rs0-2:27018,mongo-rs0-3:27019/?replicaSet=rs0")
DB_NAME = os.getenv("MONGO_DB", "banking_system")
MAX_RETRIES = 5
BASE_BACKOFF_SEC = 0.1


class InsufficientFundsError(Exception):
    """Raised when source account balance is less than transfer amount."""
    pass


class AccountNotFoundError(Exception):
    """Raised when specified account does not exist."""
    pass


def print_banner(title: str, char="=", width=75):
    print("\n" + char * width)
    print(f"  {title}")
    print(char * width)


def get_client() -> MongoClient:
    """Initialize and verify MongoClient connection to MongoDB replica set."""
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000
    )
    # Force connection check
    client.admin.command("ping")
    return client


def seed_accounts(db) -> None:
    """
    Seed initial account balances with schema:
    {account_id, holder, balance, version}
    """
    accounts = db["accounts"]
    transactions = db["transactions"]
    
    accounts.drop()
    transactions.drop()
    
    initial_accounts = [
        {"account_id": "ACC-001", "holder": "Arjun Sharma", "balance": 5000.00, "version": 1},
        {"account_id": "ACC-002", "holder": "Sneha Patel", "balance": 3000.00, "version": 1},
        {"account_id": "ACC-003", "holder": "Rahul Verma", "balance": 1000.00, "version": 1},
    ]
    
    accounts.insert_many(initial_accounts)
    print("  [INIT] Database initialized with 3 customer accounts.")


def print_account_balances(db, title="Current Account Balances"):
    """Display tabular view of account balances and document versions."""
    print(f"\n  --- {title} ---")
    print(f"  {'Account ID':<12} | {'Account Holder':<16} | {'Balance ($)':>12} | {'Version':>8}")
    print("  " + "-" * 56)
    for acc in db["accounts"].find({}, sort=[("account_id", 1)]):
        print(f"  {acc['account_id']:<12} | {acc['holder']:<16} | ${acc['balance']:>11,.2f} | {acc.get('version', 1):>8}")
    print("  " + "-" * 56)


def transfer_funds(
    client: MongoClient,
    from_acc: str,
    to_acc: str,
    amount: float,
    description: str = "Funds Transfer",
    enable_retry: bool = True
) -> dict:
    """
    Execute a multi-document bank transfer within an ACID transaction.
    Debits from_acc and credits to_acc atomically.
    Includes retry logic with exponential backoff for TransientTransactionError.
    
    Returns a result dictionary with status and diagnostic metadata.
    """
    db = client[DB_NAME]
    accounts_col = db["accounts"]
    history_col = db["transactions"]

    attempt = 0
    start_time = time.time()

    while True:
        attempt += 1
        with client.start_session() as session:
            try:
                # Start transaction with snapshot isolation and majority durability
                session.start_transaction(
                    read_concern=ReadConcern(level="snapshot"),
                    write_concern=WriteConcern(w="majority")
                )

                # Step 1: Verify source account exists and check pre-transfer balance
                sender = accounts_col.find_one({"account_id": from_acc}, session=session)
                if not sender:
                    raise AccountNotFoundError(f"Source account {from_acc} does not exist.")
                
                receiver = accounts_col.find_one({"account_id": to_acc}, session=session)
                if not receiver:
                    raise AccountNotFoundError(f"Destination account {to_acc} does not exist.")

                # Step 2: Atomic debit with balance threshold filter
                # Filter includes {balance: {"$gte": amount}} ensuring atomic check
                debit_result = accounts_col.update_one(
                    {"account_id": from_acc, "balance": {"$gte": amount}},
                    {"$inc": {"balance": -amount, "version": 1}},
                    session=session
                )

                if debit_result.matched_count == 0:
                    raise InsufficientFundsError(
                        f"Insufficient funds in {from_acc}: Available balance ${sender['balance']:,.2f}, required ${amount:,.2f}"
                    )

                # Step 3: Atomic credit to destination account
                credit_result = accounts_col.update_one(
                    {"account_id": to_acc},
                    {"$inc": {"balance": amount, "version": 1}},
                    session=session
                )

                if credit_result.matched_count == 0:
                    raise OperationFailure(f"Failed to credit destination account {to_acc}")

                # Step 4: Record immutable audit history
                tx_record = {
                    "transaction_id": f"TXN-{int(time.time()*1000)}-{random.randint(100, 999)}",
                    "from_account": from_acc,
                    "to_account": to_acc,
                    "amount": amount,
                    "description": description,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "attempt": attempt,
                    "status": "COMMITTED"
                }
                history_col.insert_one(tx_record, session=session)

                # Step 5: Commit Transaction
                session.commit_transaction()
                elapsed_ms = (time.time() - start_time) * 1000
                print(f"  [SUCCESS] Transferred ${amount:,.2f} from {from_acc} to {to_acc} (TxID: {tx_record['transaction_id']}, Attempts: {attempt}, Latency: {elapsed_ms:.1f}ms)")
                return {
                    "success": True,
                    "transaction_id": tx_record["transaction_id"],
                    "attempts": attempt,
                    "latency_ms": elapsed_ms
                }

            except InsufficientFundsError as ife:
                session.abort_transaction()
                elapsed_ms = (time.time() - start_time) * 1000
                print(f"  [ROLLBACK] Transaction aborted: {ife} (Latency: {elapsed_ms:.1f}ms)")
                return {
                    "success": False,
                    "error": str(ife),
                    "reason": "INSUFFICIENT_FUNDS",
                    "rolled_back": True,
                    "attempts": attempt
                }

            except AccountNotFoundError as anfe:
                session.abort_transaction()
                return {
                    "success": False,
                    "error": str(anfe),
                    "reason": "ACCOUNT_NOT_FOUND",
                    "rolled_back": True,
                    "attempts": attempt
                }

            except PyMongoError as pe:
                # Check for transient transaction errors suitable for retry
                is_transient = pe.has_error_label("TransientTransactionError") or "WriteConflict" in str(pe)
                
                if enable_retry and is_transient and attempt < MAX_RETRIES:
                    backoff = (BASE_BACKOFF_SEC * (2 ** (attempt - 1))) + random.uniform(0.02, 0.08)
                    print(f"  [RETRY] Transient conflict encountered on attempt {attempt}: {pe}. Retrying in {backoff*1000:.1f}ms...")
                    time.sleep(backoff)
                    continue
                else:
                    session.abort_transaction()
                    elapsed_ms = (time.time() - start_time) * 1000
                    print(f"  [ERROR] Unrecoverable transaction failure: {pe} (Latency: {elapsed_ms:.1f}ms)")
                    return {
                        "success": False,
                        "error": str(pe),
                        "reason": "TRANSIENT_EXHAUSTED" if is_transient else "PERSISTENT_ERROR",
                        "rolled_back": True,
                        "attempts": attempt
                    }


def run_lab_01_demonstration():
    """Execute complete Lab 10.1 scenarios."""
    print_banner("LAB 10.1: MULTI-DOCUMENT BANK TRANSFER TRANSACTIONS")
    
    client = get_client()
    db = client[DB_NAME]
    
    # Setup initial accounts
    seed_accounts(db)
    print_account_balances(db, "Initial State")

    # =========================================================================
    # SCENARIO 1: Valid Transfer with Sufficient Funds
    # =========================================================================
    print_banner("Scenario 1: Successful Transfer ($1,500.00 from ACC-001 -> ACC-002)", "-")
    res1 = transfer_funds(
        client,
        from_acc="ACC-001",
        to_acc="ACC-002",
        amount=1500.00,
        description="Invoice Payment #4021"
    )
    print_account_balances(db, "Post-Transfer Balances (Scenario 1)")
    
    # Assert balances
    acc1 = db["accounts"].find_one({"account_id": "ACC-001"})
    acc2 = db["accounts"].find_one({"account_id": "ACC-002"})
    assert acc1["balance"] == 3500.00, f"Expected 3500.00, got {acc1['balance']}"
    assert acc2["balance"] == 4500.00, f"Expected 4500.00, got {acc2['balance']}"
    print("  [ASSERTION PASSED] ACC-001 decremented to $3,500.00, ACC-002 incremented to $4,500.00.")

    # =========================================================================
    # SCENARIO 2: Insufficient Funds - Verify Atomicity & Rollback
    # =========================================================================
    print_banner("Scenario 2: Insufficient Funds Transfer ($5,000.00 from ACC-003 -> ACC-001)", "-")
    pre_acc3 = db["accounts"].find_one({"account_id": "ACC-003"})
    pre_acc1 = db["accounts"].find_one({"account_id": "ACC-001"})
    print(f"  Source ACC-003 Balance: ${pre_acc3['balance']:,.2f} | Requested Amount: $5,000.00")
    
    res2 = transfer_funds(
        client,
        from_acc="ACC-003",
        to_acc="ACC-001",
        amount=5000.00,
        description="Unauthorized Overdraft Attempt"
    )
    print_account_balances(db, "Post-Rollback Balances (Scenario 2)")
    
    post_acc3 = db["accounts"].find_one({"account_id": "ACC-003"})
    post_acc1 = db["accounts"].find_one({"account_id": "ACC-001"})
    
    # Verify atomicity (neither balance changed)
    assert post_acc3["balance"] == pre_acc3["balance"], "Source balance illegally altered!"
    assert post_acc1["balance"] == pre_acc1["balance"], "Destination balance illegally altered!"
    print("  [VERIFICATION PASSED] Atomic Rollback Confirmed:")
    print(f"    ACC-003: Pre=${pre_acc3['balance']:,.2f} == Post=${post_acc3['balance']:,.2f}")
    print(f"    ACC-001: Pre=${pre_acc1['balance']:,.2f} == Post=${post_acc1['balance']:,.2f}")
    print("    Zero partial updates occurred. Atomicity fully preserved.")

    # =========================================================================
    # SCENARIO 3: Activity 10.1 - Retry Logic with Exponential Backoff
    # =========================================================================
    print_banner("Scenario 3: Activity 10.1 - Exponential Backoff Retry Demonstration", "-")
    print("  Executing transfer ($400.00 from ACC-002 -> ACC-003) with active retry harness...")
    res3 = transfer_funds(
        client,
        from_acc="ACC-002",
        to_acc="ACC-003",
        amount=400.00,
        description="Vendor Settlement",
        enable_retry=True
    )
    print_account_balances(db, "Post-Scenario 3 Balances")

    # =========================================================================
    # SCENARIO 4: Concurrent Contention & TransientTransactionError Recovery
    # =========================================================================
    print_banner("Scenario 4: Concurrent Contention - Automatic Retry on Write Conflict", "-")
    print("  Simulating 2 concurrent transactions targeting ACC-001 simultaneously...")
    concurrent_results = []

    def worker_transfer(w_id, from_id, to_id, amt):
        res = transfer_funds(
            client,
            from_acc=from_id,
            to_acc=to_id,
            amount=amt,
            description=f"Concurrent Worker #{w_id}",
            enable_retry=True
        )
        concurrent_results.append((w_id, res))

    t1 = threading.Thread(target=worker_transfer, args=(1, "ACC-001", "ACC-002", 500.00))
    t2 = threading.Thread(target=worker_transfer, args=(2, "ACC-001", "ACC-003", 500.00))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    print_account_balances(db, "Final Post-Concurrency Balances (Scenario 4)")
    for wid, r in concurrent_results:
        print(f"  Worker #{wid}: Success={r.get('success')} | Attempts={r.get('attempts')} | Latency={r.get('latency_ms', 0):.1f}ms")

    # Audit Trail
    print_banner("Audit Trail: Immutable Transaction Ledger", "-")
    print(f"  {'Transaction ID':<22} | {'From':<10} | {'To':<10} | {'Amount ($)':>12} | {'Status':<10}")
    print("  " + "-" * 72)
    for record in db["transactions"].find({}, sort=[("timestamp", 1)]):
        print(f"  {record['transaction_id']:<22} | {record['from_account']:<10} | {record['to_account']:<10} | ${record['amount']:>11,.2f} | {record['status']:<10}")
    print("  " + "-" * 72)
    
    client.close()
    print_banner("LAB 10.1 COMPLETED SUCCESSFULLY")


if __name__ == "__main__":
    run_lab_01_demonstration()
