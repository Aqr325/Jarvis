"""
程序员 Agent 示例
负责代码生成、审查和调试
"""

import logging
import re
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


class CoderAgent(AgentBase):
    """
    程序员 Agent
    
    负责：
    - 代码生成
    - 代码审查
    - 调试和错误修复
    - 代码重构
    """

    SUPPORTED_LANGUAGES = ["python", "javascript", "typescript", "java", "go", "rust", "cpp", "html", "css"]

    def __init__(self):
        super().__init__()
        self._code_history: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            name="Coder Agent",
            role=AgentRole.PROGRAMMER,
            description="专业的程序员 Agent，负责代码生成、审查和调试",
            capabilities=[
                AgentCapability.CODING,
                AgentCapability.ANALYSIS,
                AgentCapability.AUTOMATION,
            ],
            expertise=[
                "python",
                "javascript",
                "typescript",
                "web development",
                "api design",
                "code review",
                "debugging",
            ],
            priority=15,
        )

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            enabled=True,
            auto_assign=True,
            temperature=0.3,  # 代码需要更准确
            max_tokens=4000,
            timeout=180,
            context_window=8192,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing CoderAgent...")
        success = await super().initialize()
        if success:
            logger.info("CoderAgent initialized successfully")
        return success

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行编程任务
        
        Args:
            task: 包含 'task_type', 'language', 'prompt' 等字段
        
        Returns:
            代码结果
        """
        task_type = task.get("task_type", "code_generation")
        language = task.get("language", "python").lower()
        prompt = task.get("prompt", task.get("description", ""))

        if not prompt:
            return {
                "success": False,
                "error": "no_prompt",
                "message": "请提供编程需求描述",
            }

        if language not in self.SUPPORTED_LANGUAGES:
            return {
                "success": False,
                "error": "unsupported_language",
                "message": f"不支持的语言: {language}，支持: {', '.join(self.SUPPORTED_LANGUAGES)}",
            }

        try:
            self.status = AgentStatus.BUSY
            
            # 根据任务类型分发
            if task_type == "code_generation":
                result = await self._generate_code(prompt, language)
            elif task_type == "code_review":
                result = await self._review_code(task)
            elif task_type == "debug":
                result = await self._debug_code(task)
            elif task_type == "refactor":
                result = await self._refactor_code(task)
            else:
                result = await self._generate_code(prompt, language)
            
            # 记录历史
            self._code_history.append({
                "task_type": task_type,
                "language": language,
                "result": result,
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Programming task failed: {e}")
            return {
                "success": False,
                "error": "programming_error",
                "message": str(e),
            }
        finally:
            self.status = AgentStatus.IDLE

    async def _generate_code(self, prompt: str, language: str) -> Dict[str, Any]:
        """生成代码"""
        # 模拟代码生成
        if language == "python":
            code = self._generate_python_code(prompt)
        elif language in ["javascript", "typescript"]:
            code = self._generate_javascript_code(prompt, language)
        else:
            code = self._generate_generic_code(prompt, language)
        
        return {
            "success": True,
            "task_type": "code_generation",
            "language": language,
            "code": code,
            "language_info": {
                "name": language,
                "extension": ".py" if language == "python" else f".{language[:3]}",
            },
        }

    def _generate_python_code(self, prompt: str) -> str:
        """生成 Python 代码"""
        return f'''"""
