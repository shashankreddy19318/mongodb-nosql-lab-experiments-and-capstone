"""
Lab 11.1 - Evaluate Shard Key Choices & MongoDB 5.0+ Resharding Analysis
Course: Distributed NoSQL Databases (MongoDB 7.0)
Author: Chintan

Objective:
  1. For an e-commerce order management system, evaluate four candidate shard keys:
     - order_id
     - customer_id
     - order_date
     - hashed customer_id
     (plus category_id and compound keys as real-world architectural comparisons).
  2. For each candidate, assess cardinality, distribution, query targeting, and hotspot risk.
  3. Draw a decision matrix and recommend the best shard key with justification.
  4. Activity 11.1 Research: MongoDB 5.0+ Resharding (Steps, Architecture & Limitations).
"""

import os
import sys

# Ensure local modules can be resolved
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config.connection import banner

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


def evaluate_shard_key(name, cardinality_val, cardinality_desc,
                       distribution_val, distribution_desc,
                       query_targeting_val, query_targeting_desc,
                       monotonic_val, monotonic_desc,
                       hotspot_risk, verdict, recommendation):
    """
    Score a shard key candidate across the 4 fundamental sharding vectors:
      - High Cardinality
      - Even Distribution
      - Targeted Queries (avoiding scatter-gather)
      - Non-Monotonic (hotspot prevention)
    """
    scores = {
        "Cardinality": "+" if cardinality_val > 100000 else ("~" if cardinality_val > 1000 else "-"),
        "Distribution": "+" if distribution_val > 0.8 else ("~" if distribution_val > 0.5 else "-"),
        "Query Targeting": "+" if query_targeting_val > 0.8 else ("~" if query_targeting_val > 0.5 else "-"),
        "Non-Monotonic": "+" if not monotonic_val else "-",
    }
    total_plus = sum(1 for v in scores.values() if v == "+")
    return {
        "name": name,
        "cardinality_desc": cardinality_desc,
        "distribution_desc": distribution_desc,
        "query_desc": query_targeting_desc,
        "monotonic_desc": monotonic_desc,
        "hotspot_risk": hotspot_risk,
        "scores": scores,
        "total_plus": total_plus,
        "verdict": verdict,
        "recommendation": recommendation,
    }


