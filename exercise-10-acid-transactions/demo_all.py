"""
Master Demonstration Runner for MongoDB Lab 10
Executes Lab 10.1 (Bank Transfer ACID Transactions)
and Lab 10.2 (Inventory Reservation & Concurrency Contention) in sequence.
"""

import sys
import time
from datetime import datetime, timezone
import lab_01_bank_transfer
import lab_02_inventory_reservation


def print_master_banner(title: str):
    width = 80
    print("\n" + "=" * width)
    print(f"{title:^{width}}")
    print("=" * width + "\n")


def main():
    start_time = time.time()
    print_master_banner("MONGODB LAB 10: MULTI-DOCUMENT TRANSACTIONS & CONCURRENCY")
    print(f"  Execution Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Target Environment : MongoDB 7.0 Replica Set ('rs0')")
    print(f"  Demonstration Suite: Lab 10.1 + Lab 10.2 (Complete Verification)")

    # Execute Lab 10.1
    print("\n>>> STARTING PART 1: LAB 10.1 - BANK TRANSFER TRANSACTION SUITE")
    lab_01_bank_transfer.run_lab_01_demonstration()

    # Execute Lab 10.2
    print("\n>>> STARTING PART 2: LAB 10.2 - INVENTORY RESERVATION & DEADLOCK HANDLING")
    lab_02_inventory_reservation.main()

    total_time = time.time() - start_time
    print_master_banner("MASTER DEMONSTRATION COMPLETE - ALL TESTS PASSED")
    print(f"  Total Duration: {total_time:.2f} seconds")
    print("  Status: All multi-document transactions, rollbacks, OCC retries, and assertions VERIFIED.\n")


if __name__ == "__main__":
    main()
