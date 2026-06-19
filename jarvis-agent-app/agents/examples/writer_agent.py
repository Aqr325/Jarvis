"""
作家 Agent 示例
负责内容创作、编辑和润色
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


class WriterAgent(AgentBase):
    """
    作家 Agent
    
    负责：
    - 文章写作
    - 内容编辑
    - 文案优化
    - 创意生成
    """

    WRITING_STYLES = [
        "professional",    # 专业
        "casual",          # 轻松
        "creative",        # 创意
        "technical",       # 技术
        "academic",        # 学术
        "marketing",       # 营销
    ]

    def __init__(self):
        super().__init__()
        self._writing_history: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="Writer Agent",
            role=AgentRole.WRITER,
            description="专业的作家 Agent，负责内容创作、编辑和润色",
            capabilities=[
                AgentCapability.WRITING,
                AgentCapability.NLP,
                AgentCapability.COMMUNICATION,
            ],
            expertise=[
                "article writing",
                "copywriting",
                "content editing",
                "creative writing",
                "technical documentation",
            ],
            priority=5,
        )

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            enabled=True,
            auto_assign=True,
            temperature=0.8,  # 写作需要更多创意
            max_tokens=3000,
            timeout=120,
            context_window=4096,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing WriterAgent...")
        success = await super().initialize()
        if success:
            logger.info("WriterAgent initialized successfully")
        return success

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行写作任务
        
        Args:
            task: 包含 'task_type', 'topic', 'style' 等字段
        
        Returns:
            写作结果
        """
        task_type = task.get("task_type", "article")
        topic = task.get("topic", task.get("title", ""))
        style = task.get("style", "professional")
        length = task.get("length", "medium")

        if not topic:
            return {
                "success": False,
                "error": "no_topic",
                "message": "请提供写作主题",
            }

        if style not in self.WRITING_STYLES:
            return {
                "success": False,
                "error": "unsupported_style",
                "message": f"不支持的风格: {style}，支持: {', '.join(self.WRITING_STYLES)}",
            }

        try:
            self.status = AgentStatus.BUSY
            
            # 根据任务类型分发
            if task_type == "article":
                result = await self._write_article(topic, style, length)
            elif task_type == "copywriting":
                result = await self._write_copy(topic, style)
            elif task_type == "edit":
                result = await self._edit_content(task)
            elif task_type == "summarize":
                result = await self._summarize_content(task)
            else:
                result = await self._write_article(topic, style, length)
            
            # 记录历史
            self._writing_history.append({
                "task_type": task_type,
                "topic": topic,
                "style": style,
                "result": result,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Writing task failed: {e}")
            return {
                "success": False,
                "error": "writing_error",
                "message": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    async def _write_article(self, topic: str, style: str, length: str) -> Dict[str, Any]:
        """写文章"""
        word_count_map = {
            "short": 300,
            "medium": 800,
            "long": 1500,
        }
        target_words = word_count_map.get(length, 800)
        
        # 生成文章大纲
        outline = [
            {"section": "引言", "content": f"介绍 {topic} 的背景和重要性"},
            {"section": "正文一", "content": f"{topic} 的核心概念解析"},
            {"section": "正文二", "content": f"{topic} 的应用场景和实践案例"},
            {"section": "正文三", "content": f"{topic} 的未来发展趋势"},
            {"section": "结论", "content": f"总结 {topic} 的价值和建议"},
        ]
        
        # 生成完整文章
        content = self._generate_article_content(topic, style, outline, target_words)
        
        return {
            "success": True,
            "task_type": "article",
            "topic": topic,
            "style": style,
            "word_count": len(content.split()),
            "outline": outline,
            "content": content,
            "estimated_reading_time": f"{len(content.split()) // 200} 分钟",
        }

    def _generate_article_content(self, topic: str, style: str, outline: List[Dict], target_words: int) -> str:
        """生成文章内容"""
        style_guides = {
            "professional": "正式、专业、客观",
            "casual": "轻松、友好、亲切",
            "creative": "生动、有趣、富有想象力",
            "technical": "准确、详细、逻辑性强",
            "academic": "严谨、规范、引用丰富",
            "marketing": "吸引人、有说服力、突出卖点",
        }
        
        style_guide = style_guides.get(style, "专业")
        
        content = f"""# {topic}

## 文章风格：{style_guide}

---

### 引言

{topic} 是当今备受关注的重要话题。随着技术的快速发展和市场需求的不断变化，深入理解 {topic} 变得越来越重要。本文将从多个角度探讨 {topic} 的核心内容。

### 核心概念

{topic} 包含了丰富的内涵和外延。其主要特点包括：

- **创新性**：不断涌现新的思路和方法
- **实用性**：能够解决实际问题
- **发展性**：持续演进和完善

### 应用场景

{topic} 在多个领域都有广泛的应用：

1. 企业级应用：帮助提升效率和竞争力
2. 个人发展：促进学习和成长
3. 社会价值：推动行业进步和创新

### 发展趋势

展望未来，{topic} 将呈现以下趋势：

- 技术融合：与其他技术相互结合
- 生态完善：形成完整的产业链
- 普及应用：走向大众市场

### 总结

{topic} 作为一个重要的领域，值得我们持续关注和研究。通过深入理解和实践，我们可以更好地把握机遇，迎接挑战。

---

*注：这是一篇示例文章，可根据具体需求进行定制和优化。*
"""
        return content

    async def _write_copy(self, topic: str, style: str) -> Dict[str, Any]:
        """写文案"""
        copy_types = ["slogan", "ad", "product", "social_media"]
        
        copies = []
        for copy_type in copy_types:
            if copy_type == "slogan":
                copies.append({
                    "type": "slogan",
                    "content": f"{topic} - 创新未来",
                    "length": "short",
                })
            elif copy_type == "ad":
                copies.append({
                    "type": "ad",
                    "content": f"发现 {topic} 的魅力，开启全新体验...",
                    "length": "medium",
                })
            elif copy_type == "product":
                copies.append({
                    "type": "product",
                    "content": f"{topic}：品质卓越，体验非凡",
                    "length": "short",
                })
            else:
                copies.append({
                    "type": "social_media",
                    "content": f"🔥 热议：{topic} 正在改变世界！#创新 #{topic}",
                    "length": "short",
                })
        
        return {
            "success": True,
            "task_type": "copywriting",
            "topic": topic,
            "style": style,
            "copies": copies,
        }

    async def _edit_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """编辑内容"""
        content = task.get("content", "")
        edit_type = task.get("edit_type", "grammar")

        suggestions = []
        
        # 语法检查
        if edit_type in ["grammar", "all"]:
            if "  " in content:
                suggestions.append({"type": "grammar", "message": "建议统一空格使用"})
            if content.count("？") != content.count("?"):
                suggestions.append({"type": "punctuation", "message": "标点符号使用不一致"})
        
        # 风格检查
        if edit_type in ["style", "all"]:
            if len(content) < 100:
                suggestions.append({"type": "style", "message": "内容较短，可考虑扩充"})
        
        # 可读性分析
        sentences = content.split('。')
        avg_sentence_length = sum(len(s) for s in sentences if s.strip()) / max(len(sentences), 1)
        
        return {
            "success": True,
            "task_type": "edit",
            "edit_type": edit_type,
            "suggestions": suggestions,
            "analysis": {
                "word_count": len(content),
                "sentence_count": len(sentences),
                "avg_sentence_length": round(avg_sentence_length, 1),
                "readability_score": min(100, max(0, 100 - len(suggestions) * 5)),
            },
            "edited_content": content,  # 实际应该返回修改后的内容
        }

    async def _summarize_content(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """内容摘要"""
        content = task.get("content", "")
        summary_length = task.get("summary_length", "short")

        if len(content) < 50:
            return {
                "success": False,
                "error": "content_too_short",
                "message": "内容过短，无法生成摘要",
            }

        # 简单摘要生成
        sentences = content.split('。')
        key_sentences = sentences[:min(3, len(sentences))]
        summary = '。'.join(key_sentences) + '。'

        return {
            "success": True,
            "task_type": "summarize",
            "original_length": len(content),
            "summary_length": len(summary),
            "summary": summary,
            "compression_ratio": f"{len(summary) / len(content) * 100:.1f}%",
        }

    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理任务类型"""
        writing_tasks = [
            "article",
            "copywriting",
            "edit",
            "summarize",
        ]
        return task_type in writing_tasks

    def get_preferred_tasks(self) -> List[str]:
        """返回偏好的任务类型"""
        return ["article", "copywriting"]

    async def shutdown(self) -> bool:
        logger.info("Shutting down WriterAgent...")
        self._writing_history.clear()
        return await super().shutdown()
