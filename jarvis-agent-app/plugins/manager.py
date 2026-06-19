"""
插件管理器 - 管理插件生命周期和动态加载
"""

import asyncio
import importlib
import inspect
import logging
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from datetime import datetime

from .interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginStatus,
    PluginCapability,
)
from .base import PluginBase
from .registry import PluginRegistry


logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """插件加载错误"""
    pass


class PluginExecutionError(Exception):
    """插件执行错误"""
    pass


class PluginManager:
    """
    插件管理器
    
    负责：
    - 插件自动发现
    - 插件加载和卸载
    - 插件生命周期管理
    - 插件依赖解析
    - 插件热插拔
    - 执行统计和监控
    """

    def __init__(self, registry: Optional[PluginRegistry] = None):
        self.registry = registry or PluginRegistry()
        self._active_plugins: Dict[str, PluginInterface] = {}
        self._execution_stats: Dict[str, Dict[str, Any]] = {}
        self._load_order: List[str] = []
        self._shutdown_lock = asyncio.Lock()
        self._running = False
        
        logger.info("PluginManager initialized")

    async def initialize(self):
        """初始化插件管理器"""
        logger.info("Initializing PluginManager...")
        self._running = True
        
        # 发现所有可用插件
        discovered = self.registry.discover_plugins()
        logger.info(f"Found {len(discovered)} discoverable plugins")
        
        # 按优先级排序
        discovered.sort(key=lambda p: p.get("priority", 0), reverse=True)
        
        # 自动加载配置为 auto_load 的插件
        for plugin_info in discovered:
            # 这里可以添加自动加载逻辑
            logger.debug(f"Discovered plugin: {plugin_info['name']} v{plugin_info['version']}")
        
        logger.info("PluginManager initialization completed")

    async def load_plugin(self, plugin: PluginInterface, config: Optional[PluginConfig] = None) -> bool:
        """
        加载单个插件
        
        Args:
            plugin: 插件实例
            config: 插件配置
        
        Returns:
            是否加载成功
        """
        plugin_id = plugin.metadata.plugin_id
        plugin_name = plugin.metadata.name
        
        logger.info(f"Loading plugin: {plugin_name} (ID: {plugin_id})")
        
        # 检查依赖
        missing_deps = self.registry.check_dependencies(plugin)
        if missing_deps:
            logger.error(f"Plugin {plugin_name} missing dependencies: {missing_deps}")
            plugin.status = PluginStatus.ERROR
            return False
        
        # 检查是否已加载
        if plugin_id in self._active_plugins:
            logger.warning(f"Plugin {plugin_name} already loaded")
            return True
        
        try:
            # 设置配置
            if config:
                plugin.config = config
            
            # 初始化插件
            plugin.status = PluginStatus.LOADING
            success = await plugin.initialize()
            
            if not success:
                logger.error(f"Plugin {plugin_name} initialization failed")
                plugin.status = PluginStatus.ERROR
                return False
            
            # 激活插件
            plugin.status = PluginStatus.ACTIVE
            self._active_plugins[plugin_id] = plugin
            self._load_order.append(plugin_id)
            
            # 初始化统计
            self._execution_stats[plugin_id] = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "last_execution": None,
            }
            
            # 注册到全局 registry
            self.registry.register_plugin(plugin, config)
            
            logger.info(f"Plugin {plugin_name} loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            plugin.status = PluginStatus.ERROR
            plugin.status = PluginStatus.ERROR
            return False

    async def load_plugin_from_file(self, file_path: str, class_name: Optional[str] = None) -> bool:
        """
        从文件加载插件
        
        Args:
            file_path: 插件文件路径
            class_name: 插件类名（可选，自动检测第一个 PluginBase 子类）
        
        Returns:
            是否加载成功
        """
        path = Path(file_path)
        if not path.exists():
            logger.error(f"Plugin file not found: {file_path}")
            return False
        
        try:
            # 动态导入
            module_name = path.stem
            spec = importlib.util.spec_from_file_location(module_name, path)
            
            if not spec or not spec.loader:
                raise PluginLoadError(f"Could not load spec from {file_path}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # 查找插件类
            plugin_class = None
            if class_name:
                plugin_class = getattr(module, class_name, None)
            else:
                # 自动查找第一个 PluginBase 子类
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        inspect.isclass(attr)
                        and issubclass(attr, PluginBase)
                        and attr != PluginBase
                    ):
                        plugin_class = attr
                        break
            
            if not plugin_class:
                raise PluginLoadError(f"No PluginBase subclass found in {file_path}")
            
            # 创建实例
            plugin = plugin_class()
            success = await self.load_plugin(plugin)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to load plugin from {file_path}: {e}")
            return False

    async def load_plugin_from_zip(self, zip_path: str) -> bool:
        """
        从 ZIP 文件加载插件包
        
        Args:
            zip_path: ZIP 文件路径
        
        Returns:
            是否加载成功
        """
        path = Path(zip_path)
        if not path.exists() or not path.suffix == ".zip":
            logger.error(f"Invalid ZIP file: {zip_path}")
            return False
        
        try:
            with zipfile.ZipFile(path, 'r') as zip_file:
                # 提取到临时目录
                extract_dir = Path(__file__).parent / "temp" / path.stem
                extract_dir.mkdir(parents=True, exist_ok=True)
                zip_file.extractall(extract_dir)
                
                # 查找主插件文件
                main_file = extract_dir / "plugin.py"
                if not main_file.exists():
                    main_file = extract_dir / "main.py"
                
                if main_file.exists():
                    success = await self.load_plugin_from_file(str(main_file))
                    return success
                else:
                    logger.error(f"No plugin.py or main.py found in {zip_path}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to load plugin from ZIP {zip_path}: {e}")
            return False

    async def unload_plugin(self, plugin_id: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_id: 插件 ID
        
        Returns:
            是否卸载成功
        """
        plugin = self._active_plugins.get(plugin_id)
        if not plugin:
            logger.warning(f"Plugin {plugin_id} not found for unload")
            return False
        
        plugin_name = plugin.metadata.name
        logger.info(f"Unloading plugin: {plugin_name}")
        
        try:
            # 设置为卸载状态
            plugin.status = PluginStatus.UNLOADING
            
            # 关闭插件
            success = await plugin.shutdown()
            
            if success:
                # 从活跃列表移除
                del self._active_plugins[plugin_id]
                
                # 从加载顺序移除
                if plugin_id in self._load_order:
                    self._load_order.remove(plugin_id)
                
                # 清理统计
                if plugin_id in self._execution_stats:
                    del self._execution_stats[plugin_id]
                
                logger.info(f"Plugin {plugin_name} unloaded successfully")
                return True
            else:
                logger.error(f"Plugin {plugin_name} shutdown failed")
                plugin.status = PluginStatus.ERROR
                return False
                
        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            plugin.status = PluginStatus.ERROR
            return False

    async def reload_plugin(self, plugin_id: str) -> bool:
        """重新加载插件（热重载）"""
        plugin = self._active_plugins.get(plugin_id)
        if not plugin:
            return False
        
        plugin_name = plugin.metadata.name
        logger.info(f"Reloading plugin: {plugin_name}")
        
        # 先卸载
        await self.unload_plugin(plugin_id)
        
        # 重新加载
        return await self.load_plugin(plugin)

    async def execute_plugin(self, plugin_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行插件
        
        Args:
            plugin_id: 插件 ID
            context: 执行上下文
        
        Returns:
            执行结果
        """
        plugin = self._active_plugins.get(plugin_id)
        if not plugin:
            return {
                "success": False,
                "error": "not_found",
                "message": f"Plugin {plugin_id} not found or not active"
            }
        
        if plugin.status != PluginStatus.ACTIVE:
            return {
                "success": False,
                "error": "not_active",
                "message": f"Plugin is in {plugin.status.value} state"
            }
        
        start_time = datetime.now()
        plugin.set_context(context)
        
        try:
            result = await plugin.safe_execute(context)
            
            # 更新统计
            stats = self._execution_stats.get(plugin_id, {})
            stats["total_executions"] = stats.get("total_executions", 0) + 1
            if result.get("success", False):
                stats["successful_executions"] = stats.get("successful_executions", 0) + 1
            else:
                stats["failed_executions"] = stats.get("failed_executions", 0) + 1
            stats["last_execution"] = start_time.isoformat()
            
            execution_time = (datetime.now() - start_time).total_seconds()
            stats["total_execution_time"] = stats.get("total_execution_time", 0) + execution_time
            
            self._execution_stats[plugin_id] = stats
            
            return result
            
        except Exception as e:
            logger.error(f"Plugin {plugin.metadata.name} execution exception: {e}")
            return {
                "success": False,
                "error": "exception",
                "message": str(e)
            }

    async def execute_by_capability(
        self, 
        capability: PluginCapability, 
        context: Dict[str, Any],
        priority_order: bool = True
    ) -> List[Dict[str, Any]]:
        """
        按能力执行所有匹配的插件
        
        Args:
            capability: 能力类型
            context: 执行上下文
            priority_order: 是否按优先级排序
        
        Returns:
            所有插件执行结果列表
        """
        plugins = self.registry.get_plugins_by_capability(capability)
        
        if priority_order:
            plugins.sort(key=lambda p: p.metadata.priority, reverse=True)
        
        results = []
        for plugin in plugins:
            result = await self.execute_plugin(plugin.metadata.plugin_id, context)
            result["plugin_name"] = plugin.metadata.name
            result["plugin_id"] = plugin.metadata.plugin_id
            results.append(result)
        
        return results

    def get_plugin_status(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """获取插件详细状态"""
        plugin = self._active_plugins.get(plugin_id)
        if not plugin:
            return None
        
        stats = self._execution_stats.get(plugin_id, {})
        
        return {
            "metadata": plugin.metadata.to_dict(),
            "config": plugin.config.to_dict(),
            "status": plugin.status.value,
            "statistics": stats,
        }

    def list_active_plugins(self) -> List[Dict[str, Any]]:
        """列出所有活跃插件"""
        result = []
        for plugin_id, plugin in self._active_plugins.items():
            stats = self._execution_stats.get(plugin_id, {})
            result.append({
                "plugin_id": plugin_id,
                "name": plugin.metadata.name,
                "version": plugin.metadata.version,
                "status": plugin.status.value,
                "capabilities": [c.value for c in plugin.metadata.capabilities],
                "statistics": stats,
            })
        return result

    def get_plugins_by_capability(self, capability: PluginCapability) -> List[Dict[str, Any]]:
        """按能力列出插件"""
        plugins = self.registry.get_plugins_by_capability(capability)
        return [
            {
                "plugin_id": p.metadata.plugin_id,
                "name": p.metadata.name,
                "version": p.metadata.version,
                "status": p.status.value,
            }
            for p in plugins
        ]

    async def shutdown_all(self):
        """关闭所有插件"""
        async with self._shutdown_lock:
            logger.info("Shutting down all plugins...")
            
            # 按相反顺序关闭（依赖顺序）
            for plugin_id in reversed(self._load_order):
                try:
                    await self.unload_plugin(plugin_id)
                except Exception as e:
                    logger.error(f"Error shutting down plugin {plugin_id}: {e}")
            
            self._running = False
            logger.info("All plugins shutdown completed")

    @property
    def active_count(self) -> int:
        """活跃插件数量"""
        return len(self._active_plugins)

    @property
    def total_execution_count(self) -> int:
        """总执行次数"""
        return sum(
            stats.get("total_executions", 0)
            for stats in self._execution_stats.values()
        )
