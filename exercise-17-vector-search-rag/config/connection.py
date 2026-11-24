"""
config/connection.py
Shared MongoDB connection utility for Chapter 17:
AI-Native MongoDB - Vector Search and RAG Foundations.

Supports:
- Singleton connection pooling to MongoDB (local or Atlas)
- Automatic replica set / standalone detection
- Graceful transparent fallback to mongomock when no active MongoDB server is reachable
- Diagnostic helpers (banner, reset_collection, print_json)
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

_client = None
_using_mock = False


def banner(text: str, char: str = "=", width: int = 70) -> None:
    """Print an eye-catching section banner."""
    print()
    print(char * width)
    print(f"  {text}")
    print(char * width)
    print()


def get_client(uri: str | None = None):
    """
    Return a singleton MongoClient.
    Tries connecting to the provided uri or MONGO_URI env var.
    Falls back to mongomock.MongoClient if no MongoDB daemon is reachable.
    """
    global _client, _using_mock
    if _client is not None:
        return _client

    connection_uri = uri or os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")

    try:
        from pymongo import MongoClient
        client = MongoClient(connection_uri, serverSelectionTimeoutMS=2000)
        # Verify connection
        client.admin.command("ping")
        _client = client
        _using_mock = False
        print(f"[OK] Connected to MongoDB at {connection_uri}")
        return _client
    except Exception as e:
        if 'client' in locals() and client is not None:
            try:
                client.close()
            except Exception:
                pass
        print(f"[WARN] Live MongoDB not reachable at {connection_uri}: {e}")
        print("[INFO] Initializing high-fidelity in-memory mongomock client for offline demonstration...")
        try:
            import mongomock
            _client = mongomock.MongoClient()
            _using_mock = True
            print("[OK] In-memory mongomock initialized successfully.")
            return _client
        except ImportError:
            raise RuntimeError("Neither live MongoDB nor mongomock is available. Please install mongomock or start mongod.")


def is_mock_active() -> bool:
    """Return whether the current client is a mock client."""
    global _using_mock
    return _using_mock


def get_db(db_name: str | None = None):
    """Return database handle."""
    client = get_client()
    name = db_name or os.getenv("MONGO_DB", "nosql_labs")
    return client[name]


def close_client():
    """Close singleton client connection."""
    global _client, _using_mock
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
        _client = None
        _using_mock = False
        print("[OK] MongoDB connection closed.")


def reset_collection(db_name: str, collection_name: str):
    """Drop and return a clean collection."""
    db = get_db(db_name)
    if collection_name in db.list_collection_names():
        db.drop_collection(collection_name)
        print(f"[OK] Dropped collection: {db_name}.{collection_name}")
    return db[collection_name]


def print_json(data) -> None:
    """Pretty-print a document or list of documents."""
    import json
    from bson import json_util
    print(json.dumps(data, indent=2, default=json_util.default))
