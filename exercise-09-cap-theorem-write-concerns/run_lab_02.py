"""
Lab 9.2: Simulate Network Partition and Observe Replication & Failover
Simulates network partitions in a 3-node MongoDB replica set using Docker network commands:
1. Baseline test on healthy 3-node replica set.
2. Partition 1: Disconnect 1 secondary (mongo-rs0-2). Test w:1, w:majority, w:all.
3. Partition 2: Disconnect 2nd secondary (mongo-rs0-3), isolating primary (mongo-rs0-1).
   Observe primary step-down, majority loss, and write failures.
4. Recovery: Reconnect both secondaries, observe re-election and data catch-up.
5. Generate chronological timeline and findings report.
"""

import subprocess
import time
import datetime
from pymongo import MongoClient, WriteConcern
from pymongo.errors import PyMongoError, WriteConcernError, ServerSelectionTimeoutError, NotPrimaryError

NETWORK_NAME = "chapter-08_default"
PRIMARY_URI = "mongodb://localhost:27017/?directConnection=true"
SEC1_CONTAINER = "mongo-rs0-2"
SEC2_CONTAINER = "mongo-rs0-3"
PRIMARY_CONTAINER = "mongo-rs0-1"

timeline = []

def log_event(event_type, description, details=""):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = {"timestamp": ts, "type": event_type, "desc": description, "details": details}
    timeline.append(entry)
    print(f"[{ts}] [{event_type:<10}] {description} {f'({details})' if details else ''}")

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip(), res.stderr.strip(), res.returncode

def get_cluster_status(client):
    try:
        status = client.admin.command("replSetGetStatus")
        members = []
        for m in status.get("members", []):
            members.append({
                "name": m["name"],
                "state": m["stateStr"],
                "health": m["health"],
                "uptime": m.get("uptime", 0)
            })
        return members
    except Exception as e:
        return [{"name": "unknown", "state": f"Error: {e}", "health": 0}]

def test_write(client, w_val, j_val=False, timeout_ms=3000, label=""):
    try:
        db = client["partition_test_db"]
        wc = WriteConcern(w=w_val, j=j_val, wtimeout=timeout_ms)
        col = db["writes"].with_options(write_concern=wc)
        doc = {"ts": time.time(), "test": label, "w": str(w_val)}
        start = time.perf_counter()
        res = col.insert_one(doc)
        elapsed = (time.perf_counter() - start) * 1000
        return True, f"SUCCESS in {elapsed:.1f}ms (id={res.inserted_id})"
    except WriteConcernError as wce:
        return False, f"TIMEOUT / WriteConcernError: {wce.details.get('errmsg', str(wce))}"
    except NotPrimaryError:
        return False, "FAILED: NotWritablePrimary (node is not Primary)"
    except Exception as e:
        return False, f"ERROR: {type(e).__name__} - {e}"

