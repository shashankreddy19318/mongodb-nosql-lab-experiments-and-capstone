"""Lab 14.1: Build a Monitoring Dashboard
Objective: Create a Python-based monitoring script that reports key MongoDB metrics.
Instructions:
1. Write a Python script that connects to MongoDB and retrieves:
   - connection count (current, available, totalCreated)
   - opcounters (insert, query, update, delete, getmore, command)
   - WiredTiger cache statistics (bytes in cache, dirty bytes, hit ratio)
   - replica set status (if applicable) & replication lag
2. Format the output as a table and write it to a log file every 30 seconds.
3. Add threshold-based alerting: print a WARNING if the cache hit ratio drops below 80 percent
   or if replication lag exceeds 10 seconds.
Activity for 14.1 (Try it yourself):
Extend the script to send alerts to a webhook URL (e.g., Slack or Discord) when a threshold is breached.
"""

import sys
import os
import time
import json
import logging
import argparse
from datetime import datetime
from pymongo import MongoClient
import requests

try:
    from tabulate import tabulate
    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False

# Ensure logs directory exists
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, "metrics.log")


def setup_logger(log_file):
    """Configure file logger to append metrics cleanly."""
    logger = logging.getLogger("mongo_monitor")
    logger.setLevel(logging.INFO)
    # Avoid duplicate handlers on re-runs
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def get_mongodb_metrics(client):
    """Retrieve key metrics from serverStatus and replSetGetStatus."""
    status = client.admin.command("serverStatus")
    wt = status.get("wiredTiger", {}).get("cache", {})
    connections = status.get("connections", {})
    opcounters = status.get("opcounters", {})
    mem = status.get("mem", {})

    # WiredTiger Cache metrics
    bytes_in_cache = wt.get("bytes currently in the cache", 0)
    max_bytes = wt.get("maximum bytes configured", 0)
    dirty_bytes = wt.get("tracked dirty bytes in the cache", 0)
    bytes_read_into_cache = wt.get("bytes read into cache", 0)
    bytes_written_from_cache = wt.get("bytes written from cache", 0)
    pages_requested = wt.get("pages requested from the cache", 0)
    pages_read_into_cache = wt.get("pages read into cache", 0)

    # Cache hit ratio:
    # If pages requested > 0: hit ratio is (pages_requested - pages_read_into_cache) / pages_requested
    # Also calculate bytes ratio if available
    if pages_requested > 0:
        cache_hit_ratio = max(0.0, min(1.0, (pages_requested - pages_read_into_cache) / pages_requested))
    else:
        cache_hit_ratio = 1.0

    cache_usage_pct = (bytes_in_cache / max_bytes * 100.0) if max_bytes > 0 else 0.0
    cache_dirty_pct = (dirty_bytes / bytes_in_cache * 100.0) if bytes_in_cache > 0 else 0.0

    # Replica Set Status & Replication Lag
    replica_info = {
        "is_replica_set": False,
        "set_name": "None (Standalone)",
        "my_state": "STANDALONE",
        "primary_member": None,
        "max_replication_lag_sec": 0.0,
        "secondaries": []
    }

    try:
        repl_status = client.admin.command("replSetGetStatus")
        replica_info["is_replica_set"] = True
        replica_info["set_name"] = repl_status.get("set", "unknown")
        
        # Locate primary optime
        primary_optime_date = None
        for member in repl_status.get("members", []):
            if member.get("stateStr") == "PRIMARY":
                replica_info["primary_member"] = member.get("name")
                primary_optime_date = member.get("optimeDate")
                break

        # Calculate lag for each secondary
        for member in repl_status.get("members", []):
            state = member.get("stateStr")
            name = member.get("name")
            if state == "SECONDARY":
                sec_optime = member.get("optimeDate")
                lag = 0.0
                if primary_optime_date and sec_optime:
                    diff = (primary_optime_date - sec_optime).total_seconds()
                    lag = max(0.0, diff)
                
                replica_info["secondaries"].append({
                    "name": name,
                    "state": state,
                    "lag_sec": lag,
                    "health": member.get("health", 1)
                })
                if lag > replica_info["max_replication_lag_sec"]:
                    replica_info["max_replication_lag_sec"] = lag
            elif member.get("self"):
                replica_info["my_state"] = state

    except Exception:
        # Standalone server: replSetGetStatus fails with code 76 (NotAReplicaSet)
        replica_info["is_replica_set"] = False
        replica_info["set_name"] = "Standalone (N/A)"
        replica_info["my_state"] = "STANDALONE"

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": status.get("version", "unknown"),
        "uptime_sec": status.get("uptime", 0),
        "connections": {
            "current": connections.get("current", 0),
            "available": connections.get("available", 0),
            "totalCreated": connections.get("totalCreated", 0),
            "active": connections.get("active", 0),
            "usage_pct": round((connections.get("current", 0) / (connections.get("current", 0) + connections.get("available", 1))) * 100, 2)
        },
        "opcounters": {
            "insert": opcounters.get("insert", 0),
            "query": opcounters.get("query", 0),
            "update": opcounters.get("update", 0),
            "delete": opcounters.get("delete", 0),
            "getmore": opcounters.get("getmore", 0),
            "command": opcounters.get("command", 0),
        },
        "cache": {
            "bytes_in_cache": bytes_in_cache,
            "bytes_in_cache_mb": round(bytes_in_cache / (1024 * 1024), 2),
            "max_bytes": max_bytes,
            "max_bytes_mb": round(max_bytes / (1024 * 1024), 2),
            "dirty_bytes": dirty_bytes,
            "dirty_bytes_mb": round(dirty_bytes / (1024 * 1024), 2),
            "bytes_read_into_cache": bytes_read_into_cache,
            "bytes_written_from_cache": bytes_written_from_cache,
            "pages_requested": pages_requested,
            "pages_read": pages_read_into_cache,
            "hit_ratio": cache_hit_ratio,
            "hit_ratio_pct": round(cache_hit_ratio * 100.0, 2),
            "usage_pct": round(cache_usage_pct, 2),
            "dirty_pct": round(cache_dirty_pct, 2)
        },
        "memory_resident_mb": mem.get("resident", 0),
        "replica_set": replica_info
    }


