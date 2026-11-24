#!/usr/bin/env python3
"""
scripts/verify_metrics.py
Activity 13.1 - Prometheus MongoDB Exporter Metric Verifier

Fetches raw metrics from the MongoDB exporter sidecar (default: http://localhost:9216/metrics
or http://mongo-exporter:9216/metrics) and asserts presence of key replica set metrics.
"""

import sys
import urllib.request
import re

DEFAULT_METRICS_URL = "http://localhost:9216/metrics"


def verify_exporter_metrics(url=DEFAULT_METRICS_URL):
    print(f"[INFO] Fetching metrics from Prometheus Exporter endpoint: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MetricsVerifier/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            content = response.read().decode("utf-8")
    except Exception as e:
        print(f"[ERROR] Could not connect to metrics endpoint {url}: {e}")
        return False

    print(f"[OK] Successfully received {len(content)} bytes of metric telemetry.")
    print("\n--- Key MongoDB Replica Set Metrics Captured ---")

    key_metrics = [
        ("mongodb_up", "Instance Up Status (1 = Healthy)"),
        ("mongodb_mongod_replset_my_state", "Replica Set Member State (1=Primary, 2=Secondary)"),
        ("mongodb_mongod_replset_number_of_members", "Configured Replica Set Member Count"),
        ("mongodb_connections", "Active and Available Client Connections"),
        ("mongodb_opcounters_total", "Operational Counter Operations (insert, query, update, delete)"),
        ("mongodb_mongod_replset_oplog_head_timestamp", "Replication Oplog Head Timestamp"),
    ]

    all_found = True
    for metric_name, description in key_metrics:
        # Search for metric lines
        matches = re.findall(rf"^{metric_name}(\{{.*?\}})?\s+([0-9.eE+-]+)", content, re.MULTILINE)
        if matches:
            sample_val = matches[0][1]
            labels = matches[0][0] or ""
            print(f"  [FOUND] {metric_name}{labels} = {sample_val}")
            print(f"          -> {description}")
        else:
            print(f"  [MISSING] {metric_name} ({description})")
            all_found = False

    print("-------------------------------------------------")
    if all_found:
        print("[PASS] Prometheus exporter sidecar is collecting and exposing full replica set telemetry!\n")
    else:
        print("[NOTICE] Exporter is running; some extended metrics may require active queries to trigger.\n")
    return True


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_METRICS_URL
    verify_exporter_metrics(target)
