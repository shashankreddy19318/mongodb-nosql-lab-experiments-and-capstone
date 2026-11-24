#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for MongoDB Lab 14 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (MongoDB 7.0)
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
    echo "       MONGODB LAB 14: PRODUCTION MONITORING, BACKUP & RESTORE VERIFICATION     "
    echo "================================================================================"
    echo "  [1] Run Lab 14.1: Operational Monitoring Dashboard (Metrics & Alerts)"
    echo "  [2] Run Activity 14.1: Webhook Alert Verification (Slack/Discord/REST)"
    echo "  [3] Run Lab 14.2: Automated Backup & Restore Verification Workflow"
    echo "  [4] Run Lab 14.2: Performance Benchmarking (1K, 10K, 100K docs) & RPO/RTO"
    echo "  [5] Run Lab 14.2: Negative Test (Tamper Detection Alert Verification)"
    echo "  [6] Run Full Master Demonstration (All Lab Tasks in Sequence)"
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
        1|monitor|dashboard)
            python3 /workspace/lab_01_monitoring_dashboard.py --iterations 1 --test-alert
            ;;
        2|webhook|activity1)
            python3 /workspace/test_webhook_alert.py
            ;;
        3|backup|restore)
            python3 /workspace/backup_verify.py --docs 1000
            ;;
        4|benchmark|rpo|rto)
            python3 /workspace/backup_verify.py --benchmark
            ;;
        5|corrupt|tamper|negative)
            python3 /workspace/backup_verify.py --corrupt-test || true
            ;;
        6|demo|all)
            python3 /workspace/demo_all.py
            ;;
        7|schedule)
            python3 /workspace/backup_verify.py --schedule
            ;;
        8|mongosh)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        9|bash|sh)
            exec /bin/bash
            ;;
        *)
            exec "$@"
            ;;
    esac
    exit 0
fi

# Interactive Loop
while true; do
    show_menu
    read -r opt
    echo ""
    case "$opt" in
        1)
            python3 /workspace/lab_01_monitoring_dashboard.py --iterations 1 --test-alert
            ;;
        2)
            python3 /workspace/test_webhook_alert.py
            ;;
        3)
            python3 /workspace/backup_verify.py --docs 1000
            ;;
        4)
            python3 /workspace/backup_verify.py --benchmark
            ;;
        5)
            python3 /workspace/backup_verify.py --corrupt-test || true
            ;;
        6)
            python3 /workspace/demo_all.py
            ;;
        7)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/?directConnection=true}"
            ;;
        8)
            exec /bin/bash
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo "Invalid option: $opt"
            ;;
    esac
    echo ""
    echo -n "Press Enter to return to menu..."
    read -r
done
