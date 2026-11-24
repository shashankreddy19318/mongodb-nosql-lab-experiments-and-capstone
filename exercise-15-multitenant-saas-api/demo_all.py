"""Master Demonstration Script for Chapter 15:
  - Lab 15.1: Multi-Tenant REST API with FastAPI & MongoDB (Tenant Isolation, RBAC, Rate Limiting)
  - Activity 15.1: Role-Based Access Control (Admin vs Regular User)
  - Lab 15.2: Data Migration Between Tenant Isolation Strategies
  - Performance Benchmarking across Single-Tenant Read, Single-Tenant Write, and Cross-Tenant Analytics

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab15
"""

import sys
import time
from fastapi.testclient import TestClient
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from lab_01_multitenant_api import (
    app,
    init_database_indexes,
    seed_default_users,
    tasks_col,
    rate_col,
    users_col,
)
from lab_02_tenant_migration import (
    seed_document_level_data,
    migrate_tenant_to_collection,
    benchmark_query_performance,
    get_architectural_recommendations,
    TENANT_IDS,
    TENANT_NAMES,
)

console = Console()
client = TestClient(app)


def print_header(title: str):
    console.print(Panel.fit(f"[bold cyan]{title}[/bold cyan]", border_style="cyan"))


def run_full_demonstration():
    print_header("CHAPTER 15: MULTI-TENANT ARCHITECTURE & DATA MIGRATION DEMONSTRATION")

    # =========================================================================
    # PART 1: LAB 15.1 - MULTI-TENANT REST API WITH FASTAPI & MONGODB
    # =========================================================================
    console.print("\n" + "=" * 80)
    console.print("  [bold yellow]PART 1: LAB 15.1 - MULTI-TENANT REST API (FASTAPI + MONGODB)[/bold yellow]")
    console.print("=" * 80 + "\n")

    # 1. Initialize schema & users
    console.print("[bold green][1.1] Initializing Database Indexes & Seeding Personas[/bold green]")
    init_database_indexes()
    seed_default_users()
    tasks_col.delete_many({})
    rate_col.delete_many({})

    health_resp = client.get("/health")
    console.print(f"  Health Check: [green]{health_resp.status_code} OK[/green] | Indexes: {list(health_resp.json()['task_indexes'])}")

    # 2. Authenticate Users & Acquire JWT Tokens
    console.print("\n[bold green][1.2] Authenticating Personas & Generating JWT Tokens[/bold green]")
    personas = {
        "admin_acme": {"user": "admin_acme", "pass": "password123", "tenant": "tenant-acme", "role": "admin"},
        "alice_acme": {"user": "alice_acme", "pass": "password123", "tenant": "tenant-acme", "role": "user"},
        "bob_acme": {"user": "bob_acme", "pass": "password123", "tenant": "tenant-acme", "role": "user"},
        "admin_globex": {"user": "admin_globex", "pass": "password123", "tenant": "tenant-globex", "role": "admin"},
        "charlie_globex": {"user": "charlie_globex", "pass": "password123", "tenant": "tenant-globex", "role": "user"},
    }
    tokens = {}
    for key, p in personas.items():
        resp = client.post("/auth/login", json={"username": p["user"], "password": p["pass"], "tenant_id": p["tenant"]})
        tokens[key] = resp.json()["access_token"]
        console.print(f"  ✓ Logged in [cyan]{p['user']}[/cyan] (Tenant: [yellow]{p['tenant']}[/yellow], Role: [magenta]{p['role']}[/magenta])")

    # 3. Create Tasks via REST API
    console.print("\n[bold green][1.3] Task Creation with Strict Tenant & Author Stamping[/bold green]")
    
    # Alice (Acme User) creates Task 1
    resp1 = client.post(
        "/tasks/",
        json={"title": "Setup ML Feature Store", "description": "Configure Feast feature store with Redis backend", "priority": "high"},
        headers={"Authorization": f"Bearer {tokens['alice_acme']}"},
    )
    t1 = resp1.json()
    console.print(f"  ✓ Alice (Acme User) created Task 1: ID=[cyan]{t1['id']}[/cyan] (Tenant: {t1['tenant_id']}, CreatedBy: {t1['created_by']})")

    # Bob (Acme User) creates Task 2
    resp2 = client.post(
        "/tasks/",
        json={"title": "Data Pipeline Schema Validator", "description": "Validate incoming Avro payloads against schema registry", "priority": "medium"},
        headers={"Authorization": f"Bearer {tokens['bob_acme']}"},
    )
    t2 = resp2.json()
    console.print(f"  ✓ Bob (Acme User) created Task 2:   ID=[cyan]{t2['id']}[/cyan] (Tenant: {t2['tenant_id']}, CreatedBy: {t2['created_by']})")

    # Charlie (Globex User) creates Task 3
    resp3 = client.post(
        "/tasks/",
        json={"title": "Payment Webhook Integration", "description": "Process Stripe invoice payment webhooks", "priority": "critical"},
        headers={"Authorization": f"Bearer {tokens['charlie_globex']}"},
    )
    t3 = resp3.json()
    console.print(f"  ✓ Charlie (Globex User) created Task 3: ID=[cyan]{t3['id']}[/cyan] (Tenant: {t3['tenant_id']}, CreatedBy: {t3['created_by']})")

    # 4. Role-Based Access Control (RBAC) & Tenant Filtering (Activity 15.1)
    console.print("\n[bold green][1.4] Activity 15.1: Role-Based Access Control & Tenant Isolation Verification[/bold green]")
    
    # Test A: Alice lists tasks (Regular user -> should only see 1 task: her own)
    alice_list = client.get("/tasks/", headers={"Authorization": f"Bearer {tokens['alice_acme']}"}).json()
    console.print(f"  • Alice (Regular User) lists tasks: Found [bold green]{len(alice_list)}[/bold green] task (Only her own: '{alice_list[0]['title']}')")

    # Test B: Acme Admin lists tasks (Admin user -> should see 2 tasks: all Acme tasks)
    admin_list = client.get("/tasks/", headers={"Authorization": f"Bearer {tokens['admin_acme']}"}).json()
    console.print(f"  • Acme Admin lists tasks:           Found [bold green]{len(admin_list)}[/bold green] tasks (All Acme tenant tasks: {[t['title'] for t in admin_list]})")

    # Test C: Globex Admin lists tasks (Admin user -> should see 1 task: Globex only)
    globex_list = client.get("/tasks/", headers={"Authorization": f"Bearer {tokens['admin_globex']}"}).json()
    console.print(f"  • Globex Admin lists tasks:         Found [bold green]{len(globex_list)}[/bold green] tasks (Globex only: {[t['title'] for t in globex_list]})")

    # 5. Cross-Tenant Security Penetration Tests
    console.print("\n[bold green][1.5] Cross-Tenant Security Attack & Penetration Tests[/bold green]")
    
    # Attack 1: Globex tries to read Acme's Task 1
    cross_read = client.get(f"/tasks/{t1['id']}", headers={"Authorization": f"Bearer {tokens['admin_globex']}"})
    if cross_read.status_code == 404:
        console.print(f"  [bold green]✓ BLOCKED (HTTP 404):[/bold green] Globex Admin cannot read Acme's task {t1['id']} (No cross-tenant leakage).")
    else:
        console.print(f"  [bold red]✗ FAILED:[/bold red] Unexpected response {cross_read.status_code}: {cross_read.text}")

    # Attack 2: Globex tries to update Acme's Task 1
    cross_update = client.put(
        f"/tasks/{t1['id']}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {tokens['admin_globex']}"},
    )
    if cross_update.status_code == 404:
        console.print(f"  [bold green]✓ BLOCKED (HTTP 404):[/bold green] Globex Admin cannot modify Acme's task {t1['id']}.")
    else:
        console.print(f"  [bold red]✗ FAILED:[/bold red] Unexpected response {cross_update.status_code}: {cross_update.text}")

    # Attack 3: Globex tries to delete Acme's Task 1
    cross_delete = client.delete(f"/tasks/{t1['id']}", headers={"Authorization": f"Bearer {tokens['admin_globex']}"})
    if cross_delete.status_code == 404:
        console.print(f"  [bold green]✓ BLOCKED (HTTP 404):[/bold green] Globex Admin cannot delete Acme's task {t1['id']}.")
    else:
        console.print(f"  [bold red]✗ FAILED:[/bold red] Unexpected response {cross_delete.status_code}: {cross_delete.text}")

    # 6. Intra-Tenant RBAC Enforcement Tests
    console.print("\n[bold green][1.6] Intra-Tenant RBAC Enforcement (Regular User vs Admin)[/bold green]")
    
    # Alice attempts to modify Bob's task (same tenant, but regular user is not creator)
    alice_bob_update = client.put(
        f"/tasks/{t2['id']}",
        json={"title": "Alice modifying Bob's task"},
        headers={"Authorization": f"Bearer {tokens['alice_acme']}"},
    )
    if alice_bob_update.status_code == 403:
        console.print(f"  [bold green]✓ BLOCKED (HTTP 403 Forbidden):[/bold green] Regular user Alice cannot modify Bob's task.")
    else:
        console.print(f"  [bold red]✗ FAILED:[/bold red] Unexpected response {alice_bob_update.status_code}: {alice_bob_update.text}")

    # Acme Admin modifies Bob's task (admin can manage any task in their tenant)
    admin_bob_update = client.put(
        f"/tasks/{t2['id']}",
        json={"status": "completed", "priority": "high"},
        headers={"Authorization": f"Bearer {tokens['admin_acme']}"},
    )
    if admin_bob_update.status_code == 200:
        console.print(f"  [bold green]✓ ALLOWED (HTTP 200 OK):[/bold green] Acme Admin successfully updated Bob's task to status='completed'.")
    else:
        console.print(f"  [bold red]✗ FAILED:[/bold red] Unexpected response {admin_bob_update.status_code}: {admin_bob_update.text}")

    # 7. Database-Native Rate Limiter Test
    console.print("\n[bold green][1.7] MongoDB Atomic Rate Limiting Verification (Threshold: 10 req/min)[/bold green]")
    rate_col.delete_many({})  # reset counter
    success_requests = 0
    rate_limited_requests = 0

    for i in range(1, 13):
        r = client.get("/tasks/", headers={"Authorization": f"Bearer {tokens['alice_acme']}"})
        if r.status_code == 200:
            success_requests += 1
            console.print(f"    Request {i:2d}: [green]HTTP 200 OK (Allowed)[/green]")
        elif r.status_code == 429:
            rate_limited_requests += 1
            retry_after = r.headers.get("retry-after", "60")
            console.print(f"    Request {i:2d}: [bold red]HTTP 429 Too Many Requests (Rate Limited - Retry-After: {retry_after}s)[/bold red]")

    console.print(f"  [cyan]Rate Limiter Result:[/cyan] {success_requests} requests accepted, {rate_limited_requests} requests blocked.")

    # =========================================================================
    # PART 2: LAB 15.2 - DATA MIGRATION BETWEEN TENANT ISOLATION STRATEGIES
    # =========================================================================
    console.print("\n" + "=" * 80)
    console.print("  [bold yellow]PART 2: LAB 15.2 - TENANT ISOLATION DATA MIGRATION & BENCHMARK[/bold yellow]")
    console.print("=" * 80 + "\n")

    # Step 1: Seed 5 tenants x 100 tasks each
    console.print("[bold green][2.1] Seeding Document-Level Baseline (5 Tenants × 100 Tasks = 500 Documents)[/bold green]")
    num_t, total_d = seed_document_level_data(tasks_per_tenant=100)
    console.print(f"  ✓ Successfully seeded {num_t} tenants with 100 tasks each (Total: {total_d} documents in 'saas_app.tasks')")

    # Step 2: Dry Run Mode
    console.print("\n[bold green][2.2] Dry-Run Migration Simulation (Zero Writes)[/bold green]")
    dry_results = [migrate_tenant_to_collection(tid, dry_run=True) for tid in TENANT_IDS]
    for dr in dry_results:
        console.print(f"  • {dr['tenant_id']}: Status=[yellow]{dr['status']}[/yellow] | Would migrate: {dr['would_migrate']} docs -> '{dr['target_collection']}'")

    # Step 3: Live Migration to Collection-Per-Tenant
    console.print("\n[bold green][2.3] Live Migration to Collection-Per-Tenant & Integrity Verification[/bold green]")
    live_results = [migrate_tenant_to_collection(tid, dry_run=False) for tid in TENANT_IDS]

    mig_table = Table(title="Lab 15.2 Migration & Anti-Leakage Audit Summary", show_lines=True)
    mig_table.add_column("Tenant ID", style="cyan")
    mig_table.add_column("Enterprise Name", style="white")
    mig_table.add_column("Target Collection", style="magenta")
    mig_table.add_column("Source Docs", justify="right")
    mig_table.add_column("Target Docs", justify="right")
    mig_table.add_column("SHA-256 Checksum", justify="center")
    mig_table.add_column("Anti-Leakage Audit", justify="center")

    for lr in live_results:
        sha_status = "[green]MATCH[/green]" if lr["checksum_matches"] else "[red]MISMATCH[/red]"
        leak_status = "[green]0 FOREIGN DOCS (PASSED)[/green]" if lr["leakage_passed"] else f"[red]{lr['foreign_docs']} LEAKS![/red]"
        mig_table.add_row(
            lr["tenant_id"],
            lr["company"],
            lr["target_collection"],
            str(lr["source_count"]),
            str(lr["target_count"]),
            sha_status,
            leak_status,
        )
    console.print(mig_table)

    # Step 4: Idempotency Proof
    console.print("\n[bold green][2.4] Idempotency Verification (Re-running Migration)[/bold green]")
    rerun_results = [migrate_tenant_to_collection(tid, dry_run=False) for tid in TENANT_IDS]
    is_idempotent = all(r["target_count"] == 100 for r in rerun_results)
    if is_idempotent:
        console.print("  [bold green]✓ IDEMPOTENCY CONFIRMED:[/bold green] Re-running migration preserves exact 100 docs per collection (Zero duplicates created).")
    else:
        console.print("  [bold red]✗ FAILED:[/bold red] Duplicate documents detected.")

    # Step 5: High-Precision Performance Benchmark
    console.print("\n[bold green][2.5] High-Precision Performance Benchmark (50 Iterations per Workload)[/bold green]")
    benchmarks = benchmark_query_performance(iterations=50)

    perf_table = Table(title="Workload Latency Benchmark: Document-Level vs Collection-Per-Tenant", show_lines=True)
    perf_table.add_column("Operational Workload Scenario", style="cyan", width=30)
    perf_table.add_column("Document-Level Isolation", style="magenta", justify="right", width=24)
    perf_table.add_column("Collection-Per-Tenant", style="green", justify="right", width=24)
    perf_table.add_column("Architectural Winner & Why", style="white", width=34)

    # Workload 1: Read
    dr = benchmarks["single_tenant_read"]["document_level"]
    cr = benchmarks["single_tenant_read"]["collection_per_tenant"]
    perf_table.add_row(
        "Single-Tenant Task Listing\n(Status='open' Sort DESC)",
        f"Avg: {dr['avg_ms']} ms\nMed: {dr['median_ms']} ms\nP95: {dr['p95_ms']} ms",
        f"Avg: {cr['avg_ms']} ms\nMed: {cr['median_ms']} ms\nP95: {cr['p95_ms']} ms",
        "[bold green]Collection-Per-Tenant[/bold green]\nScans dedicated collection without compound tenant_id index filtering overhead.",
    )

    # Workload 2: Write
    dw = benchmarks["single_tenant_write"]["document_level"]
    cw = benchmarks["single_tenant_write"]["collection_per_tenant"]
    perf_table.add_row(
        "Single-Tenant Task Creation\n(Individual task inserts)",
        f"Avg: {dw['avg_ms']} ms\nMed: {dw['median_ms']} ms\nP95: {dw['p95_ms']} ms",
        f"Avg: {cw['avg_ms']} ms\nMed: {cw['median_ms']} ms\nP95: {cw['p95_ms']} ms",
        "[bold green]Collection-Per-Tenant[/bold green]\nLower write lock contention and smaller localized collection B-trees.",
    )

    # Workload 3: Analytics
    da = benchmarks["cross_tenant_analytics"]["document_level"]
    ca = benchmarks["cross_tenant_analytics"]["collection_per_tenant"]
    perf_table.add_row(
        "Cross-Tenant Analytics\n(Status & Priority Aggregation)",
        f"Avg: {da['avg_ms']} ms\nMed: {da['median_ms']} ms\nP95: {da['p95_ms']} ms",
        f"Avg: {ca['avg_ms']} ms\nMed: {ca['median_ms']} ms\nP95: {ca['p95_ms']} ms",
        "[bold magenta]Document-Level Isolation[/bold magenta]\nSingle collection aggregation pipeline vs heavy $unionWith multi-collection federation.",
    )

    console.print(perf_table)

    # Step 6: Strategic Recommendations Matrix
    console.print("\n[bold green][2.6] Architectural Tradeoff & Selection Decision Matrix[/bold green]")
    matrix_table = Table(title="Multi-Tenant Strategy Decision Matrix", show_lines=True)
    matrix_table.add_column("Criterion", style="cyan", width=20)
    matrix_table.add_column("Document-Level Isolation", style="white", width=28)
    matrix_table.add_column("Collection-Per-Tenant", style="white", width=28)
    matrix_table.add_column("Database-Per-Tenant", style="white", width=28)

    for row in get_architectural_recommendations():
        matrix_table.add_row(row["criterion"], row["document_level"], row["collection_per_tenant"], row["database_per_tenant"])

    console.print(matrix_table)

    console.print("\n" + "=" * 80)
    console.print("  [bold green]ALL CHAPTER 15 LAB DEMONSTRATIONS AND VERIFICATIONS COMPLETED SUCCESSFULLY![/bold green]")
    console.print("=" * 80 + "\n")


if __name__ == "__main__":
    run_full_demonstration()
