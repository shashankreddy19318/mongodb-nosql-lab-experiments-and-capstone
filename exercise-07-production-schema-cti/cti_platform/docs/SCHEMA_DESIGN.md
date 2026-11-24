# Production Database Schema & Indexing Reference

**Database:** `cti_digest_prod`  
**Application:** Cyber Threat Intelligence (CTI) Platform  
**Target URL:** [https://ctidigest.com/](https://ctidigest.com/) & [Awesome Security Reports](https://github.com/jacobdjwilson/awesome-annual-security-reports)

---

## 1. Production Entity Architecture

```text
               +----------------------------------+
               |        threat_actors             |
               | (APT29, LockBit, Lazarus)        |
               +-----------------+----------------+
                                 |
                                 | 1:N (Referenced via actor_id)
                                 v
+------------------+     +-----------------------------+     +------------------+
|     sources      |     |       threat_reports        |     |      cves        |
| (Feeds, OSINT)   |     | (Incident alerts & telemetry|     | (Vulnerabilities)|
+--------+---------+     +--------------+--------------+     +--------+---------+
         |                              |                             |
         | 1:N (Referenced              | Embedded:                   | M:N (Referenced
         | via source_id)               |  - indicators (IOCs)        | via cve_ids)
         +----------------------------> |  - classification           +-------->
                                        |  - telemetry                |
                                        +-----------------------------+
```

---

## 2. Collection Schemas & Data Dictionaries

### A. Collection: `threat_reports`
Primary collection storing tactical threat reports with embedded indicators and referenced entities.

```json
{
  "_id": { "$oid": "673f10129a8f21e042" },
  "threat_id": "CTI-2026-1001",
  "title": "LockBit 4.0 Exploiting Edge Firewalls with New Anti-Analysis Modules",
  "threat_type": "Ransomware",
  "severity": "Critical",
  "cvss_score": 9.8,
  "confidence": 95,
  "description": "Tactical intelligence report detailing LockBit 4.0 exploitation...",
  "published_at": "2026-11-20T10:14:00Z",
  
  "source_id": "SRC-003",
  "actor_id": "ACT-002",
  "cve_ids": ["CVE-2026-3021"],
  
  "indicators": [
    {
      "ioc_id": "IOC-10492",
      "type": "ipv4",
      "value": "185.220.101.5",
      "reputation": "confirmed_malicious",
      "confidence_score": 98,
      "first_seen": "2026-11-20T08:00:00Z"
    },
    {
      "ioc_id": "IOC-10493",
      "type": "sha256",
      "value": "4b971a81bc598a7281f629c48b0fae2467d02cb42903332467b6e92b8d4f40f0",
      "reputation": "confirmed_malicious",
      "confidence_score": 100,
      "first_seen": "2026-11-20T08:00:00Z"
    }
  ],
  
  "classification": {
    "verdict": "Actual Threat",
    "status": "Active Threat",
    "kill_chain_stage": "Exploitation & Delivery",
    "mitre_techniques": ["T1190 - Exploit Public-Facing Application"]
  },
  
  "tags": ["ransomware", "critical", "act-002", "feed-src-003"],
  "telemetry": {
    "targeted_hosts_count": 1420,
    "is_zero_day": true,
    "remediation_status": "In Mitigation"
  }
}
```

---

## 3. Indexing Strategies (Chapter 07 Reference)

Derived from Chapter 07 indexing recommendations:

```javascript
// 1. Single Field Index on threat_type
db.threat_reports.createIndex({ "threat_type": 1 }, { name: "idx_threat_type" });

// 2. Single Field Index on severity
db.threat_reports.createIndex({ "severity": 1 }, { name: "idx_severity" });

// 3. Compound Index for multi-field filtering & sorting
// Satisfies queries like: find({ threat_type: "Ransomware" }).sort({ severity: -1, confidence: -1 })
db.threat_reports.createIndex(
  { "threat_type": 1, "severity": -1, "confidence": -1 },
  { name: "idx_compound_type_sev_conf" }
);

// 4. Multikey Index on embedded array indicators.value
// Accelerates threat hunting across IP addresses, hashes, and domains
db.threat_reports.createIndex({ "indicators.value": 1 }, { name: "idx_multikey_ioc_value" });

// 5. Multikey Index on tags array
db.threat_reports.createIndex({ "tags": 1 }, { name: "idx_multikey_tags" });

// 6. Text Search Index for full-text keyword search
db.threat_reports.createIndex(
  { "title": "text", "description": "text" },
  { name: "idx_text_search" }
);

// 7. Unique Index on Foreign Keys
db.sources.createIndex({ "source_id": 1 }, { unique: true, name: "idx_unique_source_id" });
```
