#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for Chapter 17 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (Chapter 17: AI-Native MongoDB & Vector Search)
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
    echo "    CHAPTER 17: AI-NATIVE MONGODB & VECTOR SEARCH DEMONSTRATION SUITE           "
    echo "================================================================================"
    echo "  [1] Run Lab 17.1: Build a Simple RAG Pipeline (Threat Intelligence Corpus)"
    echo "  [2] Run Activity 17.1: Multi-Turn Conversation Memory in MongoDB"
    echo "  [3] Run Lab 17.2: Compare HNSW and IVF Vector Search Index Optimization"
    echo "  [4] Run Full Master Demonstration (All Lab 17.1 & 17.2 Tasks in Sequence)"
    echo "  [5] Run Unit & Integration Test Suite (test_lab17.py)"
    echo "  [6] Generate Academic PDF Report (ReportLab Publication-Grade PDF)"
    echo "  [7] Open Interactive Mongosh Shell"
    echo "  [8] Open Interactive Bash Shell"
    echo "  [0] Exit"
    echo "================================================================================"
    echo -n "Select an option [0-8]: "
}

# Ensure MongoDB service is ready
ensure_mongodb

# If arguments are passed on command line, dispatch directly
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|rag|lab17_1|pipeline)
            python3 /workspace/lab_01_rag_pipeline.py
            ;;
        2|activity|memory|conversation)
            python3 -c "from lab_01_rag_pipeline import ThreatIntelRAGPipeline; rag = ThreatIntelRAGPipeline(); print(rag.chat('analyst_01', 'Explain the differences between tactical and strategic threat intelligence.'))"
            ;;
        3|benchmark|lab17_2|hnsw_vs_ivf|ann)
            python3 /workspace/lab_02_hnsw_vs_ivf.py
            ;;
        4|demo|all|master)
            python3 /workspace/demo_all.py
            ;;
        5|test|tests|unit)
            python3 /workspace/test_lab17.py
            ;;
        6|pdf|report)
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
            python3 /workspace/lab_01_rag_pipeline.py
            ;;
        2)
            python3 -c "from lab_01_rag_pipeline import ThreatIntelRAGPipeline; rag = ThreatIntelRAGPipeline(); print(rag.chat('analyst_01', 'Explain the differences between tactical and strategic threat intelligence.'))"
            ;;
        3)
            python3 /workspace/lab_02_hnsw_vs_ivf.py
            ;;
        4)
            python3 /workspace/demo_all.py
            ;;
        5)
            python3 /workspace/test_lab17.py
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
            echo "Exiting Chapter 17 Demonstration Environment. Goodbye!"
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
