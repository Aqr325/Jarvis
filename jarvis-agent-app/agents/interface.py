"""
Agent 核心接口定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid


class AgentRole(Enum):
    """Agent 角色类型"""
    GENERAL = "general"              # 通用助手
    RESEARCHER = "researcher"        # 研究员
    PROGRAMMER = "programmer"        # 程序员
    DESIGNER = "designer"            # 设计师
    WRITER = "writer"                # 作家
    ANALYST = "analyst"              # 分析师
    COORDINATOR = "coordinator"      # 协调员
    REVIEWER = "reviewer"            # 审核员
    SPECIALIST = "specialist"        # 专家
    ASSISTANT = "assistant"          # 助手


class AgentCapability(Enum):
    """Agent 能力类型"""
    NLP = "nlp"                      # 自然语言处理
    RESEARCH = "research"            # 研究能力
    CODING = "coding"                # 编程能力
    DESIGN = "design"                # 设计能力
    WRITING = "writing"              # 写作能力
    ANALYSIS = "analysis"            # 分析能力
    PLANNING = "planning"            # 规划能力
    COMMUNICATION = "communication"  # 沟通能力
    INTEGRATION = "integration"      # 集成能力
    AUTOMATION = "automation"        # 自动化能力


class AgentStatus(Enum):
    """Agent 状态"""
    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"
    DISABLED = "disabled"


@dataclass
class AgentMetadata:
    """Agent 元数据"""
    name: str
    role: AgentRole
    description: str
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    capabilities: List[AgentCapability] = field(default_factory=list)
    expertise: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: str = "1.0.0"
    author: str = "JARVIS Team"
    max_concurrent_tasks: int = 1
    priority: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "role": self.role.value,
            "description": self.description,
            "agent_id": self.agent_id,
            "capabilities": [c.value for c in self.capabilities],
            "expertise": self.expertise,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "author": self.author,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "priority": self.priority,
        }


@dataclass
class AgentConfig:
    """Agent 配置"""
    enabled: bool = True
    auto_assign: bool = True
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 60
    context_window: int = 4096
    metadata: Optional[AgentMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "auto_assign": self.auto_assign,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "context_window": self.context_window,
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }


class AgentInterface(ABC):
    """
    Agent 接口 - 所有 Agent 必须实现此接口
    
    主要方法：
    - initialize() - 初始化 Agent
    - execute() - 执行任务
    - collaborate() - 与其他 Agent 协作
    - shutdown() - 关闭 Agent
    """

    @property
    @abstractmethod
    def metadata(self) -> AgentMetadata:
        """返回 Agent 元数据"""
        pass

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        """返回 Agent 配置"""
        pass

    @property
    @abstractmethod
    def status(self) -> AgentStatus:
        """返回当前状态"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """初始化 Agent"""
        pass

    @abstractmethod
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行任务
        
        Args:
            task: 任务描述，包含 task_id, task_type, content 等
        
        Returns:
            执行结果
        """
        pass

    @abstractmethod
    async def collaborate(
        self,
        task: Dict[str, Any],
        collaborators: List["AgentInterface"]
    ) -> Dict[str, Any]:
        """
        与其他 Agent 协作完成任务
        
        Args:
            task: 任务描述
            collaborators: 协作者 Agent 列表
        
        Returns:
            协作结果
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """关闭 Agent"""
        pass

    # 可选方法

    async def on_task_start(self, task: Dict[str, Any]) -> None:
        """任务开始时的回调"""
        pass

    async def on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]) -> None:
        """任务完成时的回调"""
        pass

    async def on_error(self, error: Exception, task: Optional[Dict[str, Any]] = None) -> None:
        """发生错误时的回调"""
        pass

    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理某类任务"""
        return True

    def get_preferred_tasks(self) -> List[str]:
        """返回偏好的任务类型"""
        return []
