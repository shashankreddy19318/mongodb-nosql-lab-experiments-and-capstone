"""
================================================================================
Master Demo Runner: Lab 9.1 & Lab 9.2 Complete Suite
Chapter 09 - NoSQL Databases (MongoDB)
================================================================================
Runs the entire Lab 09 demonstration end-to-end:
  1. Lab 9.1: Write concern latency benchmark (w:1, w:majority, w:all, j:true/false)
  2. Lab 9.2: Network partition simulation (Phase 1, Phase 2, Phase 3 recovery)
  3. Displays complete findings, tables, and verification logs
================================================================================
"""

import sys
import os
import time

def main():
    print("*" * 84)
    print("*" + " " * 82 + "*")
    print("*" + "    MONGODB REPLICA SET CONSISTENCY & CAP THEOREM LAB DEMONSTRATION SUITE    ".center(82) + "*")
    print("*" + "                   LAB 9.1 & LAB 9.2 AUTOMATED DEMONSTRATION                 ".center(82) + "*")
    print("*" + " " * 82 + "*")
    print("*" * 84)
    print()

    # Part 1
    print(">>> STEP 1: Launching Lab 9.1 Write Concern Latency Benchmark...")
    time.sleep(1)
    import lab_01_write_concern_latency
    lab_01_write_concern_latency.main()

    print("\n" + "=" * 84)
    print(">>> STEP 2: Launching Lab 9.2 Network Partition Simulation...")
    print("=" * 84)
    time.sleep(2)
    import lab_02_simulate_partition
    lab_02_simulate_partition.main()

    print("\n" + "*" * 84)
    print("*" + " " * 82 + "*")
    print("*" + "             ALL LAB 09 DEMONSTRATION TASKS COMPLETED SUCCESSFULLY!           ".center(82) + "*")
    print("*" + " " * 82 + "*")
    print("*" * 84)

if __name__ == "__main__":
    main()
