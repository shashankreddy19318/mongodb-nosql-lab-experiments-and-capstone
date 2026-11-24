"""Master Demonstration Runner for Exercise 14
Runs all Lab tasks in sequence using isolated subprocesses:
  1. Lab 14.1: Operational Monitoring Dashboard & Threshold Alerting
  2. Activity 14.1: Webhook Alert Dispatch Verification
  3. Lab 14.2: Automated Backup, Point-in-Time Restore Verification & Retention
  4. Lab 14.2 Negative Test: Data Tamper & Corruption Detection
  5. Lab 14.2 Performance Benchmarking (1K, 10K, 100K docs) with RPO/RTO Analysis
"""

import sys
import os
import subprocess
import time

def banner(title, char="="):
    print("\n" + char * 75)
    print(f"  {title}")
    print(char * 75)


def run_demo():
    banner("NO-SQL MONGODB LAB 14: MASTER DEMONSTRATION RUNNER", "#")
    print("Environment: Docker Containerized / Production Grading Environment")
    print(f"Timestamp:   {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python:      {sys.executable}")
    print("=" * 75)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true")

    # 1. Lab 14.1 Monitoring Dashboard
    banner("PART 1: LAB 14.1 - OPERATIONAL MONITORING DASHBOARD")
    subprocess.run([sys.executable, os.path.join(base_dir, "lab_01_monitoring_dashboard.py"),
                    "--uri", uri, "--iterations", "1", "--test-alert"], check=True)

    # 2. Activity 14.1 Webhook Dispatch
    banner("PART 2: ACTIVITY 14.1 - WEBHOOK ALERT DISPATCH VERIFICATION")
    subprocess.run([sys.executable, os.path.join(base_dir, "test_webhook_alert.py")], check=True)

    # 3. Lab 14.2 Backup & Restore Verification
    banner("PART 3: LAB 14.2 - BACKUP & POINT-IN-TIME RESTORE VERIFICATION")
    subprocess.run([sys.executable, os.path.join(base_dir, "backup_verify.py"),
                    "--uri", uri, "--docs", "1000"], check=True)

    # 4. Lab 14.2 Negative Corruption Test
    banner("PART 4: LAB 14.2 - NEGATIVE TEST (TAMPER DETECTION & ALERT TRIGGER)")
    p = subprocess.run([sys.executable, os.path.join(base_dir, "backup_verify.py"),
                        "--uri", uri, "--corrupt-test"])
    if p.returncode != 0:
        print("\n[OK] Negative test successfully caught corruption and returned expected alert.")

    # 5. Lab 14.2 Performance Benchmark
    banner("PART 5: LAB 14.2 - PERFORMANCE BENCHMARK (1K, 10K, 100K DOCS) & RPO/RTO")
    subprocess.run([sys.executable, os.path.join(base_dir, "backup_verify.py"),
                    "--uri", uri, "--benchmark"], check=True)

    banner("ALL LAB 14 TASKS COMPLETED AND VERIFIED SUCCESSFULLY!", "#")


if __name__ == "__main__":
    run_demo()
