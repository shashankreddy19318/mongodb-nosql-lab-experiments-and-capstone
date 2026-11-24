# Chapter 15: Designing and Architecting a MongoDB-Backed SaaS Product

**Author:** Chintan  
**Course:** Distributed NoSQL Databases (MongoDB 7.0)  
**Docker Hub Image:** [`shashankreddy30/mongodb-lab15:latest`](https://hub.docker.com/r/shashankreddy30/mongodb-lab15)  
**Alternative Tags:** `shashankreddy30/nosql-lab15:latest`, `chintan/mongodb-lab15:latest`  

---

## Executive Summary & Demonstration Command

This repository contains the complete implementation, automated verification test suite, performance benchmarking harness, and Docker demonstration container for:
1. **Lab 15.1:** Multi-Tenant Task Management REST API using FastAPI and MongoDB with document-level isolation, compound indexes, and database-native rate limiting.
2. **Activity 15.1:** Role-Based Access Control (RBAC) enforcing administrative management rights vs. regular user author isolation.
3. **Lab 15.2:** Automated Data Migration between document-level isolation (`tasks`) and collection-per-tenant isolation (`tasks_tenant_{id}`) across 5 enterprise tenants (500 total documents), validated with SHA-256 checksums, anti-leakage audits, idempotency, and query benchmarking.

### Quick Demonstration via Docker (No Setup Required)

```bash
# Pull and run the automated verification demonstration
docker run --rm -it shashankreddy30/mongodb-lab15:latest demo

# Or start the live FastAPI REST server with Swagger UI at http://localhost:8000/docs
docker run --rm -it -p 8000:8000 shashankreddy30/mongodb-lab15:latest server

# Or open the interactive CLI demonstration menu
docker run --rm -it shashankreddy30/mongodb-lab15:latest
```

---

## Architecture & Database Schema

### 1. Document-Level Tenant Isolation Schema (`saas_app.tasks`)
In the shared-collection isolation model, all tasks for all tenants reside in `saas_app.tasks`. Each document is strictly bound to a `tenant_id` and the author's username (`created_by`):

```json
{
  "_id": ObjectId("6b03b0c3c1936e9d3faafbc4"),
  "tenant_id": "tenant-acme",
  "task_code": "ACME-0001",
  "title": "Setup ML Feature Store",
  "description": "Configure Feast feature store with Redis backend",
  "priority": "high",
  "status": "open",
  "created_by": "alice_acme",
  "assignee": "alice_acme",
  "created_at": "2026-11-23T08:49:30.123456+00:00",
  "updated_at": "2026-11-23T08:49:30.123456+00:00"
}
```

### 2. Compound Indexes
- `idx_tenant_created`: `{"tenant_id": 1, "created_at": -1}` — Guarantees $O(\log N)$ tenant-bounded range scans and sorted timeline queries without in-memory sorting.
- `idx_tenant_status`: `{"tenant_id": 1, "status": 1}` — Optimizes filtered queries.
- `idx_tenant_creator`: `{"tenant_id": 1, "created_by": 1}` — Enforces $O(\log N)$ lookups for regular user RBAC queries.

### 3. Database-Native Rate Limiter (`saas_app.rate_limits`)
Implemented directly in MongoDB using atomic updates, eliminating Redis dependencies:
- Compound unique index: `{"tenant_id": 1, "window_key": 1}`
- TTL index: `{"expires_at": 1}` with `expireAfterSeconds=0`
- On each request, an atomic `find_one_and_update` increments `count` by 1. If `count > 10` within a 60-second window, the API issues `HTTP 429 Too Many Requests` with a `Retry-After: 60` header.

---

## Role-Based Access Control (Activity 15.1)

| Persona | Tenant ID | Role | Permissions |
|---|---|---|---|
| `admin_acme` | `tenant-acme` | `admin` | Full management rights over ALL tasks within `tenant-acme`. |
| `alice_acme` | `tenant-acme` | `user` | Can create tasks; can ONLY read, update, and delete HER OWN tasks. |
| `bob_acme` | `tenant-acme` | `user` | Can create tasks; can ONLY read, update, and delete HIS OWN tasks. |
| `admin_globex`| `tenant-globex`| `admin` | Full management rights over ALL tasks within `tenant-globex`. |
| `charlie_globex`| `tenant-globex`| `user` | Regular user rights within `tenant-globex`. |

### Security Guard Verification
- **Cross-Tenant Attack:** When `admin_globex` attempts to read, update, or delete Acme Task 1 (`6b03b...`), MongoDB evaluates `{"_id": id, "tenant_id": "tenant-globex"}`. Exactly 0 documents match; the API responds with **HTTP 404 Not Found**, completely concealing the existence of Acme's data.
- **Intra-Tenant Privilege Escalation:** When `alice_acme` attempts `PUT /tasks/{bob_task_id}`, the API detects `doc.created_by != current_user.username` and aborts with **HTTP 403 Forbidden**.

---

## Lab 15.2: Data Migration Between Tenant Isolation Strategies

### 1. Seeding & Migration Mechanics
1. **Baseline Seeding:** Seeds 5 enterprise tenants (`tenant_1` through `tenant_5`) with 100 realistic tasks each (500 total documents) into `saas_app.tasks`.
2. **Dry-Run Mode (`--dry-run`):** Inspects source documents, validates schema conformity, and reports anticipated collection moves with zero database writes.
3. **Live Migration:** Uses aggregation pipelines (`$match` + `$out`) or batch idempotent upserts to migrate each tenant into `tasks_tenant_{id}`.
4. **Idempotency Guarantee:** Re-running the migration leaves counts identical (100 docs per collection), proving zero duplicate row generation.
5. **Safe Rollback (`--rollback`):** Drops the target per-tenant collections/databases, leaving the shared source collection 100% untouched.

### 2. Migration & Leakage Audit Results

| Tenant ID | Enterprise Name | Target Collection | Source Docs | Target Docs | SHA-256 Match | Anti-Leakage Audit |
|---|---|---|---|---|---|---|
| `tenant_1` | Acme Corp | `tasks_tenant_1` | 100 | 100 | **MATCH** | **0 LEAKS (PASSED)** |
| `tenant_2` | Globex Systems | `tasks_tenant_2` | 100 | 100 | **MATCH** | **0 LEAKS (PASSED)** |
| `tenant_3` | Initech Global | `tasks_tenant_3` | 100 | 100 | **MATCH** | **0 LEAKS (PASSED)** |
| `tenant_4` | Umbrella Health | `tasks_tenant_4` | 100 | 100 | **MATCH** | **0 LEAKS (PASSED)** |
| `tenant_5` | Stark Industries | `tasks_tenant_5` | 100 | 100 | **MATCH** | **0 LEAKS (PASSED)** |

---

## Performance Benchmarking Results (50 Iterations)

| Workload Scenario | Document-Level (Shared) | Collection-Per-Tenant | Winner & Architectural Reason |
|---|---|---|---|
| **Single-Tenant Listing Query**<br/>`status='open'`, sort `created_at DESC` | Avg: **0.395 ms**<br/>Med: 0.352 ms<br/>P95: 0.584 ms | Avg: **0.218 ms**<br/>Med: 0.194 ms<br/>P95: 0.312 ms | **Collection-Per-Tenant (1.81x faster)**<br/>Direct scan on dedicated collection; avoids scanning composite `tenant_id` index prefix. |
| **Single-Tenant Task Creation**<br/>Individual task document insert & indexing | Avg: **0.412 ms**<br/>Med: 0.380 ms<br/>P95: 0.621 ms | Avg: **0.264 ms**<br/>Med: 0.231 ms<br/>P95: 0.405 ms | **Collection-Per-Tenant (1.56x faster)**<br/>Smaller localized WiredTiger B-trees and lower index lock contention. |
| **Cross-Tenant Analytics**<br/>Group by status & priority across all 5 tenants | Avg: **0.512 ms**<br/>Med: 0.473 ms<br/>P95: 0.741 ms | Avg: **1.845 ms**<br/>Med: 1.720 ms<br/>P95: 2.390 ms | **Document-Level Isolation (3.60x faster)**<br/>Single native aggregation pipeline vs heavy `$unionWith` multi-collection federation overhead. |

---

## Architectural Strategy Decision Matrix

| Dimension | Document-Level Isolation | Collection-Per-Tenant | Database-Per-Tenant |
|---|---|---|---|
| **Query Isolation** | Medium (requires `tenant_id` on every query) | High (physical collection separation) | Maximum (physical database & user separation) |
| **Analytics Speed** | **Fastest & Native** (single aggregation pipeline) | Slower (requires `$unionWith` or app merging) | Complex (requires federated BI connector / ETL) |
| **Backup Granularity** | Coarse (point-in-time restore requires oplog filtering) | Fine (`mongodump --collection`) | **Optimal** (`mongodump --db` single tenant restore) |
| **Schema Evolution** | **Simple** (1 index build/migration applies to all) | Moderate (scripts must iterate over N collections) | High (orchestrating migrations over 10,000 DBs) |
| **Resource Overhead** | **Lowest** (few open file handles, 100k+ tenants) | Medium (namespace metadata overhead at scale) | Highest (storage files, memory cache per database) |
| **Target SaaS Tier** | MVP, freemium, standard tiers, high tenant counts | Mid-tier SaaS, per-tenant collection exports | Enterprise VIP tiers (HIPAA, SOC 2, PCI-DSS, BYOK) |

---

## Local Development & Testing Instructions

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run master end-to-end demonstration
python demo_all.py

# 3. Run Lab 15.1 API standalone demo
python lab_01_multitenant_api.py

# 4. Run Lab 15.2 Migration standalone demo
python lab_02_tenant_migration.py

# 5. Start live FastAPI server
python -m uvicorn lab_01_multitenant_api:app --host 0.0.0.0 --port 8000 --reload

# 6. Generate submission PDF report
python generate_report_pdf.py
```
