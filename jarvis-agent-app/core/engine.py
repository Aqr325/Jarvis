"""
J.A.R.V.I.S. Agent Core Engine
-------------------------------
The brain of the system. Coordinates perception, reasoning, execution, and memory.
"""

import json
import asyncio
import logging
import uuid
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Callable, Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jarvis.engine")


class AgentState:
    """Persistent agent state including identity, context, and session."""

    def __init__(self, name: str = "JARVIS"):
        self.name = name
        self.session_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now().isoformat()
        self.context: Dict[str, Any] = {}
        self.memory_index: List[str] = []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "context_keys": list(self.context.keys()),
            "memory_items": len(self.memory_index),
        }

    def update(self, key: str, value: Any):
        self.context[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.context.get(key, default)


class PerceptionModule:
    """Handles multimodal input capture and preprocessing."""

    def __init__(self):
        self.listeners: Dict[str, Callable] = {}
        self.buffer: deque = deque(maxlen=100)

    def register_listener(self, modality: str, handler: Callable):
        self.listeners[modality] = handler

    async def capture(self, raw_input: str, modality: str = "text") -> dict:
        self.buffer.append({"time": datetime.now().isoformat(), "raw": raw_input, "modality": modality})
        handler = self.listeners.get(modality)
        if handler:
            return await handler(raw_input)
        # Default: pass-through as text
        return {"raw": raw_input, "modality": modality, "preprocessed": True}


class MemoryManager:
    """Short-term working memory + long-term episodic memory."""

    def __init__(self, short_term_capacity: int = 50):
        self.short_buffer: deque = deque(maxlen=short_term_capacity)
        self.episodic_store: List[dict] = []
        self.user_profile: Dict[str, Any] = {}

    def add_episode(self, episode: dict):
        self.episodic_store.append(episode)
        self.short_buffer.append({"type": "episode", "data": episode, "time": datetime.now().isoformat()})

    def recall_recent(self, n: int = 10) -> List[dict]:
        return list(self.short_buffer)[-n:]

    def save_user_preference(self, key: str, value: Any):
        self.user_profile[key] = value

    def get_user_profile(self) -> dict:
        return dict(self.user_profile)


class ReasoningEngine:
    """Symbolic + neural hybrid reasoning module."""

    def __init__(self, llm_api_fn: Optional[Callable] = None):
        self.llm_fn = llm_api_fn
        self.rules: List[dict] = []
        self.knowledge_graph: Dict[str, List[str]] = {}

    def add_rule(self, condition: str, action: str):
        self.rules.append({"condition": condition, "action": action})

    def add_entity(self, entity: str, relations: List[str]):
        self.knowledge_graph[entity] = relations

    async def reason(self, query: str, context: Dict, memory: List[dict]) -> dict:
        if self.llm_fn:
            return await self.llm_fn(query, context, memory)
        # Fallback: rule-based simple matching
        for rule in self.rules:
            if rule["condition"].lower() in query.lower():
                return {"output": rule["action"], "reasoning": "rule-matched", "rule_id": self.rules.index(rule)}
        return {"output": f"I don't have enough information to answer '{query}'.", "reasoning": "default-fallback"}


class ExecutionModule:
    """Tool dispatcher, Agent orchestrator, API gateway."""

    def __init__(self):
        self.tools: Dict[str, Callable] = {}
        self.agent_registry: Dict[str, dict] = {}
        self.task_queue: deque = deque()

    def register_tool(self, name: str, fn: Callable):
        self.tools[name] = fn

    def register_agent(self, agent_name: str, config: dict):
        self.agent_registry[agent_name] = config

    async def execute_tool(self, tool_name: str, args: dict) -> dict:
        tool = self.tools.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found", "status": "error"}
        try:
            result = tool(**args)
            if asyncio.iscoroutine(result):
                result = await result
            return {"result": result, "tool": tool_name, "status": "success"}
        except Exception as e:
            return {"error": str(e), "tool": tool_name, "status": "error"}

    async def execute_task(self, task: dict) -> dict:
        self.task_queue.append(task)
        tool = task.get("tool", "")
        args = task.get("args", {})
        return await self.execute_tool(tool, args)


class JarvisAgent:
    """Main agent orchestrating all subsystems."""

    def __init__(self, name: str = "JARVIS"):
        self.state = AgentState(name)
        self.perception = PerceptionModule()
        self.memory = MemoryManager()
        self.reasoning = ReasoningEngine()
        self.execution = ExecutionModule()

    async def process(self, user_input: str, modality: str = "text") -> dict:
        logger.info(f"[Session {self.state.session_id}] Received input ({modality}): {user_input[:80]}...")

        # 1. Capture & Preprocess
        captured = await self.perception.capture(user_input, modality)

        # 2. Intent Understanding & Knowledge Retrieval
        memory_context = self.memory.recall_recent(5)
        context = {"user_context": self.state.to_dict(), "recent_memory": memory_context}

        # 3. Reasoning
        reasoning_result = await self.reasoning.reason(captured["raw"], context, memory_context)

        # 4. Build response
        response = {
            "query": captured["raw"],
            "modality": modality,
            "reasoning": reasoning_result,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.state.session_id,
        }

        # 5. Store in memory
        self.memory.add_episode(response)

        logger.info(f"[Session {self.state.session_id}] Response generated.")
        return response

    async def call_tool(self, tool: str, **kwargs) -> dict:
        return await self.execution.execute_tool(tool, kwargs)

    def add_user_preference(self, key: str, value: Any):
        self.memory.save_user_preference(key, value)

    def get_status(self) -> dict:
        return {
            "agent": self.state.name,
            "session": self.state.session_id,
            "memory_size": len(self.memory.episodic_store),
            "short_term_buffer": len(self.memory.short_buffer),
            "knowledge_graph_size": len(self.reasoning.knowledge_graph),
            "available_tools": list(self.execution.tools.keys()),
            "registered_agents": list(self.execution.agent_registry.keys()),
        }