def main():
    print("=" * 80)
    print("      LAB 9.2: NETWORK PARTITION & CAP THEOREM SIMULATION")
    print("=" * 80)
    
    # Setup client
    client = MongoClient(PRIMARY_URI, serverSelectionTimeoutMS=4000, socketTimeoutMS=4000)
    
    # 0. Initial Status
    log_event("STATE", "Checking initial 3-node replica set status")
    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']}: {m['state']} (Health={m['health']})")

    # Baseline writes
    log_event("TEST", "Running baseline writes before partition")
    ok1, msg1 = test_write(client, 1, label="baseline_w1")
    log_event("WRITE_W1", f"w:1 write: {msg1}")
    okmaj, msgmaj = test_write(client, "majority", label="baseline_wmaj")
    log_event("WRITE_WMAJ", f"w:majority write: {msgmaj}")
    okall, msgall = test_write(client, 3, label="baseline_wall")
    log_event("WRITE_WALL", f"w:all (w:3) write: {msgall}")

    # =========================================================================
    # PHASE 1: Disconnect Secondary 1 (mongo-rs0-2)
    # =========================================================================
    print("\n" + "-" * 80)
    print("PHASE 1: Disconnect Secondary 1 (mongo-rs0-2) - Majority Intact (2 of 3)")
    print("-" * 80)
    log_event("ACTION", f"Disconnecting {SEC1_CONTAINER} from network {NETWORK_NAME}")
    run_cmd(f"docker network disconnect {NETWORK_NAME} {SEC1_CONTAINER}")
    
    # Wait for heartbeat failure detection
    print("Waiting 5s for replica set to detect node isolation...")
    time.sleep(5)
    
    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']}: {m['state']} (Health={m['health']})")
    
    # Test writes with 1 secondary down
    log_event("TEST", "Testing w:1 write with 1 secondary partitioned")
    ok1, msg1 = test_write(client, 1, label="p1_w1")
    log_event("WRITE_W1", f"Outcome: {msg1}")
    
    log_event("TEST", "Testing w:majority write with 1 secondary partitioned")
    okmaj, msgmaj = test_write(client, "majority", label="p1_wmaj")
    log_event("WRITE_WMAJ", f"Outcome: {msgmaj}")
    
    log_event("TEST", "Testing w:all (w:3, timeout=3000ms) with 1 secondary partitioned")
    okall, msgall = test_write(client, 3, timeout_ms=3000, label="p1_wall")
    log_event("WRITE_WALL", f"Outcome: {msgall}")

    # =========================================================================
    # PHASE 2: Disconnect Secondary 2 (mongo-rs0-3) - Primary Isolated (1 of 3)
    # =========================================================================
    print("\n" + "-" * 80)
    print("PHASE 2: Disconnect Secondary 2 (mongo-rs0-3) - Primary Isolated (Loss of Majority)")
    print("-" * 80)
    log_event("ACTION", f"Disconnecting {SEC2_CONTAINER} from network {NETWORK_NAME}")
    run_cmd(f"docker network disconnect {NETWORK_NAME} {SEC2_CONTAINER}")

    # Monitor for primary step-down
    print("Observing replica set state as primary realizes majority is lost...")
    stepped_down = False
    stepdown_time = None
    for i in range(15):
        members = get_cluster_status(client)
        p_state = next((m['state'] for m in members if "mongo-rs0-1" in m['name']), "UNKNOWN")
        if p_state == "SECONDARY" and not stepped_down:
            stepped_down = True
            stepdown_time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
            log_event("STEP_DOWN", f"*** PRIMARY mongo-rs0-1 has STEPPED DOWN to SECONDARY ***", f"At {stepdown_time}")
            break
        elif p_state == "PRIMARY":
            print(f"  [{i+1}s] Primary still active, waiting for election timeout...")
        time.sleep(1)

    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']}: {m['state']} (Health={m['health']})")

    # Test writes in isolated state
    log_event("TEST", "Attempting w:majority write while isolated (timeout=3000ms)")
    okmaj, msgmaj = test_write(client, "majority", timeout_ms=3000, label="p2_wmaj")
    log_event("WRITE_WMAJ", f"Outcome: {msgmaj}")

    log_event("TEST", "Attempting w:1 write while isolated")
    ok1, msg1 = test_write(client, 1, timeout_ms=3000, label="p2_w1")
    log_event("WRITE_W1", f"Outcome: {msg1}")

    print("\nMaintaining partition for 15s to observe read-only cluster stability...")
    time.sleep(15)

    # =========================================================================
    # PHASE 3: Reconnect Network & Observe Recovery
    # =========================================================================
    print("\n" + "-" * 80)
    print("PHASE 3: Reconnecting Secondaries & Observing Failover/Re-election & Catch-up")
    print("-" * 80)
    log_event("ACTION", f"Reconnecting {SEC1_CONTAINER} to network {NETWORK_NAME}")
    run_cmd(f"docker network connect {NETWORK_NAME} {SEC1_CONTAINER}")
    log_event("ACTION", f"Reconnecting {SEC2_CONTAINER} to network {NETWORK_NAME}")
    run_cmd(f"docker network connect {NETWORK_NAME} {SEC2_CONTAINER}")

    print("Waiting for quorum re-establishment, election, and sync...")
    elected_primary = None
    for i in range(25):
        members = get_cluster_status(client)
        curr_primary = next((m['name'] for m in members if m['state'] == "PRIMARY"), None)
        if curr_primary and not elected_primary:
            elected_primary = curr_primary
            log_event("ELECTION", f"*** Primary ELECTED: {curr_primary} ***", f"Took ~{i+1}s")
        all_healthy = all(m['health'] == 1.0 for m in members) and len(members) == 3
        if elected_primary and all_healthy and any(m['state'] == 'PRIMARY' for m in members):
            log_event("STABLE", "All 3 nodes are reconnected, healthy, and quorum restored!")
            break
        time.sleep(1)

    members = get_cluster_status(client)
    for m in members:
        log_event("MEMBER", f"{m['name']}: {m['state']} (Health={m['health']})")

    # Verify replication after recovery
    log_event("TEST", "Testing w:majority write on recovered cluster")
    ok_rec, msg_rec = test_write(client, "majority", label="post_recovery_wmaj")
    log_event("WRITE_RECOV", f"Outcome: {msg_rec}")

    # =========================================================================
    # TIMELINE SUMMARY
    # =========================================================================
    print("\n" + "=" * 80)
    print("                   CHRONOLOGICAL TIMELINE OF EVENTS")
    print("=" * 80)
    print(f"{'Timestamp':<14} | {'Event Type':<12} | {'Description':<50}")
    print("-" * 80)
    for e in timeline:
        details_str = f" [{e['details']}]" if e['details'] else ""
        print(f"{e['timestamp']:<14} | {e['type']:<12} | {e['desc'][:48]:<48}{details_str}")
    print("=" * 80)

    client.close()
    print("\n[OK] Lab 9.2 partition simulation completed successfully.")

if __name__ == "__main__":
    main()
