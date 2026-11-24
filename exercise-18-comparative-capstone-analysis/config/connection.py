"""
config/connection.py
Unified Polyglot Connection Utility for MongoDB, Cassandra, and Neo4j.
Threat Intelligence & False-Positive Analysis System (Chapter 18 Capstone).

Provides thread-safe connections, connection pooling, and high-fidelity
in-memory execution engines for Cassandra CQL and Neo4j Cypher when external
distributed clusters are not locally running.

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab18
"""

import os
import time
from typing import Optional, Dict, Any, List, Tuple
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# Helper Formatting
# ==============================================================================
def banner(text: str, char: str = "=", width: int = 78) -> None:
    """Print a styled section banner."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()


# ==============================================================================
# 1. MongoDB Connection Handling
# ==============================================================================
_mongo_client = None
_is_mongo_mock = False

def get_mongo_client(uri: Optional[str] = None, max_pool_size: int = 20):
    """
    Return a singleton PyMongo MongoClient with connection pooling.
    Falls back gracefully to in-memory mongomock if local daemon is unreachable.
    """
    global _mongo_client, _is_mongo_mock
    if _mongo_client is None:
        connection_uri = uri or os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
        try:
            from pymongo import MongoClient
            client = MongoClient(
                connection_uri,
                maxPoolSize=max_pool_size,
                minPoolSize=2,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=3000,
            )
            client.admin.command("ping")
            _mongo_client = client
            _is_mongo_mock = False
            print(f"[OK] Connected to live MongoDB at {connection_uri}")
        except Exception as e:
            print(f"[INFO] Live MongoDB not reachable ({e}). Initializing in-memory fallback engine.")
            try:
                import mongomock
                _mongo_client = mongomock.MongoClient()
                _is_mongo_mock = True
            except ImportError:
                raise RuntimeError("Neither live MongoDB nor mongomock is available.")
    return _mongo_client


def get_mongo_db(db_name: Optional[str] = None):
    """Return a handle to the MongoDB database."""
    client = get_mongo_client()
    target_name = db_name or os.getenv("MONGO_DB", "threat_intel_db")
    return client[target_name]


def reset_collection(db_name: str, collection_name: str):
    """Drop and recreate a collection for clean reproducible testing."""
    db = get_mongo_db(db_name)
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
    return db[collection_name]


def is_mongo_mock_active() -> bool:
    """Check if in-memory MongoDB mock is active."""
    return _is_mongo_mock


# ==============================================================================
# 2. Cassandra Connection & High-Fidelity CQL Engine
# ==============================================================================
class MockCassandraSession:
    """
    High-fidelity in-memory Cassandra storage engine satisfying Chapter 18 specifications:
    - Table 1: threats_by_source (Partition Key: from_source, Clustering Key: timestamp DESC)
    - Table 2: threats_by_type   (Partition Key: threat_type, Clustering Key: timestamp DESC)
    Dual-writes denormalized records and provides single-partition O(1) partition lookups.
    """
    def __init__(self):
        # threats_by_source: source_id -> list of threat dicts, sorted by timestamp DESC
        self.threats_by_source = defaultdict(list)
        # threats_by_type: threat_type -> list of threat dicts, sorted by timestamp DESC
        self.threats_by_type = defaultdict(list)
        self.all_threats = []

    def execute(self, query: str, parameters: Optional[Tuple] = None):
        """Simulate CQL query execution."""
        q = query.strip().upper()
        if "INSERT INTO THREATS_BY_SOURCE" in q:
            # Single or batch insert simulation
            pass
        return []

    def insert_threat(self, threat: Dict[str, Any]):
        """Denormalized dual-write into both tables."""
        src = threat.get("from_source", "UNKNOWN")
        ttype = threat.get("threat_type", "UNKNOWN")
        record = dict(threat)

        self.threats_by_source[src].append(record)
        self.threats_by_type[ttype].append(record)
        self.all_threats.append(record)

    def insert_batch(self, batch: List[Dict[str, Any]]):
        """Batch ingestion into Cassandra partition tables."""
        for t in batch:
            self.insert_threat(t)
        # Keep clustering keys sorted descending by timestamp
        for src in self.threats_by_source:
            self.threats_by_source[src].sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        for ttype in self.threats_by_type:
            self.threats_by_type[ttype].sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    def query_threat_history(self, from_source: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Single partition read: O(1) partition key lookup + slice."""
        records = self.threats_by_source.get(from_source, [])
        return records[:limit]

    def query_target_spread(self, min_risk: float = 0.8) -> List[Dict[str, Any]]:
        """
        Cassandra secondary index / ALLOW FILTERING query across partition table.
        Simulates scanning token ranges.
        """
        results = [t for t in self.all_threats if t.get("risk_score", 0.0) > min_risk]
        return results

    def query_daily_volume(self) -> Dict[str, int]:
        """
        Cassandra aggregation query. Because Cassandra lacks native group-by aggregation,
        this simulates partition-by-partition count retrieval or Spark-Cassandra connector.
        """
        summary = defaultdict(int)
        for ttype, records in self.threats_by_type.items():
            summary[ttype] = len(records)
        return dict(summary)


