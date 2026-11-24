"""
================================================================================
Lab 9.2: Simulate a Network Partition & Observe Consistency vs Availability
Chapter 09 - NoSQL Databases (MongoDB)
================================================================================
Objective:
  Simulate network partitions in a 3-node replica set using Docker commands:
  - Phase 1: Partition 1 secondary (mongo-rs0-2). Quorum remains intact (2 of 3).
             Evaluate writes under w:1, w:majority, and w:all.
  - Phase 2: Partition 2nd secondary (mongo-rs0-3). Primary (mongo-rs0-1) is isolated.
             Observe primary step-down, election timeout, and write rejections.
  - Phase 3: Reconnect partitioned secondaries.
             Observe heartbeat re-establishment, leader election, and oplog catch-up.
  - Outputs chronological timeline of events and comprehensive analysis.
================================================================================
"""

import os
import sys
import time
import datetime
import subprocess
from pymongo import MongoClient, WriteConcern
from pymongo.errors import WriteConcernError, NotPrimaryError, ServerSelectionTimeoutError

NETWORK_NAME = os.getenv("DOCKER_NETWORK", "chapter-08_default")
PRIMARY_HOST = os.getenv("PRIMARY_HOST", "localhost")
PRIMARY_PORT = int(os.getenv("PRIMARY_PORT", "27017"))
SEC1_CONTAINER = os.getenv("SEC1_CONTAINER", "mongo-rs0-2")
SEC2_CONTAINER = os.getenv("SEC2_CONTAINER", "mongo-rs0-3")
PRIMARY_CONTAINER = os.getenv("PRIMARY_CONTAINER", "mongo-rs0-1")

PRIMARY_URI = f"mongodb://{PRIMARY_HOST}:{PRIMARY_PORT}/?directConnection=true"

timeline = []


def log_event(event_type, description, details=""):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {
        "timestamp": ts,
        "type": event_type,
        "desc": description,
        "details": details
    }
    timeline.append(entry)
    detail_str = f" ({details})" if details else ""
    print(f"[{ts}] [{event_type:<12}] {description}{detail_str}")


def run_docker_cmd(cmd):
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return res.returncode == 0, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def get_cluster_status(client):
    try:
        status = client.admin.command("replSetGetStatus")
        return [
            {
                "name": m["name"],
                "state": m["stateStr"],
                "health": m["health"],
                "uptime": m.get("uptime", 0)
            }
            for m in status.get("members", [])
        ]
    except Exception as e:
        return [{"name": "primary_node", "state": f"ERROR: {e}", "health": 0}]


def test_write(client, w_val, j_val=False, timeout_ms=3000, label=""):
    try:
        db = client["partition_lab_db"]
        wc = WriteConcern(w=w_val, j=j_val, wtimeout=timeout_ms)
        col = db["partition_writes"].with_options(write_concern=wc)
        doc = {
            "test_label": label,
            "w": str(w_val),
            "j": j_val,
            "timestamp": time.time(),
            "iso_time": datetime.datetime.now().isoformat()
        }
        t0 = time.perf_counter()
        res = col.insert_one(doc)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return True, f"SUCCESS in {elapsed_ms:.1f}ms (id={res.inserted_id})"
    except WriteConcernError as wce:
        err_msg = wce.details.get("errmsg", str(wce)) if hasattr(wce, "details") else str(wce)
        return False, f"TIMEOUT / WriteConcernError: {err_msg}"
    except NotPrimaryError:
        return False, "REJECTED: NotWritablePrimary (Cluster in Read-Only mode / No Primary)"
    except Exception as e:
        return False, f"FAILED: {type(e).__name__} - {e}"


