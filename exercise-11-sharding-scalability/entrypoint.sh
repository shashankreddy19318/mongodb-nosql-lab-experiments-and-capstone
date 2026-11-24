#!/usr/bin/env bash
# ==============================================================================
# Container Entrypoint for MongoDB Lab 11 Demonstration Suite
# Author: Chintan
# Course: Distributed NoSQL Databases (MongoDB 7.0)
# ==============================================================================

set -e

show_menu() {
    clear 2>/dev/null || true
    echo "================================================================================"
    echo "          MONGODB LAB 11: SHARDING & HORIZONTAL SCALABILITY                     "
    echo "================================================================================"
    echo "  [1] Run Lab 11.1: Shard Key Evaluation & Decision Matrix"
    echo "  [2] Run Activity 11.1: MongoDB 5.0+ Resharding Research (Steps & Limitations)"
    echo "  [3] Run Lab 11.2: Shard Key Hotspot Detection (10,000 Documents & collStats)"
    echo "  [4] Run Full Master Demonstration (Lab 11.1 + Lab 11.2 Complete Suite)"
    echo "  [5] Run Query explain() Routing Analysis (Targeted vs Scatter-Gather)"
    echo "  [6] Inspect Shard Statistics (collStats on hotspot_data & even_data)"
    echo "  [7] Open Interactive Mongosh Shell (Router port :27017)"
    echo "  [8] Open Interactive Bash Shell"
    echo "  [0] Exit"
    echo "================================================================================"
    echo -n "Select an option [0-8]: "
}

# If arguments provided on command line, dispatch directly
if [ "$#" -gt 0 ]; then
    case "$1" in
        1|lab1|eval)
            python3 /app/lab_01_shard_key_eval.py
            ;;
        2|resharding|activity1)
            python3 -c "import lab_01_shard_key_eval as l1; l1.display_resharding_research()"
            ;;
        3|lab2|hotspot)
            python3 /app/lab_02_shard_key_hotspot.py
            ;;
        4|demo|all)
            python3 /app/demo_all.py
            ;;
        5|explain|routing)
            python3 -c "import lab_02_shard_key_hotspot as l2; l2.run_explain_comparison(l2.get_client())"
            ;;
        6|stats|collstats)
            python3 -c "import lab_02_shard_key_hotspot as l2; client = l2.get_client(); l2.inspect_collection_stats(client, 'hotspot_data'); l2.inspect_collection_stats(client, 'even_data')"
            ;;
        7|mongosh)
            mongosh "${MONGO_URI:-mongodb://mongos-router:27017}"
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

# Otherwise present interactive menu
while true; do
    show_menu
    read -r choice
    echo ""
    case "$choice" in
        1) python3 /app/lab_01_shard_key_eval.py ;;
        2) python3 -c "import lab_01_shard_key_eval as l1; l1.display_resharding_research()" ;;
        3) python3 /app/lab_02_shard_key_hotspot.py ;;
        4) python3 /app/demo_all.py ;;
        5) python3 -c "import lab_02_shard_key_hotspot as l2; l2.run_explain_comparison(l2.get_client())" ;;
        6) python3 -c "import lab_02_shard_key_hotspot as l2; client = l2.get_client(); l2.inspect_collection_stats(client, 'hotspot_data'); l2.inspect_collection_stats(client, 'even_data')" ;;
        7) mongosh "${MONGO_URI:-mongodb://mongos-router:27017}" ;;
        8) exec /bin/bash ;;
        0|exit|q) echo "Exiting demonstration."; exit 0 ;;
        *) echo "Invalid selection: $choice" ;;
    esac
    echo ""
    echo "Press Enter to return to menu..."
    read -r _
done
