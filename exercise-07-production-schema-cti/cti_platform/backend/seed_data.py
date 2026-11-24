"""
Seed script for CTI Platform based on CTI Digest (https://ctidigest.com)
and Awesome Annual Security Reports (https://github.com/jacobdjwilson/awesome-annual-security-reports).

Populates:
1. sources (Feeds, OSINT, CERTs)
2. threat_actors (APTs, Syndicates)
3. cves (Vulnerabilities)
4. threat_reports (Primary production collection with embedded IOCs, referenced sources & actors)
5. sources_embedded_threats (Lab 7.1 Try It Yourself embedded redesign collection)
"""

import json
import random
import datetime
from bson import ObjectId
from database import db_manager

# Realistic CTI Data Definitions
SAMPLE_SOURCES = [
    {
        "source_id": "SRC-001",
        "name": "CISA Automated Indicator Sharing (AIS)",
        "source_type": "Government CERT",
        "url": "https://www.cisa.gov/ais",
        "reliability_score": 0.98,
        "is_verified_threat": False,  # Government feed is a trusted reporter, not an attacker
        "is_attacker_source": False,
        "classification": "Trusted Intelligence Feed",
        "threats_count": 0
    },
    {
        "source_id": "SRC-002",
        "name": "Mandiant Threat Intelligence",
        "source_type": "Commercial Vendor",
        "url": "https://mandiant.com/threat-intel",
        "reliability_score": 0.95,
        "is_verified_threat": False,
        "is_attacker_source": False,
        "classification": "Trusted Intelligence Feed",
        "threats_count": 0
    },
    {
        "source_id": "SRC-003",
        "name": "CrowdStrike Falcon Intelligence",
        "source_type": "Commercial Vendor",
        "url": "https://crowdstrike.com/falcon-intel",
        "reliability_score": 0.96,
        "is_verified_threat": False,
        "is_attacker_source": False,
        "classification": "Trusted Intelligence Feed",
        "threats_count": 0
    },
    {
        "source_id": "SRC-004",
        "name": "DarkWeb Forum 'BreachForums v4'",
        "source_type": "DarkWeb OSINT",
        "url": "http://breach4x...onion",
        "reliability_score": 0.45,
        "is_verified_threat": True,  # High malicious payload origin / direct adversary hosting
        "is_attacker_source": True,
        "classification": "Malicious Infrastructure / Adversary Source",
        "threats_count": 0
    },
    {
        "source_id": "SRC-005",
        "name": "Cisco Talos Threat Feed",
        "source_type": "Commercial Vendor",
        "url": "https://talosintelligence.com",
        "reliability_score": 0.94,
        "is_verified_threat": False,
        "is_attacker_source": False,
        "classification": "Trusted Intelligence Feed",
        "threats_count": 0
    },
    {
        "source_id": "SRC-006",
        "name": "Bulletproof Hosting Cluster 'AS99120'",
        "source_type": "Rogue Autonomous System",
        "url": "http://185.220.101.5",
        "reliability_score": 0.15,
        "is_verified_threat": True,  # Direct C2 server hosting threat
        "is_attacker_source": True,
        "classification": "Direct Threat Origin (C2 Hosting)",
        "threats_count": 0
    },
    {
        "source_id": "SRC-007",
        "name": "Telegram Malware Distribution Channel 'RedlineVIP'",
        "source_type": "Social OSINT",
        "url": "https://t.me/redline_vip_dumps",
        "reliability_score": 0.30,
        "is_verified_threat": True,  # Direct source of infostealer payloads
        "is_attacker_source": True,
        "classification": "Direct Threat Origin (Payload Distribution)",
        "threats_count": 0
    },
    {
        "source_id": "SRC-008",
        "name": "CERT-EU Cyber Advisories",
        "source_type": "Government CERT",
        "url": "https://cert.europa.eu",
        "reliability_score": 0.97,
        "is_verified_threat": False,
        "is_attacker_source": False,
        "classification": "Trusted Intelligence Feed",
        "threats_count": 0
    }
]

