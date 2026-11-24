"""
Activity 8.2 (Try It Yourself): Priority Configuration & Election Prediction
----------------------------------------------------------------------------
Objective:
  1. Inspect the replica set configuration (rs.conf()).
  2. Configure different priority weights across cluster members:
     - Node 1 (port 27017): Priority = 1 (Low)
     - Node 2 (port 27018): Priority = 10 (High Priority Candidate)
     - Node 3 (port 27019): Priority = 0 (Arbiter) / 3 (Secondary)
  3. Formulate and display an election outcome prediction prior to failover.
  4. Force the active primary to step down via replSetStepDown.
  5. Observe the election and compare the resulting Primary against the prediction.
"""

import sys
import socket
import time
from pymongo import MongoClient, ReadPreference
from pymongo.errors import AutoReconnect, ConnectionFailure, ServerSelectionTimeoutError

# Socket patch for Windows host resolution
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

def main():
    banner("Lab 8.2 (Try It Yourself): Priority Configuration & Election Prediction")
    print(f"Connecting to Replica Set: {REPLICA_SET_URI}\n")
    
    try:
        client = MongoClient(REPLICA_SET_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("[SUCCESS] Connected to MongoDB Replica Set (rs0)\n")
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    # 1. Fetch current config & update priorities if needed
    print("--- 1. Configuring Member Priorities (rs.reconfig) ---")
    conf = client.admin.command("replSetGetConfig")["config"]
    
    # Configure priorities: 27017 -> 1, 27018 -> 10, 27019 -> 0 (arbiter) or 3
    conf["version"] += 1
    for m in conf["members"]:
        if "27017" in m["host"]:
            m["priority"] = 1
        elif "27018" in m["host"]:
            m["priority"] = 10
        elif "27019" in m["host"] and not m.get("arbiterOnly", False):
            m["priority"] = 3
            
    try:
        client.admin.command("replSetReconfig", conf)
        print("[SUCCESS] New priorities applied via replSetReconfig.\n")
    except Exception as e:
        print(f"[INFO] replSetReconfig notice: {e}\n")

    # Read verified priorities
    time.sleep(2)
    verified_conf = client.admin.command("replSetGetConfig")["config"]
    verified_status = client.admin.command("replSetGetStatus")
    
    print("-" * 75)
    print(f"{'Member Host':<32} {'Configured Priority':<22} {'Current Role':<15}")
    print("-" * 75)
    
    current_primary = None
    predicted_winner = None
    highest_secondary_prio = -1
    
    for m in verified_conf["members"]:
        host = m["host"]
        prio = m.get("priority", 1)
        # Find matching status
        st_member = next((sm for sm in verified_status["members"] if sm["name"] == host), None)
        role = st_member["stateStr"] if st_member else "UNKNOWN"
        print(f"{host:<32} {prio:<22} {role:<15}")
        
        if role == "PRIMARY":
            current_primary = host
        elif role == "SECONDARY":
            if prio > highest_secondary_prio:
                highest_secondary_prio = prio
                predicted_winner = host

    print("-" * 75)
    print(f"Current Active Primary : {current_primary}")
    print(f"Eligible Secondaries   : {[m['name'] for m in verified_status['members'] if m['stateStr'] == 'SECONDARY']}")
    
    # 2. State the Prediction
    print("\n" + "=" * 75)
    print("  ELECTION PREDICTION")
    print("=" * 75)
    print(f"  Theoretical Rule : MongoDB replica set election algorithm strongly favors")
    print(f"                     the eligible data member with the highest priority.")
    print(f"  Target Candidate : {predicted_winner} (Priority: {highest_secondary_prio})")
    print(f"  Prediction       : When Primary ({current_primary}) steps down,")
    print(f"                     >> {predicted_winner} << WILL BE ELECTED PRIMARY.")
    print("=" * 75 + "\n")

    # 3. Trigger stepDown on current Primary
    primary_port = 27017 if "27017" in current_primary else 27018
    print(f">>> [TRIGGER] Forcing Primary ({current_primary}) to step down for 30s...")
    try:
        direct_cli = MongoClient("127.0.0.1", primary_port, directConnection=True, serverSelectionTimeoutMS=2000)
        direct_cli.admin.command("replSetStepDown", 30)
        direct_cli.close()
    except Exception as e:
        print(f"    (stepDown executed; connection closed: {type(e).__name__})")

    # 4. Observe election
    print("\nMonitoring election progress across replica set...")
    election_settled = False
    new_primary = None
    
    for attempt in range(1, 15):
        time.sleep(1)
        try:
            status_now = client.admin.command("replSetGetStatus")
            primary_entry = next((sm for sm in status_now["members"] if sm["stateStr"] == "PRIMARY"), None)
            if primary_entry:
                new_primary = primary_entry["name"]
                if new_primary != current_primary:
                    election_settled = True
                    print(f"  [T+{attempt}s] Election concluded! New Primary detected: {new_primary}")
                    break
                else:
                    print(f"  [T+{attempt}s] Node {new_primary} still reports primary...")
            else:
                print(f"  [T+{attempt}s] Quorum voting in progress (No primary elected yet)...")
        except Exception:
            print(f"  [T+{attempt}s] Polling heartbeat...")

    # 5. Verification Result
    print("\n" + "=" * 75)
    print("  VERIFICATION RESULT")
    print("=" * 75)
    print(f"  - Initial Primary Node     : {current_primary}")
    print(f"  - Predicted Winner Node    : {predicted_winner} (Priority {highest_secondary_prio})")
    print(f"  - Actual Elected Primary   : {new_primary}")
    
    if new_primary == predicted_winner:
        print("\n  >>> VERIFICATION: [SUCCESS] PREDICTION 100% VERIFIED! <<<")
        print(f"      Node {new_primary} was elected as predicted due to having the")
        print(f"      highest priority value ({highest_secondary_prio}) among available secondaries.")
    else:
        print(f"\n  >>> VERIFICATION: Elected primary was {new_primary}.")
    print("=" * 75)
    client.close()

if __name__ == "__main__":
    main()
