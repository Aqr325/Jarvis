"""
多 Agent 协作系统
支持角色分工、任务分配和结果聚合
"""

from .interface import (
    AgentInterface,
    AgentMetadata,
    AgentConfig,
    AgentRole,
    AgentCapability,
    AgentStatus,
)
from .base import AgentBase
from .registry import AgentRegistry
from .manager import AgentManager

__all__ = [
    "AgentInterface",
    "AgentMetadata",
    "AgentConfig",
    "AgentRole",
    "AgentCapability",
    "AgentStatus",
    "AgentBase",
    "AgentRegistry",
    "AgentManager",
]

__version__ = "0.1.0"
