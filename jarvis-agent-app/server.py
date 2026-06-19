"""
J.A.R.V.I.S. Backend API Server
---------------------------------
FastAPI-based HTTP API for the Jarvis Agent system.
Enhanced with rate limiting, timeout control, and WebSocket support.
"""

import asyncio
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, List, Optional

import uvicorn
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engine import JarvisAgent
from core.rate_limiter import RateLimiter
from core.timeout import TimeoutManager, TimeoutMiddleware
from core.websocket_manager import WebSocketManager
from modules.builtins import (
    DataAnalysisModule,
    FileModule,
    ReportModule,
    SchedulerModule,
    WeatherModule,
)
from modules.nlp import nlp_processor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.api")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
agent: Optional[JarvisAgent] = None
weather: Optional[WeatherModule] = None
data_analysis: Optional[DataAnalysisModule] = None
scheduler: Optional[SchedulerModule] = None
file_ops: Optional[FileModule] = None
report_gen: Optional[ReportModule] = None

sessions: Dict[str, JarvisAgent] = {}
rate_limiter = RateLimiter()
timeout_manager = TimeoutManager()
timeout_middleware = TimeoutMiddleware(timeout_manager)
ws_manager = WebSocketManager()


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    modality: str = "text"
    session_id: Optional[str] = None


class ToolRequest(BaseModel):
    tool: str
    args: Dict[str, Any] = {}


class CreateTaskRequest(BaseModel):
    title: str
    due_date: str
    priority: str = "medium"


class AnalyzeRequest(BaseModel):
    dataset_name: str


class GenerateDataRequest(BaseModel):
    name: str
    n: int = 100


# ---------------------------------------------------------------------------
# Helpers – client ID extraction
# ---------------------------------------------------------------------------
def extract_client_id(request: Request) -> str:
    """Best-effort client identification."""
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host if request.client else "unknown"


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global agent, weather, data_analysis, scheduler, file_ops, report_gen

    agent = JarvisAgent("JARVIS")

    # Initialize modules BEFORE registering tools
    weather = WeatherModule()
    data_analysis = DataAnalysisModule()
    scheduler = SchedulerModule()
    file_ops = FileModule()
    report_gen = ReportModule()

    # Register built-in modules as tools
    agent.execution.register_tool(
        "weather", lambda city: weather.get_weather(city)
    )
    agent.execution.register_tool(
        "data_analyze",
        lambda name: data_analysis.analyze(name),
    )
    agent.execution.register_tool(
        "generate_data",
        lambda name, n=100: data_analysis.generate_sample(name, n),
    )
    agent.execution.register_tool(
        "create_task",
        lambda title, due_date, priority="medium": scheduler.create_task(
            title, due_date, priority
        ),
    )
    agent.execution.register_tool(
        "list_tasks",
        lambda status=None: scheduler.list_tasks(status),
    )
    agent.execution.register_tool(
        "set_reminder",
        lambda message, delay_seconds=5: scheduler.set_reminder(
            message, delay_seconds
        ),
    )
    agent.execution.register_tool(
        "create_file",
        lambda path, content="": file_ops.create_file(path, content),
    )
    agent.execution.register_tool(
        "read_file", lambda path: file_ops.read_file(path)
    )
    agent.execution.register_tool(
        "list_directory",
        lambda path: file_ops.list_directory(path),
    )
    agent.execution.register_tool(
        "generate_report",
        lambda title, sections=None: report_gen.generate_report(
            title, sections or []
        ),
    )
    agent.execution.register_tool(
        "export_csv",
        lambda data=None, filename="output.csv": report_gen.export_csv(
            data or [], filename
        ),
    )
    agent.execution.register_tool(
        "agent_chat", lambda msg: agent.process(msg)
    )

    logger.info("J.A.R.V.I.S. Agent initialized with middleware support")

    # Background task: periodic cleanup of stale rate-limit buckets
    cleanup_task = asyncio.create_task(_periodic_cleanup())
    yield
    cleanup_task.cancel()


async def _periodic_cleanup():
    """Background loop to clean expired rate-limit buckets."""
    while True:
        await asyncio.sleep(rate_limiter._cleanup_interval)
        await rate_limiter.cleanup_expired()
        await ws_manager.heartbeat_check()


app = FastAPI(
    title="J.A.R.V.I.S. Agent API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===================================================================
# Middleware helpers (used as decorators per endpoint)
# ===================================================================
def _classify_endpoint(path: str) -> str:
    """Map a request path to a rate-limit / timeout category key."""
    if "/ws" in path:
        return "ws"
    if "/chat" in path:
        return "chat"
    if "/tool" in path:
        return "tool"
    if "/data" in path:
        return "data"
    if "/weather" in path:
        return "weather"
    if "/scheduler" in path:
        return "scheduler"
    if "/memory" in path:
        return "memory"
    return "general"


# Helper used inside each endpoint handler
async def _check_rate_limit(client_id: str, endpoint: str, tokens: int = 1):
    """Raise 429 when rate limit exceeded."""
    result = rate_limiter.is_allowed(client_id, endpoint, tokens)
    if not result["allowed"]:
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": result["retry_after"],
                "remaining": result["remaining"],
            },
            headers={"Retry-After": str(int(result["retry_after"]))},
        )
    return result


