#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for Chapter 18 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (Chapter 18: Comparative Capstone Lab)
# Use Case: Identifying False-Positives from Threat Intelligence Service
# ==============================================================================

set -e

ensure_mongodb() {
    # Check if MongoDB is reachable
    if ! mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}" --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        echo "================================================================================"
        echo "  [STARTUP] Starting local MongoDB 7.0 daemon (Replica Set 'rs0')..."
        echo "================================================================================"
        mkdir -p /data/db /workspace/logs
        mongod --replSet rs0 --bind_ip_all --logpath /workspace/logs/mongod.log --fork

        echo "  Waiting for MongoDB daemon to accept connections..."
        until mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do
            sleep 1
        done

        # Initiate replica set if needed
        mongosh --eval "try { rs.status() } catch(e) { rs.initiate({_id: 'rs0', members: [{_id: 0, host: '127.0.0.1:27017'}]}) }" --quiet >/dev/null 2>&1
        echo "  [OK] Local MongoDB 7.0 is active and replica set 'rs0' is ready."
        echo "================================================================================"
    fi
}

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "   CHAPTER 18: COMPARATIVE CAPSTONE - THREAT INTEL FALSE-POSITIVE SUITE         "
    echo "================================================================================"
    echo "  [1] Run Lab 18.1: Build Comparative System & 4-Query Benchmarking Suite       "
    echo "  [2] Run Activity 18.1: Graph-based Community Detection & False-Positive Scan  "
    echo "  [3] Run Lab 18.2: Generate Markdown Comparative Analysis Report               "
    echo "  [4] Run Master Demonstration (All Lab 18.1 & 18.2 Tasks in Sequence)          "
    echo "  [5] Run Unit & Integration Test Suite (test_lab18.py)                         "
    echo "  [6] Generate Publication-Grade Academic PDF Report (ReportLab)                "
    echo "  [7] Open Interactive Mongosh Shell                                            "
    echo "  [8] Open Interactive Bash Shell                                               "
    echo "  [0] Exit                                                                      "
    echo "================================================================================"
    echo -n "Select an option [0-8]: "
}

# Ensure MongoDB service is ready
ensure_mongodb

# If arguments are passed on command line, dispatch directly
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|lab18_1|benchmark|comparative)
            python3 /workspace/lab_01_threat_intel_system.py
            ;;
        2|activity|graph|community|fp)
            python3 -c "from lab_01_threat_intel_system import get_mongo_db, get_neo4j_driver, run_activity_18_1_detection; db = get_mongo_db('threat_intel_db'); neo = get_neo4j_driver(); run_activity_18_1_detection(db, neo)"
            ;;
        3|lab18_2|report|analysis)
            python3 /workspace/lab_02_comparative_report.py
            ;;
        4|demo|all|master)
            python3 /workspace/demo_all.py
            ;;
        5|test|tests|unit)
            python3 /workspace/test_lab18.py
            ;;
        6|pdf|generate_pdf)
            python3 /workspace/generate_report_pdf.py
            ;;
        7|mongosh)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        8|bash|sh)
            exec /bin/bash
            ;;
        *)
            exec "$@"
            ;;
    esac
    exit 0
fi

# Interactive menu loop
while true; do
    show_menu
    read -r choice
    echo ""
    case "$choice" in
        1)
            python3 /workspace/lab_01_threat_intel_system.py
            ;;
        2)
            python3 -c "from lab_01_threat_intel_system import get_mongo_db, get_neo4j_driver, run_activity_18_1_detection; db = get_mongo_db('threat_intel_db'); neo = get_neo4j_driver(); run_activity_18_1_detection(db, neo)"
            ;;
        3)
            python3 /workspace/lab_02_comparative_report.py
            ;;
        4)
            python3 /workspace/demo_all.py
            ;;
        5)
            python3 /workspace/test_lab18.py
            ;;
        6)
            python3 /workspace/generate_report_pdf.py
            ;;
        7)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        8)
            exec /bin/bash
            ;;
        0)
            echo "Exiting Chapter 18 Demonstration Suite. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid selection. Please choose an option from 0 to 8."
            ;;
    esac
    echo ""
    read -rp "Press [Enter] to return to menu..."
done
