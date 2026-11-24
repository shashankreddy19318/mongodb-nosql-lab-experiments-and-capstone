#!/bin/bash
set -e

# Start background MongoDB service if not running
mkdir -p /data/db /data/db_tls /var/log

if [ "$1" = "test" ] || [ "$1" = "demo" ] || [ -z "$1" ]; then
    echo "=========================================================="
    echo "  Starting MongoDB Security Lab Demonstration Container   "
    echo "=========================================================="
    /app/run_all_labs.sh
    
    if [ -t 0 ]; then
        echo ""
        echo "=========================================================="
        echo "  Interactive Shell Ready for Grading / Manual Inspection "
        echo "  Try connecting: mongosh -u admin -p AdminPass123!       "
        echo "=========================================================="
        exec /bin/bash
    else
        echo "Execution finished."
    fi
else
    exec "$@"
fi