async def _enforce_timeout(handler_coro, endpoint: str, client_id: str):
    """Wrap handler with timeout + circuit breaker."""
    try:
        return await timeout_manager.execute_with_timeout(
            handler_coro, endpoint, client_id
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "Gateway timeout",
                "endpoint": endpoint,
                "message": f"Service unavailable. Please try again later.",
            },
        )


# ===================================================================
# API Endpoints
# ===================================================================
@app.get("/api/status")
async def get_status(request: Request):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "general")
    return agent.get_status()


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    client_id = extract_client_id(request)
    category = _classify_endpoint("/api/chat")
    await _check_rate_limit(client_id, category)
    sid = req.session_id or agent.state.session_id

    handler = agent.process(req.message, req.modality)
    response = await _enforce_timeout(handler, category, client_id)

    return {
        "session_id": sid,
        "timestamp": response["timestamp"],
        "output": response["reasoning"]["output"],
        "reasoning": response["reasoning"]["reasoning"],
        "nlp": response["reasoning"].get("nlp_pipeline"),
    }


@app.post("/api/tool")
async def call_tool(req: ToolRequest, request: Request):
    client_id = extract_client_id(request)
    category = _classify_endpoint("/api/tool")
    await _check_rate_limit(client_id, category)

    handler = agent.call_tool(req.tool, **req.args)
    result = await _enforce_timeout(handler, category, client_id)
    return result


@app.get("/api/tools")
async def list_tools(request: Request):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "general")
    return {"available_tools": list(agent.execution.tools.keys())}


@app.post("/api/scheduler/task")
async def create_scheduler_task(
    req: CreateTaskRequest, request: Request
):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "scheduler")
    task = await scheduler.create_task(req.title, req.due_date, req.priority)
    return task


@app.get("/api/scheduler/tasks")
async def get_scheduler_tasks(
    status: Optional[str] = None, request: Request = None
):
    if request is None:
        raise HTTPException(status_code=400, detail="Request is required")
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "scheduler")
    tasks = await scheduler.list_tasks(status)
    stats = await scheduler.get_stats()
    return {"tasks": tasks, "stats": stats}


@app.post("/api/data/generate")
async def generate_data(req: GenerateDataRequest, request: Request):
    client_id = extract_client_id(request)
    category = _classify_endpoint("/api/data/generate")
    await _check_rate_limit(client_id, category)

    handler = data_analysis.generate_sample(req.name, req.n)
    result = await _enforce_timeout(handler, category, client_id)
    return result


@app.post("/api/data/analyze")
async def analyze_data(req: AnalyzeRequest, request: Request):
    client_id = extract_client_id(request)
    category = _classify_endpoint("/api/data/analyze")
    await _check_rate_limit(client_id, category)

    handler = data_analysis.analyze(req.dataset_name)
    result = await _enforce_timeout(handler, category, client_id)
    return result


@app.post("/api/files/create")
async def create_file_endpoint(
    path: str = Query(...),
    content: str = Query(""),
    request: Request = None,
):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "general")
    result = await file_ops.create_file(path, content)
    return result


@app.get("/api/files/read")
async def read_file_endpoint(
    path: str = Query(...), request: Request = None
):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "general")
    result = await file_ops.read_file(path)
    return result


@app.get("/api/memory/recent")
async def get_recent_memory(
    n: int = 10, request: Request = None
):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "memory")
    return {"episodes": agent.memory.recall_recent(n)}


@app.get("/api/memory/user-profile")
async def get_user_profile(request: Request = None):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "memory")
    return agent.memory.get_user_profile()


@app.post("/api/memory/profile")
async def set_user_profile(
    key: str = Query(...),
    value: Any = Query(...),
    request: Request = None,
):
    client_id = extract_client_id(request)
    await _check_rate_limit(client_id, "memory")
    agent.add_user_preference(key, value)
    return {"status": "updated", "key": key, "value": value}


@app.post("/api/weather")
async def get_weather_endpoint(city: str, request: Request):
    client_id = extract_client_id(request)
    category = _classify_endpoint("/api/weather")
    await _check_rate_limit(client_id, category)

    handler = weather.get_weather(city)
    result = await _enforce_timeout(handler, category, client_id)
    return result


# ===================================================================
# Circuit breaker status
# ===================================================================
@app.get("/api/admin/circuit-breaker")
async def get_circuit_breaker_status(endpoint: Optional[str] = None):
    if endpoint:
        return timeout_manager.get_circuit_status(endpoint)
    return {
        ep: timeout_manager.get_circuit_status(ep)
        for ep in timeout_manager.configs.keys()
    }


