"""
Activity 2.1 - Environment Setup Verification
Connects to both Atlas and Docker MongoDB simultaneously
and compares their server version information using server_info().
"""

import sys
import os
import json
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# ─── Configuration ───────────────────────────────────────────────
# Replace <YOUR_ATLAS_URI> with your actual MongoDB Atlas connection string
ATLAS_URI = os.getenv(
    "MONGO_URI_ATLAS",
    "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
)
DOCKER_URI = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017")


def connect_and_get_info(uri, label):
    """Connect to a MongoDB instance and return its server_info()."""
    print(f"\n{'='*60}")
    print(f"  Connecting to {label}")
    print(f"  URI: {uri[:50]}...")
    print(f"{'='*60}")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print(f"  [OK] Connection to {label} successful!")
        info = client.server_info()
        return info, client
    except ConnectionFailure as e:
        print(f"  [ERROR] Could not connect to {label}: {e}")
        return None, None


def compare_server_info(atlas_info, docker_info):
    """Compare and display server version information from both instances."""
    print(f"\n{'='*60}")
    print("  SERVER VERSION COMPARISON")
    print(f"{'='*60}")

    fields_to_compare = [
        ("version", "MongoDB Version"),
        ("gitVersion", "Git Version"),
        ("modules", "Modules"),
        ("allocator", "Memory Allocator"),
        ("javascriptEngine", "JavaScript Engine"),
        ("sysInfo", "System Info"),
        ("storageEngines", "Storage Engines"),
        ("ok", "Status"),
    ]

    print(f"\n  {'Field':<25} {'Atlas':<30} {'Docker (Local)':<30}")
    print(f"  {'-'*25} {'-'*30} {'-'*30}")

    for field, display_name in fields_to_compare:
        atlas_val = atlas_info.get(field, "N/A")
        docker_val = docker_info.get(field, "N/A")
        # Truncate long values for display
        atlas_str = str(atlas_val)[:28]
        docker_str = str(docker_val)[:28]
        match_indicator = " ✓" if atlas_val == docker_val else " ✗"
        print(f"  {display_name:<25} {atlas_str:<30} {docker_str:<30}{match_indicator}")

    # Detailed version breakdown
    print(f"\n  --- Detailed Version Info ---")
    atlas_ver = atlas_info.get("version", "unknown")
    docker_ver = docker_info.get("version", "unknown")
    print(f"  Atlas  MongoDB Version : {atlas_ver}")
    print(f"  Docker MongoDB Version : {docker_ver}")
    if atlas_ver == docker_ver:
        print("  [MATCH] Both instances are running the same MongoDB version.")
    else:
        print("  [DIFFER] The MongoDB versions are different.")

    # Build info comparison
    print(f"\n  --- Build Info ---")
    print(f"  Atlas  Build Environment: {atlas_info.get('buildEnvironment', {}).get('cc', 'N/A')}")
    print(f"  Docker Build Environment: {docker_info.get('buildEnvironment', {}).get('cc', 'N/A')}")


def save_server_info_to_json(atlas_info, docker_info, filename="server_info_comparison.json"):
    """Save the server info comparison to a JSON file."""
    # Remove non-serializable fields
    def clean_info(info):
        cleaned = {}
        for k, v in info.items():
            try:
                json.dumps(v)
                cleaned[k] = v
            except (TypeError, ValueError):
                cleaned[k] = str(v)
        return cleaned

    data = {
        "comparison": {
            "atlas_server_info": clean_info(atlas_info),
            "docker_server_info": clean_info(docker_info),
            "version_match": atlas_info.get("version") == docker_info.get("version")
        }
    }

    with open(filename, "w", indent=2) as f:
        json.dump(data, f, indent=2, default=str)
    print(f"\n  [OK] Server info saved to {filename}")


def main():
    print("=" * 60)
    print("  Activity 2.1: Atlas vs Docker MongoDB Comparison")
    print("  Comparing server_info() from both instances")
    print("=" * 60)

    # Check Python version
    print(f"\n  Python Version: {sys.version.split()[0]}")
    try:
        import pymongo
        print(f"  PyMongo Version: {pymongo.version}")
    except ImportError:
        print("  [ERROR] PyMongo is not installed. Run: pip install pymongo")
        sys.exit(1)

    # Connect to Atlas
    atlas_info, atlas_client = connect_and_get_info(ATLAS_URI, "MongoDB Atlas")

    # Connect to Docker (Local)
    docker_info, docker_client = connect_and_get_info(DOCKER_URI, "MongoDB Docker (Local)")

    # Compare if both connections succeeded
    if atlas_info and docker_info:
        compare_server_info(atlas_info, docker_info)
        save_server_info_to_json(atlas_info, docker_info)
        print("\n  [OK] Both Atlas and Docker MongoDB are running simultaneously!")
    elif atlas_info:
        print("\n  [WARN] Only Atlas is reachable. Start Docker MongoDB:")
        print("         docker run -d -p 27017:27017 --name mongo mongo:7")
    elif docker_info:
        print("\n  [WARN] Only Docker is reachable. Set MONGO_URI_ATLAS in environment.")
    else:
        print("\n  [ERROR] Neither Atlas nor Docker MongoDB could be reached.")

    # List databases from each connected instance
    for client, label in [(atlas_client, "Atlas"), (docker_client, "Docker")]:
        if client:
            print(f"\n  Databases on {label}:")
            for db_name in client.list_database_names():
                print(f"    - {db_name}")

    print(f"\n{'='*60}")
    print("  Activity 2.1 Complete")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
