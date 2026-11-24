# MongoDB Security: Authentication, RBAC, Views & TLS Encryption (Chapter 12)

Official complete solution and Docker container demonstration for **NoSQL Databases using MongoDB - Chapter 12: Database Security and the CIA Triad**.

---

## 📋 Table of Contents
1. [Overview & Objectives](#overview--objectives)
2. [Architecture & Security Framework](#architecture--security-framework)
3. [Lab 12.1: Authentication & Least-Privilege RBAC](#lab-121-authentication--least-privilege-rbac)
4. [Activity 12.1: Field-Level Redaction via Views](#activity-121-field-level-redaction-via-views)
5. [Lab 12.2: TLS / Encryption-in-Transit Setup](#lab-122-tls--encryption-in-transit-setup)
6. [Automated Demonstration with Docker](#automated-demonstration-with-docker)
7. [Docker Hub Deployment & Grading Guide](#docker-hub-deployment--grading-guide)
8. [File Structure](#file-structure)

---

## 🎯 Overview & Objectives

In production database deployments, security is enforced through defense-in-depth across the **CIA Triad** (Confidentiality, Integrity, Availability):

* **Confidentiality:** Restricting access to authorized principals via **SCRAM-SHA Authentication**, least-privilege **Role-Based Access Control (RBAC)**, field-level **Aggregation Views**, and network **TLS/SSL Encryption**.
* **Integrity:** Enforcing schema validation and preventing tampering or unauthorized modification.
* **Availability:** Ensuring cluster high availability and service uptime using replica sets and distributed sharding.

This repository encapsulates the full solution for:
* **Lab 12.1:** Configures MongoDB authentication (`--auth`), sets up an administrative user, and enforces least-privilege custom roles for application readers (`app_user_read`), writers (`app_user_write`), and restricted analysts.
* **Activity 12.1:** Implements field-level redaction using a MongoDB view (`employees_safe`) with an aggregation pipeline (`$project`) to completely omit sensitive salary data (`$$REMOVE`) and dynamically mask SSNs (`***-**-XXXX`) for non-HR personnel.
* **Lab 12.2:** Deploys a dedicated Certificate Authority (CA), generates server and client certificates with Subject Alternative Names (SAN), enforces `--tlsMode requireTLS`, proves rejection of unencrypted traffic, and validates encrypted PyMongo connections.

---

## 🏗 Architecture & Security Framework

### 1. MongoDB Sharding Cluster Architecture
In large-scale distributed deployments, client applications connect through stateless `mongos` query routers, which coordinate metadata with the Config Server Replica Set and route operations to distinct Shard Replica Sets:

```
                  +-----------------------+
                  |  Application / Client |
                  +-----------+-----------+
                              |
                              v
                  +-----------------------+
                  |     mongos Router     |
                  +-----+-----+-----+-----+
                        |     |     |
         +--------------+     |     +---------------+
         v                    v                     v
+------------------+ +------------------+ +------------------+
|     Shard 1      | |  Config Servers  | |     Shard 3      |
| (Primary/Second) | |   Replica Set    | | (Primary/Second) |
+------------------+ +------------------+ +------------------+
                              ^
                              |
                     +--------+---------+
                     |     Shard 2      |
                     | (Primary/Second) |
                     +------------------+
```

### 2. CIA Triad Defense Layers & Attack Surface Mitigation
```
+----------------------------------------------------------------------------------------------------+
|                                           ATTACK SURFACE                                           |
|  [Unauthenticated Access]   [Weak Credentials]     [Network Eavesdropping]      [Insider Threat]   |
+-------------+----------------------+--------------------------+-------------------------+----------+
              |                      |                          |                         |
           prevents               prevents                   prevents                  prevents
              |                      |                          |                         |
              v                      v                          v                         v
+----------------------------------------------------------------------------------------------------+
|                                      MONGODB SECURITY CONTROLS                                     |
|  [SCRAM-SHA Auth]           [RBAC Roles]               [TLS Encryption]          [Audit & Views]   |
+-------------+----------------------+--------------------------+-------------------------+----------+
              |                      |                          |                         |
              +----------------------+--------------------------+-------------------------+
                                     |
                                     v
+----------------------------------------------------------------------------------------------------+
|                                      CIA TRIAD DEFENSE LAYERS                                      |
|                                                                                                    |
|  * CONFIDENTIALITY: TLS In-Transit Encryption, SCRAM-SHA Authentication, Least-Privilege RBAC,     |
|                     Aggregation Views (Field Redaction), At-Rest Encryption.                       |
|  * INTEGRITY:       Schema Validation, Change Streams Auditing, TLS Message Signatures.           |
|  * AVAILABILITY:    Replica Sets, Automatic Failover, mongos Routing, Rate Limiting.               |
+----------------------------------------------------------------------------------------------------+
```

---

## 🔐 Lab 12.1: Authentication & Least-Privilege RBAC

### Concept
MongoDB ships with coarse built-in roles (`read`, `readWrite`, `clusterAdmin`). When fine-grained control is required (e.g. read only on specific collections or write only on audit logs), **custom roles** must be created using `db.createRole()` by pairing explicit `resource` scopes with allowed `actions`.

### Created Roles & Users
| User | Role / Type | Target Scope | Allowed Actions |
| :--- | :--- | :--- | :--- |
| `admin` | `userAdminAnyDatabase`, `clusterAdmin`, `readWriteAnyDatabase` | Cluster / All DBs | Full Administrative Control |
| `app_user_read` | Custom: `collectionReader` | `analytics.reports`, `nosql_labs.inventory` | `find`, `aggregate` |
| `app_user_write` | Custom: `collectionWriter` | `nosql_labs.orders` | `find`, `insert`, `update`, `delete` |
| `analyst` | Built-in: `read` | `nosql_labs`, `bookstore` | `find` |
| `app_writer` | Built-in: `readWrite` | `nosql_labs` | `find`, `insert`, `update`, `delete` |
| `log_writer` | Custom: `limitedWriter` | `nosql_labs.logs` (write), all DB (read) | `insert`, `update` (logs), `find` (all) |

### Verification Tests
1. **Positive Test:** `app_user_read` queries `analytics.reports` $\rightarrow$ **SUCCESS**.
2. **Negative Test:** `app_user_read` attempts `insertOne()` on `analytics.reports` $\rightarrow$ **REJECTED (`not authorized`)**.
3. **Negative Test:** `app_user_read` attempts `find()` on unauthorized collection `nosql_labs.secret_records` $\rightarrow$ **REJECTED (`not authorized`)**.
4. **Positive Test:** `app_user_write` inserts and retrieves from `nosql_labs.orders` $\rightarrow$ **SUCCESS**.
5. **Negative Test:** `app_user_write` attempts to read `nosql_labs.inventory` $\rightarrow$ **REJECTED (`not authorized`)**.

---

## 👁️ Activity 12.1: Field-Level Redaction via Views

### Implementation
Rather than exposing raw employee collections containing sensitive PII and financial records, an aggregation view is defined using `$project`:

```javascript
db.createView(
  "employees_safe",
  "employees",
  [
    {
      $project: {
        _id: 0,
        empId: 1,
        username: 1,
        name: 1,
        email: 1,
        department: 1,
        role: 1,
        // Mask SSN: preserve only last 4 digits
        ssn: { $concat: ["***-**-", { $substrCP: ["$ssn", 7, 4] }] },
        // Redact salary completely using $$REMOVE
        salary: "$$REMOVE"
      }
    }
  ]
);
```

### Access Separation
* **HR Officer (`hr_user`):** Granted `hr_role` on underlying `hr_db.employees`. Queries the collection directly and sees unredacted salary figures and raw SSNs.
* **General Staff (`staff_user`):** Granted `non_hr_role` **ONLY** on the view `hr_db.employees_safe`. When querying the view, `salary` is absent and `ssn` is masked. Attempting to query `hr_db.employees` directly fails with **`not authorized`**.

---

## 🔒 Lab 12.2: TLS / Encryption-in-Transit Setup

### 1. Certificate Authority & SAN Keys
Using both OpenSSL and the automated Python script (`generate_certs.py` with `cryptography`), an X.509 certificate hierarchy is constructed:
* **Root CA (`ca.crt`):** Self-signed Certificate Authority (`CN=MongoDB-CA`).
* **Server Certificate (`server.pem`):** Signed by the Root CA with Subject Alternative Names:
  * `DNS:localhost`
  * `DNS:mongodb`
  * `IP:127.0.0.1`
* **Client Certificate (`client.pem`):** For mutual TLS verification.

### 2. Enforcing TLS Mode
MongoDB is launched requiring TLS connections on port `27100`:
```bash
mongod --fork --logpath /var/log/mongodb_tls.log --dbpath /data/db_tls \
  --port 27100 --bind_ip 0.0.0.0 \
  --tlsMode requireTLS \
  --tlsCertificateKeyFile ./tls/server.pem \
  --tlsCAFile ./tls/ca.crt
```

### 3. Verification Steps
* **Negative Test:** Attempt plain connection without TLS:
  ```bash
  mongosh --port 27100 --eval 'db.runCommand({ping:1})'
  ```
  $\rightarrow$ **REJECTED!** Fails immediately with connection error / SSL handshake failure.
* **Positive Test (mongosh):**
  ```bash
  mongosh --port 27100 --tls --tlsCAFile ./tls/ca.crt --tlsAllowInvalidHostnames --eval 'db.runCommand({ping:1})'
  ```
  $\rightarrow$ **SUCCESS!** Returns `{ ping: 1, ok: 1 }`.
* **Positive Test (PyMongo):**
  ```python
  client = MongoClient(
      "mongodb://localhost:27100/?tls=true&tlsCAFile=./tls/ca.crt&tlsCertificateKeyFile=./tls/client.pem&tlsAllowInvalidHostnames=true"
  )
  client.tls_test.col.insert_one({"encrypted": True})
  doc = client.tls_test.col.find_one()
  ```
  $\rightarrow$ **SUCCESS!** Encrypted round-trip verification verified with `find_one()`.

---

## 🐳 Automated Demonstration with Docker

### Option 1: Run the Pre-built Demonstration Container
To demonstrate the entire suite, run the container:
```bash
# Pull and run the automated demonstration
docker run -it -p 27017:27017 -p 27100:27100 <your-dockerhub-username>/mongodb-security-lab:latest
```

The container automatically executes `run_all_labs.sh`, runs all positive and negative test cases, prints formatted verification tables, and drops into an interactive shell for the evaluator to test commands manually.

### Option 2: Build and Run Locally
```bash
# 1. Build local image
docker build -t mongodb-security-lab:latest .

# 2. Run container
docker run -it -p 27017:27017 -p 27100:27100 mongodb-security-lab:latest
```

### Option 3: Using Docker Compose
```bash
docker compose up --build
```

---

## 🚀 Docker Hub Deployment & Grading Guide

### For the Student (Deploy to Docker Hub)
Run the automated helper script:
* **Windows PowerShell:**
  ```powershell
  .\build_and_push.ps1 -Username "<your-dockerhub-username>"
  ```
* **Windows Command Prompt:**
  ```cmd
  build_and_push.bat
  ```
* **Linux / macOS:**
  ```bash
  chmod +x build_and_push.sh && ./build_and_push.sh
  ```

### For the Grader / Evaluator (Verification Commands)
To verify the submitted Docker container:

```bash
# 1. Pull the image from Docker Hub
docker pull <your-dockerhub-username>/mongodb-security-lab:latest

# 2. Run the automated test suite
docker run --rm <your-dockerhub-username>/mongodb-security-lab:latest demo

# 3. (Optional) Run interactive inspection
docker run -it -p 27017:27017 -p 27100:27100 <your-dockerhub-username>/mongodb-security-lab:latest bash
```

Inside the interactive shell:
* Run Lab 12.1 alone: `/app/lab_01_rbac_setup.sh`
* Run Activity 12.1 alone: `python3 /app/activity_12_1_redaction.py`
* Run Lab 12.2 alone: `/app/lab_02_tls_setup.sh`
* Connect as admin: `mongosh -u admin -p AdminPass123! --authenticationDatabase admin`
* Connect via TLS: `mongosh --port 27100 --tls --tlsCAFile /app/tls/ca.crt --tlsAllowInvalidHostnames`

---

## 📁 File Structure
```
exercise 12 nosql/
├── Dockerfile                      # Multi-stage production container setup
├── docker-compose.yml              # Compose configuration
├── entrypoint.sh                   # Startup orchestrator and demo runner
├── run_all_labs.sh                 # Master test runner with formatted pass/fail logs
├── lab_01_rbac_setup.sh            # Lab 12.1: Authentication, RBAC, least privilege
├── activity_12_1_redaction.py      # Activity 12.1: View redaction & role separation (Python)
├── activity_12_1_redaction.sh      # Activity 12.1: View redaction & role separation (mongosh)
├── lab_02_tls_setup.sh             # Lab 12.2: TLS setup, requireTLS, verification
├── generate_certs.py               # Automated X.509 cert generator (Python cryptography)
├── test_tls_pymongo.py             # PyMongo encrypted find_one() verification
├── build_and_push.bat              # 1-click Docker build & push script (Windows)
├── build_and_push.ps1              # 1-click Docker build & push script (PowerShell)
├── build_and_push.sh               # 1-click Docker build & push script (Linux/macOS)
├── architecture_sharding.jpg       # Reference architecture: MongoDB Sharding
├── architecture_security_cia.jpg   # Reference architecture: CIA Triad & MongoDB Controls
├── generate_pdf_report.ps1         # PDF generation script
├── MongoDB_Security_RBAC_TLS_Lab_Report.html # Publication-quality HTML report
├── MongoDB_Security_RBAC_TLS_Lab_Report.pdf  # Final submission PDF with Docker Hub URL
└── README.md                       # Comprehensive lab documentation
```
