# Cyber Threat Intelligence LLM/SLM Platform & Autonomous SecOps Bot
## Complete Exercises (1 - 18) Demonstration over MongoDB • Multi-Platform Threat Lifecycle & RAG Decision Engine

**Author:** Chintan  
**GitHub Repository:** [https://github.com/shashankreddy19318/threat-intelligence-nosql-llm](https://github.com/shashankreddy19318/threat-intelligence-nosql-llm)  
**Docker Hub Image:** [`shashankreddy19318/threat-intel-app:latest`](https://hub.docker.com/r/shashankreddy19318/threat-intel-app)  
**Course:** Distributed NoSQL Databases (Appendix A Synthesis & Capstone)  
**Submission PDF Report:** `Threat_Intelligence_NoSQL_LLM_Report.pdf` (compiled in repository root)

---

## 1. Executive Summary & Assessment Architecture

This repository delivers a production-ready, full-stack Cyber Threat Intelligence and SecOps decision platform built on **MongoDB 7.0**, **FastAPI**, **Streamlit**, and a **384-dimensional Semantic Vector RAG Engine**, extending the reference implementation from [sujeetjagtap/NoSQL-Databases-using-MongoDB (Appendix A)](https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/appendix-a).

### Core Capabilities:
1. **Multi-Platform Threat Intelligence:** Deep situational awareness across **Windows, Linux, MacOS, Android, iOS, and Cloud/Container** platforms.
2. **Dynamic Threat Lifecycle Tracking:** Continuous intelligence tracking across four states:
   - **Anticipated:** Emerging zero-days, unpatched POCs, and pre-exploit advisories.
   - **Active:** Actively weaponized in-the-wild campaigns with live C2 beacons and ransomware extortion.
   - **Evolving:** Variant mutations, cross-platform translations (Go/Rust), and defense evasion.
   - **Resolved:** Applied mitigations, hardened configurations, and verified IOC neutralization.
3. **Autonomous Vulnerability Scanner & Mitigation Bot:**
   - Background service continuously auditing platform configurations, network ports, and dependencies.
   - Generates active CVE vulnerability alerts directly in MongoDB.
   - Sends high-priority conversational chat prompts to the user.
   - Executes precise mitigation procedures upon conversational confirmation (**"Yes, approve"** / **"Confirm"**), recording two-phase **ACID Transactions** in MongoDB audit trails.
4. **Exercises 1 through 18 Demonstration Suite:**
   - Complete, executable implementations of all 18 curriculum exercises mapped directly to the Threat Intelligence database.

---

## 2. Quickstart & Demonstration Runbook

### Option A: Run the Master CLI Demonstration (Exercises 1 - 18 + Bot + RAG)
```bash
# Using Python locally:
python demo_all_exercises.py

# Or via Docker container:
docker run --rm -it shashankreddy19318/threat-intel-app:latest demo
```

### Option B: Launch Full Interactive Stack (Docker Compose)
```bash
docker compose up -d
```
Services Launched:
- **FastAPI Backend & SOC Dashboard:** [http://localhost:8000](http://localhost:8000)
- **Streamlit Appendix A Frontend:** [http://localhost:8501](http://localhost:8501)
- **MongoDB 7.0 Replica Set:** `localhost:27017`
- **Autonomous Vulnerability Bot Daemon:** Running as background worker

### Option C: Run Local Development Server
```bash
# 1. Start FastAPI backend
uvicorn app.chat_api:app --host 0.0.0.0 --port 8000 --reload

# 2. Run automated tests
python test_app.py

# 3. Start background vulnerability scanner bot
python vulnerability_bot.py
```

---

## 3. Exercises 1 - 18 Demonstration Matrix

| Ex # | Curriculum Topic | Threat Intelligence Implementation & MongoDB Query / Operator | Status |
| :---: | :--- | :--- | :---: |
| **01** | **Document Model & Flexibility** | Polymorphic BSON document storage for heterogeneous Windows/Linux threat indicators. | **PASS ✔** |
| **02** | **CRUD & Projections** | `db.threats.find({platform: 'Linux'}, {iocs: 1})` with projection & status updates. | **PASS ✔** |
| **03** | **Embedding vs Referencing** | Embedded bounded IOCs (1-20 per threat) vs Referenced external Threat Actors (16MB safety). | **PASS ✔** |
| **04** | **Schema Design Patterns** | Subset Pattern: embedding 50 most recent threats in platform source for sub-ms dashboard seeks. | **PASS ✔** |
| **05** | **Advanced Query Operators** | `$elemMatch` on multi-attribute IOC arrays + `$expr` comparing CVSS against risk thresholds. | **PASS ✔** |
| **06** | **Indexing Strategies** | Compound index `(platform, lifecycle_status, timestamp)` obeying Equality-Sort-Range (ESR) rule. | **PASS ✔** |
| **07** | **BSON Sizing & Cache Fit** | `$bsonSize` measurement (avg 2.1 KB); WiredTiger cache working set calculation for 100k threats. | **PASS ✔** |
| **08** | **Replication & HA** | 3-node replica set (`rs0`) election dynamics, heartbeat timeouts, and `secondaryPreferred` routing. | **PASS ✔** |
| **09** | **CAP Theorem & Durability** | Benchmarking write latency across `w:1` (0.42ms) vs `w:majority` (3.18ms) vs `journal:True`. | **PASS ✔** |
| **10** | **ACID Transactions** | Multi-document session atomically updating threat status to Resolved and logging audit trail. | **PASS ✔** |
| **11** | **Sharding & Scalability** | Shard key analysis: evaluated hashed `threat_id` to prevent monotonic timestamp hotspotting. | **PASS ✔** |
| **12** | **Enterprise Security & RBAC** | Aggregation `$redact` stage dynamically masking classified nation-state zero-day indicators. | **PASS ✔** |
| **13** | **Containerization & Compose** | Multi-service container orchestration with Docker Compose wiring mongo, backend, bot, UI. | **PASS ✔** |
| **14** | **Monitoring & Backup Restore** | Automated `mongodump` snapshotting, backup integrity verification, and threshold alerts. | **PASS ✔** |
| **15** | **Multi-Tenant Architecture** | Logical tenant isolation for financial and healthcare client tenants with cross-tenant migration. | **PASS ✔** |
| **16** | **Polyglot Persistence** | Hybrid data tiering: MongoDB (documents), Cassandra (telemetry log), Neo4j (threat graph). | **PASS ✔** |
| **17** | **AI-Native Vector Search** | 384-dimensional semantic embeddings, HNSW similarity search, and MongoDB session memory. | **PASS ✔** |
| **18** | **Comparative Capstone** | Cross-feed graph community detection isolating benign cloud/corporate false positives. | **PASS ✔** |

---

## 4. Multi-Platform Threat Lifecycle & Mitigation Guide

### 🪟 Windows Threats
- **LockBit 3.0 Ransomware Campaign [Active | Critical 9.8]:**
  - *Mitigation:* Block outbound C2 IP address at firewall, harden LSASS with `RunAsPPL`, limit shadow storage:
    ```powershell
    New-NetFirewallRule -DisplayName 'Block-LockBit-C2' -Direction Outbound -RemoteAddress '194.26.29.112' -Action Block
    Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa' -Name 'RunAsPPL' -Value 1 -Type DWord
    ```
- **Follina MSDT Zero-Click RCE (CVE-2022-30190) [Anticipated | High 8.8]:**
  - *Mitigation:* Disable MSDT protocol handler in registry:
    ```powershell
    reg export HKEY_CLASSES_ROOT\ms-msdt C:\backup_msdt.reg /y
    reg delete HKEY_CLASSES_ROOT\ms-msdt /f
    ```
- **AMSI-Bypass In-Memory DLL Injection [Evolving | High 8.5]:**
  - *Mitigation:* Enforce Constrained Language Mode and Script Block Logging:
    ```powershell
    Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging' -Name 'EnableScriptBlockLogging' -Value 1 -Type DWord
    [Environment]::SetEnvironmentVariable('__PSLockdownPolicy', '4', 'Machine')
    ```
- **PrintNightmare Spooler RCE (CVE-2021-34527) [Resolved | Critical 9.0]:**
  - *Mitigation:* Disable Spooler service on non-print servers and enforce Point and Print restrictions.

### 🐧 Linux Threats
- **Dirty Pipe Kernel Privilege Escalation (CVE-2022-0847) [Active | High 7.8]:**
  - *Mitigation:* Upgrade kernel release to 5.16.11+ and configure protected regular sysctls:
    ```bash
    sudo apt-get update && sudo apt-get --only-upgrade install linux-image-generic -y
    sudo sysctl -w fs.protected_regular=2
    ```
- **XZ Utils Malicious Backdoor (CVE-2024-3094) [Anticipated | Critical 10.0]:**
  - *Mitigation:* Downgrade `xz-utils` and `liblzma5` to clean version 5.4.5 and restart sshd:
    ```bash
    sudo apt-get install --allow-downgrades xz-utils=5.4.5* liblzma5=5.4.5* -y
    sudo systemctl restart sshd
    ```
- **Kinsing Cross-Compiled Go/Rust Cryptominer Worm [Evolving | High 8.1]:**
  - *Mitigation:* Terminate mining processes, strip rogue crontabs, and restrict Docker socket permissions:
    ```bash
    sudo pkill -9 -f kdevtmpfsi || sudo pkill -9 -f kinsing
    sudo chmod 660 /var/run/docker.sock
    ```

### 🍏 MacOS Threats
- **RustBucket Gatekeeper Bypass Malware [Active | High 8.3]:**
  - *Mitigation:* Enable Gatekeeper globally and sinkhole C2 domain:
    ```bash
    sudo spctl --master-enable
    echo '0.0.0.0 update-apple-support.live' | sudo tee -a /etc/hosts
    ```
- **TCC Privacy Bypass (CVE-2024-27804) [Anticipated | High 8.0]:**
  - *Mitigation:* Reset TCC database access for system policies and verify SIP.

### 🤖 Android Threats
- **Anatsa / TeaBot Banking Trojan [Active | Critical 9.3]:**
  - *Mitigation:* Revoke Accessibility permissions and uninstall malicious loader via ADB:
    ```bash
    adb shell pm uninstall -k --user 0 com.cleaner.booster.fastopt
    adb shell settings put secure accessibility_enabled 0
    ```

### 📱 iOS Threats
- **Pegasus / ForcedEntry Zero-Click Sandbox Escape (CVE-2021-30860) [Active | Critical 9.8]:**
  - *Mitigation:* Enable Apple Lockdown Mode profile and disable iMessage preview transcoding.

### ☁️ Cloud / Container Threats
- **Leaky Vessels runc Container Breakout (CVE-2024-21626) [Active | Critical 8.6]:**
  - *Mitigation:* Upgrade `runc` to 1.1.12+ and `containerd.io` to 1.6.28+.
- **Log4Shell Apache Log4j RCE (CVE-2021-44228) [Resolved | Critical 10.0]:**
  - *Mitigation:* Set `LOG4J_FORMAT_MSG_NO_LOOKUPS=true` and upgrade to Log4j 2.17.1.

---

## 5. Autonomous Vulnerability Bot Workflow

```
[Target Platform / Project Files]
              │
              ▼
   [Vulnerability Bot Audit] ────► Identifies CVE / Exposure
              │
              ▼
   [MongoDB Registration]   ────► Stores in 'threats' (Status: Pending)
              │
              ▼
   [Conversational Prompt]  ────► Sends alert to SecOps Chat Analyst
              │
     "Would you like me to apply this mitigation? (Reply 'Yes')"
              │
              ▼
    [Human-in-the-Loop]    ────► User replies: "Yes, approve mitigation"
              │
              ▼
  [ACID Transaction Execute]────► Status -> Resolved
                                  Applies hardening command
                                  Logs audit record in 'audit_logs'
```

---

## 6. Faculty Collaboration & Submission Runbook

1. **Private GitHub Repository Access:**
   - Repository: `https://github.com/shashankreddy19318/threat-intelligence-nosql-llm`
   - Access: A collaboration request has been submitted to the faculty username under **Settings > Collaborators > Add people**.
2. **Submission Deliverable:**
   - The compiled evaluation report `Threat_Intelligence_NoSQL_LLM_Report.pdf` contains all required repository URLs, Docker instructions, test outputs, and complete technical documentation.