def get_candidates():
    return [
        evaluate_shard_key(
            name="customer_id (Hashed)",
            cardinality_val=1000000,
            cardinality_desc="High (millions of users)",
            distribution_val=0.95,
            distribution_desc="Even (randomized 64-bit MD5/Murmur3 hash)",
            query_targeting_val=0.90,
            query_targeting_desc="High (routes customer queries to 1 shard)",
            monotonic_val=False,
            monotonic_desc="Non-monotonic (hashing scrambles order)",
            hotspot_risk="Low",
            verdict="RECOMMENDED - General Purpose Choice",
            recommendation="Optimal balance between even write distribution and single-shard query targeting for customer portals."
        ),
        evaluate_shard_key(
            name="order_id (Hashed / UUID)",
            cardinality_val=5000000,
            cardinality_desc="Very High (1:1 per order)",
            distribution_val=0.92,
            distribution_desc="Even (scrambled order IDs spread uniformly)",
            query_targeting_val=0.55,
            query_targeting_desc="Poor (requires scatter-gather for customer/date queries)",
            monotonic_val=False,
            monotonic_desc="Non-monotonic",
            hotspot_risk="Low",
            verdict="GOOD for order writes, POOR for user dashboards",
            recommendation="Excellent for write-heavy order intake, but customer order history queries must broadcast to all shards."
        ),
        evaluate_shard_key(
            name="customer_id (Range)",
            cardinality_val=1000000,
            cardinality_desc="High (distinct customer IDs)",
            distribution_val=0.50,
            distribution_desc="Uneven (whales/power users cause chunk skew)",
            query_targeting_val=0.95,
            query_targeting_desc="Excellent (all user orders on one shard)",
            monotonic_val=False,
            monotonic_desc="Non-monotonic (if randomly assigned)",
            hotspot_risk="Medium",
            verdict="CAUTION - Risk of Jumbo Chunks & Data Skew",
            recommendation="Frequent buyers create disproportionately large chunks that cannot be split if values share identical customer_id."
        ),
        evaluate_shard_key(
            name="order_date / ts (Range)",
            cardinality_val=3650,
            cardinality_desc="Medium (date-based / timestamps)",
            distribution_val=0.15,
            distribution_desc="Severely Skewed (100% of inserts hit latest chunk)",
            query_targeting_val=0.50,
            query_targeting_desc="Good for date ranges, terrible for customer lookups",
            monotonic_val=True,
            monotonic_desc="Monotonically Increasing",
            hotspot_risk="CRITICAL (Extreme Hotspot)",
            verdict="AVOID - Classic Insert Bottleneck Anti-Pattern",
            recommendation="All new writes route to the single shard owning the maxKey chunk, rendering sharding useless for write scaling."
        ),
        evaluate_shard_key(
            name="category_id (Low Card)",
            cardinality_val=50,
            cardinality_desc="Low (50 - 100 product categories)",
            distribution_val=0.25,
            distribution_desc="Severe Skew (popular categories dominate)",
            query_targeting_val=0.65,
            query_targeting_desc="Targeted for category browsing only",
            monotonic_val=False,
            monotonic_desc="Non-monotonic",
            hotspot_risk="High (Popular Category Hotspot)",
            verdict="AVOID - Low Cardinality Hard Ceiling",
            recommendation="Cluster cannot scale beyond the number of unique categories; creates massive un-splittable chunks."
        ),
        evaluate_shard_key(
            name="{ customer_id: 1, order_date: 1 } (Compound)",
            cardinality_val=5000000,
            cardinality_desc="Extremely High (compound combination)",
            distribution_val=0.85,
            distribution_desc="Even across customers, ordered by time",
            query_targeting_val=0.95,
            query_targeting_desc="Excellent (customer history + date range targeted)",
            monotonic_val=False,
            monotonic_desc="Non-monotonic prefix (customer_id breaks monotonicity)",
            hotspot_risk="Low",
            verdict="BEST ADVANCED CHOICE for E-Commerce",
            recommendation="Prefix isolates queries to a single shard; second field allows in-shard sorting and ranged chunk splits without hotspotting."
        )
    ]


def display_decision_matrix(candidates):
    """Render the comprehensive Decision Matrix."""
    if HAS_RICH:
        console = Console()
        table = Table(
            title="MongoDB Shard Key Decision Matrix: E-Commerce System",
            show_header=True,
            header_style="bold white on blue",
            show_lines=True
        )
        table.add_column("Candidate Shard Key", style="cyan bold", width=25)
        table.add_column("Cardinality", justify="center", width=12)
        table.add_column("Distribution", justify="center", width=12)
        table.add_column("Query Target", justify="center", width=12)
        table.add_column("Non-Mono?", justify="center", width=10)
        table.add_column("Hotspot Risk", justify="center", width=12)
        table.add_column("Score", justify="center", width=8)
        table.add_column("Architectural Verdict", width=38)

        for c in candidates:
            s = c["scores"]
            score_str = f"{c['total_plus']}/4"
            table.add_row(
                c["name"],
                f"{s['Cardinality']} ({c['cardinality_desc'].split()[0]})",
                f"{s['Distribution']} ({c['distribution_desc'].split()[0]})",
                f"{s['Query Targeting']} ({c['query_desc'].split()[0]})",
                s['Non-Monotonic'],
                c["hotspot_risk"],
                score_str,
                c["verdict"]
            )
        console.print(table)
    else:
        # Standard ASCII format
        header = f"{'Candidate Shard Key':<25} | {'Card':<6} | {'Dist':<6} | {'Target':<6} | {'Non-M':<6} | {'Hotspot':<10} | {'Score':<6} | {'Verdict'}"
        print(header)
        print("-" * len(header))
        for c in candidates:
            s = c["scores"]
            score_str = f"{c['total_plus']}/4"
            print(f"{c['name']:<25} | {s['Cardinality']:<6} | {s['Distribution']:<6} | {s['Query Targeting']:<6} | {s['Non-Monotonic']:<6} | {c['hotspot_risk']:<10} | {score_str:<6} | {c['verdict']}")


