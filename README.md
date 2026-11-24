# Distributed NoSQL Databases & Cyber Threat Intelligence LLM Platform

[![MongoDB Version](https://img.shields.io/badge/MongoDB-7.0-green.svg?logo=mongodb)](https://www.mongodb.com/)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-yellow.svg?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg?logo=docker)](https://www.docker.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B.svg?logo=streamlit)](https://streamlit.io/)
[![Status](https://img.shields.io/badge/All%2018%20Labs-100%25%20Verified-brightgreen.svg)]()

> **Author:** G. Shashank Reddy (Chintan)  
> **Student ID:** 24BTRCL079  
> **Curriculum:** Distributed NoSQL Databases & AI Systems  

---

## 📌 Repository Overview

This repository provides an enterprise-grade, comprehensive implementation of all **18 Distributed NoSQL Lab Exercises** alongside the **Cyber Threat Intelligence (CTI) AI Capstone Platform**.

It covers core database internals, data modeling, aggregation frameworks, high availability, clustering, sharding, enterprise security, multi-tenancy, polyglot persistence, vector search (RAG), and a full-stack containerized LLM platform.

---

## 📂 Repository Structure

```
├── capstone-threat-intelligence-llm/         # Full-Stack CTI Platform (FastAPI + Streamlit + MongoDB + LLM)
├── exercise-01-document-model/               # Lab 1: Document Model & MongoDB Fundamentals
├── exercise-02-crud-projections/             # Lab 2: CRUD Operations, Filtering & Field Projections
├── exercise-03-document-modeling/            # Lab 3: Relational vs Document Modeling Paradigms
├── exercise-04-schema-design/                # Lab 4: Schema Design, Embedding vs Referencing
├── exercise-05-advanced-queries/             # Lab 5: Advanced Query Operators & Aggregation Pipelines
├── exercise-06-indexing-strategies/          # Lab 6: Single-Field, Compound, Multikey & Text Indexes
├── exercise-07-production-schema-cti/        # Lab 7: Production Schema Design for Cyber Threat Intelligence
├── exercise-08-replication-ha/               # Lab 8: Replica Set Deployment, HA & Primary Failover
├── exercise-09-cap-theorem-write-concerns/   # Lab 9: CAP Theorem, Write Concerns (w:majority) & Read Concerns
├── exercise-10-acid-transactions/            # Lab 10: Multi-Document ACID Distributed Transactions
├── exercise-11-sharding-scalability/         # Lab 11: Horizontal Scaling, Shard Keys & Balancing
├── exercise-12-rbac-security-tls/            # Lab 12: Role-Based Access Control, Auditing & TLS
├── exercise-13-containerization-k8s/         # Lab 13: Docker Containerization & Kubernetes Deployments
├── exercise-14-monitoring-backup-restore/    # Lab 14: Telemetry Monitoring, Alerts, Backups & RPO/RTO
├── exercise-15-multitenant-saas-api/         # Lab 15: Multi-Tenant SaaS REST API & Tenant Data Migration
├── exercise-16-polyglot-persistence/         # Lab 16: Polyglot Persistence (MongoDB + Cassandra + Neo4j)
├── exercise-17-vector-search-rag/            # Lab 17: AI-Native MongoDB, Vector Embeddings & RAG
├── exercise-18-comparative-capstone-analysis/# Lab 18: Comparative Capstone Lab & False-Positive Analysis
├── reports/                                  # Official Academic & Lab PDF Reports
│   ├── MongoDB_Lab_Experiments_Report_24BTRCL079.pdf
│   └── CTI_MongoDB_Project_Report_24BTRCL079.pdf
└── README.md
```

---

## 🧪 Laboratory Exercises Index (1 to 18)

| # | Chapter / Topic | Key Technologies | Directory |
|---|---|---|---|
| **01** | Document Model & Fundamentals | PyMongo, MongoDB 7.0 | [`exercise-01-document-model`](./exercise-01-document-model/) |
| **02** | CRUD & Projections | Query Selectors, Projections | [`exercise-02-crud-projections`](./exercise-02-crud-projections/) |
| **03** | Document Modeling Paradigms | One-to-Many, Many-to-Many | [`exercise-03-document-modeling`](./exercise-03-document-modeling/) |
| **04** | Schema Design & Denormalization | Embedding vs Referencing | [`exercise-04-schema-design`](./exercise-04-schema-design/) |
| **05** | Advanced Queries & Aggregations | `$facet`, `$lookup`, `$match` | [`exercise-05-advanced-queries`](./exercise-05-advanced-queries/) |
| **06** | Indexing Strategies & Performance | Compound, Multikey, ExecutionStats | [`exercise-06-indexing-strategies`](./exercise-06-indexing-strategies/) |
| **07** | Production CTI Schema Architecture | STIX 2.1 Standard, IOC Storage | [`exercise-07-production-schema-cti`](./exercise-07-production-schema-cti/) |
| **08** | Replication & High Availability | 3-Node Replica Set, Auto-Failover | [`exercise-08-replication-ha`](./exercise-08-replication-ha/) |
| **09** | CAP Theorem & Write Concerns | `w:majority`, `linearizable` reads | [`exercise-09-cap-theorem-write-concerns`](./exercise-09-cap-theorem-write-concerns/) |
| **10** | ACID Distributed Transactions | Multi-Document Sessions, Rollbacks | [`exercise-10-acid-transactions`](./exercise-10-acid-transactions/) |
| **11** | Horizontal Sharding & Scalability | Config Servers, Mongos, Shard Keys | [`exercise-11-sharding-scalability`](./exercise-11-sharding-scalability/) |
| **12** | RBAC, TLS & Enterprise Security | User Roles, Privilege Auditing | [`exercise-12-rbac-security-tls`](./exercise-12-rbac-security-tls/) |
| **13** | Containerization & K8s Architecture | Docker Compose, StatefulSets, K8s | [`exercise-13-containerization-k8s`](./exercise-13-containerization-k8s/) |
| **14** | Monitoring, Backups & Disaster Recovery | `mongodump`, `mongorestore`, RPO/RTO | [`exercise-14-monitoring-backup-restore`](./exercise-14-monitoring-backup-restore/) |
| **15** | Multi-Tenant SaaS REST API | FastAPI, Isolation, Tenant Migration | [`exercise-15-multitenant-saas-api`](./exercise-15-multitenant-saas-api/) |
| **16** | Polyglot Persistence Architecture | MongoDB + Cassandra + Neo4j | [`exercise-16-polyglot-persistence`](./exercise-16-polyglot-persistence/) |
| **17** | AI-Native Vector Search & RAG | Cosine Similarity, Embeddings, RAG | [`exercise-17-vector-search-rag`](./exercise-17-vector-search-rag/) |
| **18** | Comparative Capstone Analysis | Threat Intel False-Positive Reduction | [`exercise-18-comparative-capstone-analysis`](./exercise-18-comparative-capstone-analysis/) |

---

## 🛡️ Main Capstone Project: Cyber Threat Intelligence LLM Platform

Located in [`capstone-threat-intelligence-llm`](./capstone-threat-intelligence-llm/), the capstone integrates a complete modern cybersecurity intelligence pipeline:

- **Data Ingestion Engine:** Automates ingestion and parsing of STIX 2.1 Indicators of Compromise (IOCs), CVE vulnerabilities, and adversary actor profiles into MongoDB.
- **RESTful API Service:** High-throughput asynchronous endpoints powered by FastAPI for querying threat indicators and MITRE ATT&CK tactics.
- **LLM Vulnerability Assistant:** Context-aware incident analysis utilizing local LLMs (Ollama) and retrieval-augmented generation (RAG) against MongoDB threat data.
- **Interactive UI Dashboard:** Built with Streamlit for real-time visualization of threat feeds, severity metrics, and AI chat analysis.
- **Dockerized Architecture:** Multi-container orchestration ready to run with a single `docker-compose up` command.

### Running the Capstone Project

```bash
cd capstone-threat-intelligence-llm

# Copy environment variables
cp .env.example .env

# Launch all services via Docker Compose
docker-compose up -d

# Or run locally with Python:
pip install -r requirements.txt
python ingest_threat_intelligence.py
streamlit run streamlit_app.py
```

---

## 📄 Official PDF Reports

The `reports/` directory contains complete academic evaluation reports:
- [MongoDB 18-Experiment Lab Report (24BTRCL079)](./reports/MongoDB_Lab_Experiments_Report_24BTRCL079.pdf)
- [Cyber Threat Intelligence Capstone Project Report (24BTRCL079)](./reports/CTI_MongoDB_Project_Report_24BTRCL079.pdf)

---

## 👨‍💻 Author

* **Student:** G. Shashank Reddy (Chintan)
* **Registration No:** 24BTRCL079
* **GitHub:** [@shashankreddy19318](https://github.com/shashankreddy19318)
