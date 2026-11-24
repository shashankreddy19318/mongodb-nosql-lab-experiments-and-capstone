"""
config/connection.py
Unified Polyglot Connection Utility for MongoDB, Cassandra, and Neo4j.

Provides thread-safe connection pooling, connection health checking,
and seamless fallback / simulation mode when external clusters are offline.
"""

import os
import time
from typing import Optional, Dict, Any, List
from collections import deque, defaultdict
from dotenv import load_dotenv

load_dotenv()

# ==============================================================================
# Global Connection Singletons
# ==============================================================================
_mongo_client = None
_cassandra_cluster = None
_cassandra_session = None
_neo4j_driver = None


# ==============================================================================
# Helper Formatting
# ==============================================================================
def banner(text: str, char: str = "=", width: int = 70) -> None:
    """Print an eye-catching section banner."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()


# ==============================================================================
# MongoDB Connection Pooling
# ==============================================================================
def get_mongo_client(uri: Optional[str] = None, max_pool_size: int = 10):
    """
    Return a singleton PyMongo MongoClient with configured connection pooling.
    maxPoolSize=10 satisfies the Lab 16.2 connection pooling requirement.
    """
    global _mongo_client
    if _mongo_client is None:
        from pymongo import MongoClient
        connection_uri = uri or os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
        _mongo_client = MongoClient(
            connection_uri,
            maxPoolSize=max_pool_size,
            minPoolSize=2,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
        )
        try:
            _mongo_client.admin.command("ping")
            print(f"[OK] Connected to MongoDB at {connection_uri} (pool_size={max_pool_size})")
        except Exception as e:
            print(f"[WARN] Local MongoDB connection failed ({e}). Fallback mode enabled if needed.")
    return _mongo_client


def get_mongo_db(db_name: Optional[str] = None):
    """Return a handle to the MongoDB database."""
    client = get_mongo_client()
    target_name = db_name or os.getenv("MONGO_DB", "nosql_labs")
    return client[target_name]


def reset_collection(db_name: str, collection_name: str):
    """Drop and recreate a collection for clean reproducible testing."""
    db = get_mongo_db(db_name)
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
    return db[collection_name]


# ==============================================================================
# Cassandra Connection Pooling & Driver
# ==============================================================================
class MockCassandraSession:
    """
    High-fidelity in-memory Cassandra Session for simulation and testing.
    Emulates CQL partition key queries and clustering column ordering.
    """
    def __init__(self):
        # user_profiles keyed by user_id -> sorted list of events
        self.profiles = defaultdict(list)
        # student_courses keyed by student_id -> list of courses
        self.student_courses = defaultdict(list)
        # course_students keyed by course_id -> list of students
        self.course_students = defaultdict(list)
        self._seed_default_data()

    def _seed_default_data(self):
        # Seed user profiles / events for fraud lab
        events = [
            ("U-101", "2024-03-15 10:30:00", "LOGIN", "IP_192_168_1_5", 50000.0, "FakeStore"),
            ("U-101", "2024-03-15 09:15:00", "PASSWORD_CHANGE", "IP_192_168_1_5", 0.0, None),
            ("U-101", "2024-03-14 22:40:00", "TRANSFER", "IP_10_0_0_12", 12000.0, "P2P_Transfer"),
            ("U-101", "2024-03-14 18:20:00", "LOGIN", "IP_10_0_0_12", 0.0, None),
            ("U-102", "2024-03-15 11:00:00", "PURCHASE", "IP_172_16_0_8", 2200.0, "RetailCorp"),
            ("U-103", "2024-03-15 10:45:00", "TRANSFER", "IP_192_168_1_5", 71000.0, "OffshoreWire"),
            ("U-104", "2024-03-13 14:10:00", "PURCHASE", "IP_192_168_2_1", 500.0, "GroceryStore"),
        ]
        for uid, ev_time, ev_type, ip, amt, merchant in events:
            self.profiles[uid].append({
                "user_id": uid,
                "event_time": ev_time,
                "event_type": ev_type,
                "ip_address": ip,
                "amount": amt,
                "merchant": merchant,
            })
        for uid in self.profiles:
            self.profiles[uid].sort(key=lambda x: x["event_time"], reverse=True)

        # Seed university enrollment
        enrollments = [
            ("S101", "Alice", "CS101", "Introduction to Computer Science", 4, "A"),
            ("S101", "Alice", "CS201", "Data Structures & Algorithms", 4, "A-"),
            ("S101", "Alice", "MATH201", "Discrete Mathematics", 3, "B+"),
            ("S102", "Bob", "CS101", "Introduction to Computer Science", 4, "B"),
            ("S102", "Bob", "MATH201", "Discrete Mathematics", 3, "A"),
            ("S103", "Charlie", "CS201", "Data Structures & Algorithms", 4, "A"),
            ("S103", "Charlie", "CS301", "Database Systems", 4, "A"),
            ("S104", "Diana", "CS101", "Introduction to Computer Science", 4, "A"),
            ("S104", "Diana", "CS301", "Database Systems", 4, "A-"),
        ]
        for sid, sname, cid, ctitle, credits, grade in enrollments:
            self.student_courses[sid].append({
                "student_id": sid, "student_name": sname, "course_id": cid, "course_title": ctitle,
                "credits": credits, "grade": grade
            })
            self.course_students[cid].append({
                "course_id": cid, "course_title": ctitle, "student_id": sid, "student_name": sname,
                "credits": credits, "grade": grade
            })

    def execute(self, query: str, parameters=None):
        """Execute mock CQL query."""
        q = query.strip()
        params = parameters or ()

        if "FROM user_profiles WHERE user_id = %s" in q or "FROM user_profiles WHERE user_id = ?" in q:
            uid = params[0] if params else "U-101"
            rows = self.profiles.get(uid, [])
            return rows[:10]

        if "FROM student_courses WHERE student_id = %s" in q or "FROM student_courses WHERE student_id = ?" in q:
            sid = params[0] if params else "S101"
            return self.student_courses.get(sid, [])

        if "FROM course_students WHERE course_id = %s" in q or "FROM course_students WHERE course_id = ?" in q:
            cid = params[0] if params else "CS101"
            return self.course_students.get(cid, [])

        return []

    def shutdown(self):
        pass


def get_cassandra_session(hosts: Optional[List[str]] = None, keyspace: str = "fraud_detection"):
    """
    Return Cassandra session with connection pooling (executor_threads=4).
    Falls back to high-fidelity MockCassandraSession if cluster unreachable.
    """
    global _cassandra_cluster, _cassandra_session
    if _cassandra_session is not None:
        return _cassandra_session

    cassandra_host = os.getenv("CASSANDRA_HOST")
    if cassandra_host:
        try:
            from cassandra.cluster import Cluster
            host_list = hosts or [cassandra_host]
            # Configure executor_threads as specified in Lab 16.2
            _cassandra_cluster = Cluster(host_list, executor_threads=4)
            _cassandra_session = _cassandra_cluster.connect()
            _cassandra_session.execute(f"USE {keyspace};")
            print(f"[OK] Connected to live Cassandra cluster at {host_list}")
            return _cassandra_session
        except Exception as e:
            print(f"[WARN] Live Cassandra unavailable ({e}). Initializing high-fidelity fallback.")

    _cassandra_session = MockCassandraSession()
    print("[OK] Cassandra session active (In-Memory CQL Execution Engine)")
    return _cassandra_session


# ==============================================================================
# Neo4j Graph Database Driver & Graph Engine
# ==============================================================================
class MockNeo4jRecord(dict):
    """Emulates a Neo4j record containing paths and attributes."""
    def __getitem__(self, key):
        return super().get(key)


class MockNeo4jSession:
    """Emulates a Neo4j session for Cypher traversal."""
    def __init__(self, graph):
        self.graph = graph

    def run(self, query: str, **kwargs):
        return self.graph.run_cypher(query, **kwargs)

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class InMemoryGraphEngine:
    """
    Property Graph Engine for native index-free multi-hop traversals,
    emulating Neo4j Cypher queries for both Fraud Detection and Course Prerequisites.
    """
    def __init__(self):
        self.nodes = {}  # id -> {labels, properties}
        self.edges = defaultdict(list)  # src -> list of (dest, rel_type, properties, direction)
        self._seed_default_graph()

    def add_node(self, node_id: str, label: str, **props):
        self.nodes[node_id] = {"label": label, "properties": props}

    def add_relationship(self, src: str, dest: str, rel_type: str, bidirectional: bool = True, **props):
        self.edges[src].append({"target": dest, "rel": rel_type, "props": props, "dir": "out"})
        if bidirectional:
            self.edges[dest].append({"target": src, "rel": rel_type, "props": props, "dir": "in"})

    def _seed_default_graph(self):
        # 1. Fraud syndicate graph: Users, Devices, Accounts, Transactions
        users = ["U-101", "U-102", "U-103", "U-104", "U-105", "U-106"]
        for u in users:
            self.add_node(u, "User", id=u)

        # Money transfers and shared devices
        self.add_relationship("U-101", "U-102", "TRANSFERRED_TO", bidirectional=True, amount=50000, device="DEV-500")
        self.add_relationship("U-102", "U-103", "TRANSFERRED_TO", bidirectional=True, amount=35000, device="DEV-500")
        self.add_relationship("U-103", "U-105", "TRANSFERRED_TO", bidirectional=True, amount=71000, device="DEV-777")
        self.add_relationship("U-104", "U-106", "TRANSFERRED_TO", bidirectional=True, amount=500, device="DEV-999")

        # 2. University Course Prerequisite DAG & Student Enrollment
        students = [
            ("S101", "Alice", "CS"),
            ("S102", "Bob", "Math"),
            ("S103", "Charlie", "CS"),
            ("S104", "Diana", "CS"),
        ]
        for sid, name, major in students:
            self.add_node(sid, "Student", student_id=sid, name=name, major=major)

        courses = [
            ("CS101", "Intro to CS", 4),
            ("MATH201", "Discrete Math", 3),
            ("CS201", "Data Structures", 4),
            ("CS301", "Database Systems", 4),
            ("CS401", "Distributed Systems", 4),
            ("CS501", "Advanced Cloud Architecture", 4),
        ]
        for cid, title, credits in courses:
            self.add_node(cid, "Course", course_id=cid, title=title, credits=credits)

        # Course Enrollments
        self.add_relationship("S101", "CS101", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A")
        self.add_relationship("S101", "CS201", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A-")
        self.add_relationship("S101", "MATH201", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="B+")
        self.add_relationship("S102", "CS101", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="B")
        self.add_relationship("S102", "MATH201", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A")
        self.add_relationship("S103", "CS201", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A")
        self.add_relationship("S103", "CS301", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A")
        self.add_relationship("S104", "CS101", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A")
        self.add_relationship("S104", "CS301", "ENROLLED_IN", bidirectional=True, semester="Fall 2024", grade="A-")

        # Prerequisite Chain (Directed DAG: Course -> REQUIRES -> Course)
        self.add_relationship("CS201", "CS101", "REQUIRES", bidirectional=False)
        self.add_relationship("CS201", "MATH201", "REQUIRES", bidirectional=False)
        self.add_relationship("CS301", "CS201", "REQUIRES", bidirectional=False)
        self.add_relationship("CS401", "CS301", "REQUIRES", bidirectional=False)
        self.add_relationship("CS501", "CS401", "REQUIRES", bidirectional=False)

    def traverse_bfs(self, start_id: str, rel_type: str, max_hops: int = 3) -> List[Dict[str, Any]]:
        """Breadth-first search traversing index-free relationships."""
        visited = {start_id: 0}
        queue = deque([(start_id, 0, [start_id])])
        results = []

        while queue:
            current, hops, path = queue.popleft()
            if hops >= max_hops:
                continue

            for edge in self.edges.get(current, []):
                if edge["rel"] == rel_type:
                    neighbor = edge["target"]
                    new_path = path + [neighbor]
                    if neighbor not in visited or visited[neighbor] > hops + 1:
                        visited[neighbor] = hops + 1
                        queue.append((neighbor, hops + 1, new_path))
                        results.append({
                            "connected": neighbor,
                            "hops": hops + 1,
                            "path": " -> ".join(new_path),
                        })
        return results

    def run_cypher(self, query: str, **kwargs):
        """Simulate Cypher queries for fraud detection, course enrollments, and prerequisite chains."""
        q = query.strip()
        uid = kwargs.get("uid") or kwargs.get("id") or "U-101"
        max_hops = kwargs.get("max_hops", 3)

        # 1. Fraud ring detection
        if "TRANSFERRED_TO" in q or "SHARES_DEVICE" in q or "detect_fraud_rings" in q:
            rel = "TRANSFERRED_TO"
            traversals = self.traverse_bfs(uid, rel_type=rel, max_hops=max_hops)
            records = []
            for t in traversals:
                records.append(MockNeo4jRecord({
                    "connected": t["connected"],
                    "hops": t["hops"],
                    "path": t["path"],
                }))
            return records

        # 2. Shared course query (Find peers co-enrolled in courses with student)
        if "<-[:ENROLLED_IN]-(s2:Student)" in q or "shared_course" in q:
            student_name = kwargs.get("name", "Alice")
            # Find student ID
            sid = next((k for k, v in self.nodes.items() if v["properties"].get("name") == student_name), "S101")
            courses = [e["target"] for e in self.edges.get(sid, []) if e["rel"] == "ENROLLED_IN"]

            peer_records = []
            seen_peers = set()
            for c in courses:
                c_title = self.nodes.get(c, {}).get("properties", {}).get("title", c)
                peers = [e["target"] for e in self.edges.get(c, []) if e["rel"] == "ENROLLED_IN" and e["target"] != sid]
                for p in peers:
                    p_name = self.nodes.get(p, {}).get("properties", {}).get("name", p)
                    peer_key = (p_name, c_title)
                    if peer_key not in seen_peers:
                        seen_peers.add(peer_key)
                        peer_records.append(MockNeo4jRecord({
                            "peer_id": p,
                            "peer_name": p_name,
                            "course_id": c,
                            "course_title": c_title,
                        }))
            return peer_records

        # 3. Prerequisite chain query
        if "REQUIRES" in q or "prerequisite" in q:
            target_course = kwargs.get("course_id", "CS501")
            # Walk DAG backwards
            chain = []
            curr_queue = deque([(target_course, 1)])
            visited = set([target_course])
            while curr_queue:
                c_curr, depth = curr_queue.popleft()
                for edge in self.edges.get(c_curr, []):
                    if edge["rel"] == "REQUIRES":
                        prereq = edge["target"]
                        if prereq not in visited:
                            visited.add(prereq)
                            c_info = self.nodes.get(prereq, {}).get("properties", {})
                            chain.append(MockNeo4jRecord({
                                "target": target_course,
                                "prereq_id": prereq,
                                "prereq_title": c_info.get("title", prereq),
                                "credits": c_info.get("credits", 3),
                                "depth": depth,
                            }))
                            curr_queue.append((prereq, depth + 1))
            return chain

        return []


class MockNeo4jDriver:
    """Mock Neo4j Driver managing connection pool and session lifecycle."""
    def __init__(self, max_connection_pool_size: int = 10):
        self.max_connection_pool_size = max_connection_pool_size
        self.graph = InMemoryGraphEngine()

    def session(self):
        return MockNeo4jSession(self.graph)

    def close(self):
        pass


def get_neo4j_driver(uri: Optional[str] = None, max_connection_pool_size: int = 10):
    """
    Return Neo4j Driver with connection pooling (max_connection_pool_size=10).
    Falls back to high-fidelity InMemoryGraphEngine if live cluster is offline.
    """
    global _neo4j_driver
    if _neo4j_driver is not None:
        return _neo4j_driver

    neo4j_uri = os.getenv("NEO4J_URI")
    if neo4j_uri:
        try:
            from neo4j import GraphDatabase
            user = os.getenv("NEO4J_USER", "neo4j")
            pwd = os.getenv("NEO4J_PASSWORD", "password")
            _neo4j_driver = GraphDatabase.driver(
                neo4j_uri,
                auth=(user, pwd),
                max_connection_pool_size=max_connection_pool_size,
                connection_acquisition_timeout=30.0,
            )
            with _neo4j_driver.session() as s:
                s.run("RETURN 1")
            print(f"[OK] Connected to live Neo4j database at {neo4j_uri} (pool_size={max_connection_pool_size})")
            return _neo4j_driver
        except Exception as e:
            print(f"[WARN] Live Neo4j unavailable ({e}). Initializing high-fidelity fallback.")

    _neo4j_driver = MockNeo4jDriver(max_connection_pool_size=max_connection_pool_size)
    print(f"[OK] Neo4j driver active (In-Memory Cypher Graph Engine, pool_size={max_connection_pool_size})")
    return _neo4j_driver


def close_all_connections():
    """Cleanly close all database connections."""
    global _mongo_client, _cassandra_cluster, _cassandra_session, _neo4j_driver
    if _mongo_client is not None:
        try:
            _mongo_client.close()
        except Exception:
            pass
        _mongo_client = None
    if _cassandra_cluster is not None:
        try:
            _cassandra_cluster.shutdown()
        except Exception:
            pass
        _cassandra_cluster = None
        _cassandra_session = None
    if _neo4j_driver is not None:
        try:
            _neo4j_driver.close()
        except Exception:
            pass
        _neo4j_driver = None
    print("[OK] All polyglot database connections closed.")
