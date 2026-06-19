"""
J.A.R.V.I.S. Agent 插件系统
支持动态加载、卸载和热插拔第三方功能模块
"""

from .interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginStatus,
    PluginCapability,
)
from .base import PluginBase
from .registry import PluginRegistry
from .manager import PluginManager

__all__ = [
    "PluginInterface",
    "PluginMetadata",
    "PluginConfig",
    "PluginStatus",
    "PluginCapability",
    "PluginBase",
    "PluginRegistry",
    "PluginManager",
]

__version__ = "0.1.0"
