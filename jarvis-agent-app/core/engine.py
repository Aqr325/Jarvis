"""
J.A.R.V.I.S. Agent Core Engine
-------------------------------
The brain of the system. Coordinates perception, reasoning, execution, and memory.
Enhanced with state-machine decision routing, multi-step reasoning chains,
and context-window management.
"""

import asyncio
import json
import logging
import uuid
from enum import Enum
from pathlib import Path
from datetime import datetime
from collections import deque
from typing import Callable, Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("jarvis.engine")


# ===================================================================
# Enums & Data Classes
# ===================================================================
class AgentStateStatus(str, Enum):
    IDLE = "idle"
    PERCEIVING = "perceiving"
    REASONING = "reasoning"
    EXECUTING = "executing"
    REMEMBERING = "remembering"
    ERROR = "error"


class DecisionStrategy(str, Enum):
    NLP_ROUTE = "nlp_route"
    STATE_MACHINE = "state_machine"
    MULTI_STEP = "multi_step"
    RULE_BASED = "rule_based"
    FALLBACK = "fallback"


class ReasoningStep:
    """A single step in a multi-step reasoning chain."""

    def __init__(self, step_type: str, description: str, result: Any = None):
        self.step_type = step_type
        self.description = description
        self.result = result
        self.timestamp = datetime.now().isoformat()
        self.success = result is not None and not isinstance(result, dict) or (
            isinstance(result, dict) and "error" not in result
        )

    def to_dict(self) -> dict:
        return {
            "step_type": self.step_type,
            "description": self.description,
            "result": self.result if not isinstance(self.result, (dict, list)) else str(self.result)[:300],
            "timestamp": self.timestamp,
            "success": self.success,
        }


# ===================================================================
# State Machine
# ===================================================================
class DecisionStateMachine:
    """
    Finite-state decision router.
    States: IDLE -> PERCEIVING -> REASONING -> EXECUTING -> REMEMBERING -> IDLE
    
    Transitions are driven by intent classification results.
    """

    # Transitions: (current_state, event) -> next_state
    TRANSITIONS = {
        (AgentStateStatus.IDLE, "input_received"): AgentStateStatus.PERCEIVING,
        (AgentStateStatus.PERCEIVING, "intent_classified"): AgentStateStatus.REASONING,
        (AgentStateStatus.REASONING, "decision_made"): AgentStateStatus.EXECUTING,
        (AgentStateStatus.EXECUTING, "tool_completed"): AgentStateStatus.REMEMBERING,
        (AgentStateStatus.EXECUTING, "needs_more_reasoning"): AgentStateStatus.REASONING,
        (AgentStateStatus.REMEMBERING, "storage_complete"): AgentStateStatus.IDLE,
        (AgentStateStatus.IDLE, "error_occurred"): AgentStateStatus.ERROR,
        (AgentStateStatus.PERCEIVING, "error_occurred"): AgentStateStatus.ERROR,
        (AgentStateStatus.REASONING, "error_occurred"): AgentStateStatus.ERROR,
        (AgentStateStatus.EXECUTING, "error_occurred"): AgentStateStatus.ERROR,
        (AgentStateStatus.REMEMBERING, "error_occurred"): AgentStateStatus.ERROR,
        (AgentStateStatus.ERROR, "recovery_attempted"): AgentStateStatus.IDLE,
    }

    def __init__(self):
        self.current_state = AgentStateStatus.IDLE
        self.state_history: List[dict] = [
            {"state": self.current_state.value, "at": datetime.now().isoformat()}
        ]

    def transition(self, event: str) -> bool:
        """Attempt state transition. Returns True if successful."""
        key = (self.current_state, event)
        next_state = self.TRANSITIONS.get(key)
        if next_state:
            old_state = self.current_state
            self.current_state = next_state
            self.state_history.append(
                {
                    "from": old_state.value,
                    "event": event,
                    "to": next_state.value,
                    "at": datetime.now().isoformat(),
                }
            )
            logger.debug(
                "State transition: %s -> %s (event=%s)",
                old_state.value, next_state.value, event,
            )
            return True
        logger.warning(
            "Invalid transition: state=%s, event=%s", self.current_state, event
        )
        return False

    def can_transition(self, event: str) -> bool:
        return (self.current_state, event) in self.TRANSITIONS

    def get_status(self) -> dict:
        return {
            "current_state": self.current_state.value,
            "history_length": len(self.state_history),
            "last_states": self.state_history[-5:],
        }


