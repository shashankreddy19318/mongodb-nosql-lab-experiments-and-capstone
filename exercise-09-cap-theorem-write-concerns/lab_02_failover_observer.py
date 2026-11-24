"""
================================================================================
Lab 8.2 / 9.2: Failover & Topology Observer
Chapter 09 - NoSQL Databases (MongoDB)
================================================================================
Monitors replica set topology every second, printing primary transitions,
node reachability changes, and partition states in real time.
================================================================================
"""

import os
import sys
import time
import datetime
from pymongo import MongoClient

RS_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/?directConnection=true")


def get_members(client):
    try:
        status = client.admin.command("replSetGetStatus")
        return status.get("members", [])
    except Exception as e:
        return []


def run_observer(duration_sec=60, poll_interval=1.0):
    print("=" * 75)
    print("           REPLICA SET TOPOLOGY & FAILOVER OBSERVER")
    print("=" * 75)
    print(f"Connecting to: {RS_URI}")
    print(f"Polling every {poll_interval}s for {duration_sec}s...")
    print("-" * 75)

    client = MongoClient(RS_URI, serverSelectionTimeoutMS=2000, socketTimeoutMS=2000)
    last_primary = None
    last_unhealthy = set()

    start_time = time.time()
    while time.time() - start_time < duration_sec:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        members = get_members(client)
        if not members:
            print(f"[{ts}] [WARN] Cannot query replSetGetStatus (primary may be down)")
            time.sleep(poll_interval)
            continue

        curr_primary = None
        curr_unhealthy = set()
        for m in members:
            if m["stateStr"] == "PRIMARY":
                curr_primary = m["name"]
            if m["health"] == 0:
                curr_unhealthy.add(m["name"])

        # Detect Primary transition
        if curr_primary != last_primary:
            if last_primary is None and curr_primary:
                print(f"[{ts}] [LEADER] Initial PRIMARY detected: {curr_primary}")
            elif curr_primary is None:
                print(f"[{ts}] [STEP_DOWN] *** PRIMARY LOST! (Former: {last_primary}) - Cluster in READ-ONLY mode ***")
            else:
                print(f"[{ts}] [FAILOVER] *** FAILOVER DETECTED: {last_primary} -> {curr_primary} ***")
            last_primary = curr_primary

        # Detect node isolation / recovery
        newly_isolated = curr_unhealthy - last_unhealthy
        newly_recovered = last_unhealthy - curr_unhealthy
        for n in newly_isolated:
            print(f"[{ts}] [ISOLATED] Node {n} became UNREACHABLE (health=0)")
        for n in newly_recovered:
            print(f"[{ts}] [RECOVERED] Node {n} REJOINED and healthy (health=1)")
        last_unhealthy = curr_unhealthy

        time.sleep(poll_interval)

    client.close()
    print("-" * 75)
    print(f"Observer stopped. Final Primary: {last_primary}")


if __name__ == "__main__":
    dur = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    run_observer(duration_sec=dur)