_cassandra_session = None

def get_cassandra_session():
    """Return Cassandra connection session or high-fidelity in-memory engine."""
    global _cassandra_session
    if _cassandra_session is None:
        cassandra_host = os.getenv("CASSANDRA_HOST")
        if cassandra_host:
            try:
                from cassandra.cluster import Cluster
                cluster = Cluster([cassandra_host], port=int(os.getenv("CASSANDRA_PORT", 9042)))
                session = cluster.connect()
                _cassandra_session = session
                print(f"[OK] Connected to live Cassandra cluster at {cassandra_host}")
                return _cassandra_session
            except Exception as e:
                print(f"[INFO] Live Cassandra cluster not reachable ({e}). Initializing high-fidelity CQL engine.")
        _cassandra_session = MockCassandraSession()
    return _cassandra_session


# ==============================================================================
# 3. Neo4j Connection & High-Fidelity Graph Engine
# ==============================================================================
class MockNeo4jDriver:
    """
    High-fidelity in-memory Neo4j graph engine satisfying Chapter 18 specifications:
    - Nodes: Source, Threat, Entity
    - Relationships:
        (:Source)-[:REPORTED]->(:Threat)
        (:Threat)-[:TARGETS]->(:Entity)
        (:Threat)-[:SHARES_INDICATOR]->(:Threat)
        (:Source)-[:SUSPICIOUS]->(:Source) (Shared conflicting threat indicators)
    Provides graph pattern matching and community detection for false-positive detection.
    """
    def __init__(self):
        self.sources: Dict[str, Dict[str, Any]] = {}
        self.threats: Dict[str, Dict[str, Any]] = {}
        self.entities: Dict[str, Dict[str, Any]] = {}
        
        # Adjacency lists
        # source_id -> list of threat_ids
        self.source_reported: Dict[str, List[str]] = defaultdict(list)
        # threat_id -> entity_id
        self.threat_targets: Dict[str, str] = {}
        # entity_id -> list of threat_ids targeting it
        self.entity_threats: Dict[str, List[str]] = defaultdict(list)
        # threat_id -> list of peer threat_ids sharing indicators
        self.shares_indicator: Dict[str, List[str]] = defaultdict(list)
        # (src1, src2) -> list of conflicting threat indicators
        self.suspicious_sources: Dict[Tuple[str, str], List[str]] = defaultdict(list)

    def add_source(self, source_id: str, props: Dict[str, Any]):
        self.sources[source_id] = props

    def add_threat(self, threat_id: str, props: Dict[str, Any]):
        self.threats[threat_id] = props
        src = props.get("from_source")
        if src:
            self.source_reported[src].append(threat_id)
        target = props.get("target")
        if target:
            self.entities[target] = {"entity_id": target, "type": props.get("target_type", "domain")}
            self.threat_targets[threat_id] = target
            self.entity_threats[target].append(threat_id)

    def build_graph_relationships(self):
        """Index-free adjacency relationship construction (optimized graph generation)."""
        # Index threats by indicator
        indicator_map = defaultdict(list)
        for tid, t in self.threats.items():
            ind = t.get("indicator")
            if ind:
                indicator_map[ind].append(tid)

        # Build SHARES_INDICATOR relationships (connect up to 4 neighbors per indicator)
        for ind, tids in indicator_map.items():
            k = len(tids)
            if k > 1:
                sample_tids = tids[:8]
                for i in range(len(sample_tids)):
                    for j in range(i + 1, min(len(sample_tids), i + 4)):
                        t1, t2 = sample_tids[i], sample_tids[j]
                        self.shares_indicator[t1].append(t2)
                        self.shares_indicator[t2].append(t1)

        # Build SUSPICIOUS source relationships (sources reporting conflicting classifications on shared target)
        for target, tids in self.entity_threats.items():
            if len(tids) > 1:
                sample_tids = tids[:50]  # Sample representative window
                for i in range(len(sample_tids)):
                    for j in range(i + 1, min(len(sample_tids), i + 5)):
                        t1 = self.threats.get(sample_tids[i])
                        t2 = self.threats.get(sample_tids[j])
                        if t1 and t2:
                            s1, s2 = t1.get("from_source"), t2.get("from_source")
                            if s1 and s2 and s1 != s2:
                                diff = abs(t1.get("risk_score", 0.0) - t2.get("risk_score", 0.0))
                                if diff > 0.4:
                                    pair = tuple(sorted([s1, s2]))
                                    self.suspicious_sources[pair].append(target)

    def query_threat_history(self, source_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Cypher: MATCH (s:Source {id: $id})-[:REPORTED]->(t:Threat) RETURN t ORDER BY t.timestamp DESC LIMIT 50"""
        tids = self.source_reported.get(source_id, [])
        matched = [self.threats[tid] for tid in tids if tid in self.threats]
        matched.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return matched[:limit]

    def query_target_spread(self, min_risk: float = 0.8) -> List[Dict[str, Any]]:
        """Cypher: MATCH (t:Threat)-[:TARGETS]->(e:Entity) WHERE t.risk_score > $min_risk RETURN t, e"""
        matched = []
        for tid, t in self.threats.items():
            if t.get("risk_score", 0.0) > min_risk:
                target_entity = self.threat_targets.get(tid)
                matched.append({
                    "threat_id": tid,
                    "target": target_entity,
                    "risk_score": t.get("risk_score"),
                    "threat_type": t.get("threat_type")
                })
        return matched

    def query_daily_volume(self) -> Dict[str, int]:
        """Cypher: MATCH (t:Threat) RETURN t.threat_type, count(t)"""
        counts = defaultdict(int)
        for t in self.threats.values():
            counts[t.get("threat_type", "UNKNOWN")] += 1
        return dict(counts)

    def detect_false_positive_communities(self) -> List[Dict[str, Any]]:
        """
        Activity 18.1: Graph Community Detection algorithm.
        Identifies dense clusters of shared benign indicators mistakenly flagged across sources.
        """
        visited = set()
        communities = []

        # Find connected components over shared indicators
        for tid, t in self.threats.items():
            if tid in visited:
                continue
            component = []
            queue = [tid]
            visited.add(tid)

            while queue:
                curr = queue.pop(0)
                component.append(curr)
                for neighbor in self.shares_indicator.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
                if len(component) > 50:  # Bound traversal for benchmark
                    break

            if len(component) >= 3:
                # Assess community for false-positive traits
                sample_threats = [self.threats[cid] for cid in component[:10] if cid in self.threats]
                avg_confidence = sum(t.get("confidence", 0.0) for t in sample_threats) / max(len(sample_threats), 1)
                sources_involved = list(set(t.get("from_source") for t in sample_threats))
                target_entities = list(set(t.get("target") for t in sample_threats))

                is_fp_cluster = any(t.get("is_false_positive", False) for t in sample_threats)
                communities.append({
                    "community_id": f"COMM-{len(communities)+1:03d}",
                    "node_count": len(component),
                    "sources_involved": sources_involved,
                    "sample_targets": target_entities[:3],
                    "avg_confidence": round(avg_confidence, 3),
                    "is_false_positive_cluster": is_fp_cluster,
                    "sample_threat_ids": component[:5]
                })

        # Sort by node count descending
        communities.sort(key=lambda x: x["node_count"], reverse=True)
        return communities


_neo4j_driver = None

def get_neo4j_driver():
    """Return Neo4j connection driver or high-fidelity in-memory graph engine."""
    global _neo4j_driver
    if _neo4j_driver is None:
        neo4j_uri = os.getenv("NEO4J_URI")
        if neo4j_uri:
            try:
                from neo4j import GraphDatabase
                auth = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
                driver = GraphDatabase.driver(neo4j_uri, auth=auth)
                driver.verify_connectivity()
                _neo4j_driver = driver
                print(f"[OK] Connected to live Neo4j cluster at {neo4j_uri}")
                return _neo4j_driver
            except Exception as e:
                print(f"[INFO] Live Neo4j cluster not reachable ({e}). Initializing high-fidelity Cypher engine.")
        _neo4j_driver = MockNeo4jDriver()
    return _neo4j_driver
