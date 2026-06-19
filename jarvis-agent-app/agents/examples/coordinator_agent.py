"""
协调员 Agent 示例
负责任务分配和 Agent 协作调度
"""

import logging
from typing import Any, Dict, List, Optional

from agents.interface import (
    AgentInterface,
    AgentMetadata,
    AgentConfig,
    AgentRole,
    AgentCapability,
    AgentStatus,
)
from agents.base import AgentBase


logger = logging.getLogger(__name__)


class CoordinatorAgent(AgentBase):
    """
    协调员 Agent (Coordinator)
    
    负责：
    - 任务分析和拆解
    - Agent 选择和分配
    - 协作调度
    - 结果聚合
    """

    def __init__(self):
        super().__init__()
        self._assigned_agents: List[AgentInterface] = []
        self._task_queue: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="Coordinator Agent",
            role=AgentRole.COORDINATOR,
            description="任务协调员 Agent，负责任务分配和 Agent 协作调度",
            capabilities=[
                AgentCapability.PLANNING,
                AgentCapability.COMMUNICATION,
                AgentCapability.ANALYSIS,
            ],
            expertise=[
                "task planning",
                "resource allocation",
                "coordination",
                "workflow optimization",
            ],
            priority=100,  # 最高优先级
        )

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            enabled=True,
            auto_assign=True,
            temperature=0.4,
            max_tokens=2000,
            timeout=300,
            context_window=8192,
        )

    def register_agent(self, agent: AgentInterface):
        """注册协作 Agent"""
        if agent not in self._assigned_agents:
            self._assigned_agents.append(agent)
            logger.info(f"Registered agent: {agent.metadata.name}")

    def unregister_agent(self, agent: AgentInterface):
        """注销协作 Agent"""
        if agent in self._assigned_agents:
            self._assigned_agents.remove(agent)
            logger.info(f"Unregistered agent: {agent.metadata.name}")

    async def initialize(self) -> bool:
        logger.info("Initializing CoordinatorAgent...")
        success = await super().initialize()
        if success:
            logger.info(f"CoordinatorAgent initialized with {len(self._assigned_agents)} agents")
        return success

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行协调任务
        
        Args:
            task: 包含 'task_type', 'content', 'priority' 等字段
        
        Returns:
            协调结果
        """
        task_type = task.get("task_type", "coordinate")
        content = task.get("content", task.get("query", ""))

        if not content:
            return {
                "success": False,
                "error": "no_content",
                "message": "请提供协调任务内容",
            }

        try:
            self.status = AgentStatus.BUSY
            
            if task_type == "analyze":
                result = await self._analyze_task(content)
            elif task_type == "assign":
                result = await self._assign_tasks(content, task)
            elif task_type == "coordinate":
                result = await self._coordinate(content, task)
            else:
                result = await self._coordinate(content, task)
            
            return result
            
        except Exception as e:
            logger.error(f"Coordination task failed: {e}")
            return {
                "success": False,
                "error": "coordination_error",
                "message": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    async def _analyze_task(self, content: str) -> Dict[str, Any]:
        """分析任务"""
        # 简单任务分析
        task_analysis = {
            "complexity": "medium",
            "estimated_agents": 2,
            "suggested_roles": ["researcher", "writer"],
            "estimated_time": "10 minutes",
            "subtasks": [
                {"id": "subtask_1", "description": "信息搜集", "estimated_time": "5 min"},
                {"id": "subtask_2", "description": "内容编写", "estimated_time": "5 min"},
            ],
        }
        
        return {
            "success": True,
            "task_type": "analyze",
            "original_content": content,
            "analysis": task_analysis,
        }

    async def _assign_tasks(self, content: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """分配任务"""
        if not self._assigned_agents:
            return {
                "success": False,
                "error": "no_agents",
                "message": "没有可用的 Agent",
            }
        
        # 根据内容选择 Agent
        assigned = []
        for agent in self._assigned_agents:
            if agent.can_handle("general"):
                assigned.append({
                    "agent_name": agent.metadata.name,
                    "agent_role": agent.metadata.role.value,
                    "assigned_subtasks": [],
                })
        
        return {
            "success": True,
            "task_type": "assign",
            "content": content,
            "assigned_agents": assigned,
            "total_agents": len(assigned),
        }

    async def _coordinate(self, content: str, task: Dict[str, Any]) -> Dict[str, Any]:
        """协调执行"""
        if not self._assigned_agents:
            return {
                "success": False,
                "error": "no_agents",
                "message": "没有可用的 Agent 进行协作",
            }
        
        # 分析任务
        analysis = await self._analyze_task(content)
        
        # 按优先级排序 Agent
        sorted_agents = sorted(
            self._assigned_agents,
            key=lambda a: a.metadata.priority,
            reverse=True
        )
        
        # 执行协作
        collaboration_result = await self.collaborate(
            {"content": content, "task_type": task.get("task_type", "general")},
            sorted_agents
        )
        
        return {
            "success": True,
            "task_type": "coordinate",
            "content": content,
            "agents_involved": len(sorted_agents),
            "analysis": analysis.get("analysis", {}),
            "collaboration_result": collaboration_result,
        }

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """获取可用的 Agent 列表"""
        return [
            {
                "name": agent.metadata.name,
                "role": agent.metadata.role.value,
                "status": agent.status.value,
                "capabilities": [c.value for c in agent.metadata.capabilities],
            }
            for agent in self._assigned_agents
        ]

    def get_task_queue(self) -> List[Dict[str, Any]]:
        """获取任务队列"""
        return self._task_queue.copy()

    async def shutdown(self) -> bool:
        logger.info("Shutting down CoordinatorAgent...")
        self._assigned_agents.clear()
        self._task_queue.clear()
        return await super().shutdown()
