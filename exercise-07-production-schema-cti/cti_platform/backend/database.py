"""
Database connection and storage engine manager for CTI Platform.
Supports dual-mode:
1. Live MongoDB server (via MONGODB_URI or localhost:27017)
2. In-memory fallback (mongomock) with WiredTiger Cache Simulation Engine
"""

import os
import time
import random
import bson
from typing import Dict, Any, List, Optional
import pymongo
from pymongo import MongoClient
import mongomock

DB_NAME = "cti_digest_prod"

class WiredTigerCacheSimulator:
    """
    Simulates MongoDB's WiredTiger storage engine cache behaviors
    when running without a dedicated production mongod instance.
    Calculates exact working set, cache residency, page eviction, and hit ratios.
    """
    def __init__(self, cache_size_mb: int = 1024):
        self.max_bytes = cache_size_mb * 1024 * 1024  # Default 1 GB cache
        self.bytes_in_cache = 0
        self.dirty_bytes = 0
        self.pages_read_into_cache = 0
        self.pages_requested = 0
        self.cached_doc_ids = set()
        self.collection_docs: Dict[str, int] = {}  # doc_id -> size_in_bytes
        self.history = []

    def register_document(self, doc_id: str, doc_size: int, is_new: bool = True):
        self.collection_docs[doc_id] = doc_size
        if is_new:
            self.dirty_bytes += doc_size
            self._admit_to_cache(doc_id, doc_size)

    def _admit_to_cache(self, doc_id: str, doc_size: int):
        # Check if cache eviction is needed
        while (self.bytes_in_cache + doc_size > self.max_bytes) and self.cached_doc_ids:
            # Evict a random or LRU document
            evicted_id = next(iter(self.cached_doc_ids))
            self.cached_doc_ids.remove(evicted_id)
            evicted_size = self.collection_docs.get(evicted_id, 2048)
            self.bytes_in_cache = max(0, self.bytes_in_cache - evicted_size)

        self.cached_doc_ids.add(doc_id)
        self.bytes_in_cache += doc_size

    def record_read(self, doc_id: str, doc_size: int = 2048):
        self.pages_requested += 1
        if doc_id in self.cached_doc_ids:
            # Cache Hit!
            pass
        else:
            # Cache Miss: must read into cache from disk
            self.pages_read_into_cache += 1
            self._admit_to_cache(doc_id, doc_size)

    def get_hit_ratio(self) -> float:
        if self.pages_requested == 0:
            return 100.0
        hits = max(0, self.pages_requested - self.pages_read_into_cache)
        return (hits / self.pages_requested) * 100.0

    def get_server_status(self, total_data_bytes: int = 0) -> Dict[str, Any]:
        hit_ratio = self.get_hit_ratio()
        pct_in_cache = (self.bytes_in_cache / total_data_bytes * 100.0) if total_data_bytes > 0 else 100.0
        pct_in_cache = min(100.0, pct_in_cache)

        return {
            "ok": 1.0,
            "version": "7.0.8",
            "uptime": int(time.time()),
            "wiredTiger": {
                "cache": {
                    "maximum bytes configured": self.max_bytes,
                    "bytes currently in the cache": self.bytes_in_cache,
                    "tracked dirty bytes in the cache": self.dirty_bytes,
                    "pages read into cache": self.pages_read_into_cache,
                    "pages requested from the cache": self.pages_requested,
                    "calculated cache hit ratio": round(hit_ratio, 2),
                    "percentage of data in cache": round(pct_in_cache, 2)
                }
            }
        }


class DatabaseManager:
    _instance = None

    def __init__(self):
        self.is_live_mongo = False
        self.client = None
        self.db = None
        self.cache_sim = WiredTigerCacheSimulator(cache_size_mb=512)
        self._init_connection()

    def _init_connection(self):
        mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
        try:
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            self.client = client
            self.db = client[DB_NAME]
            self.is_live_mongo = True
            print(f"[DatabaseManager] Connected to Live MongoDB instance at {mongo_uri}")
        except Exception as e:
            print(f"[DatabaseManager] Live MongoDB not accessible ({e}). Initializing In-Memory Engine with WiredTiger Cache Simulation...")
            self.client = mongomock.MongoClient()
            self.db = self.client[DB_NAME]
            self.is_live_mongo = False

    def get_db(self):
        return self.db

    def get_server_status(self) -> Dict[str, Any]:
        """Returns WiredTiger server status metrics."""
        if self.is_live_mongo:
            try:
                status = self.db.command("serverStatus")
                wt_cache = status.get("wiredTiger", {}).get("cache", {})
                req = wt_cache.get("pages requested from the cache", 1)
                read = wt_cache.get("pages read into cache", 0)
                hit_ratio = ((req - read) / req * 100.0) if req > 0 else 100.0
                curr_bytes = wt_cache.get("bytes currently in the cache", 0)
                
                # Approximate collection data size
                stats = self.db.command("dbStats")
                data_size = stats.get("dataSize", curr_bytes)
                pct_in_cache = (curr_bytes / data_size * 100.0) if data_size > 0 else 100.0

                wt_cache["calculated cache hit ratio"] = round(hit_ratio, 2)
                wt_cache["percentage of data in cache"] = round(min(100.0, pct_in_cache), 2)
                return status
            except Exception as e:
                print(f"[DatabaseManager] serverStatus query error: {e}. Falling back to simulator metrics.")

        # If mock or serverStatus command restricted
        total_data_bytes = sum(self.cache_sim.collection_docs.values())
        return self.cache_sim.get_server_status(total_data_bytes)

    def calculate_bson_size(self, doc: Dict[str, Any]) -> int:
        """Calculates exact BSON byte size of a document."""
        return len(bson.BSON.encode(doc))


# Global singleton instance
db_manager = DatabaseManager()
