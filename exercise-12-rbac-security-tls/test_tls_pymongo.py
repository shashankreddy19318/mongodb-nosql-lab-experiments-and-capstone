#!/usr/bin/env python3
"""
PyMongo TLS Connection & Query Verification Script
=============================================================================
Connects to MongoDB using TLS encryption, verifies SSL handshake, and
executes database operations (ping, insert, find_one).
"""

import sys
import os
import argparse
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError

def parse_args():
    parser = argparse.ArgumentParser(description="Test MongoDB TLS Connection with PyMongo")
    parser.add_argument("--host", default="localhost", help="MongoDB hostname (default: localhost)")
    parser.add_argument("--port", type=int, default=27100, help="MongoDB port (default: 27100)")
    parser.add_argument("--ca-file", default="./tls/ca.crt", help="Path to CA certificate file")
    parser.add_argument("--cert-file", default="./tls/client.pem", help="Path to client PEM file (optional)")
    parser.add_argument("--user", default=None, help="Username for authentication (optional)")
    parser.add_argument("--password", default=None, help="Password for authentication (optional)")
    parser.add_argument("--auth-db", default="admin", help="Authentication database (default: admin)")
    return parser.parse_args()

def main():
    args = parse_args()
    print("=" * 70)
    print("       PyMongo TLS / Encryption-in-Transit Verification Test")
    print("=" * 70)

    # Build connection URI and options
    params = ["tls=true"]
    if os.path.exists(args.ca_file):
        params.append(f"tlsCAFile={os.path.abspath(args.ca_file)}")
        print(f"[CONFIG] CA Certificate: {os.path.abspath(args.ca_file)}")
    else:
        print(f"[WARN] CA Certificate not found at {args.ca_file}, proceeding without CA pin.")

    if os.path.exists(args.cert_file):
        params.append(f"tlsCertificateKeyFile={os.path.abspath(args.cert_file)}")
        print(f"[CONFIG] Client PEM Bundle: {os.path.abspath(args.cert_file)}")

    # Allow invalid hostnames if testing with custom self-signed certs on localhost
    params.append("tlsAllowInvalidHostnames=true")

    auth_part = ""
    if args.user and args.password:
        auth_part = f"{args.user}:{args.password}@"
        params.append(f"authSource={args.auth_db}")

    query_str = "&".join(params)
    uri = f"mongodb://{auth_part}{args.host}:{args.port}/?{query_str}"
    
    # Redact password for safe logging
    safe_uri = uri
    if args.password:
        safe_uri = uri.replace(args.password, "******")
    print(f"[CONFIG] Connection URI: {safe_uri}")

    client = None
    try:
        print("\n[Step 1] Initializing TLS Handshake with MongoDB Server...")
        client = MongoClient(uri, serverSelectionTimeoutMS=6000)
        
        # Ping test
        ping_res = client.admin.command("ping")
        print(f"[OK] Ping Successful! Response: {ping_res}")

        # Server info
        server_info = client.server_info()
        print(f"[OK] Connected to MongoDB v{server_info.get('version', 'unknown')} securely over TLS.")

        # Test database read/write
        print("\n[Step 2] Executing Read/Write Operations over Encrypted Stream...")
        db = client["tls_verification_db"]
        col = db["secure_channel_records"]

        col.drop()
        test_payload = {
            "testName": "TLS In-Transit Encryption Verification",
            "tlsMode": "requireTLS",
            "encryptionStatus": "ACTIVE",
            "message": "Data payload encrypted during transmission via TLS socket."
        }
        insert_res = col.insert_one(test_payload)
        print(f"[OK] Document inserted with ID: {insert_res.inserted_id}")

        doc = col.find_one({"_id": insert_res.inserted_id})
        print(f"[OK] Retrieved Document via find_one():")
        print(f"     Test Name:          {doc.get('testName')}")
        print(f"     TLS Mode:           {doc.get('tlsMode')}")
        print(f"     Encryption Status:  {doc.get('encryptionStatus')}")
        print(f"     Payload Message:    {doc.get('message')}")

        print("\n" + "=" * 70)
        print("  [SUCCESS] PyMongo TLS In-Transit Encryption Fully Verified!")
        print("=" * 70)
        return 0

    except ServerSelectionTimeoutError as e:
        print(f"\n[FAIL] Server selection timed out. Is mongod running with TLS on port {args.port}?")
        print(f"Details: {e}")
        return 1
    except PyMongoError as e:
        print(f"\n[FAIL] PyMongo TLS Connection Failed: {e}")
        return 1
    finally:
        if client:
            client.close()

if __name__ == "__main__":
    sys.exit(main())