def main():
    print("=" * 82)
    print("       LAB 9.2: NETWORK PARTITION SIMULATION & FAULT TOLERANCE")
    print("=" * 82)
    print(f"Docker Network:      {NETWORK_NAME}")
    print(f"Primary Target:      {PRIMARY_URI}")
    print(f"Partition Targets:   {SEC1_CONTAINER}, {SEC2_CONTAINER}")
    print("-" * 82)

    client = MongoClient(PRIMARY_URI, serverSelectionTimeoutMS=4000, socketTimeoutMS=4000)

    # 1. Baseline Health Check
    log_event("STATE", "Checking initial replica set status before partition")
    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']} -> {m['state']} (Health={m['health']})")

    # Baseline writes
    log_event("TEST", "Running baseline writes (Cluster healthy)")
    ok1, msg1 = test_write(client, 1, label="baseline_w1")
    log_event("WRITE_W1", f"Baseline w:1: {msg1}")

    okmaj, msgmaj = test_write(client, "majority", label="baseline_wmaj")
    log_event("WRITE_WMAJ", f"Baseline w:majority: {msgmaj}")

    okall, msgall = test_write(client, 3, label="baseline_wall")
    log_event("WRITE_WALL", f"Baseline w:all (w:3): {msgall}")

    # =========================================================================
    # PHASE 1: Isolate Secondary 1 (mongo-rs0-2)
    # =========================================================================
    print("\n" + "-" * 82)
    print("PHASE 1: Disconnecting Secondary 1 (mongo-rs0-2) -> Majority Intact (2 of 3 nodes)")
    print("-" * 82)
    log_event("ACTION", f"Executing: docker network disconnect {NETWORK_NAME} {SEC1_CONTAINER}")
    ok, out, err = run_docker_cmd(f"docker network disconnect {NETWORK_NAME} {SEC1_CONTAINER}")
    if not ok:
        print(f"  [!] Note on disconnect: {err or out}")

    print("Waiting 6s for cluster heartbeats to detect disconnected secondary...")
    time.sleep(6)

    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']} -> {m['state']} (Health={m['health']})")

    # Writes during Phase 1
    log_event("TEST", "Testing w:1 write with 1 secondary isolated")
    ok1, msg1 = test_write(client, 1, label="phase1_w1")
    log_event("WRITE_W1", f"Outcome: {msg1}")

    log_event("TEST", "Testing w:majority write with 1 secondary isolated")
    okmaj, msgmaj = test_write(client, "majority", label="phase1_wmaj")
    log_event("WRITE_WMAJ", f"Outcome: {msgmaj}")

    log_event("TEST", "Testing w:all (w:3, timeout=3000ms) with 1 secondary isolated")
    okall, msgall = test_write(client, 3, timeout_ms=3000, label="phase1_wall")
    log_event("WRITE_WALL", f"Outcome: {msgall}")

    # =========================================================================
    # PHASE 2: Isolate Secondary 2 (mongo-rs0-3) -> Primary Lost Majority
    # =========================================================================
    print("\n" + "-" * 82)
    print("PHASE 2: Disconnecting Secondary 2 (mongo-rs0-3) -> Primary Isolated (1 of 3 nodes)")
    print("-" * 82)
    log_event("ACTION", f"Executing: docker network disconnect {NETWORK_NAME} {SEC2_CONTAINER}")
    ok, out, err = run_docker_cmd(f"docker network disconnect {NETWORK_NAME} {SEC2_CONTAINER}")
    if not ok:
        print(f"  [!] Note on disconnect: {err or out}")

    print("Monitoring primary node for automatic step-down (electionTimeout = 10s)...")
    stepped_down = False
    for elapsed_sec in range(15):
        members = get_cluster_status(client)
        primary_member = next((m for m in members if "mongo-rs0-1" in m["name"]), None)
        if primary_member and primary_member["state"] == "SECONDARY":
            stepped_down = True
            log_event("STEP_DOWN", "*** PRIMARY mongo-rs0-1 HAS STEPPED DOWN TO SECONDARY ***", f"After {elapsed_sec+1}s")
            break
        elif primary_member and primary_member["state"] == "PRIMARY":
            print(f"  [t+{elapsed_sec+1}s] Primary still heartbeat-polling unreachable secondaries...")
        time.sleep(1)

    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']} -> {m['state']} (Health={m['health']})")

    # Writes during isolated phase
    log_event("TEST", "Attempting w:majority write on isolated node (timeout=3000ms)")
    okmaj, msgmaj = test_write(client, "majority", timeout_ms=3000, label="phase2_wmaj")
    log_event("WRITE_WMAJ", f"Outcome: {msgmaj}")

    log_event("TEST", "Attempting w:1 write on isolated node")
    ok1, msg1 = test_write(client, 1, timeout_ms=3000, label="phase2_w1")
    log_event("WRITE_W1", f"Outcome: {msg1}")

    print("\nHolding partition for 12 seconds to observe stable read-only state...")
    time.sleep(12)

    # =========================================================================
    # PHASE 3: Reconnect Network & Observe Healing & Catch-Up
    # =========================================================================
    print("\n" + "-" * 82)
    print("PHASE 3: Reconnecting Secondaries -> Quorum Restored & Cluster Healed")
    print("-" * 82)
    log_event("ACTION", f"Executing: docker network connect {NETWORK_NAME} {SEC1_CONTAINER}")
    run_docker_cmd(f"docker network connect {NETWORK_NAME} {SEC1_CONTAINER}")
    log_event("ACTION", f"Executing: docker network connect {NETWORK_NAME} {SEC2_CONTAINER}")
    run_docker_cmd(f"docker network connect {NETWORK_NAME} {SEC2_CONTAINER}")

    print("Observing leader election, heartbeat restoration, and oplog catch-up...")
    restored = False
    for sec in range(25):
        members = get_cluster_status(client)
        all_healthy = all(m.get("health", 0) == 1.0 for m in members) and len(members) == 3
        has_primary = any(m.get("state") == "PRIMARY" for m in members)
        if all_healthy and has_primary and not restored:
            restored = True
            elected = next(m["name"] for m in members if m["state"] == "PRIMARY")
            log_event("ELECTION", f"*** Leader Election Complete: PRIMARY is {elected} ***", f"Took ~{sec+1}s")
            log_event("HEALED", "All 3 replica set members are online, healthy, and synchronized!")
            break
        time.sleep(1)

    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']} -> {m['state']} (Health={m['health']})")

    # Final write on recovered cluster
    log_event("TEST", "Testing write concern on recovered cluster")
    # If mongo-rs0-1 is primary, write directly; else write to elected primary
    current_primary = next((m["name"] for m in members if m["state"] == "PRIMARY"), None)
    if current_primary and "mongo-rs0-1" in current_primary:
        ok_rec, msg_rec = test_write(client, "majority", label="phase3_recovered")
        log_event("WRITE_RECOV", f"w:majority write to restored Primary: {msg_rec}")
    else:
        log_event("INFO", f"Current primary is {current_primary}. Direct write to mongo-rs0-1 routes to secondary.")

    # Chronological Summary Table
    print("\n" + "=" * 82)
    print("                   CHRONOLOGICAL TIMELINE OF PARTITION EVENTS")
    print("=" * 82)
    print(f"{'Timestamp':<14} | {'Event Type':<14} | {'Description':<48}")
    print("-" * 82)
    for e in timeline:
        d = f" [{e['details']}]" if e['details'] else ""
        print(f"{e['timestamp']:<14} | {e['type']:<14} | {e['desc'][:46]:<46}{d}")
    print("=" * 82)

    client.close()
    print("\n[OK] Lab 9.2 completed successfully.")


if __name__ == "__main__":
    main()
