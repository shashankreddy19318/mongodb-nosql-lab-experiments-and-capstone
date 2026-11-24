# MongoDB Lab 09: The CAP Theorem & Write Concern Latency

Comprehensive laboratory implementation and demonstration suite for **Chapter 09: The CAP Theorem in Practice** (Sujeet Jagtap Textbook Curriculum).

[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/chintan/mongodb-lab09)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg)](https://www.python.org/)

---

## 📋 Table of Contents
1. [Overview & Objectives](#overview--objectives)
2. [Quickstart for Graders (Demonstration)](#quickstart-for-graders-demonstration)
3. [Lab 9.1: Write Concern Latency Benchmark](#lab-91-write-concern-latency-benchmark)
4. [CAP & PACELC Theoretical Matrix](#cap--pacelc-theoretical-matrix)
5. [Lab 9.2: Network Partition & Failover Simulation](#lab-92-network-partition--failover-simulation)
6. [Timeline of Partition Events](#timeline-of-partition-events)
7. [Docker Submission & Build Guide](#docker-submission--build-guide)
8. [File Structure](#file-structure)

---

## 🎯 Overview & Objectives
This lab provides concrete empirical evidence of the **CAP Theorem** and **PACELC Model** using a 3-node MongoDB replica set:
- **Lab 9.1:** Measures write latency, throughput, and percentiles (P50, P99) across write concerns (`w:1`, `w:majority`, `w:all`) and journaling options (`j:true` vs `j:false`) over 1,000 document writes.
- **Lab 9.2:** Simulates network partitions using Docker bridge network disconnections, observing leader step-down, write rejection (`NotWritablePrimary`), cluster degradation to read-only, leader re-election, and oplog catch-up.

---

## 🚀 Quickstart for Graders (Demonstration)

The entire laboratory suite is containerized. Evaluators can demonstrate all tasks with a single command:

### Option A: Automated Master Demonstration (Recommended)
```bash
docker run --rm -it chintan/mongodb-lab09:latest demo
```
*Executes Lab 9.1 latency benchmark (all 6 configurations) followed by Lab 9.2 partition simulation.*

### Option B: Interactive CLI Menu
```bash
docker run --rm -it chintan/mongodb-lab09:latest
```
*Presents a numbered menu allowing you to launch Lab 9.1, Lab 9.2, the failover observer, or interactive mongosh shell.*

### Option C: Full Multi-Container Cluster (Docker Compose)
```bash
docker compose up --build
```
*Orchestrates 3 isolated MongoDB replica set containers (`mongo-rs0-1`, `mongo-rs0-2`, `mongo-rs0-3`) on a custom bridge network alongside the demonstration runner.*

---

## 📊 Lab 9.1: Write Concern Latency Benchmark

### Empirical Results (1,000 Documents per Configuration)
| Configuration | Total Time (s) | Avg Latency (ms) | P50 Median (ms) | P99 Tail (ms) | Throughput (ops/s) | Slowdown vs Base |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`w:1, j:false`** | 2.031 s | **2.03 ms** | 1.61 ms | 6.71 ms | **492.5 ops/s** | **1.00x (Baseline)** |
| **`w:1, j:true`** | 5.122 s | **5.12 ms** | 4.67 ms | 13.16 ms | 195.2 ops/s | 2.53x |
| **`w:majority, j:false`** | 7.005 s | **7.00 ms** | 6.32 ms | 15.12 ms | 142.8 ops/s | 3.46x |
| **`w:majority, j:true`** | 6.670 s | **6.66 ms** | 6.16 ms | 14.73 ms | 149.9 ops/s | 3.29x |
| **`w:all (w:3), j:false`** | 4.638 s | **4.63 ms** | 4.25 ms | 8.91 ms | 215.6 ops/s | 2.29x |
| **`w:all (w:3), j:true`** | 8.075 s | **8.07 ms** | 7.31 ms | 19.38 ms | 123.8 ops/s | **3.98x** |

### Key Analytical Findings:
1. **`w:1` is fastest:** Returns immediately once the primary acknowledges in memory (WiredTiger cache). No network RPC round-trips required.
2. **`w:majority` latency cost:** Adds 2.5x to 3.5x latency because the primary holds acknowledgment until at least one secondary replicates and acknowledges the write.
3. **`w:all` cluster constraint:** Bound by the slowest node in the replica set, peaking at 8.07 ms average and 19.38 ms P99.
4. **Does journaling (`j:true`) add significant latency?**
   - **For `w:1`:** Yes (+152.6% latency overhead, 5.12 ms vs 2.03 ms) due to synchronous disk `fsync`.
   - **For `w:majority`:** No significant difference, because disk flush happens concurrently with network replication RTT.

---

## 🧭 CAP & PACELC Theoretical Matrix

| Write Concern | Latency | Durability Guarantee | CAP Classification | Target Workload / Scenario |
| :--- | :---: | :--- | :--- | :--- |
| **`w:1, j:false`** | **Lowest** (2.03 ms) | Data in primary memory cache only. Vulnerable to crash before checkpoint flush. | **AP-leaning** (High Availability) | Telemetry, IoT metrics, ephemeral clickstreams, caching layers. |
| **`w:1, j:true`** | **Low** (5.12 ms) | Data persisted on primary disk journal. Survives primary crash; vulnerable to failover rollback. | **CP-leaning** (Local Durability) | Standard CRUD records, user profiles, content management. |
| **`w:majority, j:true`** | **Medium** (6.66 ms) | Committed to majority of nodes (2/3). **Guaranteed zero rollback** on primary failover. | **Strong CP** (Strict Consistency) | Financial transactions, payments, accounts, inventory state. |
| **`w:all, j:true`** | **Highest** (8.07 ms) | Persisted on all 3 nodes. Maximum blast-radius protection. | **Strongest CP** (Blocks writes if any node fails) | Regulatory compliance archives, audit trails, key management. |

---

## ⚡ Lab 9.2: Network Partition & Failover Simulation

### 3-Phase Experiment Breakdown:
1. **Phase 1: Disconnect Secondary 1 (`mongo-rs0-2`)**
   - 2 of 3 voting nodes remain (`mongo-rs0-1` and `mongo-rs0-3`).
   - Quorum maintained (2 > 1.5). Primary maintains leadership.
   - `w:1` succeeds (3.3 ms); `w:majority` succeeds (74.6 ms); `w:all` **times out** after 3000 ms.
2. **Phase 2: Disconnect Secondary 2 (`mongo-rs0-3`)**
   - Primary `mongo-rs0-1` completely isolated (1 of 3 nodes).
   - Election timeout expires: **Primary automatically STEPS DOWN to SECONDARY at 02:41:28.300**.
   - All writes rejected with `NotWritablePrimary`. Cluster enters **read-only mode**, preventing split-brain.
3. **Phase 3: Reconnection & Recovery**
   - Reconnected both secondaries. Heartbeats resumed.
   - Quorum detected; election held (`mongo-rs0-3` elected Primary; priority takeover restores `mongo-rs0-1`).
   - Oplog catch-up completes; `w:majority` writes resume successfully.

---

## ⏱️ Timeline of Partition Events

```text
[02:41:05.243] [STATE       ] Initial 3-node cluster verified healthy. Primary: mongo-rs0-1
[02:41:05.302] [WRITE_BASE  ] Baseline writes succeed: w:1 (21.8ms), w:majority (33.4ms), w:all (2.4ms)
[02:41:05.338] [ACTION      ] Disconnecting mongo-rs0-2 from Docker network
[02:41:12.359] [MEMBER_CHECK] Majority maintained (2/3). mongo-rs0-1 remains PRIMARY
[02:41:12.362] [WRITE_P1    ] w:1 succeeds (3.3ms); w:majority succeeds (74.6ms); w:all TIMEOUT (3000ms)
[02:41:15.452] [ACTION      ] Disconnecting mongo-rs0-3. Primary mongo-rs0-1 is now isolated
[02:41:28.300] [STEP_DOWN   ] *** PRIMARY mongo-rs0-1 STEPS DOWN TO SECONDARY (Majority Lost) ***
[02:41:28.303] [WRITE_REJECT] All writes rejected (NotWritablePrimary). Cluster is READ-ONLY
[02:41:43.305] [ACTION      ] Reconnected secondaries to network. Quorum restored
[02:41:48.406] [ELECTION    ] Election held. All 3 nodes report Health: 1.0. Oplog catch-up completes
[02:42:39.112] [RECOVERY_OK ] Priority takeover restores mongo-rs0-1 as Primary. w:majority writes succeed
```

---

## 🐳 Docker Submission & Build Guide

### Local Build & Test:
```bash
# 1. Build Docker image
docker build -t mongodb-lab09:latest .

# 2. Run automated test
docker run --rm -it mongodb-lab09:latest demo
```

### Push to Docker Hub:
```bash
# 1. Log in to Docker Hub
docker login

# 2. Tag with your Docker Hub username
docker tag mongodb-lab09:latest chintan/mongodb-lab09:latest

# 3. Push image
docker push chintan/mongodb-lab09:latest
```
Public Docker Hub URL: `https://hub.docker.com/r/chintan/mongodb-lab09`

---

## 📁 File Structure
```text
exercise 9 nosql/
├── Dockerfile                                    # Container build definition
├── docker-compose.yml                            # Multi-container orchestration
├── entrypoint.sh                                 # Container entrypoint & CLI menu
├── demo_all.py                                   # Master end-to-end demo runner
├── lab_01_write_concern_latency.py               # Lab 9.1 benchmark script
├── lab_02_simulate_partition.py                  # Lab 9.2 partition simulation
├── lab_02_failover_observer.py                   # Real-time topology observer
├── generate_pdf.py                               # Academic PDF report generator
├── Lab_09_Report_CAP_Theorem_and_Write_Concerns.pdf # Official PDF submission report
└── README.md                                     # Project documentation
```
