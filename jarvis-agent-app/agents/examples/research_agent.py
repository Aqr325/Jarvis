"""
研究员 Agent 示例
负责信息搜集、分析和报告生成
"""

import logging
from typing import Any, Dict, List

from agents.interface import (
    AgentInterface,
    AgentMetadata,
    AgentConfig,
    AgentRole,
    AgentCapability,
    AgentStatus,
)
from agents.base import AgentBase


logger = logging.getLogger(__name__)


class ResearchAgent(AgentBase):
    """
    研究员 Agent
    
    负责：
    - 信息搜集和整理
    - 资料分析
    - 报告撰写
    - 趋势预测
    """

    def __init__(self):
        super().__init__()
        self._research_history: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="Research Agent",
            role=AgentRole.RESEARCHER,
            description="专业的研究员 Agent，负责信息搜集、分析和报告生成",
            capabilities=[
                AgentCapability.RESEARCH,
                AgentCapability.NLP,
                AgentCapability.ANALYSIS,
            ],
            expertise=[
                "web research",
                "data analysis",
                "trend analysis",
                "report writing",
                "competitive analysis",
            ],
            priority=10,
        )

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            enabled=True,
            auto_assign=True,
            temperature=0.5,  # 研究需要更准确的答案
            max_tokens=3000,
            timeout=120,
            context_window=4096,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing ResearchAgent...")
        success = await super().initialize()
        if success:
            logger.info("ResearchAgent initialized successfully")
        return success

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行研究任务
        
        Args:
            task: 包含 'topic', 'scope', 'depth' 等字段
        
        Returns:
            研究结果
        """
        task_type = task.get("task_type", "general_research")
        topic = task.get("topic", task.get("query", ""))
        scope = task.get("scope", "general")
        depth = task.get("depth", "standard")

        if not topic:
            return {
                "success": False,
                "error": "no_topic",
                "message": "请提供研究主题",
            }

        try:
            self.status = AgentStatus.BUSY
            
            # 根据任务类型分发
            if task_type == "web_research":
                result = await self._web_research(topic, scope, depth)
            elif task_type == "competitive_analysis":
                result = await self._competitive_analysis(topic)
            elif task_type == "trend_analysis":
                result = await self._trend_analysis(topic)
            elif task_type == "data_analysis":
                result = await self._data_analysis(task)
            else:
                result = await self._general_research(topic, scope, depth)
            
            # 记录历史
            self._research_history.append({
                "topic": topic,
                "task_type": task_type,
                "result": result,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Research task failed: {e}")
            return {
                "success": False,
                "error": "research_error",
                "message": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    async def _web_research(self, topic: str, scope: str, depth: str) -> Dict[str, Any]:
        """网络研究"""
        # 模拟研究过程
        findings = [
            {"source": "web", "title": f"{topic} - 概述", "summary": f"关于 {topic} 的综合介绍"},
            {"source": "web", "title": f"{topic} - 最新发展", "summary": f"{topic} 领域的最新动态"},
            {"source": "web", "title": f"{topic} - 行业分析", "summary": f"{topic} 的行业现状和未来趋势"},
        ]
        
        return {
            "success": True,
            "topic": topic,
            "task_type": "web_research",
            "findings": findings,
            "summary": self._generate_summary(findings),
            "sources_count": len(findings),
        }

    async def _competitive_analysis(self, topic: str) -> Dict[str, Any]:
        """竞品分析"""
        analysis = {
            "competitors": [
                {
                    "name": f"竞品 A - {topic}",
                    "strengths": ["技术领先", "用户口碑好", "市场覆盖广"],
                    "weaknesses": ["价格较高", "功能复杂"],
                },
                {
                    "name": f"竞品 B - {topic}",
                    "strengths": ["价格亲民", "易用性强"],
                    "weaknesses": ["功能较少", "性能一般"],
                },
            ],
            "market_position": "中等",
            "recommendations": ["差异化竞争", "关注用户体验"],
        }
        
        return {
            "success": True,
            "topic": topic,
            "task_type": "competitive_analysis",
            "analysis": analysis,
        }

    async def _trend_analysis(self, topic: str) -> Dict[str, Any]:
        """趋势分析"""
        trends = {
            "current_trends": [
                f"{topic} 正在向 AI 驱动方向发展",
                "用户偏好个性化和定制化",
                "跨平台集成成为趋势",
            ],
            "future_predictions": [
                "预计未来 1-2 年内技术将更加成熟",
                "市场规模将持续增长",
                "行业竞争将更加激烈",
            ],
            "opportunities": ["技术创新", "市场拓展", "用户体验优化"],
            "risks": ["技术迭代", "政策变化", "市场竞争"],
        }
        
        return {
            "success": True,
            "topic": topic,
            "task_type": "trend_analysis",
            "trends": trends,
        }

    async def _data_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """数据分析"""
        data = task.get("data", {})
        
        analysis = {
            "descriptive": {
                "mean": 0.0,
                "median": 0.0,
                "std": 0.0,
            },
            "insights": ["数据分析完成，发现关键趋势"],
            "recommendations": ["建议进一步挖掘细分领域"],
        }
        
        return {
            "success": True,
            "topic": task.get("topic", "数据分析"),
            "task_type": "data_analysis",
            "analysis": analysis,
        }

    async def _general_research(self, topic: str, scope: str, depth: str) -> Dict[str, Any]:
        """通用研究"""
        return await self._web_research(topic, scope, depth)

    def _generate_summary(self, findings: List[Dict[str, Any]]) -> str:
        """生成摘要"""
        if not findings:
            return "未找到相关信息"
        
        titles = [f["title"] for f in findings]
        return f"完成了关于 {', '.join(titles[:3])} 等主题的研究，共搜集到 {len(findings)} 份资料"

    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理任务类型"""
        research_tasks = [
            "web_research",
            "competitive_analysis",
            "trend_analysis",
            "data_analysis",
            "general_research",
        ]
        return task_type in research_tasks

    def get_preferred_tasks(self) -> List[str]:
        """返回偏好的任务类型"""
        return ["web_research", "competitive_analysis", "trend_analysis"]

    def get_research_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取研究历史"""
        return self._research_history[-limit:]

    async def shutdown(self) -> bool:
        logger.info("Shutting down ResearchAgent...")
        self._research_history.clear()
        return await super().shutdown()
