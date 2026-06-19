"""
插件核心接口定义
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Type, Callable
import uuid


class PluginStatus(Enum):
    """插件状态"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"
    UNLOADING = "unloading"


class PluginCapability(Enum):
    """插件能力类型"""
    NLP_EXTENSION = "nlp_extension"      # NLP 扩展
    TOOL_PROVIDER = "tool_provider"     # 工具提供者
    DATA_PROCESSOR = "data_processor"   # 数据处理
    INTEGRATION = "integration"          # 第三方集成
    UI_COMPONENT = "ui_component"        # UI 组件
    MODEL_ADAPTER = "model_adapter"      # 模型适配器


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str
    author: str
    description: str
    plugin_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    capabilities: List[PluginCapability] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    homepage: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    priority: int = 0  # 加载优先级，数值越大越先加载

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "plugin_id": self.plugin_id,
            "capabilities": [c.value for c in self.capabilities],
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "homepage": self.homepage,
            "license": self.license,
            "tags": self.tags,
            "priority": self.priority,
        }


@dataclass
class PluginConfig:
    """插件配置"""
    enabled: bool = True
    auto_load: bool = False
    config: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30  # 执行超时（秒）
    rate_limit: Optional[int] = None  # 每秒最大调用次数
    metadata: Optional[PluginMetadata] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "auto_load": self.auto_load,
            "config": self.config,
            "timeout": self.timeout,
            "rate_limit": self.rate_limit,
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }


class PluginInterface(ABC):
    """
    插件接口 - 所有插件必须实现此接口
    
    生命周期：
    1. initialize() - 初始化插件
    2. execute() - 执行插件功能
    3. shutdown() - 插件关闭
    """

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """返回插件元数据"""
        pass

    @property
    @abstractmethod
    def config(self) -> PluginConfig:
        """返回插件配置"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化插件
        返回是否初始化成功
        """
        pass

    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行插件功能
        
        Args:
            context: 执行上下文，包含用户输入、历史对话等信息
        
        Returns:
            执行结果字典
        """
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """
        关闭插件，释放资源
        返回是否成功关闭
        """
        pass

    # 可选方法 - 插件可以按需实现

    async def on_load(self) -> None:
        """插件加载时的回调"""
        pass

    async def on_unload(self) -> None:
        """插件卸载时的回调"""
        pass

    async def on_error(self, error: Exception) -> None:
        """插件发生错误时的回调"""
        pass

    def get_tools(self) -> List[Dict[str, Any]]:
        """返回插件提供的工具列表"""
        return []

    def get_handlers(self) -> Dict[str, Callable]:
        """返回插件注册的事件处理器"""
        return {}
