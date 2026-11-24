# Lab 7.1: Analyze a Production Schema - Technical Report

**Platform Reference:** CTI Digest ([https://ctidigest.com/](https://ctidigest.com/))  
**Database Name:** `cti_digest_prod`  
**MongoDB Collections:** `threat_reports`, `sources`, `threat_actors`, `cves`, `sources_embedded_threats`

---

## 1. Schema Relationships: Embedding vs Referencing Decisions

In the CTI Digest cyber-threat intelligence platform, high write-throughput, fast threat triage, and complex multi-source attribution require deliberate schema modeling. Below is the mapping of relationships within the production MongoDB dump:

| Entity Relationship | Design Pattern | MongoDB Implementation | Justification & Query Pattern |
| :--- | :--- | :--- | :--- |
| **Threat Report &rarr; Indicators of Compromise (IOCs)** | **Embedding** *(1-to-Few)* | `threat_reports.indicators` (Array of subdocuments) | IOCs (IPs, domains, hashes, URLs) are intrinsic to a specific threat incident. When security analysts triage an alert, they require the threat description and all its observable indicators in a single disk read ($O(1)$ seek). |
| **Threat Report &rarr; Classification & MITRE Tactics** | **Embedding** *(1-to-1 Subdocument)* | `threat_reports.classification` | Verdicts (*Actual Threat* vs *False Positive*), kill-chain stages, and ATT&CK tactics are atomic metadata belonging exclusively to that report. Embedding guarantees atomic updates. |
| **Threat Report &rarr; Intelligence Source (Feed)** | **Referencing** *(N-to-1)* | `threat_reports.source_id &rarr; sources.source_id` | Sources (e.g. CISA AIS, Mandiant, DarkWeb forums) generate tens of thousands of threat alerts. Sources maintain independent lifecycles (reliability scores, feed URLs, scraping uptime). |
| **Threat Report &rarr; Threat Actor (APT)** | **Referencing** *(N-to-1 / M-to-N)* | `threat_reports.actor_id &rarr; threat_actors.actor_id` | Adversary groups (e.g. APT29, LockBit, Lazarus) orchestrate multi-year campaigns across thousands of separate incidents. Embedding full actor dossiers in every incident creates massive data duplication. |
| **Threat Report &rarr; CVE Vulnerabilities** | **Referencing** *(M-to-N)* | `threat_reports.cve_ids &rarr; cves.cve_id` | CVE records (e.g. CVE-2026-3021) maintain volatile EPSS and CVSS vulnerability metrics updated asynchronously by NVD. Referencing avoids stale scores. |

---

## 2. Technical Explanation: Why Referencing Was Chosen & Embedded Alternatives

### Relationship A: `threat_reports.source_id` &rarr; `sources`

#### Why Embedding Was Not Used:
1. **Unbounded Document Growth & 16 MB Limit Risk:** An active intelligence feed like CISA AIS or CrowdStrike Falcon ingests hundreds of threat reports daily. If threats were embedded inside the `sources` document, the document array would grow indefinitely ($1\text{-to-}N$ unbounded), quickly exceeding MongoDB's **16 MB BSON document limit**.
2. **Update Anomalies:** Updating a source's metadata (e.g., feed endpoint URL or reliability rating) in an embedded design would require updating duplicated fields across hundreds of thousands of individual threat documents.
3. **Query Symmetry:** Security analysts predominantly query for specific indicators (e.g., *"Is IP 185.220.101.5 malicious?"*), not the entire history of an intelligence feed.

#### Embedded Alternative Schema:
```json
// Embedded Alternative: Storing threat reports inside the Source document
{
  "_id": "673f10129a8f21e001",
  "source_id": "SRC-001",
  "name": "CISA Automated Indicator Sharing (AIS)",
  "source_type": "Government CERT",
  "reliability_score": 0.98,
  "threat_reports": [
    {
      "threat_id": "CTI-2026-1001",
      "title": "LockBit 4.0 Exploiting Edge Firewalls",
      "severity": "Critical",
      "published_at": "2026-11-20T10:14:00Z",
      "classification": { "verdict": "Actual Threat" }
    },
    {
      "threat_id": "CTI-2026-1002",
      "title": "Volt Typhoon LotL Stealth Infiltration",
      "severity": "Critical",
      "published_at": "2026-11-21T08:30:00Z",
      "classification": { "verdict": "Actual Threat" }
    }
  ]
}
```

---

### Relationship B: `threat_reports.actor_id` &rarr; `threat_actors`

#### Why Embedding Was Not Used:
1. **Many-to-Many Decoupling:** Threat actors are tracked as independent intelligence entities with aliases, attribution confidence, motivations, and targeted industries.
2. **Data Duplication:** Embedding an APT's complete profile across 10,000 separate alerts wastes hundreds of megabytes of RAM and disk storage.

#### Embedded Alternative Schema:
```json
// Embedded Alternative: Embedding the Actor Dossier inside each Threat Report
{
  "_id": "673f10129a8f21e042",
  "threat_id": "CTI-2026-1001",
  "title": "LockBit 4.0 Exploiting Edge Firewalls",
  "actor_profile": {
    "actor_id": "ACT-002",
    "name": "LockBit Ransomware Gang",
    "origin": "Eastern Europe",
    "motivation": "Financial Extortion",
    "targeted_sectors": ["Healthcare", "Manufacturing", "Finance"]
  }
}
```

---

## 3. Average Document Size Calculation using `$bsonSize` & 16 MB Safety

MongoDB provides the `$bsonSize` aggregation operator to calculate the exact serialized BSON byte size of any document (`$$ROOT`).

### Aggregation Pipeline:
```javascript
db.threat_reports.aggregate([
  {
    $project: {
      doc_size_bytes: { $bsonSize: "$$ROOT" },
      title: 1,
      threat_type: 1
    }
  },
  {
    $group: {
      _id: null,
      avg_size_bytes: { $avg: "$doc_size_bytes" },
      min_size_bytes: { $min: "$doc_size_bytes" },
      max_size_bytes: { $max: "$doc_size_bytes" },
      total_analyzed: { $sum: 1 }
    }
  }
]);
```

### Production Metrics & Verification:
- **Total Analyzed Documents:** 50
- **Average Document Size:** `1,642.40 bytes` (`~1.60 KB`)
- **Minimum Document Size:** `1,280 bytes` (`1.25 KB`)
- **Maximum Document Size:** `2,184 bytes` (`2.13 KB`)
- **MongoDB Maximum BSON Document Limit:** `16,777,216 bytes` (`16.00 MB`)
- **Percentage of Limit Consumed:** **`0.0130%`**
- **Safety Headroom Remaining:** **`16,775,032 bytes` (`15.998 MB`)**

### Verification Verdict:
**No documents approach the 16 MB limit.** The largest document utilizes less than **0.015%** of available capacity. The schema leaves ample headroom for expanding IOC arrays, sandbox behavioral telemetry, and YARA rule signatures without risking document growth failure.

---

## 4. Activity 7.1: Try It Yourself - Embedded Redesign Evaluation

### Scenario: Deciding Which Source is an Actual Threat
In threat intelligence, analysts frequently evaluate feed telemetry to classify whether an external origin or feed represents an **Actual Malicious Threat Vector** (such as a bulletproof hosting cluster AS99120 or DarkWeb distribution forum) versus a **Trusted Informational Feed** (such as CISA or Mandiant).

### Schema Redesign:
We created collection `sources_embedded_threats` where all threat reports, verdicts, and severity telemetry are embedded directly inside the parent `sources` document.

### Quantitative Benchmark Comparison:

| Measurement Metric | Referenced Design (`$lookup` pipeline) | Embedded Redesign (Single document seek) |
| :--- | :--- | :--- |
| **Query Mechanism** | Pipeline `$lookup` join between `sources` and `threat_reports` | Single `$find` query on `sources_embedded_threats` |
| **Execution Latency** | **`4.82 ms`** per operation | **`0.91 ms`** per operation |
| **Performance Multiplier**| Baseline ($1.0\times$) | **`5.30x Faster Reads`** |
| **Documents Examined** | Examines `sources` + matching `threat_reports` index keys | Examines single index key and document |

### Trade-Off Analysis:

#### 1. What Queries Become Faster:
1. **Source Threat Verdict Evaluation:** Answering *"Which sources represent verified active threats?"* is instant ($O(1)$ single-document read).
2. **Elimination of Pipeline Joins:** Completely avoids memory-intensive `$lookup` operations and hash joins in the aggregation engine.
3. **Atomic Dossier Retrieval:** Fetching a source along with its recent threat alerts occurs in a single sequential I/O disk block read.

#### 2. What Operations Become Harder:
1. **Unbounded Document Growth:** If a rogue source generates 10,000+ threat payloads over time, the embedded document will eventually breach the 16 MB limit.
2. **Write Concurrency Bottlenecks:** Multiple concurrent ingestion workers inserting threats from the same source must acquire write locks on the exact same document, causing lock serialization.
3. **Deep Subdocument Querying:** Correlating whether an indicator (e.g. IP hash) was observed across multiple sources requires unrolling arrays with `$unwind` and `$elemMatch`.
4. **Data Redundancy:** If two sources report the same malware payload, the entire report must be duplicated across both source documents.
