# Cyber Threat Intelligence (CTI) Platform - NoSQL Lab 7.1 & Lab 7.2

A complete, production-grade Cyber Threat Intelligence Platform and NoSQL schema analysis workbench built for **Lab 7.1 (Production Schema Analysis & $bsonSize)** and **Lab 7.2 (Working Set & WiredTiger Cache Analysis)** based on [CTI Digest](https://ctidigest.com/) and [Awesome Annual Security Reports](https://github.com/jacobdjwilson/awesome-annual-security-reports).

---

## 🚀 Key Features

### 1. Cyber Threat Intelligence Platform (Frontend & Backend)
- **Threat Search & Filtering:** Real-time multi-attribute search across CVEs, Indicators of Compromise (IPs, domains, hashes), APT threat actors, severities, and threat types.
- **Threat Classification Engine:** Re-classify analyst verdicts (*Actual Threat* vs *False Positive / Benign*), adjust severity, and view MITRE ATT&CK tactics.
- **Intelligence Feed Verdicts:** Classify whether an external intelligence origin represents an active threat origin (e.g. DarkWeb forum or rogue AS) vs trusted feed (CISA, Mandiant).

### 2. Lab 7.1: Analyze a Production Schema
- **Embedding vs Referencing Visualizer:** Categorizes relationships in CTI Digest into embedded (IOCs, classification) vs referenced (sources, actors, CVEs).
- **Referencing Rationale & Embedded Alternatives:** In-depth technical justifications for avoiding embedding (16 MB limit prevention, update anomalies, independent lifecycles) and JSON models for embedded alternatives.
- **Document Size Calculator ($bsonSize):** Aggregates exact BSON byte sizes of all documents (`$$ROOT`), reporting average, minimum, maximum sizes, and proving safety against the 16 MB limit.
- **Activity 7.1 "Try It Yourself" Workbench:** Live benchmarking runner comparing Referenced ($lookup) vs Embedded design for source threat classification with speedup ratios.

### 3. Lab 7.2: Working Set Analysis & WiredTiger Cache Fit
- **100,000 Documents Ingestion (~2 KB each):** Generates and inserts 100,000 documents seeded from *Awesome Annual Security Reports* into `working_set_reports`.
- **WiredTiger Cache Inspector:** Live extraction and calculation of `db.serverStatus().wiredTiger.cache` metrics:
  - Cache size (`maximum bytes configured`)
  - Memory residency (`bytes currently in the cache`)
  - Tracked dirty bytes
  - Cache Hit Ratio formula: `(pages requested - pages read) / pages requested * 100`
- **Random Reads Workload Runner:** Simulates random queries across 100,000 documents, plotting cache hit ratio stabilization with interactive Chart.js graphs.
- **Activity 7.2 "Try It Yourself" 10-Second Monitor:** Autonomous background engine that crawls for new external threat reports, ingests them into MongoDB, and reports WiredTiger cache hit ratio every 10 seconds.

---

## 📂 Project Architecture

```text
cti_platform/
├── backend/
│   ├── app.py                     # Flask REST API & Static Web Server
│   ├── database.py                # Dual-mode (Live MongoDB / Mock with WiredTiger Cache Engine)
│   ├── seed_data.py               # CTI Digest production dataset seeder
│   ├── lab7_1_analysis.py         # Lab 7.1 CLI runner ($bsonSize, schema analysis, benchmarks)
│   ├── lab7_2_working_set.py      # Lab 7.2 CLI runner (100k docs ~2KB, serverStatus, random reads)
│   ├── monitor_wiredtiger_threats.py # Activity 7.2 10-second cache monitor & auto-crawler
│   ├── indexing_scripts.py        # Chapter 07 Indexing strategies (single, compound, multikey, text)
│   ├── export_mongo_dump.py       # MongoDB JSON/BSON dump exporter
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── index.html                 # Single Page Application Dashboard
│   ├── css/
│   │   └── styles.css             # Modern dark cybersecurity UI
│   └── js/
│       ├── app.js                 # App bootloader & tab switcher
│       ├── threats.js             # Search, filter, and classification module
│       ├── lab7_1.js              # Lab 7.1 Schema Studio & $bsonSize module
│       └── lab7_2.js              # Lab 7.2 Working Set & WiredTiger module
├── dumps/
│   ├── cti_digest_dump.json       # Production MongoDB dump for Lab 7.1
│   ├── sources.json               # Dump of intelligence sources
│   ├── threat_reports.json        # Dump of threat reports
│   └── sample_security_report_2kb.json # Sample 2KB security report template
├── docs/
│   ├── LAB_7_1_REPORT.md          # Complete written analysis for Lab 7.1 & Activity 7.1
│   ├── LAB_7_2_REPORT.md          # Complete written analysis for Lab 7.2 & Activity 7.2
│   └── SCHEMA_DESIGN.md           # Production schema reference & indexing scripts
├── run_backend.bat                # 1-Click launcher for Web Platform
├── run_lab7_1.bat                 # 1-Click launcher for Lab 7.1 CLI
├── run_lab7_2.bat                 # 1-Click launcher for Lab 7.2 CLI
└── run_monitor.bat                # 1-Click launcher for Activity 7.2 10s Monitor
```

---

## 🛠️ Quick Start Instructions

### Running the Web Platform
Simply double-click `run_backend.bat` or run:
```powershell
cd backend
python app.py
```
Open your browser at: **`http://localhost:5000`**

### Running Lab 7.1 CLI Analysis
```powershell
cd backend
python lab7_1_analysis.py
```

### Running Lab 7.2 CLI Working Set & Random Reads
```powershell
cd backend
python lab7_2_working_set.py
```

### Running Activity 7.2 10-Second Monitoring & Crawler
```powershell
cd backend
python monitor_wiredtiger_threats.py --interval 10
```

---

## 📚 References
- **CTI Digest:** [https://ctidigest.com/](https://ctidigest.com/)
- **Awesome Annual Security Reports:** [https://github.com/jacobdjwilson/awesome-annual-security-reports/](https://github.com/jacobdjwilson/awesome-annual-security-reports/)
- **NoSQL Databases using MongoDB (Chapter 07):** Sujeet Jagtap ([GitHub](https://github.com/sujeetjagtap/NoSQL-Databases-using-MongoDB/tree/main/chapter-07))
