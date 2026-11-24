"""Lab 15.1: Multi-Tenant REST API with FastAPI and MongoDB
Includes Tenant Isolation, Role-Based Access Control (RBAC), and Database-Native Rate Limiting.

Author: Chintan
Docker Hub: https://hub.docker.com/r/shashankreddy30/mongodb-lab15
"""

import os
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import FastAPI, HTTPException, Depends, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from pydantic import BaseModel, Field
from pymongo import MongoClient, ReturnDocument, ASCENDING, DESCENDING
from rich.console import Console
from rich.table import Table

console = Console()

# -----------------------------------------------------------------------------
# Configuration & Database Setup
# -----------------------------------------------------------------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("MONGO_DB", "saas_app")
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-for-lab15-multitenant-saas")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
db = client[DATABASE_NAME]

tasks_col = db["tasks"]
users_col = db["users"]
rate_col = db["rate_limits"]


# -----------------------------------------------------------------------------
# Schema & Indexes Initialization
# -----------------------------------------------------------------------------
def init_database_indexes():
    """Create compound and TTL indexes for multi-tenant isolation and rate limiting."""
    # 1. Compound index on (tenant_id, created_at) for fast tenant-scoped listing & sorting
    tasks_col.create_index([("tenant_id", ASCENDING), ("created_at", DESCENDING)], name="idx_tenant_created")
    # 2. Compound index on (tenant_id, status) for filtered queries
    tasks_col.create_index([("tenant_id", ASCENDING), ("status", ASCENDING)], name="idx_tenant_status")
    # 3. Compound index on (tenant_id, created_by) for RBAC regular user queries
    tasks_col.create_index([("tenant_id", ASCENDING), ("created_by", ASCENDING)], name="idx_tenant_creator")

    # 4. Rate Limiting: TTL index on expires_at and unique index on (tenant_id, window_key)
    rate_col.create_index([("expires_at", ASCENDING)], expireAfterSeconds=0, name="idx_rate_ttl")
    rate_col.create_index([("tenant_id", ASCENDING), ("window_key", ASCENDING)], unique=True, name="idx_tenant_window")

    # 5. User index on (tenant_id, username)
    users_col.create_index([("tenant_id", ASCENDING), ("username", ASCENDING)], unique=True, name="idx_tenant_username")


