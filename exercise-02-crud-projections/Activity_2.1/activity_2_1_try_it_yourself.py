"""
Activity 2.1 - Try It Yourself
Extended environment verification: checks Python, PyMongo, Docker,
local MongoDB, Atlas MongoDB, and optional packages.
Prints a summary checklist of the environment readiness.
"""

import sys
import os
import json
import subprocess
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure


# ─── Configuration ───────────────────────────────────────────────
ATLAS_URI = os.getenv(
    "MONGO_URI_ATLAS",
    "mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
)
LOCAL_URI = os.getenv("MONGO_URI_LOCAL", "mongodb://localhost:27017")


def banner(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def check_python_version():
    """Check Python version."""
    ver = sys.version.split()[0]
    print(f"  Python Version : {ver}")
    major, minor = sys.version_info[:2]
    if major >= 3 and minor >= 10:
        print("  [OK] Python 3.10+ detected")
        return True
    else:
        print("  [WARN] Python 3.10+ recommended")
        return False


def check_pymongo():
    """Check if PyMongo is installed."""
    try:
        import pymongo
        print(f"  PyMongo Version: {pymongo.version}")
        return True
    except ImportError:
        print("  PyMongo        : NOT INSTALLED")
        print("  Fix: pip install pymongo")
        return False


def check_docker():
    """Check if Docker is installed and MongoDB container is running."""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            print(f"  Docker         : {result.stdout.strip()}")
            # Check for running MongoDB container
            ps = subprocess.run(
                ["docker", "ps", "--filter", "ancestor=mongo:7", "--format", "{{.Names}}"],
                capture_output=True, text=True, timeout=5
            )
            if ps.stdout.strip():
                print(f"  Mongo Container: Running ({ps.stdout.strip()})")
            else:
                print("  Mongo Container: NOT RUNNING")
                print("  Fix: docker run -d -p 27017:27017 --name mongo mongo:7")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  Docker         : NOT INSTALLED")
    return False


def check_mongo_local():
    """Check if local MongoDB is reachable."""
    try:
        client = MongoClient(LOCAL_URI, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
        info = client.server_info()
        print(f"  MongoDB Local  : v{info['version']} [OK]")

        # Print server details
        print(f"    Platform     : {info.get('platform', 'N/A')}")
        print(f"    JS Engine    : {info.get('javascriptEngine', 'N/A')}")
        print(f"    Allocator    : {info.get('allocator', 'N/A')}")
        return True
    except (ConnectionFailure, Exception):
        print("  MongoDB Local  : NOT RUNNING")
        print("  Fix: docker run -d -p 27017:27017 --name mongo mongo:7")
        return False


def check_mongo_atlas():
    """Check if Atlas MongoDB is reachable."""
    if "<username>" in ATLAS_URI or "<password>" in ATLAS_URI:
        print("  MongoDB Atlas  : NOT CONFIGURED")
        print("  Fix: Set MONGO_URI_ATLAS environment variable with your Atlas URI")
        return False
    try:
        client = MongoClient(ATLAS_URI, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        info = client.server_info()
        print(f"  MongoDB Atlas  : v{info['version']} [OK]")

        # Print server details
        print(f"    Modules      : {info.get('modules', 'N/A')}")
        print(f"    JS Engine    : {info.get('javascriptEngine', 'N/A')}")
        return True
    except Exception as e:
        print(f"  MongoDB Atlas  : FAILED ({e})")
        return False


def check_optional_packages():
    """Check optional packages for later chapters."""
    optional = ["fastapi", "streamlit", "neo4j", "cassandra", "rich", "dotenv"]
    print("\n  Optional Packages:")
    for pkg in optional:
        try:
            __import__(pkg)
            print(f"    {pkg:<16}: installed")
        except ImportError:
            print(f"    {pkg:<16}: not installed (optional)")


def save_results_to_json(results, filename="environment_check.json"):
    """Save environment check results to JSON."""
    data = {
        "environment_check": {
            "python_version": sys.version.split()[0],
            "checks": results,
            "total_passed": sum(1 for v in results.values() if v),
            "total_checks": len(results)
        }
    }
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
    print(f"\n  [OK] Results saved to {filename}")


def main():
    banner("Activity 2.1 - Try It Yourself: Environment Verification")

    results = {}

    print("\n--- Core Components ---")
    results["Python 3.10+"] = check_python_version()
    results["PyMongo"] = check_pymongo()
    results["Docker"] = check_docker()
    results["MongoDB Local"] = check_mongo_local()
    results["MongoDB Atlas"] = check_mongo_atlas()

    check_optional_packages()

    # Summary
    print(f"\n{'─'*60}")
    print("  SUMMARY")
    print(f"{'─'*60}")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    for name, status in results.items():
        icon = "✓" if status else "✗"
        print(f"  [{icon}] {name}")

    print(f"\n  Core checks passed: {passed}/{total}")
    if passed >= 3:
        print("  [OK] You are ready to start the labs!")
    else:
        print("  [WARN] Some required components are missing. See above for fixes.")

    save_results_to_json(results)

    banner("Activity 2.1 - Try It Yourself Complete")


if __name__ == "__main__":
    main()
