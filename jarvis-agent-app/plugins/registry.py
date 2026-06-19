"""
插件注册中心 - 管理所有已注册插件
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
import logging

from .interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginStatus,
    PluginCapability,
)
from .base import PluginBase


logger = logging.getLogger(__name__)


class PluginRegistry:
    """
    插件注册中心
    
    负责：
    - 插件发现和加载
    - 插件注册和注销
    - 插件依赖解析
    - 插件版本检查
    """

    def __init__(self):
        self._plugins: Dict[str, PluginInterface] = {}
        self._plugin_classes: Dict[str, Type[PluginInterface]] = {}
        self._plugin_paths: Dict[str, str] = {}
        self._loaded_plugins: Dict[str, bool] = {}
        self._discovery_paths: List[Path] = []
        
        # 默认插件路径
        self._default_plugin_path = Path(__file__).parent / "plugins"
        self._core_plugin_path = Path(__file__).parent.parent / "plugins"
        
        self._register_discovery_paths()

    def _register_discovery_paths(self):
        """注册插件发现路径"""
        default_paths = [
            self._default_plugin_path,
            self._core_plugin_path,
            Path.home() / ".jarvis" / "plugins",
            Path.cwd() / "plugins",
        ]
        
        for path in default_paths:
            self.add_discovery_path(path)

    def add_discovery_path(self, path: Path):
        """添加插件发现路径"""
        path = Path(path).resolve()
        if path not in self._discovery_paths:
            self._discovery_paths.append(path)
            logger.info(f"Added plugin discovery path: {path}")

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """
        发现所有可用插件
        
        Returns:
            插件信息列表
        """
        discovered = []
        
        for path in self._discovery_paths:
            if not path.exists():
                continue
                
            logger.debug(f"Scanning plugin path: {path}")
            
            # 扫描 Python 文件
            for py_file in path.rglob("*.py"):
                if py_file.name.startswith("_"):
                    continue
                    
                try:
                    plugin_info = self._scan_plugin_file(py_file)
                    if plugin_info:
                        discovered.append(plugin_info)
                except Exception as e:
                    logger.warning(f"Failed to scan plugin file {py_file}: {e}")
        
        # 去重（按插件名）
        seen = set()
        unique_discovered = []
        for plugin in discovered:
            if plugin["name"] not in seen:
                seen.add(plugin["name"])
                unique_discovered.append(plugin)
        
        logger.info(f"Discovered {len(unique_discovered)} plugins")
        return unique_discovered

    def _scan_plugin_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """扫描单个插件文件，提取元数据"""
        # 动态导入模块
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        
        if not spec or not spec.loader:
            return None
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # 查找 PluginBase 子类
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, PluginBase)
                and attr != PluginBase
            ):
                try:
                    instance = attr()
                    metadata = instance.metadata
                    return {
                        "name": metadata.name,
                        "version": metadata.version,
                        "author": metadata.author,
                        "description": metadata.description,
                        "class_name": attr_name,
                        "file_path": str(file_path),
                        "capabilities": [c.value for c in metadata.capabilities],
                        "dependencies": metadata.dependencies,
                    }
                except Exception as e:
                    logger.warning(f"Failed to instantiate plugin from {file_path}: {e}")
        
        return None

    def register_plugin(self, plugin: PluginInterface, config: Optional[PluginConfig] = None):
        """注册单个插件实例"""
        plugin_id = plugin.metadata.plugin_id
        self._plugins[plugin_id] = plugin
        self._plugin_paths[plugin_id] = "inline"
        
        if config:
            plugin.config = config
        
        logger.info(f"Registered plugin: {plugin.metadata.name} (ID: {plugin_id})")

    def register_plugin_class(self, plugin_class: Type[PluginInterface], source: str = "inline"):
        """注册插件类（延迟实例化）"""
        class_name = plugin_class.__name__
        self._plugin_classes[class_name] = plugin_class
        
        # 尝试获取元数据
        try:
            # 创建临时实例获取元数据
            temp_instance = plugin_class()
            metadata = temp_instance.metadata
            self._plugin_classes[f"{metadata.name}_class"] = plugin_class
            logger.info(f"Registered plugin class: {class_name} (Plugin: {metadata.name})")
        except Exception as e:
            logger.warning(f"Could not get metadata for plugin class {class_name}: {e}")

    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """获取已注册的插件"""
        return self._plugins.get(plugin_id)

    def get_plugin_by_name(self, name: str) -> Optional[PluginInterface]:
        """按名称获取插件"""
        for plugin in self._plugins.values():
            if plugin.metadata.name.lower() == name.lower():
                return plugin
        return None

    def get_plugins_by_capability(self, capability: PluginCapability) -> List[PluginInterface]:
        """按能力获取插件列表"""
        matching = []
        for plugin in self._plugins.values():
            if capability in plugin.metadata.capabilities:
                matching.append(plugin)
        return matching

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有已注册插件"""
        result = []
        for plugin in self._plugins.values():
            result.append({
                "metadata": plugin.metadata.to_dict(),
                "config": plugin.config.to_dict(),
                "status": plugin.status.value,
            })
        return result

    def check_dependencies(self, plugin: PluginInterface) -> List[str]:
        """检查插件依赖是否满足"""
        missing = []
        for dep in plugin.metadata.dependencies:
            dep_plugin = self.get_plugin_by_name(dep)
            if not dep_plugin or dep_plugin.status != PluginStatus.ACTIVE:
                missing.append(dep)
        return missing

    def check_version_compatibility(self, plugin: PluginInterface, required_version: str) -> bool:
        """检查版本兼容性（简单实现）"""
        # 简单版本比较（实际应该使用语义化版本）
        return True

    def unregister_plugin(self, plugin_id: str) -> bool:
        """注销插件"""
        if plugin_id in self._plugins:
            del self._plugins[plugin_id]
            if plugin_id in self._plugin_paths:
                del self._plugin_paths[plugin_id]
            logger.info(f"Unregistered plugin ID: {plugin_id}")
            return True
        return False

    def clear(self):
        """清空所有注册的插件"""
        self._plugins.clear()
        self._plugin_classes.clear()
        self._plugin_paths.clear()
        logger.info("Cleared all registered plugins")

    @property
    def plugin_count(self) -> int:
        """已注册插件数量"""
        return len(self._plugins)

    @property
    def active_plugin_count(self) -> int:
        """活跃插件数量"""
        return sum(1 for p in self._plugins.values() if p.status == PluginStatus.ACTIVE)