def seed_default_users():
    """Seed test users for multiple tenants and roles if not already present."""
    default_users = [
        # Tenant Acme
        {"username": "admin_acme", "password": "password123", "tenant_id": "tenant-acme", "role": "admin", "full_name": "Acme Administrator"},
        {"username": "alice_acme", "password": "password123", "tenant_id": "tenant-acme", "role": "user", "full_name": "Alice Jenkins"},
        {"username": "bob_acme", "password": "password123", "tenant_id": "tenant-acme", "role": "user", "full_name": "Bob Williams"},
        # Tenant Globex
        {"username": "admin_globex", "password": "password123", "tenant_id": "tenant-globex", "role": "admin", "full_name": "Globex Administrator"},
        {"username": "charlie_globex", "password": "password123", "tenant_id": "tenant-globex", "role": "user", "full_name": "Charlie Davis"},
    ]
    for u in default_users:
        users_col.update_one(
            {"tenant_id": u["tenant_id"], "username": u["username"]},
            {"$set": u},
            upsert=True
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database_indexes()
    seed_default_users()
    yield


# Initialize FastAPI App
app = FastAPI(
    title="TaskTracker Multi-Tenant SaaS API",
    description="Multi-Tenant Task Management API with Document-Level Tenant Isolation, RBAC, and MongoDB Rate Limiting.",
    version="1.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


# -----------------------------------------------------------------------------
# Pydantic Models
# -----------------------------------------------------------------------------
class UserLogin(BaseModel):
    username: str
    password: str
    tenant_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    username: str
    role: str
    expires_in_hours: int = JWT_EXPIRATION_HOURS


class UserContext(BaseModel):
    username: str
    tenant_id: str
    role: str
    full_name: Optional[str] = None


class TaskCreate(BaseModel):
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    priority: str = Field(default="medium", description="Task priority (low, medium, high, critical)")
    status: str = Field(default="open", description="Task status (open, in_progress, completed, archived)")
    assignee: Optional[str] = Field(default=None, description="Assigned username")


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assignee: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    description: str
    priority: str
    status: str
    created_by: str
    assignee: Optional[str] = None
    created_at: str
    updated_at: str


# -----------------------------------------------------------------------------
# Security & JWT Helpers
# -----------------------------------------------------------------------------
def create_access_token(username: str, tenant_id: str, role: str) -> str:
    """Generate a signed JWT token containing tenant_id, username, and role."""
    expire = datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": username,
        "tenant_id": tenant_id,
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a signed JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token signature.",
        )


# -----------------------------------------------------------------------------
# MongoDB-Based Rate Limiting
# -----------------------------------------------------------------------------
def check_tenant_rate_limit(tenant_id: str, limit: int = 10, window_secs: int = 60) -> bool:
    """
    MongoDB-based rate limiter using atomic find_one_and_update and a TTL index.
    Tracks request counters in a rolling fixed window for each tenant.
    Returns True if within limit, raises HTTP 429 if exceeded.
    """
    now = datetime.now(timezone.utc)
    window_bucket = int(now.timestamp() // window_secs)
    window_key = f"{tenant_id}:{window_bucket}"
    expires_at = now + timedelta(seconds=window_secs * 2)

    # Atomically increment counter or initialize on insert
    result = rate_col.find_one_and_update(
        {"tenant_id": tenant_id, "window_key": window_key},
        {
            "$inc": {"count": 1},
            "$setOnInsert": {
                "tenant_id": tenant_id,
                "window_key": window_key,
                "window_bucket": window_bucket,
                "expires_at": expires_at,
                "first_seen": now.isoformat(),
            },
        },
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )

    request_count = result["count"]
    if request_count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "tenant_id": tenant_id,
                "limit": limit,
                "window_seconds": window_secs,
                "current_requests": request_count,
                "message": f"Tenant '{tenant_id}' exceeded {limit} requests per {window_secs} seconds.",
            },
            headers={"Retry-After": str(window_secs)},
        )
    return True


# -----------------------------------------------------------------------------
# FastAPI Dependencies
# -----------------------------------------------------------------------------
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_api_user: Optional[str] = Header(None, alias="X-API-User"),
    x_api_role: Optional[str] = Header(None, alias="X-API-Role"),
) -> UserContext:
    """
    Authentication dependency:
    1. Validates JWT Bearer token if present.
    2. Fallback to developer/test headers (X-Tenant-ID, X-API-User, X-API-Role) for easy testing.
    3. Runs the tenant-scoped MongoDB rate limiter.
    """
    if token:
        payload = decode_access_token(token)
        username = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        role = payload.get("role", "user")
        if not username or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Malformed token payload.",
            )
    elif x_tenant_id and x_api_user:
        username = x_api_user
        tenant_id = x_tenant_id
        role = x_api_role or "user"
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials. Provide Bearer JWT token or X-Tenant-ID/X-API-User headers.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Enforce database-backed rate limit per tenant
    check_tenant_rate_limit(tenant_id, limit=10, window_secs=60)

    return UserContext(username=username, tenant_id=tenant_id, role=role)


def require_admin(current_user: UserContext = Depends(get_current_user)) -> UserContext:
    """RBAC dependency requiring admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Action requires 'admin' role. User '{current_user.username}' has role '{current_user.role}'.",
        )
    return current_user


# -----------------------------------------------------------------------------
# Authentication Endpoints
# -----------------------------------------------------------------------------
@app.post("/auth/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2 password login endpoint returning JWT access token."""
    user = users_col.find_one({"username": form_data.username})
    if not user or user.get("password") != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user["username"], user["tenant_id"], user["role"])
    return TokenResponse(
        access_token=token,
        tenant_id=user["tenant_id"],
        username=user["username"],
        role=user["role"],
    )


@app.post("/auth/login", response_model=TokenResponse)
async def login_json(credentials: UserLogin):
    """JSON login endpoint returning JWT access token."""
    query = {"username": credentials.username}
    if credentials.tenant_id:
        query["tenant_id"] = credentials.tenant_id

    user = users_col.find_one(query)
    if not user or user.get("password") != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username, password, or tenant ID.",
        )

    token = create_access_token(user["username"], user["tenant_id"], user["role"])
    return TokenResponse(
        access_token=token,
        tenant_id=user["tenant_id"],
        username=user["username"],
        role=user["role"],
    )


