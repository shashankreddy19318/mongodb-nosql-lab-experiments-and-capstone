"""
config/connection.py
Unified connection provider for MongoDB, Cassandra, and Neo4j.
Compatible with Chapters 1-18 capstone scripts.
"""

import os
import time
from typing import Optional, Dict, Any, List
from collections import defaultdict
from app.database import get_mongo_client, get_db as get_mongo_db, is_mock_active as is_mongo_mock_active

def banner(text: str, char: str = "=", width: int = 78) -> None:
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()

def reset_collection(db, collection_name: str):
    if collection_name in db.list_collection_names():
        db[collection_name].drop()

class SimulatedCassandraSession:
    def __init__(self):
        self.tables = defaultdict(list)
    
    def execute(self, query: str, params: Optional[Any] = None):
        return []

class SimulatedNeo4jDriver:
    def __init__(self):
        self.nodes = []
        self.edges = []
    
    def session(self):
        return self

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def run(self, query: str, parameters: Optional[Dict[str, Any]] = None):
        class Result:
            def data(self):
                return []
            def single(self):
                return {}
        return Result()

_cassandra_session = None
_neo4j_driver = None

def get_cassandra_session():
    global _cassandra_session
    if _cassandra_session is None:
        _cassandra_session = SimulatedCassandraSession()
    return _cassandra_session

def get_neo4j_driver():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = SimulatedNeo4jDriver()
    return _neo4j_driver