SAMPLE_ACTORS = [
    {
        "actor_id": "ACT-001",
        "name": "APT29 (Cozy Bear / Nobelium)",
        "origin": "Russian Federation",
        "motivation": "Cyber Espionage & Diplomatic Intelligence",
        "targeted_sectors": ["Government", "Defense", "Think Tanks", "Cloud Providers"],
        "known_malware": ["Sunburst", "WellMess", "EnvyScout"]
    },
    {
        "actor_id": "ACT-002",
        "name": "LockBit Ransomware Gang",
        "origin": "Eastern Europe",
        "motivation": "Financial Extortion",
        "targeted_sectors": ["Healthcare", "Manufacturing", "Finance", "Critical Infrastructure"],
        "known_malware": ["LockBit 3.0", "LockBit 4.0 Green", "StealBit"]
    },
    {
        "actor_id": "ACT-003",
        "name": "Lazarus Group (Hidden Cobra)",
        "origin": "DPRK (North Korea)",
        "motivation": "Cryptocurrency Theft & Defense Espionage",
        "targeted_sectors": ["Crypto Exchanges", "Defense Contractors", "Banks"],
        "known_malware": ["AppleJeus", "BLINDINGCAN", "FastCash"]
    },
    {
        "actor_id": "ACT-004",
        "name": "Volt Typhoon",
        "origin": "People's Republic of China",
        "motivation": "Pre-positioning & Critical Infrastructure Sabotage",
        "targeted_sectors": ["Electric Grid", "Water Treatment", "Telecommunications", "Ports"],
        "known_malware": ["Living-off-the-Land (LotL)", "KV-botnet"]
    },
    {
        "actor_id": "ACT-005",
        "name": "Scattered Spider (UNC3944)",
        "origin": "Transnational / Western Teens",
        "motivation": "Financial Theft & SIM Swapping",
        "targeted_sectors": ["Hospitality", "Gaming", "Telecom", "Retail"],
        "known_malware": ["MimiKatz", "AnyDesk", "Ngrok"]
    }
]

SAMPLE_CVES = [
    {
        "cve_id": "CVE-2026-3021",
        "cvss_score": 9.8,
        "epss_score": 0.892,
        "description": "Pre-authentication buffer overflow in Enterprise VPN Gateway allowing arbitrary code execution.",
        "status": "Actively Exploited in the Wild"
    },
    {
        "cve_id": "CVE-2026-1184",
        "cvss_score": 8.8,
        "epss_score": 0.745,
        "description": "Privilege escalation vulnerability in Linux Kernel eBPF subsystem.",
        "status": "Public Exploit Available"
    },
    {
        "cve_id": "CVE-2026-4409",
        "cvss_score": 9.1,
        "epss_score": 0.912,
        "description": "SQL Injection in Apache ActiveMQ web console resulting in remote shell invocation.",
        "status": "Actively Exploited in the Wild"
    },
    {
        "cve_id": "CVE-2025-21298",
        "cvss_score": 7.5,
        "epss_score": 0.430,
        "description": "Microsoft Outlook Remote Code Execution Vulnerability.",
        "status": "Patch Available"
    }
]

