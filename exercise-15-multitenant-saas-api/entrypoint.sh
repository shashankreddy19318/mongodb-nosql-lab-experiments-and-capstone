#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for Chapter 15 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (Chapter 15: Multi-Tenant SaaS & Data Migration)
# Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab15
# ==============================================================================

set -e

ensure_mongodb() {
    # Check if MongoDB is reachable
    if ! mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/saas_app?directConnection=true}" --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; then
        echo "================================================================================"
        echo "  [STARTUP] Starting local MongoDB 7.0 daemon..."
        echo "================================================================================"
        mkdir -p /data/db /workspace/logs
        mongod --bind_ip_all --logpath /workspace/logs/mongod.log --fork

        echo "  Waiting for MongoDB daemon to accept connections..."
        until mongosh --eval "db.adminCommand('ping')" --quiet >/dev/null 2>&1; do
            sleep 1
        done
        echo "  [OK] Local MongoDB 7.0 is active on port 27017."
        echo "================================================================================"
    fi
}

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "   CHAPTER 15: MULTI-TENANT SAAS ARCHITECTURE & DATA MIGRATION DEMONSTRATION    "
    echo "================================================================================"
    echo "  [1] Run Lab 15.1: Multi-Tenant REST API Demonstration (FastAPI + MongoDB)"
    echo "  [2] Run Activity 15.1: Role-Based Access Control (Admin vs Regular User)"
    echo "  [3] Run Lab 15.2: Tenant Isolation Migration (Document -> Collection-Per-Tenant)"
    echo "  [4] Run Lab 15.2: Performance Benchmark (Single-Tenant vs Cross-Tenant)"
    echo "  [5] Run Full Master Demonstration (All Lab Tasks in Sequence)"
    echo "  [6] Launch Live FastAPI Web Server (Port 8000 with Swagger UI at /docs)"
    echo "  [7] Generate Publication-Grade Academic PDF Report"
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
        1|api|lab15_1|lab1)
            python3 /workspace/lab_01_multitenant_api.py
            ;;
        2|activity|rbac)
            python3 -c "import demo_all; demo_all.run_full_demonstration()"
            ;;
        3|migration|lab15_2|lab2)
            python3 /workspace/lab_02_tenant_migration.py
            ;;
        4|benchmark|perf)
            python3 -c "import lab_02_tenant_migration as m; m.run_lab2_demo()"
            ;;
        5|demo|all|full|verify)
            python3 /workspace/demo_all.py
            ;;
        6|server|serve|web)
            echo "Starting FastAPI server on http://0.0.0.0:8000..."
            echo "Interactive API documentation available at: http://localhost:8000/docs"
            exec uvicorn lab_01_multitenant_api:app --host 0.0.0.0 --port 8000
            ;;
        7|pdf|report)
            python3 /workspace/generate_report_pdf.py
            ;;
        8|mongosh|mongo)
            exec mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/saas_app?directConnection=true}"
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

# Interactive Terminal Loop
while true; do
    show_menu
    read -r choice
    case "$choice" in
        1)
            echo ""
            python3 /workspace/lab_01_multitenant_api.py
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        2)
            echo ""
            python3 /workspace/lab_01_multitenant_api.py
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        3)
            echo ""
            python3 /workspace/lab_02_tenant_migration.py
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        4)
            echo ""
            python3 -c "import lab_02_tenant_migration as m; m.run_lab2_demo()"
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        5)
            echo ""
            python3 /workspace/demo_all.py
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        6)
            echo ""
            echo "Starting FastAPI server on http://0.0.0.0:8000 (Ctrl+C to stop)..."
            echo "Swagger UI Documentation: http://localhost:8000/docs"
            uvicorn lab_01_multitenant_api:app --host 0.0.0.0 --port 8000
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        7)
            echo ""
            python3 /workspace/generate_report_pdf.py
            echo ""
            read -p "Press [Enter] to return to the menu..."
            ;;
        8)
            mongosh "${MONGO_URI:-mongodb://127.0.0.1:27017/saas_app?directConnection=true}"
            ;;
        9)
            /bin/bash
            ;;
        0|exit|q|quit)
            echo "Exiting demonstration environment. Goodbye!"
            exit 0
            ;;
        *)
            echo "Invalid option. Please enter a number between 0 and 9."
            sleep 1
            ;;
    esac
done
