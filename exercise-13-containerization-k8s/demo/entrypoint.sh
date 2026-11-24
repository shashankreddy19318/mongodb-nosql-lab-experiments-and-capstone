#!/bin/bash
set -e

# Docker Entrypoint for NoSQL Lab 13 Demonstration Image
echo "=========================================================="
echo "  NoSQL Databases Using MongoDB - Exercise 13"
echo "  Docker Demonstration & Evaluation Environment"
echo "=========================================================="

# If arguments are passed, execute them
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

# Otherwise launch the interactive demo runner
python3 /workspace/demo/run_demo.py