SAMPLE_THREAT_TITLES = [
    ("LockBit 4.0 Exploiting Edge Firewalls with New Anti-Analysis Modules", "Ransomware", "Critical", 9.8, "ACT-002", "CVE-2026-3021", "SRC-003"),
    ("Volt Typhoon LotL Stealth Infiltration into Water SCADA Systems", "APT", "Critical", 9.6, "ACT-004", "CVE-2026-1184", "SRC-001"),
    ("RedLine Infostealer New Variant Bypassing Windows Defender via DLL Sideloading", "Infostealer", "High", 8.4, "ACT-005", "CVE-2025-21298", "SRC-007"),
    ("Lazarus Targeting Web3 Developers via Weaponized NPM Dependency Confusion", "Phishing", "High", 8.9, "ACT-003", "CVE-2026-4409", "SRC-002"),
    ("APT29 Spearphishing Campaign Impersonating Diplomatic Attache Invitations", "APT", "High", 8.7, "ACT-001", "CVE-2025-21298", "SRC-002"),
    ("Mirai-Variant Botnet 'DarkStorm' Exploiting Zero-Day in IoT Routers", "Botnet", "Medium", 7.2, "ACT-005", "CVE-2026-3021", "SRC-006"),
    ("Scattered Spider Multi-Factor Authentication Fatigue Campaign against Okta Tenants", "Phishing", "High", 8.5, "ACT-005", "CVE-2026-1184", "SRC-003"),
    ("BlackCat/ALPHV Successor Group Deploying Rust-based Cross-Platform Encryptor", "Ransomware", "Critical", 9.7, "ACT-002", "CVE-2026-4409", "SRC-005"),
    ("Qakbot Successor 'Pikabot' Re-emerging with Modular Proxy Payloads", "Trojan", "Medium", 7.6, "ACT-005", "CVE-2025-21298", "SRC-005"),
    ("Rogue AS99120 Hosting Malicious Cobalt Strike Beacons for Eastern Cybercartels", "Command and Control", "High", 8.8, "ACT-002", "CVE-2026-3021", "SRC-006")
]

MITRE_TECHNIQUES = [
    "T1190 - Exploit Public-Facing Application",
    "T1059.001 - PowerShell Execution",
    "T1566.001 - Spearphishing Attachment",
    "T1078 - Valid Accounts",
    "T1486 - Data Encrypted for Impact",
    "T1071.001 - Web Protocols Command and Control",
    "T1055 - Process Injection",
    "T1041 - Exfiltration Over C2 Channel"
]

