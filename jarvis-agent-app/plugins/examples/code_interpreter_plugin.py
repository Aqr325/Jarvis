"""
代码解释器插件示例
安全执行和解释代码片段
"""

from typing import Any, Dict, List
import logging
import ast
import re

from plugins.interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginCapability,
)
from plugins.base import PluginBase


logger = logging.getLogger(__name__)


class CodeInterpreterPlugin(PluginBase):
    """
    代码解释器插件
    
    安全地执行和解释代码片段，支持：
    - Python 代码执行（沙盒模式）
    - 代码分析和解释
    - 代码转换和重构
    - 代码生成
    """

    # 允许的内置函数
    ALLOWED_BUILTINS = {
        'print', 'len', 'str', 'int', 'float', 'list', 'dict', 'set', 'tuple',
        'sum', 'min', 'max', 'abs', 'round', 'sorted', 'reversed', 'enumerate',
        'zip', 'map', 'filter', 'range', 'True', 'False', 'None',
    }

    # 允许的模块
    ALLOWED_MODULES = {
        'math', 'random', 'datetime', 'collections', 'itertools', 'functools',
        'typing', 'json', 're', 'os', 'sys',
    }

    def __init__(self):
        super().__init__()
        self._execution_history: List[Dict[str, Any]] = []
        self._sandbox_enabled = True

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Code Interpreter Plugin",
            version="1.0.0",
            author="JARVIS Team",
            description="安全代码解释和执行插件，支持 Python 代码沙盒执行和代码分析",
            capabilities=[PluginCapability.TOOL_PROVIDER, PluginCapability.NLP_EXTENSION],
            tags=["code", "python", "interpreter", "sandbox"],
            priority=15,
        )

    @property
    def config(self) -> PluginConfig:
        return PluginConfig(
            enabled=True,
            auto_load=False,
            config={
                "sandbox_enabled": True,
                "max_execution_time": 5,
                "max_output_length": 1000,
                "allowed_modules": list(self.ALLOWED_MODULES),
            },
            timeout=10,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing CodeInterpreterPlugin...")
        success = await super().initialize()
        if success:
            self._sandbox_enabled = self.config.config.get("sandbox_enabled", True)
            logger.info(f"CodeInterpreterPlugin initialized with sandbox: {self._sandbox_enabled}")
        return success

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行代码解释任务
        
        Args:
            context: 包含 'code', 'task' (execute/analyze/explain/generate)
        
        Returns:
            执行结果
        """
        code = context.get("code", context.get("input", ""))
        task = context.get("task", "execute")
        
        if not code:
            return {
                "success": False,
                "error": "no_code",
                "message": "请提供代码",
            }

        try:
            if task == "execute":
                return await self._execute_code(code)
            elif task == "analyze":
                return self._analyze_code(code)
            elif task == "explain":
                return await self._explain_code(code)
            elif task == "generate":
                return await self._generate_code(context.get("prompt", code))
            else:
                return {
                    "success": False,
                    "error": "unknown_task",
                    "message": f"未知任务类型: {task}",
                }
            
        except Exception as e:
            logger.error(f"Code interpreter error: {e}")
            return {
                "success": False,
                "error": "execution_error",
                "message": str(e),
            }

    async def _execute_code(self, code: str) -> Dict[str, Any]:
        """
        安全执行代码
        
        使用 AST 进行静态分析，确保代码安全
        """
        # 安全检查
        safety_check = self._check_code_safety(code)
        if not safety_check["safe"]:
            return {
                "success": False,
                "error": "unsafe_code",
                "message": safety_check["reason"],
                "details": safety_check["details"],
            }

        # 准备执行环境
        safe_globals = {
            "__builtins__": {k: __builtins__[k] for k in self.ALLOWED_BUILTINS if k in __builtins__},
        }
        
        # 导入允许模块
        for module_name in self.config.config.get("allowed_modules", []):
            try:
                module = __import__(module_name)
                safe_globals[module_name] = module
            except ImportError:
                pass

        try:
            # 执行代码
            local_vars = {}
            
            # 限制输出长度
            original_print = safe_globals.get('print', print)
            
            def safe_print(*args, **kwargs):
                output = ' '.join(map(str, args))
                if len(output) > self.config.config.get("max_output_length", 1000):
                    output = output[:self.config.config["max_output_length"]] + "... (truncated)"
                print(output, **kwargs)
            
            safe_globals['print'] = safe_print
            
            # 执行
            exec(code, safe_globals, local_vars)
            
            # 获取结果
            result_vars = {k: v for k, v in local_vars.items() 
                          if not k.startswith('_') and not callable(v)}
            
            self._record_history(code, "execute", success=True)
            
            return {
                "success": True,
                "task": "execute",
                "result": result_vars,
                "message": "代码执行成功",
            }
            
        except Exception as e:
            self._record_history(code, "execute", success=False, error=str(e))
            return {
                "success": False,
                "error": "runtime_error",
                "message": str(e),
            }

    def _check_code_safety(self, code: str) -> Dict[str, Any]:
        """检查代码安全性"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                "safe": False,
                "reason": "语法错误",
                "details": str(e),
            }
        
        # 检查禁止的节点类型
        prohibited_types = {
            ast.ImportFrom,  # from import
            ast.Call,  # 函数调用（检查具体函数）
            ast.Attribute,  # 属性访问
        }
        
        dangerous_calls = {'eval', 'exec', 'compile', 'open', 'input', '__import__'}
        dangerous_attrs = {'__import__', 'eval', 'exec', 'compile', 'open', 'system', 'popen'}
        
        for node in ast.walk(tree):
            # 检查危险调用
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in dangerous_calls:
                    return {
                        "safe": False,
                        "reason": f"禁止的函数调用: {node.func.id}",
                        "details": "使用 eval/exec/open 等函数存在安全风险",
                    }
                
                # 检查模块方法调用
                if isinstance(node.func, ast.Attribute):
                    attr_chain = self._get_attribute_chain(node.func)
                    if any(d in attr_chain for d in dangerous_attrs):
                        return {
                            "safe": False,
                            "reason": f"禁止的属性访问: {attr_chain}",
                            "details": f"访问 {attr_chain} 存在安全风险",
                        }
            
            # 检查动态导入
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module not in self.ALLOWED_MODULES:
                    return {
                        "safe": False,
                        "reason": f"不允许的模块: {node.module}",
                        "details": f"只能导入以下模块: {', '.join(self.ALLOWED_MODULES)}",
                    }
        
        return {"safe": True, "reason": "", "details": []}

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """获取完整的属性链"""
        parts = []
        current = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
        return '.'.join(reversed(parts))

    def _analyze_code(self, code: str) -> Dict[str, Any]:
        """分析代码"""
        try:
            tree = ast.parse(code)
            
            # 统计信息
            stats = {
                "lines": len(code.split('\n')),
                "functions": sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)),
                "classes": sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef)),
                "imports": sum(1 for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
                "loops": sum(1 for node in ast.walk(tree) if isinstance(node, (ast.For, ast.While))),
                "conditionals": sum(1 for node in ast.walk(tree) if isinstance(node, ast.If)),
            }
            
            # 复杂度分析
            complexity = self._calculate_complexity(tree)
            
            return {
                "success": True,
                "task": "analyze",
                "statistics": stats,
                "complexity": complexity,
                "suggestions": self._get_code_suggestions(code, stats, complexity),
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "error": "syntax_error",
                "message": f"语法错误: {str(e)}",
            }

    def _calculate_complexity(self, tree: ast.AST) -> Dict[str, Any]:
        """计算代码复杂度"""
        # 简单的圈复杂度计算
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        
        return {
            "cyclomatic": complexity,
            "level": "低" if complexity < 5 else "中" if complexity < 10 else "高",
        }

    async def _explain_code(self, code: str) -> Dict[str, Any]:
        """解释代码"""
        # 简单解释：基于代码结构
        try:
            tree = ast.parse(code)
            
            explanations = []
            
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    explanations.append(f"函数 `{node.name}`: 定义了一个函数")
                elif isinstance(node, ast.ClassDef):
                    explanations.append(f"类 `{node.name}`: 定义了一个类")
                elif isinstance(node, ast.Assign):
                    explanations.append("变量赋值: 设置变量值")
            
            return {
                "success": True,
                "task": "explain",
                "explanations": explanations,
                "summary": f"这段代码包含 {len(explanations)} 个主要组成部分",
            }
            
        except SyntaxError as e:
            return {
                "success": False,
                "error": "syntax_error",
                "message": f"无法解释代码（语法错误）: {str(e)}",
            }

    async def _generate_code(self, prompt: str) -> Dict[str, Any]:
        """生成代码（简单实现）"""
        # 这里可以集成 LLM 来生成代码
        # 暂时返回一个示例
        
        generated_code = f"""# 根据需求生成的代码示例
# 需求: {prompt}

def example_function():
    '''示例函数'''
    print("代码生成示例")
    return True
"""
        
        return {
            "success": True,
            "task": "generate",
            "generated_code": generated_code,
            "language": "python",
        }

    def _get_code_suggestions(self, code: str, stats: Dict, complexity: Dict) -> List[str]:
        """获取代码改进建议"""
        suggestions = []
        
        if stats["functions"] == 0 and stats["lines"] > 20:
            suggestions.append("考虑将代码拆分为多个函数以提高可读性")
        
        if complexity["cyclomatic"] > 10:
            suggestions.append("代码复杂度较高，建议简化逻辑或使用更早返回模式")
        
        if '  ' in code and '    ' not in code:
            suggestions.append("建议使用 4 个空格进行缩进")
        
        return suggestions

    def _record_history(self, code: str, task: str, success: bool, error: str = ""):
        """记录执行历史"""
        self._execution_history.append({
            "code": code[:200] + "..." if len(code) > 200 else code,
            "task": task,
            "success": success,
            "error": error,
        })
        
        # 限制历史数量
        if len(self._execution_history) > 50:
            self._execution_history = self._execution_history[-50:]

    def get_tools(self) -> List[Dict[str, Any]]:
        """返回代码工具"""
        return [
            {
                "name": "execute_code",
                "description": "安全执行 Python 代码片段",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要执行的 Python 代码"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "analyze_code",
                "description": "分析代码结构和复杂度",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要分析的代码"
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "explain_code",
                "description": "解释代码的功能",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "要解释的代码"
                        }
                    },
                    "required": ["code"]
                }
            },
        ]

    async def shutdown(self) -> bool:
        logger.info("Shutting down CodeInterpreterPlugin...")
        self._execution_history.clear()
        return await super().shutdown()
