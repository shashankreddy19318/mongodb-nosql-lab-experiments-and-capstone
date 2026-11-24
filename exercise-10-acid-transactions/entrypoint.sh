#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for MongoDB Lab 10 Demonstration Suite
# Author: chintan
# Course: Distributed NoSQL Databases (MongoDB 7.0)
# ==============================================================================

set -e

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "       MONGODB LAB 10: MULTI-DOCUMENT TRANSACTIONS & CONCURRENCY                "
    echo "================================================================================"
    echo "  [1] Run Lab 10.1: Bank Transfer Transaction (ACID, Rollback & Retry)"
    echo "  [2] Run Lab 10.2: Inventory Reservation (Contention, Retry & Benchmarks)"
    echo "  [3] Run Full Master Demonstration (Lab 10.1 + Lab 10.2 Complete Suite)"
    echo "  [4] Run Lab 10.2 Concurrency Stress Test Only (8 Threads vs 5 Items)"
    echo "  [5] Run Throughput Benchmark (1, 4, 8, 16 Worker Threads)"
    echo "  [6] Open Interactive Mongosh Shell"
    echo "  [7] Open Interactive Bash Shell"
    echo "  [0] Exit"
    echo "================================================================================"
    echo -n "Select an option [0-7]: "
}

# If arguments provided on command line, evaluate directly
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|lab1|transfer)
            python3 /app/lab_01_bank_transfer.py
            ;;
        2|lab2|inventory)
            python3 /app/lab_02_inventory_reservation.py
            ;;
        3|all|demo)
            python3 /app/demo_all.py
            ;;
        4|concurrency)
            python3 -c "import lab_02_inventory_reservation as l2; client = l2.get_client(); l2.run_concurrency_test(client, False); l2.run_concurrency_test(client, True)"
            ;;
        5|throughput)
            python3 -c "import lab_02_inventory_reservation as l2; client = l2.get_client(); l2.run_throughput_benchmark(client)"
            ;;
        6|mongosh)
            mongosh "${MONGO_URI:-mongodb://mongo-rs0-1:27017,mongo-rs0-2:27018,mongo-rs0-3:27019/?replicaSet=rs0}"
            ;;
        7|bash|sh)
            exec /bin/bash
            ;;
        *)
            exec "$@"
            ;;
    esac
    exit 0
fi

# Otherwise interactive loop
while true; do
    show_menu
    read -r choice
    echo ""
    case "$choice" in
        1) python3 /app/lab_01_bank_transfer.py ;;
        2) python3 /app/lab_02_inventory_reservation.py ;;
        3) python3 /app/demo_all.py ;;
        4) python3 -c "import lab_02_inventory_reservation as l2; client = l2.get_client(); l2.run_concurrency_test(client, False); l2.run_concurrency_test(client, True)" ;;
        5) python3 -c "import lab_02_inventory_reservation as l2; client = l2.get_client(); l2.run_throughput_benchmark(client)" ;;
        6) mongosh "${MONGO_URI:-mongodb://mongo-rs0-1:27017,mongo-rs0-2:27018,mongo-rs0-3:27019/?replicaSet=rs0}" ;;
        7) exec /bin/bash ;;
        0|exit|q) echo "Exiting demonstration."; exit 0 ;;
        *) echo "Invalid choice: $choice" ;;
    esac
    echo ""
    echo "Press Enter to return to menu..."
    read -r _
done