def evaluate_alerts(metrics, test_alert=False):
    """Check thresholds:
    1. Cache Hit Ratio < 80% (0.80) -> WARNING
    2. Replication Lag > 10 seconds -> WARNING
    3. Connection Usage > 80% -> WARNING
    """
    alerts = []
    
    # Threshold 1: Cache Hit Ratio < 80%
    hit_ratio = metrics["cache"]["hit_ratio"]
    hit_pct = metrics["cache"]["hit_ratio_pct"]
    if hit_ratio < 0.80 or test_alert:
        val = 74.5 if test_alert else hit_pct
        alerts.append({
            "level": "WARNING",
            "metric": "WiredTiger Cache Hit Ratio",
            "current_value": f"{val:.1f}%",
            "threshold": "< 80.0%",
            "message": f"Cache hit ratio dropped to {val:.1f}% (below 80% threshold). Potential disk I/O pressure!",
            "timestamp": metrics["timestamp"]
        })

    # Threshold 2: Replication Lag > 10 seconds
    repl = metrics["replica_set"]
    if repl["is_replica_set"]:
        for sec in repl["secondaries"]:
            lag = sec["lag_sec"]
            if lag > 10.0 or (test_alert and sec == repl["secondaries"][0]):
                eff_lag = 14.8 if test_alert else lag
                alerts.append({
                    "level": "WARNING",
                    "metric": f"Replication Lag ({sec['name']})",
                    "current_value": f"{eff_lag:.1f}s",
                    "threshold": "> 10.0s",
                    "message": f"Replication lag on {sec['name']} is {eff_lag:.1f} seconds (exceeds 10s threshold). High RPO risk!",
                    "timestamp": metrics["timestamp"]
                })
    elif test_alert and not any(a["metric"].startswith("Replication") for a in alerts):
        alerts.append({
            "level": "WARNING",
            "metric": "Replication Lag (Simulated Secondary)",
            "current_value": "12.4s",
            "threshold": "> 10.0s",
            "message": "Simulated replication lag on mongo-rs-sec01 is 12.4s (exceeds 10s threshold). High RPO risk!",
            "timestamp": metrics["timestamp"]
        })

    # Threshold 3: Connection Usage > 80%
    conn_usage = metrics["connections"]["usage_pct"]
    if conn_usage > 80.0:
        alerts.append({
            "level": "WARNING",
            "metric": "Connection Pool Saturation",
            "current_value": f"{conn_usage:.1f}%",
            "threshold": "> 80.0%",
            "message": f"Connection pool usage is {conn_usage:.1f}% ({metrics['connections']['current']} active). Approaching connection limit!",
            "timestamp": metrics["timestamp"]
        })

    return alerts


