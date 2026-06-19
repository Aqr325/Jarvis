"""
Agent 注册表
管理所有已注册的 Agent 实例，支持按角色、能力和状态查找
"""

import logging
from typing import Dict, List, Optional, Type

from .interface import AgentInterface, AgentRole, AgentCapability, AgentStatus

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Agent 注册表 - 单例模式"""

    _instance: Optional["AgentRegistry"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents: Dict[str, AgentInterface] = {}
            cls._instance._role_index: Dict[AgentRole, List[str]] = {}
            cls._instance._capability_index: Dict[AgentCapability, List[str]] = {}
        return cls._instance

    def register(self, agent: AgentInterface) -> bool:
        """注册一个 Agent"""
        name = agent.metadata.name
        if name in self._agents:
            logger.warning(f"Agent '{name}' already registered, replacing")
        self._agents[name] = agent

        # 更新角色索引
        role = agent.metadata.role
        if role not in self._role_index:
            self._role_index[role] = []
        if name not in self._role_index[role]:
            self._role_index[role].append(name)

        # 更新能力索引
        for cap in agent.metadata.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            if name not in self._capability_index[cap]:
                self._capability_index[cap].append(name)

        logger.info(f"Agent registered: {name} (role={role.value})")
        return True

    def unregister(self, name: str) -> bool:
        """注销一个 Agent"""
        agent = self._agents.pop(name, None)
        if agent is None:
            return False

        # 清理索引
        role = agent.metadata.role
        if role in self._role_index and name in self._role_index[role]:
            self._role_index[role].remove(name)

        for cap in agent.metadata.capabilities:
            if cap in self._capability_index and name in self._capability_index[cap]:
                self._capability_index[cap].remove(name)

        logger.info(f"Agent unregistered: {name}")
        return True

    def get(self, name: str) -> Optional[AgentInterface]:
        """获取 Agent"""
        return self._agents.get(name)

    def get_by_role(self, role: AgentRole) -> List[AgentInterface]:
        """按角色查找"""
        names = self._role_index.get(role, [])
        return [self._agents[n] for n in names if n in self._agents]

    def get_by_capability(self, capability: AgentCapability) -> List[AgentInterface]:
        """按能力查找"""
        names = self._capability_index.get(capability, [])
        return [self._agents[n] for n in names if n in self._agents]

    def get_by_status(self, status: AgentStatus) -> List[AgentInterface]:
        """按状态查找"""
        return [a for a in self._agents.values() if a.status == status]

    def list_all(self) -> List[AgentInterface]:
        """列出所有 Agent"""
        return list(self._agents.values())

    def get_idle_agents(self) -> List[AgentInterface]:
        """获取所有空闲 Agent"""
        return self.get_by_status(AgentStatus.IDLE)

    @property
    def count(self) -> int:
        return len(self._agents)

    @property
    def status_summary(self) -> Dict[str, int]:
        """状态摘要"""
        summary = {}
        for agent in self._agents.values():
            status = agent.status.value
            summary[status] = summary.get(status, 0) + 1
        return summary

    def clear(self):
        """清空注册表"""
        self._agents.clear()
        self._role_index.clear()
        self._capability_index.clear()
        logger.info("Agent registry cleared")
