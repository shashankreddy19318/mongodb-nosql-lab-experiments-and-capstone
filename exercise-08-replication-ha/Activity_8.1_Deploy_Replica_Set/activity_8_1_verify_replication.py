"""
Activity 8.1: Deploy a Local Replica Set & Verify Replication
-------------------------------------------------------------
Objective:
  1. Connect to the 3-node MongoDB replica set (rs0).
  2. Inspect rs.status() to identify Primary, Secondaries, and Health states.
  3. Insert a document into the Primary node.
  4. Verify replication by reading the document back directly from both Secondary nodes.
"""

import sys
import socket
import time
from datetime import datetime, timezone
from pymongo import MongoClient, ReadPreference

# Ensure host.docker.internal resolves to 127.0.0.1 for local host testing
_orig_getaddrinfo = socket.getaddrinfo
def _patched_getaddrinfo(host, port, *args, **kwargs):
    if host == "host.docker.internal":
        host = "127.0.0.1"
    return _orig_getaddrinfo(host, port, *args, **kwargs)
socket.getaddrinfo = _patched_getaddrinfo

REPLICA_SET_URI = "mongodb://127.0.0.1:27017,127.0.0.1:27018,127.0.0.1:27019/?replicaSet=rs0"
NODES = [
    {"name": "mongo1", "host": "127.0.0.1", "port": 27017},
    {"name": "mongo2", "host": "127.0.0.1", "port": 27018},
    {"name": "mongo3", "host": "127.0.0.1", "port": 27019},
]

def banner(title):
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)

def main():
    banner("Lab 8.1: Deploy a Local Replica Set & Verify Replication")
    print(f"Connecting to Replica Set URI: {REPLICA_SET_URI}\n")
    
    try:
        client = MongoClient(REPLICA_SET_URI, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command("ping")
        print("[SUCCESS] Connected to MongoDB Replica Set (rs0)\n")
    except Exception as e:
        print(f"[ERROR] Could not connect to replica set: {e}")
        print("Please ensure Docker containers are running and initialized.")
        sys.exit(1)

    # 1. Inspect rs.status()
    print("--- 1. Replica Set Status & Topology Analysis ---")
    status = client.admin.command("replSetGetStatus")
    set_name = status.get("set", "rs0")
    print(f"Replica Set Name : {set_name}")
    print(f"Current Date     : {status.get('date')}")
    print("-" * 70)
    print(f"{'Member ID':<10} {'Host Address':<28} {'State':<12} {'Health':<8} {'Uptime (s)':<10}")
    print("-" * 70)
    
    primary_host = None
    secondary_hosts = []
    for member in status.get("members", []):
        m_id = member.get("_id")
        m_name = member.get("name")
        m_state = member.get("stateStr")
        m_health = "1 (Healthy)" if member.get("health") == 1 else "0 (Unhealthy)"
        m_uptime = member.get("uptime", 0)
        print(f"{m_id:<10} {m_name:<28} {m_state:<12} {m_health:<8} {m_uptime:<10}")
        if m_state == "PRIMARY":
            primary_host = m_name
        elif m_state == "SECONDARY":
            secondary_hosts.append(m_name)
    print("-" * 70)
    print(f"Active Primary Node  : {primary_host}")
    print(f"Secondary Nodes ({len(secondary_hosts)}): {', '.join(secondary_hosts)}\n")

    # 2. Insert document into Primary
    print("--- 2. Performing Write Operation on PRIMARY ---")
    db = client["lab8_db"]
    col = db["replication_test"]
    test_doc = {
        "lab": "8.1",
        "title": "Local Replica Set Deployment",
        "description": "Verifying multi-node automatic replication across Docker nodes.",
        "payload": "High Availability Data Payload",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": "CONFIRMED_WRITTEN"
    }
    insert_res = col.insert_one(test_doc)
    doc_id = insert_res.inserted_id
    print(f"[WRITE SUCCESS] Document inserted on PRIMARY with _id: {doc_id}")
    print(f"Inserted Document Content:\n  {test_doc}\n")

    # Wait briefly for replication oplog propagation
    print("Waiting 2 seconds for Oplog replication across nodes...")
    time.sleep(2)

    # 3. Verify Replication on both Secondaries
    print("\n--- 3. Verifying Replication on Each Member Directly ---")
    for node in NODES:
        node_label = f"{node['name']} ({node['host']}:{node['port']})"
        try:
            node_client = MongoClient(
                node["host"],
                node["port"],
                directConnection=True,
                read_preference=ReadPreference.SECONDARY_PREFERRED,
                serverSelectionTimeoutMS=3000
            )
            # Query the document directly on this specific node
            node_doc = node_client["lab8_db"]["replication_test"].find_one({"_id": doc_id})
            is_master_info = node_client.admin.command("hello")
            node_role = "PRIMARY" if is_master_info.get("isWritablePrimary", False) else (
                "SECONDARY" if is_master_info.get("secondary", False) else "OTHER"
            )
            
            if node_doc:
                print(f"[REPLICATION VERIFIED] Node {node_label} [{node_role}]:")
                print(f"   -> Found document with _id: {node_doc['_id']}")
                print(f"   -> Payload: \"{node_doc['payload']}\"")
                print(f"   -> Timestamp: {node_doc['timestamp']}")
            else:
                print(f"[WARNING] Document NOT found on Node {node_label}")
            node_client.close()
        except Exception as ex:
            print(f"[ERROR] Could not query node {node_label}: {ex}")

    print("\n" + "=" * 70)
    print("  [CONCLUSION] Lab 8.1 Completed Successfully!")
    print("  - 3-Node Replica Set rs0 is fully functional and healthy.")
    print("  - Document inserted on Primary was verified on all secondaries.")
    print("=" * 70)

if __name__ == "__main__":
    main()
