"""
插件系统 API 定义 - Pydantic 模型
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PluginCapabilityEnum(str, Enum):
    """插件能力类型"""
    NLP_EXTENSION = "nlp_extension"
    TOOL_PROVIDER = "tool_provider"
    DATA_PROCESSOR = "data_processor"
    INTEGRATION = "integration"
    UI_COMPONENT = "ui_component"
    MODEL_ADAPTER = "model_adapter"


class PluginStatusEnum(str, Enum):
    """插件状态"""
    UNLOADED = "unloaded"
    LOADING = "loading"
    LOADED = "loaded"
    ACTIVE = "active"
    ERROR = "error"
    DISABLED = "disabled"


class PluginMetadataModel(BaseModel):
    """插件元数据模型"""
    name: str
    version: str
    author: str
    description: str
    plugin_id: Optional[str] = None
    capabilities: List[PluginCapabilityEnum] = []
    dependencies: List[str] = []
    homepage: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = []
    priority: int = 0


class PluginConfigModel(BaseModel):
    """插件配置模型"""
    enabled: bool = True
    auto_load: bool = False
    config: Dict[str, Any] = {}
    timeout: int = 30
    rate_limit: Optional[int] = None


class PluginInfoModel(BaseModel):
    """插件信息模型"""
    metadata: PluginMetadataModel
    config: PluginConfigModel
    status: PluginStatusEnum


class PluginListItemModel(BaseModel):
    """插件列表项"""
    plugin_id: str
    name: str
    version: str
    status: PluginStatusEnum
    capabilities: List[PluginCapabilityEnum]


class PluginLoadRequest(BaseModel):
    """加载插件请求"""
    plugin_id: Optional[str] = None
    file_path: Optional[str] = None
    class_name: Optional[str] = None
    config: Optional[PluginConfigModel] = None


class PluginExecuteRequest(BaseModel):
    """执行插件请求"""
    plugin_id: str
    context: Dict[str, Any] = Field(default_factory=dict)


class PluginExecuteResponse(BaseModel):
    """执行插件响应"""
    success: bool
    plugin_name: str
    plugin_id: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    message: Optional[str] = None


class PluginStatusResponse(BaseModel):
    """插件状态响应"""
    plugin_id: str
    name: str
    version: str
    status: PluginStatusEnum
    capabilities: List[PluginCapabilityEnum]
    statistics: Dict[str, Any]
    metadata: Dict[str, Any]
    config: Dict[str, Any]


class PluginListResponse(BaseModel):
    """插件列表响应"""
    total: int
    active: int
    plugins: List[PluginListItemModel]


class PluginCapabilitiesResponse(BaseModel):
    """插件能力列表响应"""
    capabilities: List[str]
    plugins_by_capability: Dict[str, List[PluginListItemModel]]


class PluginLoadResponse(BaseModel):
    """加载插件响应"""
    success: bool
    plugin_id: str
    name: str
    message: str
    details: Optional[Dict[str, Any]] = None


class PluginUnloadResponse(BaseModel):
    """卸载插件响应"""
    success: bool
    plugin_id: str
    name: str
    message: str


class PluginReloadResponse(BaseModel):
    """重载插件响应"""
    success: bool
    plugin_id: str
    name: str
    message: str


class PluginExecuteByCapabilityRequest(BaseModel):
    """按能力执行插件请求"""
    capability: PluginCapabilityEnum
    context: Dict[str, Any] = Field(default_factory=dict)
    priority_order: bool = True


class PluginExecuteByCapabilityResponse(BaseModel):
    """按能力执行插件响应"""
    capability: str
    executed_count: int
    results: List[PluginExecuteResponse]
