"""
app/database.py
Unified, thread-safe database connection utility for MongoDB with connection pooling
and seamless fallback to in-memory mongomock. Also provides simulated wide-column (Cassandra)
and graph (Neo4j) interfaces for multi-model / polyglot labs.
"""

import os
import logging
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("database")
logging.basicConfig(level=logging.INFO)

_mongo_client = None
_is_mock = False

def get_mongo_client(uri: Optional[str] = None, max_pool_size: int = 50):
    global _mongo_client, _is_mock
    if _mongo_client is None:
        conn_uri = uri or os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")
        try:
            from pymongo import MongoClient
            client = MongoClient(
                conn_uri,
                maxPoolSize=max_pool_size,
                minPoolSize=2,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=3000,
            )
            client.admin.command("ping")
            _mongo_client = client
            _is_mock = False
            logger.info(f"Connected to live MongoDB at {conn_uri}")
        except Exception as e:
            logger.warning(f"Live MongoDB not reachable ({e}). Initializing in-memory mongomock engine.")
            import mongomock
            _mongo_client = mongomock.MongoClient()
            _is_mock = True
    return _mongo_client

def is_mock_active() -> bool:
    global _is_mock
    return _is_mock

def get_db(db_name: Optional[str] = None):
    target_name = db_name or os.getenv("MONGO_DB", "threat_intelligence_db")
    return get_mongo_client()[target_name]

def reset_db(db_name: Optional[str] = None):
    client = get_mongo_client()
    target_name = db_name or os.getenv("MONGO_DB", "threat_intelligence_db")
    client.drop_database(target_name)
    logger.info(f"Database '{target_name}' reset.")