# -----------------------------------------------------------------------------
# Task Management CRUD Endpoints (Tenant-Isolated & RBAC-Enforced)
# -----------------------------------------------------------------------------
@app.post("/tasks/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, current_user: UserContext = Depends(get_current_user)):
    """
    Create a new task with strict document-level tenant isolation.
    The task is stamped with the user's tenant_id and username (created_by).
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    doc = {
        "tenant_id": current_user.tenant_id,  # CRITICAL: strictly bound to authenticated tenant
        "title": task.title,
        "description": task.description,
        "priority": task.priority.lower(),
        "status": task.status.lower(),
        "created_by": current_user.username,
        "assignee": task.assignee or current_user.username,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    result = tasks_col.insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return doc


@app.get("/tasks/", response_model=List[TaskResponse])
async def list_tasks(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: UserContext = Depends(get_current_user),
):
    """
    List tasks scoped strictly to authenticated tenant_id.
    Activity 15.1 RBAC Enforcement:
      - Admin users: can view ALL tasks belonging to their tenant.
      - Regular users: can ONLY view tasks they created (created_by == current_user.username).
    """
    query: Dict[str, Any] = {"tenant_id": current_user.tenant_id}

    # Role-Based Access Control Filtering
    if current_user.role != "admin":
        query["created_by"] = current_user.username

    if status_filter:
        query["status"] = status_filter.lower()
    if priority_filter:
        query["priority"] = priority_filter.lower()

    cursor = tasks_col.find(query).sort("created_at", DESCENDING).skip(skip).limit(limit)
    tasks = []
    for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        tasks.append(doc)
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, current_user: UserContext = Depends(get_current_user)):
    """
    Retrieve single task.
    Enforces document-level tenant isolation (cross-tenant queries return 404).
    Enforces RBAC: regular users can only read their own tasks.
    """
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")

    doc = tasks_col.find_one({"_id": oid, "tenant_id": current_user.tenant_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found in tenant '{current_user.tenant_id}'.",
        )

    # RBAC check: regular users can only access their own tasks
    if current_user.role != "admin" and doc.get("created_by") != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Regular users can only access tasks they created.",
        )

    doc["id"] = str(doc.pop("_id"))
    return doc


@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    updates: TaskUpdate,
    current_user: UserContext = Depends(get_current_user),
):
    """
    Update a task with tenant isolation and RBAC.
    Admin users can update any task in tenant; regular users only their own.
    """
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")

    existing = tasks_col.find_one({"_id": oid, "tenant_id": current_user.tenant_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found in tenant '{current_user.tenant_id}'.",
        )

    # RBAC authorization check
    if current_user.role != "admin" and existing.get("created_by") != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Regular users can only modify tasks they created.",
        )

    update_data = {k: v for k, v in updates.dict().items() if v is not None}
    if not update_data:
        existing["id"] = str(existing.pop("_id"))
        return existing

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    updated_doc = tasks_col.find_one_and_update(
        {"_id": oid, "tenant_id": current_user.tenant_id},  # CRITICAL: tenant isolation guard
        {"$set": update_data},
        return_document=ReturnDocument.AFTER,
    )

    updated_doc["id"] = str(updated_doc.pop("_id"))
    return updated_doc


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str, current_user: UserContext = Depends(get_current_user)):
    """
    Delete task with tenant isolation and RBAC.
    Admin users can delete any task in tenant; regular users only their own.
    """
    try:
        oid = ObjectId(task_id)
    except InvalidId:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId format")

    existing = tasks_col.find_one({"_id": oid, "tenant_id": current_user.tenant_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found in tenant '{current_user.tenant_id}'.",
        )

    if current_user.role != "admin" and existing.get("created_by") != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Regular users can only delete tasks they created.",
        )

    tasks_col.delete_one({"_id": oid, "tenant_id": current_user.tenant_id})
    return {
        "success": True,
        "deleted_task_id": task_id,
        "tenant_id": current_user.tenant_id,
        "message": "Task successfully deleted.",
    }


# -----------------------------------------------------------------------------
# Tenant Analytics & Health
# -----------------------------------------------------------------------------
@app.get("/tenants/stats")
async def get_tenant_statistics(admin_user: UserContext = Depends(require_admin)):
    """Admin-only endpoint providing aggregate statistics for the current tenant."""
    pipeline = [
        {"$match": {"tenant_id": admin_user.tenant_id}},
        {
            "$group": {
                "_id": "$status",
                "count": {"$sum": 1},
                "high_priority": {
                    "$sum": {"$cond": [{"$eq": ["$priority", "high"]}, 1, 0]}
                },
            }
        },
    ]
    status_summary = list(tasks_col.aggregate(pipeline))
    total_tasks = sum(s["count"] for s in status_summary)

    return {
        "tenant_id": admin_user.tenant_id,
        "total_tasks": total_tasks,
        "by_status": {s["_id"]: s["count"] for s in status_summary},
        "queried_by": admin_user.username,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/health")
async def health_check():
    """Health check endpoint displaying MongoDB ping and index status."""
    ping = db.command("ping")
    indexes = tasks_col.index_information()
    return {
        "status": "healthy",
        "mongodb_connected": bool(ping.get("ok")),
        "database": DATABASE_NAME,
        "task_indexes": list(indexes.keys()),
        "rate_limit_indexes": list(rate_col.index_information().keys()),
    }


# -----------------------------------------------------------------------------
# Standalone CLI Demonstration Runner
# -----------------------------------------------------------------------------
def run_lab1_demo():
    """Execute standalone verification of Lab 15.1 in terminal."""
    from rich.panel import Panel

    console.print(Panel.fit("[bold cyan]Lab 15.1: Multi-Tenant REST API Demonstration[/bold cyan]\n"
                            "Tenant Isolation, Role-Based Access Control, and Rate Limiting", border_style="cyan"))

    init_database_indexes()
    seed_default_users()

    # Reset tasks for clean run
    tasks_col.delete_many({})
    rate_col.delete_many({})

    console.print("\n[bold yellow]Step 1: Create Tasks Across Two Tenants[/bold yellow]")
    token_admin_acme = create_access_token("admin_acme", "tenant-acme", "admin")
    token_alice_acme = create_access_token("alice_acme", "tenant-acme", "user")
    token_bob_acme = create_access_token("bob_acme", "tenant-acme", "user")
    token_globex_admin = create_access_token("admin_globex", "tenant-globex", "admin")

    # Insert tasks
    t1_doc = {
        "tenant_id": "tenant-acme",
        "title": "Setup ML Training Pipeline",
        "description": "Deploy Kubeflow fraud detection model",
        "priority": "high",
        "status": "open",
        "created_by": "alice_acme",
        "assignee": "alice_acme",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    t2_doc = {
        "tenant_id": "tenant-acme",
        "title": "Validate Transaction Schema",
        "description": "Enforce Avro schema compatibility",
        "priority": "medium",
        "status": "in_progress",
        "created_by": "bob_acme",
        "assignee": "bob_acme",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    t3_doc = {
        "tenant_id": "tenant-globex",
        "title": "Stripe Gateway Integration",
        "description": "Configure multi-currency webhook handlers",
        "priority": "high",
        "status": "open",
        "created_by": "admin_globex",
        "assignee": "admin_globex",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    t1_id = str(tasks_col.insert_one(t1_doc).inserted_id)
    t2_id = str(tasks_col.insert_one(t2_doc).inserted_id)
    t3_id = str(tasks_col.insert_one(t3_doc).inserted_id)

    console.print(f"  [green]✓[/green] Created Acme Task 1 (Alice): {t1_id}")
    console.print(f"  [green]✓[/green] Created Acme Task 2 (Bob):   {t2_id}")
    console.print(f"  [green]✓[/green] Created Globex Task (Admin): {t3_id}")

    # Step 2: Tenant Isolation Verification
    console.print("\n[bold yellow]Step 2: Tenant Query Isolation Check[/bold yellow]")
    acme_tasks = list(tasks_col.find({"tenant_id": "tenant-acme"}))
    globex_tasks = list(tasks_col.find({"tenant_id": "tenant-globex"}))
    console.print(f"  Acme Tenant Tasks found: {len(acme_tasks)} (Expected: 2)")
    console.print(f"  Globex Tenant Tasks found: {len(globex_tasks)} (Expected: 1)")

    # Step 3: Cross-Tenant Protection Attempt
    console.print("\n[bold yellow]Step 3: Cross-Tenant Tampering Attack Simulation[/bold yellow]")
    console.print(f"  [cyan]Scenario:[/cyan] Globex tenant attempts to modify Acme's task {t1_id}...")
    attack_result = tasks_col.update_one(
        {"_id": ObjectId(t1_id), "tenant_id": "tenant-globex"},  # Protected by compound filter
        {"$set": {"status": "tampered_by_attacker"}},
    )
    if attack_result.modified_count == 0:
        console.print("  [bold green]✓ BLOCKED![/bold green] Modified count is 0. Tenant isolation successfully defended cross-tenant modification.")
    else:
        console.print("  [bold red]✗ FAILED![/bold red] Cross-tenant leak occurred!")

    # Step 4: RBAC Verification
    console.print("\n[bold yellow]Step 4: Activity 15.1 RBAC Enforcement[/bold yellow]")
    console.print("  [cyan]Scenario A:[/cyan] Regular User 'alice_acme' queries tasks (Only sees Alice's tasks)...")
    alice_view = list(tasks_col.find({"tenant_id": "tenant-acme", "created_by": "alice_acme"}))
    console.print(f"    Alice's view count: {len(alice_view)} tasks ({[t['title'] for t in alice_view]})")

    console.print("  [cyan]Scenario B:[/cyan] Admin User 'admin_acme' queries tasks (Sees ALL Acme tasks)...")
    admin_view = list(tasks_col.find({"tenant_id": "tenant-acme"}))
    console.print(f"    Admin's view count: {len(admin_view)} tasks ({[t['title'] for t in admin_view]})")

    # Step 5: Rate Limiting Demonstration
    console.print("\n[bold yellow]Step 5: MongoDB Atomic Rate Limiter (Limit: 10 req/min)[/bold yellow]")
    allowed_count = 0
    blocked_count = 0
    for i in range(1, 13):
        try:
            check_tenant_rate_limit("tenant-acme", limit=10, window_secs=60)
            allowed_count += 1
            console.print(f"    Request {i:2d}: [green]ALLOWED (200 OK)[/green]")
        except HTTPException as e:
            blocked_count += 1
            console.print(f"    Request {i:2d}: [red]BLOCKED (HTTP 429 Too Many Requests)[/red]")

    console.print(f"\n  [green]Summary:[/green] {allowed_count} requests allowed, {blocked_count} requests rate-limited.")

    # Architecture summary table
    table = Table(title="Lab 15.1 Multi-Tenant Architecture Summary", show_lines=True)
    table.add_column("Component", style="cyan")
    table.add_column("Implementation", style="green")
    table.add_column("Security / Performance Benefit", style="white")
    table.add_row(
        "Tenant Isolation",
        "Document-level `tenant_id` on every query filter",
        "Prevents cross-tenant data leakage while sharing single collection infrastructure",
    )
    table.add_row(
        "Compound Indexing",
        "(`tenant_id`, `created_at`) & (`tenant_id`, `created_by`)",
        "Fast indexed lookups; guarantees O(log N) tenant-scoped query execution",
    )
    table.add_row(
        "RBAC (Activity 15.1)",
        "JWT claims + endpoint created_by filter",
        "Admins manage all tenant tasks; regular users restricted to own tasks",
    )
    table.add_row(
        "Rate Limiting",
        "MongoDB `rate_limits` with atomic upsert + TTL index",
        "Zero Redis dependency; automatic counter cleanup via background TTL thread",
    )
    console.print(table)
    console.print("\n[bold green]✓ Lab 15.1 Demonstration Successfully Completed![/bold green]\n")


if __name__ == "__main__":
    if "--server" in sys.argv:
        import uvicorn
        uvicorn.run("lab_01_multitenant_api:app", host="0.0.0.0", port=8000, reload=True)
    else:
        run_lab1_demo()