def generate_sample_iocs(count=4):
    types = ["ipv4", "domain", "sha256", "url"]
    iocs = []
    for _ in range(count):
        t = random.choice(types)
        if t == "ipv4":
            val = f"{random.randint(45, 195)}.{random.randint(10, 250)}.{random.randint(1, 254)}.{random.randint(1, 254)}"
        elif t == "domain":
            val = f"c2-{random.choice(['sync', 'update', 'auth', 'telemetry', 'gateway'])}-{random.randint(100, 999)}.org"
        elif t == "sha256":
            val = "".join(random.choices("0123456789abcdef", k=64))
        else:
            val = f"https://cdn-evil-{random.randint(10, 99)}.net/payload_{random.randint(1000, 9999)}.bin"
        
        iocs.append({
            "ioc_id": f"IOC-{random.randint(10000, 99999)}",
            "type": t,
            "value": val,
            "reputation": random.choice(["confirmed_malicious", "suspicious", "high_risk"]),
            "confidence_score": random.randint(75, 100),
            "first_seen": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
    return iocs

def seed_database():
    """Seeds the database with production schema for CTI Digest."""
    db = db_manager.get_db()
    
    # 1. Clean existing collections
    for col_name in ["sources", "threat_actors", "cves", "threat_reports", "sources_embedded_threats", "working_set_reports"]:
        try:
            db[col_name].drop()
        except Exception:
            pass

    # 2. Insert Sources
    db.sources.insert_many(SAMPLE_SOURCES)
    print(f"[Seed] Inserted {len(SAMPLE_SOURCES)} intelligence sources.")

    # 3. Insert Threat Actors
    db.threat_actors.insert_many(SAMPLE_ACTORS)
    print(f"[Seed] Inserted {len(SAMPLE_ACTORS)} threat actors.")

    # 4. Insert CVEs
    db.cves.insert_many(SAMPLE_CVES)
    print(f"[Seed] Inserted {len(SAMPLE_CVES)} CVE entries.")

    # 5. Insert Threat Reports (Realistic production documents with embedded IOCs and referenced source/actor/CVE)
    reports = []
    now = datetime.datetime.now(datetime.timezone.utc)
    
    # Generate 50 realistic enriched threat reports
    for i in range(50):
        template = SAMPLE_THREAT_TITLES[i % len(SAMPLE_THREAT_TITLES)]
        title, threat_type, severity, cvss, actor_id, cve_id, source_id = template
        
        # Determine verdict: Is this an actual threat or benign/false positive?
        # Malicious rogue sources (SRC-004, SRC-006, SRC-007) generate direct actual threats
        is_direct_adversary_source = source_id in ["SRC-004", "SRC-006", "SRC-007"]
        actual_threat_verdict = "Actual Threat" if (is_direct_adversary_source or random.random() > 0.15) else "False Positive"

        doc = {
            "threat_id": f"CTI-2026-{1000 + i}",
            "title": f"{title} [Variant #{i + 1}]",
            "threat_type": threat_type,
            "severity": severity,
            "cvss_score": cvss,
            "confidence": random.randint(80, 99),
            "description": f"Detailed tactical intelligence report on {threat_type} activity originating from observed telemetry. Adversaries observed deploying stealth techniques targeting enterprise infrastructure.",
            "published_at": (now - datetime.timedelta(days=random.randint(0, 45))).isoformat(),
            
            # --- REFERENCING DECISIONS ---
            # Referenced to avoid duplicating large changing metadata and prevent document unbounded growth
            "source_id": source_id,            # References 'sources.source_id'
            "actor_id": actor_id,              # References 'threat_actors.actor_id'
            "cve_ids": [cve_id],               # References 'cves.cve_id'

            # --- EMBEDDING DECISIONS ---
            # Embedded because IOCs are tightly coupled to this specific report instance and retrieved together
            "indicators": generate_sample_iocs(count=random.randint(3, 7)),
            
            # Embedded classification and mitigation
            "classification": {
                "verdict": actual_threat_verdict,
                "status": "Active Threat" if actual_threat_verdict == "Actual Threat" else "Benign / Whitelisted",
                "kill_chain_stage": random.choice(["Initial Access", "Command & Control", "Impact / Encryption", "Credential Access"]),
                "mitre_techniques": random.sample(MITRE_TECHNIQUES, k=2)
            },
            "tags": [threat_type.lower(), severity.lower(), actor_id.lower(), f"feed-{source_id.lower()}"],
            "telemetry": {
                "targeted_hosts_count": random.randint(50, 5000),
                "is_zero_day": (cvss >= 9.5),
                "remediation_status": random.choice(["Open", "Patched", "In Mitigation"])
            }
        }
        reports.append(doc)

    db.threat_reports.insert_many(reports)
    print(f"[Seed] Inserted {len(reports)} enriched threat reports into 'threat_reports'.")

    # Update threat counts in sources
    for src in SAMPLE_SOURCES:
        cnt = db.threat_reports.count_documents({"source_id": src["source_id"]})
        db.sources.update_one({"source_id": src["source_id"]}, {"$set": {"threats_count": cnt}})

    # 6. Seed Lab 7.1 Try It Yourself Redesigned Collection: sources_embedded_threats
    # In this redesigned schema, threats are embedded directly inside the source document!
    embedded_sources = []
    for src in SAMPLE_SOURCES:
        src_copy = dict(src)
        src_threats = list(db.threat_reports.find({"source_id": src["source_id"]}))
        
        # Redesign: Decide which source is an actual threat by embedding threat verdicts and payloads inside the source!
        src_copy["embedded_threats"] = src_threats
        src_copy["threat_summary"] = {
            "total_threats": len(src_threats),
            "actual_threats_count": sum(1 for t in src_threats if t.get("classification", {}).get("verdict") == "Actual Threat"),
            "highest_severity": "Critical" if any(t["severity"] == "Critical" for t in src_threats) else "High"
        }
        # Explicit verdict deciding if this source itself is an actual threat vector
        src_copy["is_actual_threat_source"] = src_copy["threat_summary"]["actual_threats_count"] > 0 and src_copy["is_attacker_source"]
        embedded_sources.append(src_copy)

    db.sources_embedded_threats.insert_many(embedded_sources)
    print(f"[Seed] Created Lab 7.1 Try It Yourself embedded redesign collection 'sources_embedded_threats'.")

    # Register documents in cache simulator
    for r in reports:
        doc_size = db_manager.calculate_bson_size(r)
        db_manager.cache_sim.register_document(str(r["_id"]), doc_size)

    return True

if __name__ == "__main__":
    seed_database()