def send_webhook_alert(webhook_url, alert):
    """Activity 14.1: Send alerts to webhook (Slack, Discord, or generic endpoint)."""
    if not webhook_url:
        return False
    
    payload = {
        "text": f"🚨 *[MongoDB Monitor Alert]* {alert['message']}",
        "attachments": [
            {
                "fallback": alert["message"],
                "color": "#FF9900" if alert["level"] == "WARNING" else "#FF0000",
                "title": f"Threshold Breach: {alert['metric']}",
                "fields": [
                    {"title": "Severity", "value": alert["level"], "short": True},
                    {"title": "Current Value", "value": alert["current_value"], "short": True},
                    {"title": "Configured Threshold", "value": alert["threshold"], "short": True},
                    {"title": "Timestamp", "value": alert["timestamp"], "short": True}
                ],
                "footer": "MongoDB Real-time Operations Monitor | Lab 14.1"
            }
        ],
        # Discord & standard webhook compatibility
        "content": (
            f"🚨 **[MongoDB Monitor Alert - {alert['level']}]**\n"
            f"> **Metric:** {alert['metric']}\n"
            f"> **Current Value:** `{alert['current_value']}` (Threshold: `{alert['threshold']}`)\n"
            f"> **Detail:** {alert['message']}\n"
            f"> **Time:** {alert['timestamp']}"
        )
    }

    try:
        resp = requests.post(
            webhook_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        if resp.status_code in (200, 204):
            print(f"  [WEBHOOK SUCCESS] Alert dispatched to {webhook_url} (HTTP {resp.status_code})")
            return True
        else:
            print(f"  [WEBHOOK WARNING] Server returned status {resp.status_code}: {resp.text[:100]}")
            return False
    except Exception as exc:
        print(f"  [WEBHOOK ERROR] Failed to deliver alert to webhook: {exc}")
        return False


def format_table_ascii(metrics):
    """Generate plaintext ASCII table for logging and fallback console."""
    rows = [
        ["MongoDB Version", metrics["version"]],
        ["Uptime", f"{metrics['uptime_sec']}s ({metrics['uptime_sec'] // 60}m)"],
        ["Connections (Current)", f"{metrics['connections']['current']:,}"],
        ["Connections (Available)", f"{metrics['connections']['available']:,}"],
        ["Connection Pool Usage", f"{metrics['connections']['usage_pct']}%"],
        ["Opcounters: Insert", f"{metrics['opcounters']['insert']:,}"],
        ["Opcounters: Query", f"{metrics['opcounters']['query']:,}"],
        ["Opcounters: Update", f"{metrics['opcounters']['update']:,}"],
        ["Opcounters: Delete", f"{metrics['opcounters']['delete']:,}"],
        ["Opcounters: Command", f"{metrics['opcounters']['command']:,}"],
        ["WiredTiger Cache In Use", f"{metrics['cache']['bytes_in_cache_mb']} MB ({metrics['cache']['usage_pct']}%)"],
        ["WiredTiger Cache Max", f"{metrics['cache']['max_bytes_mb']} MB"],
        ["WiredTiger Dirty Bytes", f"{metrics['cache']['dirty_bytes_mb']} MB ({metrics['cache']['dirty_pct']}%)"],
        ["Pages Requested from Cache", f"{metrics['cache']['pages_requested']:,}"],
        ["Pages Read into Cache", f"{metrics['cache']['pages_read']:,}"],
        ["WiredTiger Cache Hit Ratio", f"{metrics['cache']['hit_ratio_pct']}%"],
        ["Replica Set Mode", metrics['replica_set']['set_name']],
        ["Replica Member State", metrics['replica_set']['my_state']],
        ["Max Replication Lag", f"{metrics['replica_set']['max_replication_lag_sec']:.2f}s"]
    ]
    if HAS_TABULATE:
        return tabulate(rows, headers=["Metric Name", "Current Value"], tablefmt="grid")
    
    # Built-in f-string table
    lines = ["+------------------------------+------------------------------+"]
    lines.append("| Metric Name                  | Current Value                |")
    lines.append("+------------------------------+------------------------------+")
    for name, val in rows:
        lines.append(f"| {name:<28} | {val:<28} |")
    lines.append("+------------------------------+------------------------------+")
    return "\n".join(lines)


def display_dashboard(metrics, alerts):
    """Render rich visual table to console."""
    if HAS_RICH:
        table = Table(title=f"MongoDB Operations Dashboard [{metrics['timestamp']}]", header_style="bold cyan")
        table.add_column("Category", style="yellow", width=18)
        table.add_column("Metric", style="white", width=30)
        table.add_column("Value", justify="right", style="green", width=24)

        table.add_row("Server", "MongoDB Version", str(metrics["version"]))
        table.add_row("Server", "Uptime", f"{metrics['uptime_sec']}s")
        table.add_row("Connections", "Current / Available", f"{metrics['connections']['current']} / {metrics['connections']['available']}")
        table.add_row("Connections", "Pool Saturation", f"{metrics['connections']['usage_pct']}%")
        table.add_row("Operations", "Inserts / Queries", f"{metrics['opcounters']['insert']:,} / {metrics['opcounters']['query']:,}")
        table.add_row("Operations", "Updates / Deletes", f"{metrics['opcounters']['update']:,} / {metrics['opcounters']['delete']:,}")
        table.add_row("Operations", "Commands Executed", f"{metrics['opcounters']['command']:,}")
        table.add_row("WiredTiger", "Cache Size / Max", f"{metrics['cache']['bytes_in_cache_mb']} MB / {metrics['cache']['max_bytes_mb']} MB")
        table.add_row("WiredTiger", "Cache Usage", f"{metrics['cache']['usage_pct']}%")
        table.add_row("WiredTiger", "Dirty Cache", f"{metrics['cache']['dirty_bytes_mb']} MB ({metrics['cache']['dirty_pct']}%)")
        
        hit_style = "bold green" if metrics['cache']['hit_ratio'] >= 0.80 else "bold red"
        table.add_row("WiredTiger", "Cache Hit Ratio", f"[{hit_style}]{metrics['cache']['hit_ratio_pct']}%[/{hit_style}]")
        
        table.add_row("Replication", "Replica Set Name", metrics['replica_set']['set_name'])
        table.add_row("Replication", "Current State", metrics['replica_set']['my_state'])
        lag = metrics['replica_set']['max_replication_lag_sec']
        lag_style = "green" if lag <= 10.0 else "bold red"
        table.add_row("Replication", "Replication Lag", f"[{lag_style}]{lag:.2f}s[/{lag_style}]")
        
        console.print(table)
        
        if alerts:
            for alert in alerts:
                console.print(Panel(
                    f"[bold red]WARNING: {alert['metric']}[/bold red]\n"
                    f"Current: [yellow]{alert['current_value']}[/yellow] | Threshold: [yellow]{alert['threshold']}[/yellow]\n"
                    f"Detail: {alert['message']}",
                    title="⚠️ THRESHOLD BREACH DETECTED",
                    border_style="red"
                ))
        else:
            console.print("[bold green]✔ All operational metrics within normal thresholds.[/bold green]\n")
    else:
        print("\n" + "=" * 65)
        print(f" MongoDB Operations Dashboard [{metrics['timestamp']}]")
        print("=" * 65)
        print(format_table_ascii(metrics))
        if alerts:
            print("\n*** ACTIVE ALERTS ***")
            for alert in alerts:
                print(f"[WARNING] {alert['metric']}: {alert['current_value']} (Threshold: {alert['threshold']}) - {alert['message']}")
        else:
            print("\n[OK] All operational metrics within normal thresholds.")


def main():
    parser = argparse.ArgumentParser(description="Lab 14.1: MongoDB Operational Metrics Monitoring Dashboard")
    parser.add_argument("--uri", default=os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/?directConnection=true"),
                        help="MongoDB Connection URI")
    parser.add_argument("--interval", type=int, default=30,
                        help="Metrics collection interval in seconds (default: 30s as per instructions)")
    parser.add_argument("--iterations", type=int, default=1,
                        help="Number of iterations to run (default: 1 for demo, 0 for infinite loop)")
    parser.add_argument("--log-file", default=DEFAULT_LOG_FILE,
                        help="Log file path (default: logs/metrics.log)")
    parser.add_argument("--webhook-url", default=os.getenv("WEBHOOK_URL", ""),
                        help="Webhook URL for alert dispatch (Slack/Discord/generic)")
    parser.add_argument("--test-alert", action="store_true",
                        help="Simulate threshold breaches to test alert handling & webhook dispatch")
    args = parser.parse_args()

    logger = setup_logger(args.log_file)
    print("=" * 70)
    print("  Lab 14.1: MongoDB Operational Monitoring Dashboard")
    print(f"  Target URI: {args.uri}")
    print(f"  Log File:   {args.log_file}")
    print(f"  Interval:   {args.interval}s")
    if args.webhook_url:
        print(f"  Webhook:    {args.webhook_url}")
    if args.test_alert:
        print("  Notice:     --test-alert enabled (Simulating metric threshold breach)")
    print("=" * 70)

    try:
        client = MongoClient(args.uri, serverSelectionTimeoutMS=5000)
        client.admin.command("ping")
        print("[OK] Successfully connected to MongoDB instance.")
    except Exception as exc:
        print(f"[FATAL] Cannot connect to MongoDB at {args.uri}: {exc}")
        sys.exit(1)

    iteration_count = 0
    try:
        while True:
            iteration_count += 1
            metrics = get_mongodb_metrics(client)
            alerts = evaluate_alerts(metrics, test_alert=args.test_alert)

            # Display to console
            display_dashboard(metrics, alerts)

            # Write formatted table & structured log entry to log file
            ascii_table = format_table_ascii(metrics)
            logger.info(f"METRICS_SNAPSHOT_CYCLE_{iteration_count}\n{ascii_table}")
            logger.info(f"JSON_METRICS: {json.dumps(metrics)}")

            # Process Alerts
            for alert in alerts:
                logger.warning(f"THRESHOLD_BREACH: {alert['metric']} = {alert['current_value']} (Threshold: {alert['threshold']}) - {alert['message']}")
                if args.webhook_url:
                    send_webhook_alert(args.webhook_url, alert)

            print(f"[LOGGED] Metrics snapshot appended to {args.log_file} (Cycle #{iteration_count})")

            # Check loop termination
            if args.iterations > 0 and iteration_count >= args.iterations:
                print(f"\n[DONE] Completed requested {args.iterations} iteration(s).")
                break

            print(f"Waiting {args.interval}s until next collection cycle (Ctrl+C to stop)...\n")
            time.sleep(args.interval)

    except KeyboardInterrupt:
        print("\n[INFO] Monitoring loop terminated by user.")
    finally:
        client.close()
        print("[OK] MongoDB client connection closed.")


if __name__ == "__main__":
    main()