def display_detailed_analysis(candidates):
    """Print in-depth qualitative evaluation for each candidate key."""
    print("\n" + "=" * 80)
    print("  QUALITATIVE EVALUATION OF CANDIDATE SHARD KEYS")
    print("=" * 80)

    for idx, c in enumerate(candidates, 1):
        print(f"\n[{idx}] Candidate: {c['name']}")
        print(f"    - Cardinality:    {c['cardinality_desc']}")
        print(f"    - Distribution:   {c['distribution_desc']}")
        print(f"    - Query Target:   {c['query_desc']}")
        print(f"    - Monotonicity:   {c['monotonic_desc']} (Hotspot Risk: {c['hotspot_risk']})")
        print(f"    - Verdict:        {c['verdict']}")
        print(f"    - Recommendation: {c['recommendation']}")


def display_resharding_research():
    """Activity 11.1: Research MongoDB 5.0+ Resharding (Steps and Limitations)."""
    banner("Activity 11.1: Research MongoDB 5.0+ Resharding Architecture")

    print("""
1. BACKGROUND & PROBLEM CONTEXT:
--------------------------------
Prior to MongoDB 5.0, choosing a shard key was a permanent, irreversible architectural decision.
If an application outgrew its shard key (e.g. data skewed on customer_id or write bottlenecks on
order_date), operators were forced to manually create a new sharded collection, write dual-write
proxy application logic, dump and restore terabytes of data, and schedule prolonged maintenance downtime.

Starting with MongoDB 5.0, MongoDB introduced live, online resharding via the:
    sh.reshardCollection("<database>.<collection>", { <newKey>: 1 | "hashed" })
command, allowing administrators to change the shard key of an existing sharded collection
with zero application downtime and minimal write disruption.


2. STEP-BY-STEP RESHARDING EXECUTION PHASES:
--------------------------------------------
Phase 1: Initialization & Validation
  - The administrator issues sh.reshardCollection(namespace, newShardKey).
  - The mongos router contacts the Config Server Primary to ensure cluster health, verify that no
    other resharding or balancer conflicting operation is in progress, and validate the new shard key
    index rules (e.g., uniqueness constraints).

Phase 2: Destination Collection Creation
  - The Config Server creates a temporary internal destination collection across all shards.
  - The balancer assigns initial chunk distribution ranges based on the new shard key specification.

Phase 3: Background Document Cloning (Initial Sync)
  - Donor shards scan their local source collection and stream documents over the internal network
    to the designated recipient shards holding the corresponding chunk ranges for the new shard key.
  - While cloning occurs, the application continues reading and writing to the source collection normally.

Phase 4: Oplog Application & Catch-Up Sync
  - Destination shards actively tail the source shards' Operation Log (oplog).
  - Any inserts, updates, or deletes that occurred after the initial clone scan began are applied
    incrementally to keep the temporary destination collection in sync with the source.

Phase 5: Critical Section & Atomic Cutover
  - Once the oplog lag drops below a tight threshold (typically < 2 seconds), the cluster enters
    the 'critical section'.
  - Writes to the collection are briefly queued/paused for 1 to 3 seconds.
  - The Config Server atomically updates the cluster routing metadata to point the collection
    namespace to the newly partitioned destination chunks.
  - The pause is released, writes resume immediately routed via the new shard key, and the old collection
    is asynchronously dropped in the background.


3. OPERATIONAL LIMITATIONS & CAVEATS:
-------------------------------------
- Single Active Operation: Only ONE resharding operation can run per cluster at any given time.
- Storage Overhead: Requires substantial free disk space—a minimum of 2x the existing collection
  size plus index overhead across all shards during the cloning phase.
- I/O & CPU Utilization: Initial sync and oplog tailing generate significant background network traffic
  and disk I/O, which can impact latency if the cluster is already running above 70% capacity.
- Unique Index Restrictions: Any existing unique indexes on the collection must be a prefix of the
  new shard key; otherwise, the command will be rejected before starting.
- Unsupported Collections: Cannot reshard system collections, capped collections, or time-series
  collections.
- Abort Mechanics: An ongoing resharding can be halted using sh.abortReshardCollection(), but the rollback
  and cleanup of cloned documents incurs an operational cleanup delay.
""")


def main():
    banner("Lab 11.1: Evaluate Shard Key Choices & Decision Matrix")
    candidates = get_candidates()
    display_decision_matrix(candidates)
    display_detailed_analysis(candidates)
    display_resharding_research()
    banner("Lab 11.1 Complete")


if __name__ == "__main__":
    main()
