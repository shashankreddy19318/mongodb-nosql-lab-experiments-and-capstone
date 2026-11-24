#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for MongoDB Lab 09 Demonstration
# ==============================================================================

set -e

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "       MONGODB LAB 09: CAP THEOREM & WRITE CONCERN DEMONSTRATION SUITE          "
    echo "================================================================================"
    echo "  [1] Run Lab 9.1: Write Concern Latency Benchmark (w:1, w:majority, w:all)"
    echo "  [2] Run Lab 9.2: Network Partition & Failover Simulation"
    echo "  [3] Run Full Master Demonstration (Lab 9.1 + Lab 9.2 Complete)"
    echo "  [4] Run Failover Observer (Real-time Topology Monitor)"
    echo "  [5] Open Interactive Mongosh Shell"
    echo "  [6] Open Interactive Bash Shell"
    echo "  [0] Exit"
    echo "================================================================================"
    echo -n "Select an option [0-6]: "
}

# If arguments provided on command line, evaluate
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|lab1)
            python3 /app/lab_01_write_concern_latency.py
            ;;
        2|lab2)
            python3 /app/lab_02_simulate_partition.py
            ;;
        3|all|demo)
            python3 /app/demo_all.py
            ;;
        4|observer)
            python3 /app/lab_02_failover_observer.py 60
            ;;
        5|mongosh)
            mongosh "${MONGO_URI:-mongodb://mongo-rs0-1:27017/?replicaSet=rs0}"
            ;;
        6|bash|sh)
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
        1) python3 /app/lab_01_write_concern_latency.py ;;
        2) python3 /app/lab_02_simulate_partition.py ;;
        3) python3 /app/demo_all.py ;;
        4) python3 /app/lab_02_failover_observer.py 60 ;;
        5) mongosh "${MONGO_URI:-mongodb://mongo-rs0-1:27017/?replicaSet=rs0}" ;;
        6) exec /bin/bash ;;
        0|exit|q) echo "Exiting."; exit 0 ;;
        *) echo "Invalid choice: $choice" ;;
    esac
    echo ""
    echo "Press Enter to return to menu..."
    read -r _
done
