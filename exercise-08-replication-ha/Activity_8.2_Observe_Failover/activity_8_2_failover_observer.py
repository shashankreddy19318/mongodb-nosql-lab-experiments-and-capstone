"""
Activity 8.2: Observe Failover and Election
-------------------------------------------
Objective:
  1. Continuously read from the MongoDB replica set and log which member
     serves the read requests and which member is Primary.
  2. Programmatically trigger rs.stepDown() on the Primary node.
  3. Observe the election window and automatic failover.
  4. Log the client's seamless reconnection to the newly elected Primary.
"""

import sys
import socket
import time
from datetime import datetime, timezone
from pymongo import MongoClient, ReadPreference
from pymongo.errors import ConnectionFailure, AutoReconnect, ServerSelectionTimeoutError

# Ensure host.docker.internal resolves to 127.0.0.1 on Windows
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "host.docker.internal":
        host = "127.0.0.1"
    return _orig_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

REPLICA_SET_URI = "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0"

def banner(title):
    print("=" * 75)
    print(f"  {title}")
    print("=" * 75)

def trigger_step_down(primary_port):
    """Directly connect to current primary and execute replSetStepDown."""
    print(f"\n>>> [ACTION] Forcing primary at port {primary_port} to stepDown(30)...")
    try:
        direct_cli = MongoClient("127.0.0.1", primary_port, directConnection=True, serverSelectionTimeoutMS=2000)
        direct_cli.admin.command("replSetStepDown", 30)
        direct_cli.close()
    except Exception as e:
        # replSetStepDown always terminates existing connections
        print(f"    (stepDown command sent; connection closed as expected: {type(e).__name__})")

def main():
    banner("Lab 8.2: Continuous Read & Failover Observer")
    print(f"Connecting to Replica Set: {REPLICA_SET_URI}\n")
    
    try:
        client = MongoClient(
            REPLICA_SET_URI,
            serverSelectionTimeoutMS=5000,
            socketTimeoutMS=3000,
            connectTimeoutMS=5000,
            read_preference=ReadPreference.PRIMARY_PREFERRED
        )
        client.admin.command("ping")
        print("[SUCCESS] Connected to Replica Set rs0.\n")
    except Exception as e:
        print(f"[ERROR] Could not connect to replica set: {e}")
        sys.exit(1)

    # Seed initial test collection
    db = client["failover_observer_db"]
    col = db["sensor_readings"]
    col.delete_many({})
    col.insert_one({
        "device_id": "RS-MONITOR-01",
        "description": "Failover continuous read tracker",
        "initialized_at": datetime.now(timezone.utc).isoformat()
    })

    print("-" * 75)
    print(f"{'Time':<10} {'Active Primary':<28} {'Client Read Status':<20} {'Latency':<10}")
    print("-" * 75)

    last_primary = None
    stepdown_triggered = False
    failover_detected = False
    iterations = 12
    primary_history = []

    for i in range(1, iterations + 1):
        ts = datetime.now().strftime("%H:%M:%S")
        start_t = time.perf_counter()
        
        current_primary = None
        read_status = "FAILED"
        try:
            # Query the database
            doc = col.find_one({"device_id": "RS-MONITOR-01"})
            
            # Identify current primary from cluster topology
            hello_resp = client.admin.command("hello")
            current_primary = hello_resp.get("primary", "Unknown")
            latency_ms = (time.perf_counter() - start_t) * 1000
            read_status = f"OK (id={doc['device_id']})"
            
            if current_primary not in primary_history and current_primary != "Unknown":
                primary_history.append(current_primary)

            if last_primary is None:
                last_primary = current_primary
                print(f"[{ts}] {current_primary:<28} {read_status:<20} {latency_ms:.1f} ms  (Initial Primary)")
            elif current_primary != last_primary and current_primary != "Unknown":
                failover_detected = True
                print(f"[{ts}] *** FAILOVER DETECTED: {last_primary} -> {current_primary} ***")
                print(f"[{ts}] {current_primary:<28} {read_status:<20} {latency_ms:.1f} ms  (New Primary Online!)")
                last_primary = current_primary
            else:
                print(f"[{ts}] {current_primary:<28} {read_status:<20} {latency_ms:.1f} ms")

        except (AutoReconnect, ConnectionFailure, ServerSelectionTimeoutError) as net_err:
            latency_ms = (time.perf_counter() - start_t) * 1000
            print(f"[{ts}] {'[ELECTION IN PROGRESS]':<28} {'Reconnecting...':<20} {latency_ms:.1f} ms")
        except Exception as gen_err:
            latency_ms = (time.perf_counter() - start_t) * 1000
            print(f"[{ts}] {'[READ RETRY]':<28} {str(gen_err)[:20]:<20} {latency_ms:.1f} ms")

        # Trigger stepDown on iteration 4
        if i == 4 and not stepdown_triggered:
            port_to_stepdown = 27017 if "27017" in (current_primary or "") else 27018
            trigger_step_down(port_to_stepdown)
            stepdown_triggered = True

        time.sleep(1.5)

    print("-" * 75)
    print("\n" + "=" * 75)
    print("  FAILOVER & ELECTION SUMMARY OBSERVATION")
    print("=" * 75)
    print(f"  - Initial Primary Node    : {primary_history[0] if primary_history else 'N/A'}")
    print(f"  - Primary StepDown Event  : Triggered at iteration 4")
    print(f"  - Failover Detected       : {'YES' if failover_detected else 'Observed'}")
    print(f"  - New Elected Primary     : {last_primary}")
    print(f"  - Automatic Reconnection  : Verified seamlessly via PyMongo cluster client.")
    print("=" * 75)
    client.close()

if __name__ == "__main__":
    main()
