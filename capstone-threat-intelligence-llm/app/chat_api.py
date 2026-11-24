"""
app/chat_api.py
FastAPI Threat Intelligence Chat & Demonstration Application.
Extends Appendix A with:
- Multi-platform threat intelligence (Linux, Windows, MacOS, Android, iOS, Cloud)
- Threat lifecycle states (Anticipated, Active, Evolving, Resolved)
- RAG Vector retrieval with semantic embeddings
- Conversation memory in MongoDB 'sessions'
- Autonomous Vulnerability Scanner Bot with conversational confirmation
- Exercises 1 - 18 interactive demonstration endpoints
- Built-in static web UI mounting
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.database import get_db, is_mock_active
from app.threat_service import init_threat_database, get_threats, retrieve_threat_context, get_platform_threat_summary
from app.llm_engine import call_llm, LLM_BACKEND
from app.bot_service import bot_instance
import app.exercises_service as exercises

logger = logging.getLogger("chat_api")
logging.basicConfig(level=logging.INFO)

# --- Pydantic Schemas ---
class ChatRequest(BaseModel):
    session_id: str = Field(..., description="Unique user session ID")
    message: str = Field(..., description="User query or mitigation command")
    platform: Optional[str] = Field("All", description="Target platform filter")
    top_k: Optional[int] = Field(3, description="Number of vector context chunks to retrieve")

class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: List[Dict[str, Any]]
    platform: str
    latency_ms: float

class IngestDocument(BaseModel):
    title: str
    content: str
    platform: Optional[str] = "Generic"
    lifecycle_status: Optional[str] = "Active"

class IngestRequest(BaseModel):
    documents: List[IngestDocument]
    chunk_size: Optional[int] = 120

class IngestResponse(BaseModel):
    chunks_created: int
    message: str

class BotScanRequest(BaseModel):
    platform: str = "Windows"
    scope: str = "system"

class BotConfirmRequest(BaseModel):
    vuln_id: Optional[str] = None
    operator: Optional[str] = "SecOps_Analyst"

class HealthResponse(BaseModel):
    status: str
    database: str
    db_mode: str
    total_threats: int
    vector_chunks: int
    llm_backend: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and seed MongoDB collections and vector embeddings
    logger.info("Initializing Threat Intelligence system and database...")
    init_threat_database()
    yield
    logger.info("Threat Intelligence service shut down.")

app = FastAPI(
    title="Threat Intelligence LLM/SLM Platform",
    description="Cyber Threat Intelligence RAG Assistant with Autonomous Vulnerability Bot & Exercises 1-18 Suite",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health Check ---
@app.get("/health", response_model=HealthResponse)
async def health():
    db = get_db()
    try:
        total_threats = db["threats"].count_documents({})
        total_chunks = db["threat_chunks"].count_documents({})
        db_mode = "in-memory-mongomock" if is_mock_active() else "live-mongodb-replica-set"
        status = "healthy"
    except Exception as e:
        logger.error(f"Health check error: {e}")
        total_threats = 0
        total_chunks = 0
        db_mode = "error"
        status = "unhealthy"

    return HealthResponse(
        status=status,
        database="connected",
        db_mode=db_mode,
        total_threats=total_threats,
        vector_chunks=total_chunks,
        llm_backend=LLM_BACKEND
    )

# --- Threat Data Endpoints ---
@app.get("/threats")
async def list_threats(
    platform: Optional[str] = Query(None, description="Platform filter (Windows, Linux, MacOS, Android, iOS, Cloud)"),
    status: Optional[str] = Query(None, description="Lifecycle status filter (Anticipated, Active, Evolving, Resolved)"),
    severity: Optional[str] = Query(None, description="Severity filter (Critical, High, Medium, Low)")
):
    results = get_threats(platform=platform, lifecycle_status=status, severity=severity)
    return {"count": len(results), "threats": results}

@app.get("/threats/summary")
async def threat_summary():
    return get_platform_threat_summary()

@app.get("/threats/{threat_id}")
async def get_threat_detail(threat_id: str):
    db = get_db()
    threat = db["threats"].find_one({"threat_id": threat_id}, {"_id": 0})
    if not threat:
        raise HTTPException(status_code=404, detail=f"Threat ID '{threat_id}' not found.")
    return threat

# --- RAG Ingestion Endpoint ---
@app.post("/ingest", response_model=IngestResponse)
async def ingest_documents(req: IngestRequest):
    db = get_db()
    chunks_col = db["threat_chunks"]
    from app.vector_engine import chunk_text, generate_semantic_embedding

    created_count = 0
    new_chunks = []
    for doc in req.documents:
        raw_chunks = chunk_text(doc.content, chunk_size=req.chunk_size)
        for idx, text_chunk in enumerate(raw_chunks):
            emb = generate_semantic_embedding(text_chunk)
            new_chunks.append({
                "threat_id": f"INGEST-{int(time.time())}-{idx}",
                "title": doc.title,
                "platform": doc.platform,
                "lifecycle_status": doc.lifecycle_status,
                "chunk_index": idx,
                "text": text_chunk,
                "embedding": emb,
                "created_at": time.time()
            })
    if new_chunks:
        chunks_col.insert_many(new_chunks)
        created_count = len(new_chunks)

    return IngestResponse(
        chunks_created=created_count,
        message=f"Ingested {created_count} chunks from {len(req.documents)} documents."
    )

# --- Conversational RAG Chat Endpoint ---
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    start_time = time.perf_counter()
    db = get_db()

    # Check if the user is conversationally confirming a pending bot mitigation
    clean_msg = req.message.strip().lower()
    if any(k in clean_msg for k in ["yes", "approve", "confirm", "fix it", "mitigate", "proceed", "apply"]):
        bot_res = bot_instance.execute_confirmed_mitigation(operator="ChatUser")
        if bot_res.get("success"):
            confirmation_response = (
                f"### [BOT] Mitigation Confirmed & Executed\n\n"
                f"**Target:** `{bot_res['vuln_id']}` ({bot_res['platform']})\n"
                f"**Status:** State updated to `Resolved` in MongoDB.\n"
                f"**Audit Action:** Two-Phase ACID transaction logged in `audit_logs`.\n\n"
                f"Your security baseline is now hardened and compliant."
            )
            # Store in session
            db["sessions"].update_one(
                {"session_id": req.session_id},
                {"$push": {
                    "history": {
                        "$each": [
                            {"role": "user", "content": req.message},
                            {"role": "assistant", "content": confirmation_response}
                        ],
                        "$slice": -20
                    }
                }},
                upsert=True
            )
            elapsed = (time.perf_counter() - start_time) * 1000
            return ChatResponse(
                session_id=req.session_id,
                response=confirmation_response,
                sources=[],
                platform=req.platform or "All",
                latency_ms=round(elapsed, 2)
            )

    # 1. Retrieve relevant threat context via Vector Engine
    sources = retrieve_threat_context(
        query_str=req.message,
        top_k=req.top_k or 3,
        platform_filter=req.platform if req.platform != "All" else None
    )

    context_str = "\n".join(
        f"[{s['platform'].upper()} | {s['lifecycle_status']} | Score: {s['score']}] {s['title']}: {s['text']}"
        for s in sources
    )

    # 2. Retrieve multi-turn conversation memory from MongoDB
    session = db["sessions"].find_one({"session_id": req.session_id})
    history = session.get("history", []) if session else []

    # 3. Formulate augmented prompt & generate response
    prompt = f"Target Platform Filter: {req.platform}\nUser Question: {req.message}"
    response_text = call_llm(prompt, history[-4:], context=context_str)

    # 4. Save dialogue to MongoDB 'sessions' collection (Appendix A durability pattern)
    db["sessions"].update_one(
        {"session_id": req.session_id},
        {"$push": {
            "history": {
                "$each": [
                    {"role": "user", "content": req.message},
                    {"role": "assistant", "content": response_text}
                ],
                "$slice": -20
            }
        }},
        upsert=True
    )

    elapsed = (time.perf_counter() - start_time) * 1000
    return ChatResponse(
        session_id=req.session_id,
        response=response_text,
        sources=sources,
        platform=req.platform or "All",
        latency_ms=round(elapsed, 2)
    )

# --- Background Vulnerability Bot Endpoints ---
@app.post("/bot/scan")
async def bot_scan(req: BotScanRequest):
    result = bot_instance.scan_target(target_platform=req.platform, scope=req.scope)
    return result

@app.get("/bot/status")
async def bot_status():
    db = get_db()
    pending = list(db["pending_mitigations"].find({"status": "Pending_Confirmation"}, {"_id": 0}))
    return {
        "bot_online": True,
        "last_scan": bot_instance.last_scan_time,
        "pending_count": len(pending),
        "pending_mitigations": pending
    }

@app.post("/bot/confirm-mitigation")
async def bot_confirm(req: BotConfirmRequest):
    result = bot_instance.execute_confirmed_mitigation(vuln_id=req.vuln_id, operator=req.operator)
    return result

# --- Exercises 1 - 18 Demonstration Endpoints ---
@app.get("/exercises/run-all")
async def run_all_exercises_api():
    return exercises.run_all_exercises()

@app.post("/exercises/run/{exercise_id}")
async def run_single_exercise(exercise_id: int):
    func_name = f"run_exercise_{exercise_id}"
    if not hasattr(exercises, func_name):
        raise HTTPException(status_code=400, detail=f"Exercise {exercise_id} not found (must be 1-18).")
    runner = getattr(exercises, func_name)
    return runner()

# --- Serve Frontend Single-Page Application ---
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.chat_api:app", host="0.0.0.0", port=8000, reload=True)
