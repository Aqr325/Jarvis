"""
插件基类 - 提供通用功能和默认实现
"""

import asyncio
import logging
from typing import Any, Dict, Optional
from .interface import PluginInterface, PluginMetadata, PluginConfig, PluginStatus


logger = logging.getLogger(__name__)


class PluginBase(PluginInterface):
    """
    插件基类
    
    所有自定义插件都应该继承这个基类：
    
    ```python
    class MyPlugin(PluginBase):
        @property
        def metadata(self) -> PluginMetadata:
            return PluginMetadata(
                name="My Plugin",
                version="1.0.0",
                author="Author Name",
                description="Plugin description",
                capabilities=[PluginCapability.TOOL_PROVIDER],
            )
        
        @property
        def config(self) -> PluginConfig:
            return PluginConfig(
                enabled=True,
                auto_load=False,
                config={"key": "value"}
            )
        
        async def initialize(self) -> bool:
            # 初始化逻辑
            return True
        
        async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
            # 执行逻辑
            return {"result": "success"}
        
        async def shutdown(self) -> bool:
            # 清理逻辑
            return True
    ```
    """

    def __init__(self):
        self._status = PluginStatus.UNLOADED
        self._context: Optional[Dict[str, Any]] = None
        self._error_handler: Optional[callable] = None
        self._cleanup_callbacks: list = []

    @property
    def status(self) -> PluginStatus:
        """当前插件状态"""
        return self._status

    @status.setter
    def status(self, value: PluginStatus):
        self._status = value
        logger.debug(f"Plugin {self.metadata.name} status changed to {value.value}")

    def set_context(self, context: Dict[str, Any]):
        """设置执行上下文"""
        self._context = context

    def register_cleanup(self, callback: callable):
        """注册清理回调函数"""
        self._cleanup_callbacks.append(callback)

    def register_error_handler(self, handler: callable):
        """注册错误处理器"""
        self._error_handler = handler

    async def execute_with_timeout(self, context: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
        """
        带超时的执行方法
        
        Args:
            context: 执行上下文
            timeout: 超时时间（秒）
        
        Returns:
            执行结果
        """
        try:
            task = asyncio.create_task(self.execute(context))
            result = await asyncio.wait_for(task, timeout=timeout)
            return result
        except asyncio.TimeoutError:
            logger.error(f"Plugin {self.metadata.name} execution timed out after {timeout}s")
            return {
                "success": False,
                "error": "timeout",
                "message": f"Plugin execution exceeded {timeout} second timeout"
            }
        except Exception as e:
            logger.error(f"Plugin {self.metadata.name} execution failed: {e}")
            if self._error_handler:
                await self._error_handler(e)
            else:
                await self.on_error(e)
            return {
                "success": False,
                "error": str(e),
                "message": "Plugin execution failed"
            }

    async def safe_execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        安全执行 - 自动处理异常和状态管理
        
        Args:
            context: 执行上下文
        
        Returns:
            执行结果字典
        """
        if self._status != PluginStatus.ACTIVE:
            return {
                "success": False,
                "error": "not_active",
                "message": f"Plugin is in {self._status.value} state, cannot execute"
            }

        try:
            self.status = PluginStatus.LOADING
            result = await self.execute_with_timeout(
                context,
                self.config.timeout
            )
            self.status = PluginStatus.ACTIVE
            return result
        except Exception as e:
            self.status = PluginStatus.ERROR
            return {
                "success": False,
                "error": "execution_error",
                "message": str(e)
            }

    async def initialize(self) -> bool:
        """默认初始化实现"""
        logger.info(f"Initializing plugin: {self.metadata.name}")
        self.status = PluginStatus.LOADING
        try:
            await self.on_load()
            self.status = PluginStatus.LOADED
            logger.info(f"Plugin {self.metadata.name} initialized successfully")
            return True
        except Exception as e:
            self.status = PluginStatus.ERROR
            logger.error(f"Failed to initialize plugin {self.metadata.name}: {e}")
            return False

    async def shutdown(self) -> bool:
        """默认关闭实现"""
        logger.info(f"Shutting down plugin: {self.metadata.name}")
        self.status = PluginStatus.UNLOADING
        try:
            # 执行清理回调
            for callback in self._cleanup_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.warning(f"Cleanup callback failed: {e}")
            
            await self.on_unload()
            self.status = PluginStatus.UNLOADED
            logger.info(f"Plugin {self.metadata.name} shutdown successfully")
            return True
        except Exception as e:
            self.status = PluginStatus.ERROR
            logger.error(f"Failed to shutdown plugin {self.metadata.name}: {e}")
            return False

    async def on_error(self, error: Exception) -> None:
        """默认错误处理"""
        logger.error(f"Plugin {self.metadata.name} error: {error}")