# ===================================================================
# WebSocket endpoint
# ===================================================================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    """Real-time bidirectional communication channel."""
    if not client_id:
        client_id = str(uuid.uuid4())[:8]

    await websocket.accept()
    registered_id = await ws_manager.connect(websocket, client_id)

    logger.info(f"WebSocket client connected: {registered_id}")

    try:
        while True:
            raw = await websocket.receive_text()
            ws_manager.connections[registered_id].heartbeat()

            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await ws_manager.send_to_client(
                    registered_id,
                    ws_manager.TYPE_ERROR,
                    {"message": "Invalid JSON payload"},
                )
                continue

            msg_type = data.get("type", "chat")
            payload = data.get("data", {})

            if msg_type == "chat":
                # Route through the agent with streaming support
                user_input = payload.get("message", "")
                session_id = payload.get("session_id", None)
                sid = session_id or agent.state.session_id

                await ws_manager.send_tool_progress(
                    registered_id, "agent", "processing", {"query": user_input}
                )

                # Non-streaming: get full response then send
                memory_context = agent.memory.recall_recent(5)
                context = {
                    "user_context": agent.state.to_dict(),
                    "recent_memory": memory_context,
                }

                if agent.reasoning.nlp:
                    nlp_result = await agent.reasoning.nlp.process(user_input)
                    intent_response = await agent.reasoning.nlp.generate_response(
                        nlp_result["intent"],
                        nlp_result["entities"],
                        nlp_result["sentiment"],
                        nlp_result["confidence"],
                    )
                    reasoning_detail = {
                        "output": intent_response["response"],
                        "reasoning": f"intent={nlp_result['intent']} (conf={nlp_result['confidence']:.2f})",
                        "nlp_pipeline": {
                            "intent": nlp_result["intent"],
                            "confidence": nlp_result["confidence"],
                            "entities": nlp_result["entities"],
                            "sentiment": nlp_result["sentiment"],
                            "action_needed": intent_response["action_needed"],
                        },
                    }
                else:
                    reasoning_detail = await agent.reasoning.reason(
                        user_input, context, memory_context
                    )

                response_obj = {
                    "query": user_input,
                    "modality": "websocket",
                    "reasoning": reasoning_detail,
                    "timestamp": datetime.now().isoformat(),
                    "session_id": sid,
                }
                agent.memory.add_episode(response_obj)

                # Stream the response text as typewriter
                response_text = reasoning_detail["output"]
                if response_text and len(response_text) > 20:
                    chunk_size = 10
                    chunks = [
                        response_text[i : i + chunk_size]
                        for i in range(0, len(response_text), chunk_size)
                    ]
                    await ws_manager.stream_response(
                        registered_id, chunks, delay=0.05
                    )
                else:
                    await ws_manager.send_to_client(
                        registered_id,
                        ws_manager.TYPE_CHAT_RESPONSE,
                        {
                            "partial": False,
                            "message": response_text,
                            "complete": True,
                        },
                    )

            elif msg_type == "tool_call":
                tool = payload.get("tool", "")
                tool_args = payload.get("args", {})
                await ws_manager.send_tool_progress(
                    registered_id, tool, "started", tool_args
                )
                result = await agent.call_tool(tool, **tool_args)
                await ws_manager.send_tool_progress(
                    registered_id,
                    tool,
                    "completed",
                    {"result": str(result)[:200]},
                )

            elif msg_type == "ping":
                await ws_manager.send_to_client(
                    registered_id,
                    ws_manager.TYPE_HEARTBEAT,
                    {"pong": True, "connections": ws_manager.get_connection_count()},
                )

            else:
                await ws_manager.send_to_client(
                    registered_id,
                    ws_manager.TYPE_NOTIFICATION,
                    {"message": f"Unknown message type: {msg_type}"},
                )

    except WebSocketDisconnect:
        await ws_manager.disconnect(registered_id)
        logger.info(f"WebSocket client disconnected: {registered_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {registered_id}: {e}")
        await ws_manager.send_to_client(
            registered_id,
            ws_manager.TYPE_ERROR,
            {"message": str(e)},
        )
        await ws_manager.disconnect(registered_id)


# ===================================================================
# Health check
# ===================================================================
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "J.A.R.V.I.S. Agent",
        "version": "0.2.0",
        "websocket_enabled": True,
        "rate_limiting": "active",
    }


# ===================================================================
# Static file catch-all — serves frontend for non-API routes
# ===================================================================
from pathlib import Path

_public_root = Path(__file__).resolve().parent / "public"


@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """Serve frontend static files. Only catches non-API paths."""
    # Skip API/ws paths — already handled by specific routes above
    if full_path.startswith(("api/", "api", "ws")):
        return JSONResponse({"error": "Not found"}, status_code=404)

    # Try exact file, root path, or SPA fallback to index.html
    candidate = _public_root / full_path if full_path else _public_root / "index.html"
    if candidate.is_file():
        return FileResponse(str(candidate))
    index = _public_root / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return JSONResponse({"error": "Not found"}, status_code=404)
