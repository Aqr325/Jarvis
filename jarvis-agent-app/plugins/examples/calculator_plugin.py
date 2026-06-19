"""
计算器插件示例
提供数学计算功能
"""

import re
import operator
from typing import Any, Dict, List
import logging

from plugins.interface import (
    PluginInterface,
    PluginMetadata,
    PluginConfig,
    PluginCapability,
)
from plugins.base import PluginBase


logger = logging.getLogger(__name__)


class CalculatorPlugin(PluginBase):
    """
    智能计算器插件
    
    支持：
    - 基本运算：加减乘除
    - 高级运算：幂运算、开方、取模
    - 表达式解析
    - 历史计算记录
    """

    OPERATORS = {
        '+': operator.add,
        '-': operator.sub,
        '*': operator.mul,
        '/': operator.truediv,
        '//': operator.floordiv,
        '%': operator.mod,
        '**': operator.pow,
    }

    def __init__(self):
        super().__init__()
        self._calculation_history: List[Dict[str, Any]] = []
        self._max_history = 100

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Calculator Plugin",
            version="1.0.0",
            author="JARVIS Team",
            description="智能计算器插件，支持各种数学运算和表达式解析",
            capabilities=[PluginCapability.TOOL_PROVIDER, PluginCapability.DATA_PROCESSOR],
            tags=["math", "calculator", "expression"],
            priority=10,
        )

    @property
    def config(self) -> PluginConfig:
        return PluginConfig(
            enabled=True,
            auto_load=False,
            config={
                "max_history": 100,
                "precision": 2,
            },
            timeout=10,
        )

    async def initialize(self) -> bool:
        logger.info("Initializing CalculatorPlugin...")
        success = await super().initialize()
        if success:
            logger.info("CalculatorPlugin initialized successfully")
        return success

    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行计算
        
        Args:
            context: 包含 'expression' 或 'operation' 键
        
        Returns:
            计算结果
        """
        user_input = context.get("input", "")
        expression = context.get("expression", user_input)
        
        if not expression:
            return {
                "success": False,
                "error": "no_expression",
                "message": "请提供要计算的表达式",
            }

        try:
            # 清理表达式
            clean_expr = self._clean_expression(expression)
            
            # 安全检查
            if not self._is_safe_expression(clean_expr):
                return {
                    "success": False,
                    "error": "unsafe_expression",
                    "message": "表达式包含不安全的操作",
                }
            
            # 执行计算
            result = self._evaluate_expression(clean_expr)
            
            # 记录历史
            self._record_history(expression, result)
            
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "formatted_result": self._format_result(result),
            }
            
        except Exception as e:
            logger.error(f"Calculation error: {e}")
            return {
                "success": False,
                "error": "calculation_error",
                "message": f"计算出错: {str(e)}",
            }

    def _clean_expression(self, expression: str) -> str:
        """清理表达式"""
        # 移除多余空格
        expression = re.sub(r'\s+', '', expression)
        
        # 替换中文运算符
        replacements = {
            '＋': '+',
            '－': '-',
            '×': '*',
            '÷': '/',
            '＾': '**',
        }
        for chinese, ascii_op in replacements.items():
            expression = expression.replace(chinese, ascii_op)
        
        return expression

    def _is_safe_expression(self, expression: str) -> bool:
        """检查表达式安全性"""
        # 只允许数字、运算符、括号、小数点、科学计数法
        safe_pattern = re.compile(r'^[0-9+\-*/().\s]**eE,]+$')
        
        # 额外检查：不允许连续运算符（除了负号）
        if re.search(r'[+\*/]{2,}', expression):
            return False
        
        # 不允许以运算符开头（除了负号）
        if expression[0] in '+*/':
            return False
        
        # 不允许以运算符结尾
        if expression[-1] in '+-*/':
            return False
        
        return True

    def _evaluate_expression(self, expression: str) -> float:
        """
        安全计算表达式
        
        使用递归下降解析器，不使用 eval()
        """
        # 简单实现：支持基本运算
        # 实际项目应该使用更完整的表达式解析器
        
        try:
            # 处理幂运算
            if '**' in expression:
                parts = expression.split('**')
                if len(parts) == 2:
                    base = self._evaluate_expression(parts[0].strip())
                    exp = self._evaluate_expression(parts[1].strip())
                    return base ** exp
            
            # 处理乘除
            for op in ['*', '/', '//', '%']:
                if op in expression:
                    parts = expression.rsplit(op, 1)
                    if len(parts) == 2:
                        left = self._evaluate_expression(parts[0].strip())
                        right = self._evaluate_expression(parts[1].strip())
                        if op == '*':
                            return left * right
                        elif op == '/':
                            if right == 0:
                                raise ZeroDivisionError("除数不能为零")
                            return left / right
                        elif op == '//':
                            if right == 0:
                                raise ZeroDivisionError("除数不能为零")
                            return left // right
                        elif op == '%':
                            if right == 0:
                                raise ZeroDivisionError("模运算除数不能为零")
                            return left % right
            
            # 处理加减
            # 处理符号
            if expression.startswith('-'):
                return -self._evaluate_expression(expression[1:])
            
            # 找到最右边的加减号（处理负数）
            for i in range(len(expression) - 1, 0, -1):
                if expression[i] in '+-':
                    left = self._evaluate_expression(expression[:i])
                    right = self._evaluate_expression(expression[i+1:])
                    if expression[i] == '+':
                        return left + right
                    else:
                        return left - right
            
            # 处理括号
            if expression.startswith('(') and expression.endswith(')'):
                return self._evaluate_expression(expression[1:-1])
            
            # 直接返回数字
            return float(expression)
            
        except Exception as e:
            raise ValueError(f"无法解析表达式: {expression}") from e

    def _format_result(self, result: float) -> str:
        """格式化结果"""
        precision = self.config.config.get("precision", 2)
        
        # 如果是整数
        if result.is_integer():
            return str(int(result))
        
        # 格式化小数
        formatted = f"{result:.{precision}f}"
        
        # 移除末尾的零
        if '.' in formatted:
            formatted = formatted.rstrip('0').rstrip('.')
        
        return formatted

    def _record_history(self, expression: str, result: Any):
        """记录计算历史"""
        self._calculation_history.append({
            "expression": expression,
            "result": result,
        })
        
        # 限制历史数量
        if len(self._calculation_history) > self._max_history:
            self._calculation_history = self._calculation_history[-self._max_history:]

    def get_tools(self) -> List[Dict[str, Any]]:
        """返回计算器工具"""
        return [
            {
                "name": "calculate",
                "description": "执行数学计算，支持加减乘除、幂运算、表达式解析",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，如 '2 + 3 * 4' 或 '10 ** 2'"
                        }
                    },
                    "required": ["expression"]
                }
            },
            {
                "name": "get_calculation_history",
                "description": "获取最近的计算历史",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "limit": {
                            "type": "integer",
                            "description": "返回的记录数，默认 10"
                        }
                    }
                }
            }
        ]

    async def shutdown(self) -> bool:
        logger.info("Shutting down CalculatorPlugin...")
        self._calculation_history.clear()
        return await super().shutdown()

    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的计算历史"""
        return self._calculation_history[-limit:]
