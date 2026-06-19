"""
Agent 管理器
负责 Agent 生命周期管理、任务分配和结果聚合
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from .interface import AgentInterface, AgentRole, AgentStatus, AgentMetadata
from .registry import AgentRegistry

logger = logging.getLogger(__name__)


class AgentManager:
    """Agent 管理器 - 协调多个 Agent 协作"""

    def __init__(self):
        self.registry = AgentRegistry()
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._results: Dict[str, Dict[str, Any]] = {}
        self._running = False
        self._task_id_counter = 0

    async def initialize_agents(self, agents: List[AgentInterface]) -> bool:
        """初始化并注册多个 Agent"""
        results = await asyncio.gather(
            *[self._init_single(agent) for agent in agents],
            return_exceptions=True
        )
        success_count = sum(1 for r in results if r is True)
        logger.info(f"Initialized {success_count}/{len(agents)} agents")
        return success_count > 0

    async def _init_single(self, agent: AgentInterface) -> bool:
        try:
            success = await agent.initialize()
            if success:
                self.registry.register(agent)
            return success
        except Exception as e:
            logger.error(f"Failed to initialize agent {agent.metadata.name}: {e}")
            return False

    async def assign_task(
        self,
        task: Dict[str, Any],
        preferred_agent: Optional[str] = None,
        required_role: Optional[AgentRole] = None,
    ) -> Dict[str, Any]:
        """分配任务给合适的 Agent"""
        agent = None

        # 1. 使用指定 Agent
        if preferred_agent:
            agent = self.registry.get(preferred_agent)

        # 2. 按角色查找空闲 Agent
        if agent is None and required_role:
            candidates = self.registry.get_by_role(required_role)
            idle = [a for a in candidates if a.status == AgentStatus.IDLE]
            if idle:
                agent = idle[0]

        # 3. 找任意空闲 Agent
        if agent is None:
            idle_agents = self.registry.get_idle_agents()
            if idle_agents:
                agent = idle_agents[0]

        if agent is None:
            return {
                "success": False,
                "error": "no_available_agent",
                "message": "没有可用的 Agent",
            }

        # 执行任务
        task_id = f"task_{self._task_id_counter}"
        self._task_id_counter += 1

        try:
            logger.info(f"Assigning {task_id} to {agent.metadata.name}")
            result = await agent.execute(task)
            result["task_id"] = task_id
            result["agent"] = agent.metadata.name
            self._results[task_id] = result
            return result
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return {
                "success": False,
                "task_id": task_id,
                "agent": agent.metadata.name,
                "error": str(e),
            }

    async def assign_parallel(
        self,
        tasks: List[Dict[str, Any]],
        required_role: Optional[AgentRole] = None,
    ) -> List[Dict[str, Any]]:
        """并行分配多个任务"""
        coros = [
            self.assign_task(task, required_role=required_role)
            for task in tasks
        ]
        results = await asyncio.gather(*coros, return_exceptions=True)
        return [
            r if not isinstance(r, Exception) else {"success": False, "error": str(r)}
            for r in results
        ]

    async def broadcast(
        self,
        message: Dict[str, Any],
        target_role: Optional[AgentRole] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """广播消息给多个 Agent"""
        if target_role:
            agents = self.registry.get_by_role(target_role)
        else:
            agents = self.registry.list_all()

        tasks = [self.assign_task(message, preferred_agent=a.metadata.name) for a in agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            "broadcast": True,
            "target_count": len(agents),
            "results": [
                r if not isinstance(r, Exception) else {"error": str(r)}
                for r in results
            ],
        }

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        return self._results.get(task_id)

    def get_all_results(self) -> Dict[str, Any]:
        """获取所有任务结果"""
        return dict(self._results)

    def get_status_report(self) -> Dict[str, Any]:
        """生成状态报告"""
        agents = self.registry.list_all()
        return {
            "total_agents": len(agents),
            "status_summary": self.registry.status_summary,
            "completed_tasks": len(self._results),
            "agents": [
                {
                    "name": a.metadata.name,
                    "role": a.metadata.role.value,
                    "status": a.status.value,
                    "capabilities": [c.value for c in a.metadata.capabilities],
                }
                for a in agents
            ],
        }

    async def shutdown_all(self):
        """关闭所有 Agent"""
        agents = self.registry.list_all()
        results = await asyncio.gather(
            *[agent.shutdown() for agent in agents],
            return_exceptions=True
        )
        success = sum(1 for r in results if r is True)
        self.registry.clear()
        self._results.clear()
        logger.info(f"Shutdown {success}/{len(agents)} agents")