根据需求生成的 Python 代码
需求: {prompt}
"""

def solution_function(input_data):
    """
    根据需求实现的功能函数
    
    Args:
        input_data: 输入数据
    
    Returns:
        处理结果
    """
    # TODO: 实现具体逻辑
    result = None
    
    # 处理逻辑
    # ...
    
    return result


if __name__ == "__main__":
    # 测试代码
    sample_input = {{}}
    result = solution_function(sample_input)
    print(f"结果: {{result}}")
'''

    def _generate_javascript_code(self, prompt: str, language: str) -> str:
        """生成 JavaScript/TypeScript 代码"""
        extension = "ts" if language == "typescript" else "js"
        return f'''/**
 * 根据需求生成的 {language.upper()} 代码
 * 需求: {prompt}
 */

function solutionFunction(inputData) {{
    /**
     * 根据需求实现的功能函数
     * @param {{Object}} inputData - 输入数据
     * @returns {{Promise<Object>}} 处理结果
     */
    
    // TODO: 实现具体逻辑
    let result = null;
    
    // 处理逻辑
    // ...
    
    return result;
}}

// 导出
module.exports = {{ solutionFunction }};
'''

    def _generate_generic_code(self, prompt: str, language: str) -> str:
        """生成通用代码"""
        return f'''// {language.upper()} 代码示例
// 需求: {prompt}

// TODO: 根据具体需求实现代码逻辑
'''

    async def _review_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """代码审查"""
        code = task.get("code", "")
        language = task.get("language", "python").lower()
        
        issues = []
        
        # 简单代码质量检查
        if len(code) == 0:
            issues.append({"type": "error", "message": "代码为空"})
        
        # 检查代码风格
        if "TODO" in code:
            issues.append({"type": "warning", "message": "代码包含 TODO 标记，尚未完成"})
        
        if code.count("  ") > 10:  # 多个连续空格
            issues.append({"type": "suggestion", "message": "建议统一缩进风格"})
        
        # 计算代码行数
        lines = code.split('\n')
        loc = len(lines)
        blank_lines = sum(1 for line in lines if line.strip() == "")
        comment_lines = sum(1 for line in lines if line.strip().startswith('#') or line.strip().startswith('//'))
        
        return {
            "success": True,
            "task_type": "code_review",
            "language": language,
            "statistics": {
                "total_lines": loc,
                "blank_lines": blank_lines,
                "comment_lines": comment_lines,
                "code_lines": loc - blank_lines - comment_lines,
            },
            "issues": issues,
            "summary": f"代码审查完成，共 {loc} 行，发现 {len(issues)} 个潜在问题",
            "quality_score": max(0, 100 - len(issues) * 10),
        }

    async def _debug_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """调试代码"""
        code = task.get("code", "")
        error_message = task.get("error", "")
        
        suggestions = []
        
        if "undefined" in error_message.lower() or "NameError" in error_message:
            suggestions.append("检查变量是否已定义")
        
        if "type" in error_message.lower():
            suggestions.append("检查数据类型是否正确")
        
        if "index" in error_message.lower() or "out of range" in error_message.lower():
            suggestions.append("检查数组/列表索引是否越界")
        
        if "permission" in error_message.lower():
            suggestions.append("检查文件/资源访问权限")
        
        return {
            "success": True,
            "task_type": "debug",
            "error_analysis": error_message,
            "suggestions": suggestions if suggestions else ["请提供更多错误信息以便诊断"],
            "debug_steps": [
                "1. 复现错误",
                "2. 检查输入数据",
                "3. 逐步调试关键代码",
                "4. 验证修复方案",
            ],
        }

    async def _refactor_code(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """重构代码"""
        code = task.get("code", "")
        refactoring_type = task.get("refactoring_type", "general")
        
        improvements = []
        
        if refactoring_type in ["general", "readability"]:
            improvements.append("提取重复代码为函数")
            improvements.append("添加清晰的变量和函数命名")
            improvements.append("添加文档字符串")
        
        if refactoring_type in ["general", "performance"]:
            improvements.append("优化循环内的重复计算")
            improvements.append("使用更高效的数据结构")
        
        if refactoring_type in ["general", "maintainability"]:
            improvements.append("遵循单一职责原则")
            improvements.append("添加类型提示")
        
        return {
            "success": True,
            "task_type": "refactor",
            "refactoring_type": refactoring_type,
            "improvements": improvements,
            "estimated_effort": "中等",
            "priority_issues": ["建议优先处理性能相关的改进"],
        }

    def can_handle(self, task_type: str) -> bool:
        """检查是否能处理任务类型"""
        coding_tasks = [
            "code_generation",
            "code_review",
            "debug",
            "refactor",
        ]
        return task_type in coding_tasks

    def get_preferred_tasks(self) -> List[str]:
        """返回偏好的任务类型"""
        return ["code_generation", "code_review"]

    async def shutdown(self) -> bool:
        logger.info("Shutting down CoderAgent...")
        self._code_history.clear()
        return await super().shutdown()
