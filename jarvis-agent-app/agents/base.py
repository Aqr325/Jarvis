"""
Agent 基类 - 提供通用功能和默认实现
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from .interface import (
    AgentInterface,
    AgentMetadata,
    AgentConfig,
    AgentRole,
    AgentStatus,
)


logger = logging.getLogger(__name__)


class AgentBase(AgentInterface):
    """
    Agent 基类
    
    所有自定义 Agent 都应该继承这个基类：
    
    ```python
    class ResearchAgent(AgentBase):
        @property
        def metadata(self) -> AgentMetadata:
            return AgentMetadata(
                name="Research Agent",
                role=AgentRole.RESEARCHER,
                description="负责信息搜集和研究",
                capabilities=[AgentCapability.RESEARCH, AgentCapability.NLP],
                expertise=["web search", "data analysis", "report writing"],
            )
        
        @property
        def config(self) -> AgentConfig:
            return AgentConfig(
                enabled=True,
                auto_assign=True,
                temperature=0.7,
            )
        
        async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
            # 实现研究任务逻辑
            pass
    ```
    """

    def __init__(self):
        self._status = AgentStatus.IDLE
        self._current_task: Optional[Dict[str, Any]] = None
        self._task_history: List[Dict[str, Any]] = []
        self._error_handler: Optional[callable] = None
        self._context: Dict[str, Any] = {}

    @property
    def status(self) -> AgentStatus:
        """当前状态"""
        return self._status

    @status.setter
    def status(self, value: AgentStatus):
        self._status = value
        logger.debug(f"Agent {self.metadata.name} status changed to {value.value}")

    def set_context(self, context: Dict[str, Any]):
        """设置上下文"""
        self._context = context

    def register_error_handler(self, handler: callable):
        """注册错误处理器"""
        self._error_handler = handler

    def record_task(self, task: Dict[str, Any], result: Dict[str, Any]):
        """记录任务历史"""
        self._task_history.append({
            "task": task,
            "result": result,
            "timestamp": asyncio.get_event_loop().time(),
        })
        
        # 限制历史记录
        if len(self._task_history) > 100:
            self._task_history = self._task_history[-100:]

    async def execute_with_timeout(self, task: Dict[str, Any], timeout: int = 60) -> Dict[str, Any]:
        """带超时的执行"""
        try:
            task_id = task.get("task_id", "unknown")
            logger.info(f"Agent {self.metadata.name} executing task {task_id}")
            
            # 任务开始回调
            await self.on_task_start(task)
            
            # 执行任务
            task_future = asyncio.create_task(self._execute_task(task))
            result = await asyncio.wait_for(task_future, timeout=timeout)
            
            # 任务完成回调
            await self.on_task_complete(task, result)
            
            # 记录历史
            self.record_task(task, result)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task.get('task_id')} timed out after {timeout}s")
            return {
                "success": False,
                "error": "timeout",
                "message": f"任务执行超时（{timeout}秒）",
                "task_id": task.get("task_id"),
            }
        except Exception as e:
            logger.error(f"Task {task.get('task_id')} failed: {e}")
            await self.on_error(e, task)
            
            if self._error_handler:
                await self._error_handler(e, task)
            
            return {
                "success": False,
                "error": str(e),
                "message": "任务执行失败",
                "task_id": task.get("task_id"),
            }

    async def _execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """内部执行方法（子类实现）"""
        self._current_task = task
        self.status = AgentStatus.BUSY
        
        try:
            result = await self.execute(task)
            return result
        finally:
            self._current_task = None
            self.status = AgentStatus.IDLE

    async def collaborate(
        self,
        task: Dict[str, Any],
        collaborators: List[AgentInterface]
    ) -> Dict[str, Any]:
        """
        默认协作实现 - 简单顺序执行
        
        子类可以重写此方法实现更复杂的协作逻辑
        """
        if not collaborators:
            return await self.execute(task)
        
        # 按优先级排序
        collaborators.sort(
            key=lambda a: a.metadata.priority if hasattr(a, 'metadata') else 0,
            reverse=True
        )
        
        results = []
        current_context = task.copy()
        
        # 依次执行
        for agent in collaborators:
            try:
                result = await agent.execute(current_context)
                results.append({
                    "agent": agent.metadata.name if hasattr(agent, 'metadata') else "unknown",
                    "result": result,
                })
                
                # 更新上下文用于下一个 Agent
                if result.get("success"):
                    current_context = {**current_context, **result}
                    
            except Exception as e:
                logger.warning(f"Collaborator {agent.metadata.name if hasattr(agent, 'metadata') else 'unknown'} failed: {e}")
                results.append({
                    "agent": agent.metadata.name if hasattr(agent, 'metadata') else "unknown",
                    "error": str(e),
                })
        
        # 聚合结果
        return {
            "success": any(r.get("success", False) for r in results),
            "collaboration_results": results,
            "message": f"协作完成，{len(results)} 个 Agent 参与",
        }

    async def initialize(self) -> bool:
        """默认初始化"""
        logger.info(f"Initializing Agent: {self.metadata.name}")
        
        try:
            self.status = AgentStatus.IDLE
            logger.info(f"Agent {self.metadata.name} initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.metadata.name}: {e}")
            self.status = AgentStatus.ERROR
            return False

    async def shutdown(self) -> bool:
        """默认关闭"""
        logger.info(f"Shutting down Agent: {self.metadata.name}")
        
        try:
            self._task_history.clear()
            self._current_task = None
            self.status = AgentStatus.OFFLINE
            logger.info(f"Agent {self.metadata.name} shutdown successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to shutdown agent {self.metadata.name}: {e}")
            self.status = AgentStatus.ERROR
            return False

    async def on_task_start(self, task: Dict[str, Any]) -> None:
        """默认任务开始回调"""
        pass

    async def on_task_complete(self, task: Dict[str, Any], result: Dict[str, Any]) -> None:
        """默认任务完成回调"""
        pass

    async def on_error(self, error: Exception, task: Optional[Dict[str, Any]] = None) -> None:
        """默认错误处理"""
        logger.error(f"Agent {self.metadata.name} error: {error}")

    def can_handle(self, task_type: str) -> bool:
        """默认实现：所有 Agent 都能处理"""
        # 子类可以重写此方法
        return True

    def get_preferred_tasks(self) -> List[str]:
        """返回偏好的任务类型"""
        return []

    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self._task_history[-limit:]
