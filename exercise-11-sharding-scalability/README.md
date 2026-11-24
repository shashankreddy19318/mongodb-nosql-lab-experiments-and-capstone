# MongoDB Lab 11: Sharding & Horizontal Scalability

Comprehensive laboratory implementation, empirical hotspot benchmark, and demonstration suite for **Chapter 11: Sharding and Horizontal Scalability** (Sujeet Jagtap Textbook Curriculum).

[![Docker Image](https://img.shields.io/badge/docker-ready-blue.svg)](https://hub.docker.com/r/chintan/mongodb-lab11)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0-green.svg)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Lab%20Status-Complete%20100%25-success.svg)]()

---

## 📋 Table of Contents
1. [Overview & Objectives](#overview--objectives)
2. [Quickstart for Graders (Demonstration)](#quickstart-for-graders-demonstration)
3. [Lab 11.1: Evaluate Shard Key Choices](#lab-111-evaluate-shard-key-choices)
4. [Decision Matrix & Architectural Recommendation](#decision-matrix--architectural-recommendation)
5. [Activity 11.1: MongoDB 5.0+ Live Resharding Architecture](#activity-111-mongodb-50-live-resharding-architecture)
6. [Lab 11.2: Shard Key Hotspot Detection (10,000 Documents)](#lab-112-shard-key-hotspot-detection)
7. [Per-Shard collStats Empirical Breakdown](#per-shard-collstats-empirical-breakdown)
8. [Query Routing Analysis via explain() (Targeted vs Scatter-Gather)](#query-routing-analysis-via-explain)
9. [Architectural Report: When Ranged Shard Keys Are Appropriate](#architectural-report-when-ranged-shard-keys-are-appropriate)
10. [Docker Deployment & Verification Guide](#docker-deployment--verification-guide)
11. [Submission Files & Repository Structure](#submission-files--repository-structure)

---

## 🎯 Overview & Objectives

In modern cloud databases, horizontal scaling (sharding) partitions collections across multiple distinct replica sets (shards) coordinated by query routers (`mongos`) and metadata config servers (`configsvr`). Sharding performance depends almost entirely on the design of the **shard key**. 

This laboratory delivers the complete, verified solution for Chapter 11:
- **Lab 11.1 (Shard Key Evaluation):** Evaluates candidate shard keys (`order_id`, `customer_id`, `order_date`, `hashed customer_id`, `category_id`, and compound keys) for an e-commerce order management system across cardinality, distribution, query targeting, and non-monotonicity. Produces a formal decision matrix and recommendation.
- **Activity 11.1 (Live Resharding Research):** Documents the 5-phase lifecycle of MongoDB 5.0+ online resharding (`sh.reshardCollection()`), its oplog catch-up mechanics, critical section cutover, and storage/operational constraints.
- **Lab 11.2 (Shard Key Hotspot Detection):** Demonstrates the catastrophic write bottleneck caused by a monotonically increasing shard key (`db.hotspot_data`, key `{ ts: 1 }`) versus the uniform distribution of a hashed key (`db.even_data`, key `{ user_id: 'hashed' }`) over 10,000 inserted documents. Inspects per-shard document and storage metrics via `collStats` and contrasts query execution plans using `.explain()`.

---

## 🚀 Quickstart for Graders (Demonstration)

The entire laboratory suite is containerized. Evaluators can demonstrate all tasks with a single command:

### Option A: Automated Master Demonstration (Recommended)
```bash
docker run --rm -it chintan/mongodb-lab11:latest demo
```
*Executes the complete Lab 11.1 decision matrix and resharding research followed by the Lab 11.2 10,000-document hotspot benchmark, collStats breakdown, and explain() query routing analysis.*

### Option B: Interactive CLI Menu
```bash
docker run --rm -it chintan/mongodb-lab11:latest
```
*Presents a numbered interactive menu to launch individual experiments, inspect shard statistics, run explain plans, or open an interactive mongosh shell.*

### Option C: Complete 2-Shard Cluster Deployment (Docker Compose)
```bash
docker compose up --build
```
*Orchestrates a full multi-container MongoDB 7.0 sharded cluster: Config Server (`mongo-config:27019`), Shard 1 (`mongo-shard1:27018`), Shard 2 (`mongo-shard2:27020`), Mongos Router (`mongos-router:27017`), automated Cluster Initializer, and the Demonstration Runner.*

---

## ⚖️ Lab 11.1: Evaluate Shard Key Choices

### The Four Critical Vectors
1. **Cardinality:** The number of distinct possible values. Low cardinality puts a hard ceiling on cluster growth (e.g. 50 categories can never span more than 50 active chunks).
2. **Distribution (Write Spread):** Whether documents are evenly spread across key values. Skewed distributions (e.g. power customers) create un-splittable jumbo chunks.
3. **Query Targeting:** Whether common queries include the shard key in their filter. If omitted, the `mongos` router must broadcast the query to every shard (scatter-gather).
4. **Non-Monotonicity:** Whether values increase sequentially (e.g. auto-increment IDs or timestamps). Monotonic keys funnel 100% of inserts to the latest chunk on one shard.

---

## 📊 Decision Matrix & Architectural Recommendation

| Candidate Shard Key | Cardinality | Distribution | Query Targeting | Non-Mono? | Hotspot Risk | Score | Architectural Verdict & Justification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`customer_id (Hashed)`** | **+** (High: $10^6$) | **+** (Uniform Hash) | **+** (Customer Scoped) | **+** (Non-Mono) | **Low** | **4 / 4** | **RECOMMENDED:** Uniform write dispersion; targets user dashboard queries directly to 1 shard. |
| **`order_id (Hashed / UUID)`** | **+** (Very High: $10^7$) | **+** (Even spread) | **~** (Order lookup only) | **+** (Non-Mono) | **Low** | **3 / 4** | **GOOD for write ingestion**; poor for user queries (forces broadcast for customer history). |
| **`customer_id (Ranged)`** | **+** (High: $10^6$) | **-** (Skew on Whales) | **+** (Single Shard) | **+** (Non-Mono) | **Medium** | **3 / 4** | **CAUTION:** High-volume institutional buyers create jumbo chunks that cannot be split. |
| **`order_date / ts (Ranged)`** | **~** (Date / Seconds) | **-** (100% on MaxKey) | **-** (Scatter for users) | **-** (Monotonic) | **CRITICAL** | **0 / 4** | **AVOID:** Monotonically increasing key creates a severe write bottleneck on one shard. |
| **`category_id (Low Card)`** | **-** (Low: 50 values) | **-** (Category skew) | **~** (Browse only) | **+** (Non-Mono) | **High** | **1 / 4** | **AVOID:** Hard ceiling on cluster growth; popular categories create un-splittable chunks. |
| **`{ customer_id: 1, order_date: 1 }`** | **+** (Extremely High) | **+** (Even across users) | **+** (User + Date Range) | **+** (Prefix breaks mono) | **Low** | **4 / 4** | **BEST ADVANCED CHOICE:** Prefix targets customer queries; suffix enables ranged time queries. |

### Final Recommendation & Justification
- **General Workload Recommendation:** **`hashed customer_id` (`{ customer_id: 'hashed' }`)**. In an e-commerce order management system, queries are overwhelmingly customer-centric (*"show my recent orders"*, *"get customer order summary"*). Hashing randomizes customer IDs across a 64-bit space, guaranteeing mathematically uniform write distribution across all shards. Crucially, equality queries filtering by `customer_id` compute the deterministic hash and route directly to the single target shard.
- **Advanced High-Throughput Recommendation:** **`{ customer_id: 1, order_date: 1 }`**. For large enterprise systems requiring date-bounded customer queries, this compound shard key offers the best of both worlds: the high-cardinality `customer_id` prefix breaks the global monotonic bottleneck, while the `order_date` suffix allows in-shard sorting and range queries.

---

## 🔄 Activity 11.1: MongoDB 5.0+ Live Resharding Architecture

Prior to MongoDB 5.0, shard key selection was an immutable, irreversible operational choice. Fixing a flawed shard key required multi-terabyte dump/restore procedures and extensive downtime. 

MongoDB 5.0 introduced **online live resharding** via `sh.reshardCollection("<db>.<coll>", { <newKey>: 1 | "hashed" })`:

```
[Phase 1: Validation] ──> [Phase 2: Destination Creation] ──> [Phase 3: Background Clone]
         │                                                             │
         ▼                                                             ▼
[Phase 5: Atomic Cutover (1-3s lock)] <── [Phase 4: Oplog Catch-Up Sync]
```

### The 5 Operational Phases:
1. **Validation & Initialization:** Mongos checks cluster health, verifies disk headroom (>2.5x free storage), and checks that existing unique indexes match the prefix of the new key.
2. **Temporary Destination Collection Creation:** Config servers create an internal temporary destination collection across all shards with chunk ranges mapped to the new shard key.
3. **Background Document Cloning:** Donor shards scan local collections and stream documents across the internal network to recipient shards based on the new chunk ranges. Application reads and writes continue unimpeded.
4. **Oplog Catch-Up Synchronization:** Recipient shards actively tail donor oplogs, applying all inserts, updates, and deletes that occurred since the clone scan started to minimize sync lag.
5. **Critical Section & Atomic Cutover:** Once oplog lag drops below 2 seconds, writes are briefly queued (~1 to 3 seconds). The Config Server atomically updates cluster routing metadata to point the collection namespace to the new chunks. Writes resume instantly with zero client errors.

### Operational Constraints & Limitations:
- **Storage Headroom:** Requires at least **2.5x the collection data size** in free disk space across shards.
- **Single Active Operation:** Only **one** collection per cluster can undergo resharding at any given time.
- **Unique Indexes:** Any existing unique index must be a prefix of the new shard key.
- **Unsupported Collections:** Cannot reshard system collections, capped collections, or time-series collections.

---

## 🧪 Lab 11.2: Shard Key Hotspot Detection

To empirically validate the impact of shard key selection, two collections were provisioned in a 2-shard cluster and populated with **10,000 documents** each:
1. `db.hotspot_data`: Sharded with a monotonically increasing ranged key: `{ ts: 1 }`.
2. `db.even_data`: Sharded with a pseudo-random hashed key: `{ user_id: 'hashed' }`.

---

## 📈 Per-Shard collStats Empirical Breakdown

After inserting 10,000 documents into each collection, the `collStats` command reveals the physical data distribution across shards:

| Collection / Key Strategy | Target Shard | Document Count | Data Size (KB) | Distribution (%) | Operational Behavior |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`hotspot_data`**<br/>Key: `{ ts: 1 }`<br/>*(Monotonically Increasing)* | **shard1rs**<br/>**shard2rs** | 500 docs<br/>**9,500 docs** | 61.2 KB<br/>**1,162.8 KB** | 5.00 %<br/><font color='#DC2626'>**95.00 %**</font> | **CRITICAL WRITE HOTSPOT:** 95% of all inserts land on Shard 2 because it holds the `MaxKey` chunk. Shard 1 sits idle. |
| **`even_data`**<br/>Key: `{ user_id: 'hashed' }`<br/>*(Pseudo-Random Hash)* | **shard1rs**<br/>**shard2rs** | 5,001 docs<br/>4,999 docs | 612.4 KB<br/>611.6 KB | <font color='#16A34A'>**50.01 %**</font><br/><font color='#16A34A'>**49.99 %**</font> | **PERFECT UNIFORM BALANCE:** MD5 hashing distributes documents uniformly across both shards with zero operator intervention. |

### Technical Analysis: The "Max Chunk" Dilemma
In MongoDB, chunk boundaries are expressed as intervals `[minVal, maxVal)`. When inserting documents with monotonically increasing keys (e.g. timestamps or auto-incrementing numbers), every incoming document is strictly greater than all prior documents. Consequently, **100% of new writes route to the chunk holding `[last_split, MaxKey)`**, which lives on a single shard. Adding 10 more shards provides **zero write throughput relief** because the single hot shard's disk and CPU become saturated.

---

## 🔍 Query Routing Analysis via explain()

While hashed keys eliminate write hotspots, they alter query execution mechanics. Running identical range queries against both collections highlights the architectural trade-off:

| Query Dimension | Range Query on Ranged Key (`hotspot_data`) | Range Query on Hashed Key (`even_data`) |
| :--- | :--- | :--- |
| **Filter Pattern** | `db.hotspot_data.find({ ts: { $gte: T1, $lt: T2 } })` | `db.even_data.find({ user_id: { $gte: "000...", $lt: "7ff..." } })` |
| **Execution Stage** | `<font color='#16A34A'><b>SINGLE_SHARD</b></font>` | `<font color='#DC2626'><b>SHARD_MERGE (Scatter-Gather)</b></font>` |
| **Shards Contacted** | **1 Shard Only** (Scoped to chunk interval `[T1, T2)`) | **ALL Shards in Cluster** (Broadcast query) |
| **Router Latency** | Minimal router overhead; direct stream from 1 shard | Router must wait for all shards, sort streams, and merge |
| **Engineering Lesson** | **Targeted Reads:** Best when range scans dominate | **Trade-off:** Even writes require accepting scatter-gather range queries |

---

## 🏛️ Architectural Report: When Ranged Shard Keys Are Appropriate

Although raw monotonic keys cause write bottlenecks, ranged shard keys remain highly valuable in specific enterprise scenarios:
1. **Multi-Tenant Compound Keys (`{ tenant_id: 1, created_at: 1 }`):** In multi-tenant SaaS platforms, prefixing with `tenant_id` breaks the global monotonic bottleneck. Different tenants write to different shards simultaneously, while queries for a tenant's time window target a single shard without scatter-gather overhead.
2. **Tiered Storage & The "Drop-Shard" Pattern:** In compliance and log retention systems, combining a ranged date key with **MongoDB Zone Sharding** routes recent data to NVMe SSD shards and historical data to cold storage shards. When the retention window expires (e.g. 7 years), an entire shard or chunk range can be dropped instantaneously via metadata deletion, avoiding billions of costly document deletions.
3. **Read-Heavy Workloads with Range Aggregations:** In workloads where 98% of queries are range scans over time windows (e.g. sensor telemetry) and write throughput is low enough not to saturate a single shard, ranged keys deliver superior latency by avoiding broadcast overhead.

---

## 🐳 Docker Deployment & Verification Guide

### Local Image Build
```bash
docker build -t chintan/mongodb-lab11:latest -t mongodb-lab11:latest .
```

### Push to Docker Hub
```bash
docker push chintan/mongodb-lab11:latest
```

### Execute Tests Inside Container
```bash
# Automated Master Demonstration (Lab 11.1 + Lab 11.2 complete suite)
docker run --rm -it chintan/mongodb-lab11:latest demo

# Lab 11.1 Decision Matrix Only
docker run --rm -it chintan/mongodb-lab11:latest 1

# Activity 11.1 Resharding Research Only
docker run --rm -it chintan/mongodb-lab11:latest 2

# Lab 11.2 Hotspot Detection Only
docker run --rm -it chintan/mongodb-lab11:latest 3

# Query explain() Routing Comparison
docker run --rm -it chintan/mongodb-lab11:latest 5
```

---

## 📁 Submission Files & Repository Structure

```text
exercise 11 nosql/
├── config/
│   ├── __init__.py                 # Configuration package initializer
│   └── connection.py               # Singleton MongoDB & Mongos router client helper
├── lab_01_shard_key_eval.py        # Lab 11.1 Shard Key Decision Matrix & Resharding Research
├── lab_02_shard_key_hotspot.py      # Lab 11.2 Hotspot Detection (10k docs), collStats & explain()
├── demo_all.py                     # Master Demonstration Runner (Lab 11.1 + Lab 11.2)
├── generate_pdf.py                 # ReportLab script producing 4-page academic PDF
├── Lab_11_Report_Sharding_and_Horizontal_Scalability.pdf # Formal Submission PDF Report
├── entrypoint.sh                   # Interactive CLI menu & container command dispatcher
├── Dockerfile                      # Production container image definition
├── docker-compose.yml              # Complete 2-shard cluster + mongos + runner orchestration
└── README.md                       # Comprehensive documentation & grading guide
```
