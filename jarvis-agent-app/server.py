"""
J.A.R.V.I.S. Backend API Server
---------------------------------
FastAPI-based HTTP API for the Jarvis Agent system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import uuid
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engine import JarvisAgent
from modules.builtins import WeatherModule, DataAnalysisModule, SchedulerModule, FileModule, ReportModule

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis.api")

app = FastAPI(title="J.A.R.V.I.S. Agent API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global state ---
agent: Optional[JarvisAgent] = None
weather: Optional[WeatherModule] = None
data_analysis: Optional[DataAnalysisModule] = None
scheduler: Optional[SchedulerModule] = None
file_ops: Optional[FileModule] = None
report_gen: Optional[ReportModule] = None
sessions: Dict[str, JarvisAgent] = {}


# --- Pydantic models ---
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


# --- Initialization ---
@app.on_event("startup")
async def startup():
    global agent, weather, data_analysis, scheduler, file_ops, report_gen

    agent = JarvisAgent("JARVIS")

    # Register built-in modules as tools
    agent.execution.register_tool("weather", lambda city: asyncio.create_task(weather.get_weather(city)))
    agent.execution.register_tool("data_analyze", lambda name: asyncio.create_task(data_analysis.analyze(name)))
    agent.execution.register_tool("generate_data", lambda name, n=100: asyncio.create_task(data_analysis.generate_sample(name, n)))
    agent.execution.register_tool("create_task", lambda title, due_date, priority="medium": asyncio.create_task(scheduler.create_task(title, due_date, priority)))
    agent.execution.register_tool("list_tasks", lambda status=None: asyncio.create_task(scheduler.list_tasks(status)))
    agent.execution.register_tool("set_reminder", lambda message, delay_seconds=5: asyncio.create_task(scheduler.set_reminder(message, delay_seconds)))
    agent.execution.register_tool("create_file", lambda path, content="": asyncio.create_task(file_ops.create_file(path, content)))
    agent.execution.register_tool("read_file", lambda path: asyncio.create_task(file_ops.read_file(path)))
    agent.execution.register_tool("list_directory", lambda path: asyncio.create_task(file_ops.list_directory(path)))
    agent.execution.register_tool("generate_report", lambda title, sections="[]": asyncio.create_task(report_gen.generate_report(title, eval(sections))))
    agent.execution.register_tool("export_csv", lambda data="[]", filename="output.csv": asyncio.create_task(report_gen.export_csv(eval(data), filename)))
    agent.execution.register_tool("agent_chat", lambda msg: asyncio.create_task(agent.process(msg)))

    # Init modules
    global weather, data_analysis, scheduler, file_ops, report_gen
    weather = WeatherModule()
    data_analysis = DataAnalysisModule()
    scheduler = SchedulerModule()
    file_ops = FileModule()
    report_gen = ReportModule()

    logger.info("J.A.R.V.I.S. Agent initialized")


# --- API Endpoints ---
@app.get("/api/status")
async def get_status():
    return agent.get_status()


@app.post("/api/chat")
async def chat(req: ChatRequest):
    sid = req.session_id or agent.state.session_id
    response = await agent.process(req.message, req.modality)
    return {
        "session_id": sid,
        "timestamp": response["timestamp"],
        "output": response["reasoning"]["output"],
        "reasoning": response["reasoning"]["reasoning"],
    }


@app.post("/api/tool")
async def call_tool(req: ToolRequest):
    result = await agent.call_tool(req.tool, **req.args)
    return result


@app.get("/api/tools")
async def list_tools():
    return {"available_tools": agent.execution.tools.keys()}


@app.post("/api/scheduler/task")
async def create_scheduler_task(req: CreateTaskRequest):
    task = await scheduler.create_task(req.title, req.due_date, req.priority)
    return task


@app.get("/api/scheduler/tasks")
async def get_scheduler_tasks(status: str = None):
    tasks = await scheduler.list_tasks(status)
    stats = await scheduler.get_stats()
    return {"tasks": tasks, "stats": stats}


@app.post("/api/data/generate")
async def generate_data(req: GenerateDataRequest):
    result = await data_analysis.generate_sample(req.name, req.n)
    return result


@app.post("/api/data/analyze")
async def analyze_data(req: AnalyzeRequest):
    result = await data_analysis.analyze(req.dataset_name)
    return result


@app.post("/api/files/create")
async def create_file_endpoint(path: str, content: str = ""):
    result = await file_ops.create_file(path, content)
    return result


@app.get("/api/files/read")
async def read_file_endpoint(path: str):
    result = await file_ops.read_file(path)
    return result


@app.get("/api/memory/recent")
async def get_recent_memory(n: int = 10):
    return {"episodes": agent.memory.recall_recent(n)}


@app.get("/api/memory/user-profile")
async def get_user_profile():
    return agent.memory.get_user_profile()


@app.post("/api/memory/profile")
async def set_user_profile(key: str, value: Any):
    agent.add_user_preference(key, value)
    return {"status": "updated", "key": key, "value": value}


@app.post("/api/weather")
async def get_weather_endpoint(city: str):
    result = await weather.get_weather(city)
    return result


# --- Health check ---
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "J.A.R.V.I.S. Agent", "version": "0.1.0"}
