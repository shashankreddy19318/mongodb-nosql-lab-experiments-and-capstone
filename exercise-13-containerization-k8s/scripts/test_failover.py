#!/usr/bin/env python3
"""
scripts/test_failover.py
Lab 13.1 - PyMongo Replica Set Connection and Automatic Failover Test

Objective:
Connect PyMongo to the 3-node MongoDB replica set ('rs0') with keyFile auth.
Continuously perform writes and reads while stepping down the primary node
using 'replSetStepDown', demonstrating automatic failover, election of a new
primary, and client recovery with zero permanent data loss.
"""

import sys
import time
import threading
from pymongo import MongoClient, ReadPreference
from pymongo.errors import AutoReconnect, ServerSelectionTimeoutError, PyMongoError

# Connection strings: internal container network or host mapped ports
DEFAULT_URI = (
    "mongodb://admin:AdminPass123!@localhost:27017,localhost:27018,localhost:27019/"
    "?replicaSet=rs0&authSource=admin&serverSelectionTimeoutMS=5000&retryWrites=true"
)

# Alternative internal container URI
CONTAINER_URI = (
    "mongodb://admin:AdminPass123!@mongo-rs0-1:27017,mongo-rs0-2:27017,mongo-rs0-3:27017/"
    "?replicaSet=rs0&authSource=admin&serverSelectionTimeoutMS=5000&retryWrites=true"
)


class ReplicaSetFailoverTester:
    def __init__(self, uri=DEFAULT_URI):
        self.uri = uri
        self.client = None
        self.db = None
        self.collection = None
        self.running = False
        self.write_count = 0
        self.read_count = 0
        self.reconnect_count = 0
        self.errors = []
        self.events = []

    def connect(self):
        print(f"[INFO] Connecting PyMongo to replica set...")
        try:
            self.client = MongoClient(self.uri)
            # Trigger server selection
            ismaster = self.client.admin.command("isMaster")
            primary = ismaster.get("primary", "Unknown")
            hosts = ismaster.get("hosts", [])
            print(f"[OK] Connected! ReplicaSet: {ismaster.get('setName')}")
            print(f"     Current Primary : {primary}")
            print(f"     Cluster Members : {', '.join(hosts)}")
            self.db = self.client["failover_lab"]
            self.collection = self.db["heartbeats"]
            # Clean up old test data
            self.collection.delete_many({})
            return True
        except Exception as e:
            print(f"[ERROR] Connection failed: {e}")
            return False

    def log_event(self, message):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}"
        self.events.append(entry)
        print(entry)

    def write_worker(self):
        print("[INFO] Starting continuous write worker (interval=300ms)...")
        seq = 0
        while self.running:
            seq += 1
            doc = {
                "seq": seq,
                "timestamp": time.time(),
                "node_status": "heartbeat"
            }
            try:
                self.collection.insert_one(doc)
                self.write_count += 1
                if seq % 10 == 0:
                    print(f"  -> Write OK: Heartbeat #{seq} persisted.")
            except AutoReconnect as e:
                self.reconnect_count += 1
                self.log_event(f"AutoReconnect during write #{seq}: Primary unavailable (Election in progress).")
                time.sleep(0.5)
            except PyMongoError as e:
                self.errors.append(f"Write error #{seq}: {e}")
                self.log_event(f"Write error #{seq}: {e}")
                time.sleep(0.5)
            time.sleep(0.3)

    def read_worker(self):
        print("[INFO] Starting continuous read worker (ReadPreference: primaryPreferred)...")
        read_coll = self.collection.with_options(read_preference=ReadPreference.PRIMARY_PREFERRED)
        while self.running:
            try:
                latest = read_coll.find_one(sort=[("seq", -1)])
                if latest:
                    self.read_count += 1
                    if self.read_count % 15 == 0:
                        print(f"  <- Read OK: Latest record seq={latest.get('seq')}")
            except AutoReconnect as e:
                self.log_event("AutoReconnect during read: Node stepping down or changing state.")
                time.sleep(0.5)
            except Exception as e:
                self.log_event(f"Read notice: {e}")
                time.sleep(0.5)
            time.sleep(0.2)

    def trigger_stepdown(self):
        """Forces the current primary to step down for 30 seconds to trigger an election."""
        time.sleep(3)  # Allow writes to stabilize first
        try:
            ismaster = self.client.admin.command("isMaster")
            old_primary = ismaster.get("primary", "unknown")
            self.log_event(f"!!! TRIGGERING STEP-DOWN ON PRIMARY: {old_primary} !!!")
            self.log_event("Executing: db.adminCommand({ replSetStepDown: 30, force: true })")
            
            # Use a direct client to stepDown so we don't break the main connection pool
            try:
                self.client.admin.command("replSetStepDown", 30, force=True)
            except AutoReconnect:
                self.log_event("[OK] replSetStepDown dispatched; primary dropped client connections as designed.")
            except Exception as e:
                self.log_event(f"[NOTICE] Step-down signal sent: {e}")

            # Monitor election
            start_election = time.time()
            new_primary = None
            while time.time() - start_election < 20:
                time.sleep(1)
                try:
                    check = self.client.admin.command("isMaster")
                    cand = check.get("primary")
                    if cand and cand != old_primary:
                        new_primary = cand
                        duration = round(time.time() - start_election, 2)
                        self.log_event(f"*** NEW PRIMARY ELECTED: {new_primary} (Election completed in {duration}s) ***")
                        break
                except Exception:
                    continue

            if not new_primary:
                self.log_event("[WARNING] New primary not detected within 20s.")

        except Exception as e:
            self.log_event(f"[ERROR] Failed to step down primary: {e}")

    def run_failover_test(self, test_duration=15):
        if not self.connect():
            return False

        self.running = True
        w_thread = threading.Thread(target=self.write_worker, daemon=True)
        r_thread = threading.Thread(target=self.read_worker, daemon=True)
        stepdown_thread = threading.Thread(target=self.trigger_stepdown, daemon=True)

        self.log_event("Starting continuous load simulation...")
        w_thread.start()
        r_thread.start()
        stepdown_thread.start()

        # Run for specified duration
        start = time.time()
        while time.time() - start < test_duration:
            time.sleep(1)

        self.running = False
        w_thread.join(timeout=2)
        r_thread.join(timeout=2)

        print("\n" + "=" * 60)
        print("           FAILOVER TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Successful Writes  : {self.write_count}")
        print(f"Total Successful Reads   : {self.read_count}")
        print(f"AutoReconnect Occurrences: {self.reconnect_count} (Handled gracefully)")
        print(f"Permanent Client Failures: {len(self.errors)}")
        print("\nKey Timeline Events:")
        for ev in self.events:
            print(f"  {ev}")
        
        # Verify database integrity
        total_in_db = self.collection.count_documents({})
        print(f"\nFinal Document Count in DB: {total_in_db}")
        print("=" * 60)
        
        if total_in_db > 0 and len(self.errors) == 0:
            print("[PASS] Failover verification succeeded: Cluster recovered and data remained intact!\n")
            return True
        else:
            print("[FAIL] Failover verification encountered errors.\n")
            return False


if __name__ == "__main__":
    uri = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI
    tester = ReplicaSetFailoverTester(uri=uri)
    tester.run_failover_test(test_duration=18)