# ===================================================================
# Context Window Manager
# ===================================================================
class ContextWindowManager:
    """
    Manages the agent's working context window with sliding-window
    semantics and relevance-based summarization.
    """

    def __init__(self, max_tokens: int = 4000, max_messages: int = 50):
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.message_buffer: deque = deque(maxlen=max_messages)
        self._token_estimator = lambda text: max(1, len(text) // 4)

    def add_message(self, role: str, content: str, metadata: dict = None):
        msg = {
            "role": role,
            "content": content,
            "tokens": self._token_estimator(content),
            "time": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.message_buffer.append(msg)
        self._trim_if_needed()

    def get_context(self) -> List[dict]:
        """Return the current context window."""
        return list(self.message_buffer)

    def get_summary(self) -> str:
        """Return a summary of recent conversation."""
        if not self.message_buffer:
            return "No conversation history."
        recent = list(self.message_buffer)[-10:]
        parts = []
        for msg in recent:
            role_label = msg["role"].upper()
            snippet = msg["content"][:100]
            parts.append(f"[{role_label}] {snippet}")
        return "\n".join(parts)

    def _trim_if_needed(self):
        """Remove oldest messages if token limit exceeded."""
        total_tokens = sum(m["tokens"] for m in self.message_buffer)
        while total_tokens > self.max_tokens and len(self.message_buffer) > 1:
            removed = self.message_buffer.popleft()
            total_tokens -= removed["tokens"]

    def get_relevant_memory(self, query: str, n: int = 5) -> List[dict]:
        """Simple keyword-based relevance retrieval."""
        query_words = set(query.lower().split())
        scored: List[tuple] = []
        for msg in self.message_buffer:
            score = len(query_words & set(msg["content"].lower().split()))
            if score > 0:
                scored.append((score, msg))
        scored.sort(key=lambda x: -x[0])
        return [m for _, m in scored[:n]]


# ===================================================================
# AgentState
# ===================================================================
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


# ===================================================================
# PerceptionModule
# ===================================================================
class PerceptionModule:
    """Handles multimodal input capture and preprocessing."""

    def __init__(self):
        self.listeners: Dict[str, Callable] = {}
        self.buffer: deque = deque(maxlen=100)

    def register_listener(self, modality: str, handler: Callable):
        self.listeners[modality] = handler

    async def capture(self, raw_input: str, modality: str = "text") -> dict:
        self.buffer.append(
            {
                "time": datetime.now().isoformat(),
                "raw": raw_input,
                "modality": modality,
            }
        )
        handler = self.listeners.get(modality)
        if handler:
            return await handler(raw_input)
        return {"raw": raw_input, "modality": modality, "preprocessed": True}


# ===================================================================
# MemoryManager
# ===================================================================
class MemoryManager:
    """Short-term working memory + long-term episodic memory."""

    def __init__(self, short_term_capacity: int = 50):
        self.short_buffer: deque = deque(maxlen=short_term_capacity)
        self.episodic_store: List[dict] = []
        self.user_profile: Dict[str, Any] = {}

    def add_episode(self, episode: dict):
        self.episodic_store.append(episode)
        self.short_buffer.append(
            {
                "type": "episode",
                "data": episode,
                "time": datetime.now().isoformat(),
            }
        )

    def recall_recent(self, n: int = 10) -> List[dict]:
        return list(self.short_buffer)[-n:]

    def save_user_preference(self, key: str, value: Any):
        self.user_profile[key] = value

    def get_user_profile(self) -> dict:
        return dict(self.user_profile)


# ===================================================================
# ReasoningEngine (State Machine + Multi-Step)
# ===================================================================
class ReasoningEngine:
    """
    Symbolic + neural hybrid reasoning module with:
    - State-machine decision routing
    - Multi-step reasoning chains
    - Context-window management
    - NLP integration for intelligent intent classification
    """

    def __init__(self, llm_api_fn: Optional[Callable] = None):
        self.llm_fn = llm_api_fn
        self.rules: List[dict] = []
        self.knowledge_graph: Dict[str, List[str]] = {}
        self._nlp_processor = None
        self.state_machine = DecisionStateMachine()
        self.context_window = ContextWindowManager()
        self._reasoning_chain: List[ReasoningStep] = []

    @property
    def nlp(self):
        if self._nlp_processor is None:
            try:
                from modules.nlp import nlp_processor
                self._nlp_processor = nlp_processor
            except ImportError:
                self._nlp_processor = None
        return self._nlp_processor

    def add_rule(self, condition: str, action: str):
        self.rules.append({"condition": condition, "action": action})

    def add_entity(self, entity: str, relations: List[str]):
        self.knowledge_graph[entity] = relations

    def _reset_chain(self):
        self._reasoning_chain = []

    def _add_step(self, step_type: str, description: str, result: Any = None):
        step = ReasoningStep(step_type, description, result)
        self._reasoning_chain.append(step)

    async def _nlp_route(self, query: str, context: Dict, memory: List[dict]) -> dict:
        """Route based on NLP intent classification."""
        self._add_step("nlp_process", "Running NLP pipeline")

        nlp_result = await self.nlp.process(query)
        intent = nlp_result["intent"]
        entities = nlp_result["entities"]
        sentiment = nlp_result["sentiment"]
        confidence = nlp_result["confidence"]

        self._add_step(
            "intent_classification",
            f"Intent: {intent}",
            {"confidence": confidence},
        )

        intent_response = await self.nlp.generate_response(
            intent, entities, sentiment, confidence
        )
        self._add_step(
            "response_generation",
            "Generated response via NLP",
            {"action_needed": intent_response["action_needed"]},
        )

        return {
            "output": intent_response["response"],
            "reasoning": f"intent={intent} (conf={confidence:.2f})",
            "nlp_pipeline": {
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "sentiment": sentiment,
                "action_needed": intent_response["action_needed"],
            },
        }

    async def _state_machine_route(
        self, query: str, context: Dict, memory: List[dict], nlp_result: dict
    ) -> dict:
        """Use state machine for structured decision routing."""
        # Transition: IDLE -> PERCEIVING
        self.state_machine.transition("input_received")
        self._add_step("state_transition", "IDLE -> PERCEIVING", "input_received")

        # Transition: PERCEIVING -> REASONING
        intent = nlp_result["intent"]
        confidence = nlp_result["confidence"]
        self.state_machine.transition("intent_classified")
        self._add_step(
            "state_transition",
            "PERCEIVING -> REASONING",
            f"intent={intent} conf={confidence:.2f}",
        )

        # State-machine rules for complex decisions
        # Rule: tool_call intents should trigger EXECUTION then loop back to REASONING
        tool_call_intents = {
            "weather_query",
            "task_create",
            "task_list",
            "file_create",
            "file_read",
            "data_analyze",
            "data_generate",
            "report_generate",
            "export_csv",
        }

        if intent in tool_call_intents:
            self._add_step(
                "decision_routing",
                f"Tool call detected: {intent} -> EXECUTING",
            )
            self.state_machine.transition("decision_made")
            return {
                "output": f"Routing to tool execution for intent: {intent}",
                "reasoning": f"state_machine:{intent}",
                "action_needed": intent,
                "confidence": confidence,
            }

        # For non-tool intents, fall through to response generation
        self._add_step("decision_routing", "No tool needed -> generate response")
        self.state_machine.transition("decision_made")

        return {
            "output": nlp_result.get("response", "Understood. How can I help?"),
            "reasoning": f"state_machine:conversation ({intent})",
            "nlp_pipeline": {
                "intent": intent,
                "confidence": confidence,
                "entities": nlp_result.get("entities", []),
            },
        }

    async def _multi_step_reasoning(
        self, query: str, context: Dict, memory: List[dict]
    ) -> dict:
        """Break down complex queries into multi-step reasoning chains."""
        steps: List[ReasoningStep] = []

        # Step 1: Intent analysis
        self._add_step("analysis", "Step 1: Intent analysis")
        nlp_result = await self.nlp.process(query)
        intent = nlp_result["intent"]

        # Step 2: Context retrieval
        self._add_step("context_retrieval", "Step 2: Retrieving relevant context")
        relevant_context = self.context_window.get_relevant_memory(query, n=3)
        self._add_step(
            "context_loaded",
            f"Retrieved {len(relevant_context)} relevant memories",
        )

        # Step 3: Knowledge graph lookup
        self._add_step("kg_lookup", "Step 3: Knowledge graph lookup")
        entities = nlp_result.get("entities", [])
        kg_findings = []
        for entity in entities:
            relations = self.knowledge_graph.get(entity, [])
            kg_findings.append({"entity": entity, "relations": relations})
        self._add_step(
            "kg_complete",
            f"Looked up {len(entities)} entities",
        )

        # Step 4: Response synthesis
        self._add_step("synthesis", "Step 4: Synthesizing response")
        intent_response = await self.nlp.generate_response(
            intent,
            entities,
            nlp_result["sentiment"],
            nlp_result["confidence"],
        )

        return {
            "output": intent_response["response"],
            "reasoning": f"multi_step: {len(steps) + 4} steps",
            "nlp_pipeline": {
                "intent": intent,
                "confidence": nlp_result["confidence"],
                "entities": entities,
                "sentiment": nlp_result["sentiment"],
            },
            "kg_findings": kg_findings,
            "relevant_context_count": len(relevant_context),
            "reasoning_chain": [s.to_dict() for s in self._reasoning_chain],
        }

    async def reason(
        self,
        query: str,
        context: Dict,
        memory: List[dict],
        strategy: Optional[DecisionStrategy] = None,
    ) -> dict:
        self._reset_chain()

        # Determine strategy
        if strategy is None:
            strategy = DecisionStrategy.NLP_ROUTE if self.nlp else DecisionStrategy.FALLBACK

        # Update context window
        self.context_window.add_message("user", query)

        try:
            if strategy == DecisionStrategy.NLP_ROUTE and self.nlp:
                self.state_machine.transition("input_received")
                result = await self._nlp_route(query, context, memory)

            elif strategy == DecisionStrategy.STATE_MACHINE and self.nlp:
                nlp_result = await self.nlp.process(query)
                result = await self._state_machine_route(
                    query, context, memory, nlp_result
                )

            elif strategy == DecisionStrategy.MULTI_STEP:
                result = await self._multi_step_reasoning(query, context, memory)

            elif strategy == DecisionStrategy.RULE_BASED:
                result = await self._rule_based_reasoning(query, context, memory)

            else:
                result = await self._fallback_reason(query, context, memory)

        except Exception as e:
            logger.error("Reasoning error: %s", str(e))
            self.state_machine.transition("error_occurred")
            result = {
                "output": f"An error occurred during reasoning: {str(e)}",
                "reasoning": "error",
                "error": str(e),
            }

        # Final transition: REMEMBERING -> IDLE (via memory store)
        self.context_window.add_message("assistant", result.get("output", ""))

        return result

    async def _rule_based_reasoning(
        self, query: str, context: Dict, memory: List[dict]
    ) -> dict:
        for rule in self.rules:
            if rule["condition"].lower() in query.lower():
                self._add_step("rule_match", f"Rule matched: {rule['condition']}")
                return {
                    "output": rule["action"],
                    "reasoning": "rule-matched",
                    "rule_id": self.rules.index(rule),
                }
        return {
            "output": f"I don't have a rule for '{query}'.",
            "reasoning": "rule-based-fallback",
        }

    async def _fallback_reason(
        self, query: str, context: Dict, memory: List[dict]
    ) -> dict:
        if self.llm_fn:
            return await self.llm_fn(query, context, memory)
        for rule in self.rules:
            if rule["condition"].lower() in query.lower():
                return {
                    "output": rule["action"],
                    "reasoning": "rule-matched",
                    "rule_id": self.rules.index(rule),
                }
        return {
            "output": f"I don't have enough information to answer '{query}'.",
            "reasoning": "default-fallback",
        }

    def get_reasoning_chain(self) -> List[dict]:
        return [s.to_dict() for s in self._reasoning_chain]


# ===================================================================
# ExecutionModule
# ===================================================================
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


# ===================================================================
# JarvisAgent (Main Orchestrator)
# ===================================================================
class JarvisAgent:
    """Main agent orchestrating all subsystems."""

    def __init__(self, name: str = "JARVIS"):
        self.state = AgentState(name)
        self.perception = PerceptionModule()
        self.memory = MemoryManager()
        self.reasoning = ReasoningEngine()
        self.execution = ExecutionModule()

    async def process(
        self,
        user_input: str,
        modality: str = "text",
        reasoning_strategy: Optional[DecisionStrategy] = None,
    ) -> dict:
        logger.info(
            f"[Session {self.state.session_id}] Received input ({modality}): {user_input[:80]}..."
        )

        # 1. Capture & Preprocess
        captured = await self.perception.capture(user_input, modality)

        # 2. Intent Understanding & Knowledge Retrieval
        memory_context = self.memory.recall_recent(5)
        context = {
            "user_context": self.state.to_dict(),
            "recent_memory": memory_context,
        }

        # 3. Reasoning (with strategy selection)
        reasoning_result = await self.reasoning.reason(
            captured["raw"], context, memory_context, reasoning_strategy
        )

        # 4. Build response
        response = {
            "query": captured["raw"],
            "modality": modality,
            "reasoning": reasoning_result,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.state.session_id,
            "state_machine": self.reasoning.state_machine.get_status(),
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
            "state_machine": self.reasoning.state_machine.get_status(),
            "reasoning_strategy": "state_machine" if self.reasoning.nlp else "nlp",
        }
