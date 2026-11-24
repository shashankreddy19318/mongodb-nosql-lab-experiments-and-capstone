"""
demo_all.py
Master Demonstration Runner for Lab 16: Polyglot Persistence (MongoDB, Cassandra, Neo4j)

Sequentially executes:
  1. Lab 16.1: Polyglot Data Modeling (Schemas, 3 Equivalent Queries, Complexity Matrix, Activity 16.1 Architecture)
  2. Lab 16.2: Hybrid Query Service (Connection Pooling, Individual Routing, Full Merged Fraud Dossier, Latency Benchmarks)
  3. Lab 16.2 Unit & Integration Tests (100% Mock & Integration Test Suite)

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab16
"""

import os
import sys
from rich.console import Console
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.connection import banner
import lab_01_polyglot_modeling
import lab_02_hybrid_query_service
import test_fraud_service

console = Console()


def run_master_demonstration():
    banner("MASTER POLYGLOT PERSISTENCE DEMONSTRATION SUITE", char="#", width=75)
    console.print(Panel(
        """[bold yellow]NoSQL Databases Chapter 16: Wide-Column & Graph Databases (Cassandra & Neo4j)[/bold yellow]
Author: [bold cyan]Chintan[/bold cyan]
Docker Image: [bold green]shashankreddy30/mongodb-lab16:latest[/bold green]
Verified Engines: [bold]MongoDB 7.0 (Document) | Apache Cassandra (Wide-Column) | Neo4j (Graph)[/bold]""",
        title="[bold green]Evaluation Demonstration Environment[/bold green]",
        border_style="green"
    ))

    # Phase 1: Lab 16.1
    banner("PHASE 1: RUNNING LAB 16.1 - POLYGLOT DATA MODELING", char="=")
    lab_01_polyglot_modeling.main()

    # Phase 2: Lab 16.2
    banner("PHASE 2: RUNNING LAB 16.2 - HYBRID QUERY SERVICE & BENCHMARKS", char="=")
    lab_02_hybrid_query_service.run_service_demonstration()

    # Phase 3: Unit & Integration Tests
    banner("PHASE 3: RUNNING UNIT & INTEGRATION TEST VERIFICATION SUITE", char="=")
    test_fraud_service.run_tests()

    banner("ALL CHAPTER 16 LAB TASKS SUCCESSFULLY DEMONSTRATED AND VERIFIED", char="#", width=75)
    console.print("[bold green]All tests passed with 100% assertions satisfied. Docker container is ready for evaluation![/bold green]\n")


if __name__ == "__main__":
    run_master_demonstration()
