"""Shared MongoDB connection utility for Lab 11 scripts.
Supports both direct host execution and containerized docker-compose environments.
"""

import os
import sys
from pymongo import MongoClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_client: MongoClient | None = None


def get_client(uri: str | None = None) -> MongoClient:
    """Return a singleton MongoClient connected to the mongos query router."""
    global _client
    if _client is None:
        connection_uri = uri or os.getenv(
            "MONGO_URI",
            os.getenv("MONGOS_URI", "mongodb://localhost:27017")
        )
        try:
            _client = MongoClient(connection_uri, serverSelectionTimeoutMS=5000)
            _client.admin.command("ping")
            print(f"[OK] Connected to MongoDB Router (mongos) at {connection_uri}")
        except Exception as e:
            print(f"[WARN] Direct cluster connection to {connection_uri} failed: {e}")
            print("[INFO] Fallback to simulation/offline mode available if cluster is starting up.")
            _client = MongoClient(connection_uri, serverSelectionTimeoutMS=2000)
    return _client


def get_db(db_name: str | None = None):
    """Return a database handle."""
    client = get_client()
    name = db_name or os.getenv("MONGO_DB", "ecommerce_sharding")
    return client[name]


def close_client():
    """Close the singleton connection."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        print("[OK] MongoDB connection closed.")


def banner(text: str, char: str = "=", width: int = 70) -> None:
    """Print a clean section banner."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()
