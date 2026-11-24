# MongoDB Lab 10: Multi-Document Transactions & Concurrency

Comprehensive laboratory implementation, stress test, and demonstration suite for **Chapter 10: Transactions, Atomicity, and Durability** (Sujeet Jagtap Textbook Curriculum).

[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/chintan/mongodb-lab10)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Lab%20Status-Complete%20100%25-success.svg)]()

---

## 📋 Table of Contents
1. [Overview & Objectives](#overview--objectives)
2. [Quickstart for Graders (Demonstration)](#quickstart-for-graders-demonstration)
3. [Lab 10.1: Implement a Bank Transfer Transaction](#lab-101-implement-a-bank-transfer-transaction)
4. [Activity 10.1: Retry Logic with Exponential Backoff](#activity-101-retry-logic-with-exponential-backoff)
5. [Lab 10.2: Inventory Reservation with Deadlock Handling](#lab-102-inventory-reservation-with-deadlock-handling)
6. [Contention Stress Test: With vs Without Retry](#contention-stress-test-with-vs-without-retry)
7. [Throughput Benchmark across Concurrency Levels (1, 4, 8, 16 Threads)](#throughput-benchmark-across-concurrency-levels)
8. [Architectural Evaluation: Transactions vs findAndModify](#architectural-evaluation-transactions-vs-findandmodify)
9. [Docker Deployment & Verification Guide](#docker-deployment--verification-guide)
10. [Submission Files & Repository Structure](#submission-files--repository-structure)

---

## 🎯 Overview & Objectives

While single-document updates in MongoDB are inherently atomic, distributed enterprise workflows require multi-document and cross-collection **ACID transactional guarantees**. This repository delivers the complete solution for Chapter 10:
- **Lab 10.1 (Bank Transfer):** Multi-document financial transaction executing atomic debit, atomic credit, and audit log generation using PyMongo `ClientSession`. Guarantees snapshot isolation (`readConcern: snapshot`) and majority persistence (`writeConcern: majority`). Validates that insufficient funds abort the transaction and roll back both balances with zero data loss.
- **Activity 10.1 (Exponential Backoff):** Catches transient write conflicts (`TransientTransactionError` / `WriteConflict`, code 112) under concurrent execution and resolves them using randomized exponential backoff.
- **Lab 10.2 (Inventory Reservation):** Models an e-commerce inventory reservation and order placement system using optimistic concurrency control (OCC). Runs concurrency stress tests using Python `ThreadPoolExecutor` (8 simultaneous threads competing for 5 units), benchmarks throughput across 1, 4, 8, and 16 worker pools, and contrasts ACID multi-document transactions with single-document `findAndModify`.

---

## 🚀 Quickstart for Graders (Demonstration)

The entire laboratory suite is containerized. Evaluators can demonstrate all tasks with a single command:

### Option A: Automated Master Demonstration (Recommended)
```bash
docker run --rm -it --network host chintan/mongodb-lab10:latest demo
```
*Executes the complete Lab 10.1 suite (Scenarios 1-4) followed by Lab 10.2 (Contention, Throughput Benchmark, and findAndModify Comparison).*

### Option B: Interactive CLI Menu
```bash
docker run --rm -it --network host chintan/mongodb-lab10:latest
```
*Presents a numbered interactive menu to launch individual experiments, view contention dynamics, or open an interactive mongosh shell.*

### Option C: Complete Cluster Deployment (Docker Compose)
```bash
docker compose up --build
```
*Orchestrates 3 isolated MongoDB replica set containers (`mongo-rs0-1`, `mongo-rs0-2`, `mongo-rs0-3`) on a custom bridge network (`mongo-net`) alongside the demonstration runner.*

---

## 💳 Lab 10.1: Implement a Bank Transfer Transaction

### Schema Design
- **`accounts` Collection:** `{account_id: str, holder: str, balance: float, version: int}`
- **`transactions` Collection:** `{transaction_id: str, from_account: str, to_account: str, amount: float, description: str, timestamp: str, status: str}`

### Implementation Mechanics
Inside a `with client.start_session() as session:` block:
```python
with session.start_transaction(
    read_concern=ReadConcern(level="snapshot"),
    write_concern=WriteConcern(w="majority")
):
    # Atomic debit with balance threshold filter
    debit_result = accounts.update_one(
        {"account_id": from_acc, "balance": {"$gte": amount}},
        {"$inc": {"balance": -amount, "version": 1}},
        session=session
    )
    if debit_result.matched_count == 0:
        raise InsufficientFundsError("Insufficient funds")  # Triggers rollback

    # Atomic credit
    accounts.update_one(
        {"account_id": to_acc},
        {"$inc": {"balance": amount, "version": 1}},
        session=session
    )

    # Append immutable audit ledger
    transactions.insert_one(tx_record, session=session)
```

### Verification Scenarios
1. **Scenario 1 (Valid Transfer):** Transfers $1,500.00 from `ACC-001` ($5,000) to `ACC-002` ($3,000). Both balances update atomically to $3,500 and $4,500.
2. **Scenario 2 (Insufficient Funds Rollback):** `ACC-003` ($1,000) attempts to transfer $5,000.00 to `ACC-001`. Filter matches 0 documents, exception is raised, and transaction aborts. Verification confirms `ACC-003` remains $1,000.00 and `ACC-001` remains $3,500.00—**zero partial writes**.

---

## 🔁 Activity 10.1: Retry Logic with Exponential Backoff

When concurrent transactions contend for the same account documents, WiredTiger raises `TransientTransactionError` (Error Code 112: `WriteConflict`). Our retry harness catches this error label and applies exponential backoff:
$$\Delta t_{\text{backoff}} = 0.1 \times 2^{\text{attempt}-1} + \text{jitter}$$

### Empirical Concurrency Proof
Two worker threads target `ACC-001` simultaneously:
```text
Simulating 2 concurrent transactions targeting ACC-001 simultaneously...
[RETRY] Transient conflict encountered on attempt 1: Caused by :: Write conflict during plan execution and yielding is disabled. Retrying in 165.1ms...
[SUCCESS] Transferred $500.00 from ACC-001 to ACC-002 (TxID: TXN-1795384277-109, Attempts: 1, Latency: 8.9ms)
[SUCCESS] Transferred $500.00 from ACC-001 to ACC-003 (TxID: TXN-1795384277-887, Attempts: 2, Latency: 218.2ms)
```
Worker 1 commits on attempt 1; Worker 2 detects the conflict, backs off for 165ms, retries, and commits successfully on attempt 2!

---

## 📦 Lab 10.2: Inventory Reservation with Deadlock Handling

### Schema Design
- **`inventory` Collection:** `{product_id: str, name: str, stock: int, price: float, version: int}`
- **`orders` Collection:** `{order_id: str, customer_id: str, items: [...], status: str, total: float, created_at: str}`

---

## ⚔️ Contention Stress Test: With vs Without Retry

We dispatch **8 simultaneous threads** using Python's `ThreadPoolExecutor` to reserve 1 unit each when only **5 units** exist in inventory:

| Metric / Dimension | Condition A: WITHOUT Retry | Condition B: WITH Retry (OCC Backoff) | Engineering Significance |
| :--- | :---: | :---: | :--- |
| **Concurrent Worker Threads** | 8 threads | 8 threads | Extreme lock contention on single document |
| **Initial Inventory Stock** | 5 units | 5 units | Contention ratio: 1.6x |
| **Successful Reservations** | **1 reservation** | **5 reservations** | Retry logic guarantees 100% allocation |
| **Write Conflict Aborts** | **7 failed threads** | **0 unhandled aborts** | Conflicts resolved via backoff |
| **Stock Exhaustion Rejections** | 0 (never reached) | **3 clean rejections** | Clean rejection once stock reaches 0 |
| **Remaining Stock in DB** | 4 units (phantom stock) | **0 units (fully cleared)** | Zero stranded units |
| **Confirmed Orders in DB** | 1 order | **5 orders** | Strict 1:1 inventory-to-order parity |
| **Total Wall-Clock Latency** | 86.2 ms (fast failure) | 255.8 ms (backoff resolution) | Latency trade-off for consistency |

---

## 📊 Throughput Benchmark across Concurrency Levels

Testing 10 reservation operations per thread across increasing concurrency pools:

| Concurrency Level | Total Ops | Wall Time (s) | Throughput (ops/sec) | Avg Latency | P95 Latency | Contention Dynamics |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1 Worker** | 10 | 0.14 s | **73.5 ops/sec** | 13.4 ms | 59.3 ms | Zero contention; purely serial latency |
| **4 Workers** | 40 | 0.36 s | **112.0 ops/sec** | 29.9 ms | 256.2 ms | Peak throughput; 1.52x scaling efficiency |
| **8 Workers** | 80 | 1.03 s | **77.9 ops/sec** | 76.8 ms | 484.9 ms | Throughput declines due to lock contention |
| **16 Workers** | 160 | 1.81 s | **87.3 ops/sec** | 143.8 ms | 573.3 ms | Plateau; P95 tail latency surges 9.6x |

---

## 🏛️ Architectural Evaluation: Transactions vs findAndModify

| Evaluation Vector | Multi-Document ACID Transactions | findAndModify (`find_one_and_update`) |
| :--- | :--- | :--- |
| **Cross-Collection Atomicity** | **Guaranteed:** Decrement and order creation commit or abort together. | **None:** Decrement succeeds, but order creation is a separate uncoordinated step. |
| **Crash Inconsistency Risk** | **Zero Risk:** Automatically rolls back on crash or validation error. | **High Vulnerability:** Crash after decrement permanently loses inventory without order record! |
| **Isolation Level** | **Snapshot Isolation:** Point-in-time multi-document read view. | **Read Committed:** Single-document lock only. |
| **Throughput (Sequential)** | ~90 - 110 ops/sec (Two-Phase Commit & session overhead). | ~105 - 140 ops/sec (Lightweight single-node atomic operation). |
| **Contention Failure Mode** | Aborts with `WriteConflict` (requires retry). | Queues on document write lock (no retry needed). |
| **Recommended Use Cases** | Financial transfers, inventory checkout, balance transfers. | Counters, sequence generators, rate limiters. |

---

## 🐳 Docker Deployment & Verification Guide

### Build the Image Locally
```bash
docker build -t chintan/mongodb-lab10:latest -t mongodb-lab10:latest .
```

### Push to Docker Hub
```bash
docker push chintan/mongodb-lab10:latest
```

### Execute Tests Inside Container
```bash
# Run Master Demonstration
docker run --rm -it --network host chintan/mongodb-lab10:latest demo

# Run Lab 10.1 Bank Transfer Suite
docker run --rm -it --network host chintan/mongodb-lab10:latest 1

# Run Lab 10.2 Inventory Reservation Suite
docker run --rm -it --network host chintan/mongodb-lab10:latest 2
```

---

## 📁 Submission Files & Repository Structure

```text
exercise 10 nosql/
├── lab_01_bank_transfer.py         # Lab 10.1 Bank Transfer & Activity 10.1 Retry Logic
├── lab_02_inventory_reservation.py # Lab 10.2 Inventory Reservation, OCC & Benchmarking
├── demo_all.py                     # Master Demonstration Runner (Labs 10.1 + 10.2)
├── generate_pdf.py                 # ReportLab script producing 4-page academic PDF
├── Lab_10_Report_Multi_Document_Transactions_and_Concurrency.pdf # Submission PDF Report
├── entrypoint.sh                   # Interactive CLI menu & container command dispatcher
├── Dockerfile                      # Production container image definition
├── docker-compose.yml              # Complete 3-node replica set + runner orchestration
└── README.md                       # Comprehensive documentation & grading guide
```
