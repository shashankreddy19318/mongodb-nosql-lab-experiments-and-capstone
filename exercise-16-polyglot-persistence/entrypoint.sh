#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for Chapter 16 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (Chapter 16: Cassandra, Neo4j, MongoDB)
# ==============================================================================

set -e

ensure_mongodb() {
    # Check if MongoDB is reachable
    if ! mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}" --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        echo "================================================================================"
        echo "  [STARTUP] Starting local MongoDB 7.0 instance (Replica Set 'rs0')..."
        echo "================================================================================"
        mkdir -p /data/db /workspace/logs
        mongod --replSet rs0 --bind_ip_all --logpath /workspace/logs/mongod.log --fork

        echo "  Waiting for MongoDB daemon to accept connections..."
        until mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do
            sleep 1
        done

        # Initiate replica set if needed
        mongosh --eval "try { rs.status() } catch(e) { rs.initiate({_id: 'rs0', members: [{_id: 0, host: '127.0.0.1:27017'}]}) }" --quiet >/dev/null 2>&1
        echo "  [OK] Local MongoDB 7.0 is active and replica set 'rs0' is initiated."
        echo "================================================================================"
    fi
}

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "    CHAPTER 16: POLYGLOT PERSISTENCE (MONGODB, CASSANDRA, NEO4J) DEMONSTRATION  "
    echo "================================================================================"
    echo "  [1] Run Lab 16.1: Polyglot Data Modeling (University Course Enrollment)"
    echo "  [2] Run Activity 16.1: Hybrid University Architecture & Prerequisite DAG"
    echo "  [3] Run Lab 16.2: Hybrid Query Service (Fraud Detection & Routing)"
    echo "  [4] Run Lab 16.2: Latency Benchmarks (Mongo, Cassandra, Neo4j Profiling)"
    echo "  [5] Run Unit & Integration Tests (100% Mock & Circuit Breaker Tests)"
    echo "  [6] Run Full Master Demonstration (All Lab Tasks in Sequence)"
    echo "  [7] Generate Submission Report PDF (Publication-Grade Academic PDF)"
    echo "  [8] Open Interactive Mongosh Shell"
    echo "  [9] Open Interactive Bash Shell"
    echo "  [0] Exit"
    echo "================================================================================"
    echo -n "Select an option [0-9]: "
}

# Ensure MongoDB service is ready
ensure_mongodb

# If arguments are passed on command line, dispatch directly
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|modeling|lab16_1|course)
            python3 /workspace/lab_01_polyglot_modeling.py
            ;;
        2|activity|architecture|prereq)
            python3 -c "import lab_01_polyglot_modeling as l; l.display_activity_hybrid_architecture()"
            ;;
        3|service|hybrid|fraud)
            python3 /workspace/lab_02_hybrid_query_service.py
            ;;
        4|benchmark|latency|profile)
            python3 -c "from lab_02_hybrid_query_service import FraudQueryService; s = FraudQueryService(); import pprint; pprint.pprint(s.benchmark_latencies(iterations=30))"
            ;;
        5|test|tests|unit)
            python3 /workspace/test_fraud_service.py
            ;;
        6|demo|all)
            python3 /workspace/demo_all.py
            ;;
        7|pdf|report)
            python3 /workspace/generate_report_pdf.py
            ;;
        mongosh)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        bash|sh)
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
            python3 /workspace/lab_01_polyglot_modeling.py
            ;;
        2)
            python3 -c "import lab_01_polyglot_modeling as l; l.display_activity_hybrid_architecture()"
            ;;
        3)
            python3 /workspace/lab_02_hybrid_query_service.py
            ;;
        4)
            python3 -c "from lab_02_hybrid_query_service import FraudQueryService; s = FraudQueryService(); import pprint; pprint.pprint(s.benchmark_latencies(iterations=30))"
            ;;
        5)
            python3 /workspace/test_fraud_service.py
            ;;
        6)
            python3 /workspace/demo_all.py
            ;;
        7)
            python3 /workspace/generate_report_pdf.py
            ;;
        8)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        9)
            exec /bin/bash
            ;;
        0)
            echo "Exiting Chapter 16 Demonstration Environment. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option: $choice. Press Enter to retry..."
            ;;
    esac
    echo ""
    echo -n "Press [Enter] to return to menu..."
    read -r
done
