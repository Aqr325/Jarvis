"""
示例 Agent 模块
包含三个角色分工明确的 Agent：研究员、程序员、作家
"""

from .research_agent import ResearchAgent
from .coder_agent import CoderAgent
from .writer_agent import WriterAgent

__all__ = ["ResearchAgent", "CoderAgent", "WriterAgent"]
