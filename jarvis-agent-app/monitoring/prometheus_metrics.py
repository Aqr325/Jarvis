"""
Prometheus 指标收集
"""

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from typing import Dict, Any
import time
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# API 指标
# =============================================================================

# API 请求总数
api_requests_total = Counter(
    "api_requests_total",
    "Total API requests",
    ["endpoint", "method", "status_code", "user_role"],
)

# API 请求延迟
api_request_duration = Histogram(
    "api_request_duration_seconds",
    "API request duration in seconds",
    ["endpoint", "method"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)

# API 请求处理时间摘要
api_request_summary = Summary(
    "api_request_summary_seconds",
    "API request processing summary",
    ["endpoint"],
)

# =============================================================================
# Agent 指标
# =============================================================================

# 活跃 Agent 数量
agent_active_count = Gauge(
    "agent_active_count",
    "Number of active agents",
    ["agent_type", "role"],
)

# Agent 任务执行总数
agent_tasks_total = Counter(
    "agent_tasks_total",
    "Total tasks executed by agents",
    ["agent_name", "task_type", "status"],
)

# Agent 任务执行时间
agent_task_duration = Histogram(
    "agent_task_duration_seconds",
    "Agent task execution duration",
    ["agent_name", "task_type"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30, 60],
)

# 当前 Agent 状态
agent_current_status = Gauge(
    "agent_current_status",
    "Current agent status (idle=0, busy=1, error=2, offline=3)",
    ["agent_name", "agent_id"],
)

# Agent 队列长度
agent_queue_length = Gauge(
    "agent_queue_length",
    "Number of pending tasks in agent queue",
    ["agent_name"],
)

# =============================================================================
# 插件指标
# =============================================================================

# 活跃插件数量
plugin_active_count = Gauge(
    "plugin_active_count",
    "Number of active plugins",
)

# 插件执行总数
plugin_executions_total = Counter(
    "plugin_executions_total",
    "Total plugin executions",
    ["plugin_name", "status"],
)

# 插件执行时间
plugin_execution_duration = Histogram(
    "plugin_execution_duration_seconds",
    "Plugin execution duration",
    ["plugin_name"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5],
)

# =============================================================================
# LLM 模型指标
# =============================================================================

# LLM 调用总数
llm_calls_total = Counter(
    "llm_calls_total",
    "Total LLM API calls",
    ["model_name", "provider", "status"],
)

# LLM 响应时间
llm_response_duration = Histogram(
    "llm_response_duration_seconds",
    "LLM response time",
    ["model_name", "provider"],
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)

# LLM Token 使用量
llm_tokens_used = Counter(
    "llm_tokens_used_total",
    "Total LLM tokens used",
    ["model_name", "token_type"],  # token_type: prompt, completion, total
)

# LLM 请求成本
llm_cost_total = Counter(
    "llm_cost_total_usd",
    "Total LLM API cost in USD",
    ["model_name", "provider"],
)

# =============================================================================
# 系统资源指标
# =============================================================================

# 内存使用
memory_usage_bytes = Gauge(
    "memory_usage_bytes",
    "Memory usage in bytes",
    ["type"],  # type: rss, vms, shared
)

# CPU 使用率
cpu_usage_percent = Gauge(
    "cpu_usage_percent",
    "CPU usage percentage",
)

# 请求队列长度
request_queue_length = Gauge(
    "request_queue_length",
    "Number of pending requests",
)

# 活动 WebSocket 连接数
websocket_connections = Gauge(
    "websocket_connections",
    "Number of active WebSocket connections",
)

# =============================================================================
# 缓存指标
# =============================================================================

# 缓存命中率
cache_hit_ratio = Gauge(
    "cache_hit_ratio",
    "Cache hit ratio (0-1)",
    ["cache_type"],
)

# 缓存大小
cache_size = Gauge(
    "cache_size_items",
    "Cache size in number of items",
    ["cache_type"],
)

# =============================================================================
# 数据库指标
# =============================================================================

# 数据库连接数
db_connections_active = Gauge(
    "db_connections_active",
    "Number of active database connections",
)

# 数据库查询时间
db_query_duration = Histogram(
    "db_query_duration_seconds",
    "Database query duration",
    ["query_type"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1],
)

# =============================================================================
# 自定义指标收集器
# =============================================================================

class MetricsCollector:
    """
    自定义指标收集器
    
    提供便捷的指标记录方法
    """

    @staticmethod
    def record_api_request(endpoint: str, method: str, status_code: int, user_role: str = "anonymous", duration: float = None):
        """记录 API 请求"""
        api_requests_total.labels(
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user_role=user_role,
        ).inc()

        if duration is not None:
            api_request_duration.labels(
                endpoint=endpoint,
                method=method,
            ).observe(duration)

    @staticmethod
    def record_agent_task(agent_name: str, task_type: str, status: str, duration: float = None):
        """记录 Agent 任务"""
        agent_tasks_total.labels(
            agent_name=agent_name,
            task_type=task_type,
            status=status,
        ).inc()

        if duration is None:
            # 可以使用时间上下文管理器
            pass
        else:
            agent_task_duration.labels(
                agent_name=agent_name,
                task_type=task_type,
            ).observe(duration)

    @staticmethod
    def set_agent_status(agent_name: str, agent_id: str, status: int):
        """设置 Agent 状态"""
        agent_current_status.labels(
            agent_name=agent_name,
            agent_id=agent_id,
        ).set(status)

    @staticmethod
    def record_plugin_execution(plugin_name: str, status: str, duration: float = None):
        """记录插件执行"""
        plugin_executions_total.labels(
            plugin_name=plugin_name,
            status=status,
        ).inc()

        if duration is not None:
            plugin_execution_duration.labels(
                plugin_name=plugin_name,
            ).observe(duration)

    @staticmethod
    def record_llm_call(model_name: str, provider: str, status: str, duration: float = None, tokens: int = 0, cost: float = 0):
        """记录 LLM 调用"""
        llm_calls_total.labels(
            model_name=model_name,
            provider=provider,
            status=status,
        ).inc()

        if duration is not None:
            llm_response_duration.labels(
                model_name=model_name,
                provider=provider,
            ).observe(duration)

        if tokens > 0:
            llm_tokens_used.labels(
                model_name=model_name,
                token_type="total",
            ).inc(tokens)

        if cost > 0:
            llm_cost_total.labels(
                model_name=model_name,
                provider=provider,
            ).inc(cost)

    @staticmethod
    def record_websocket_connection(count: int):
        """记录 WebSocket 连接数"""
        websocket_connections.set(count)


class MetricsMiddleware:
    """
    Prometheus 指标中间件
    
    自动收集 API 请求指标
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        """中间件调用"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = scope.get("request")
        if not request:
            await self.app(scope, receive, send)
            return

        path = request.url.path
        method = request.method
        start_time = time.time()

        # 记录响应
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
                duration = time.time() - start_time

                # 获取用户角色（如果有）
                user_role = "anonymous"
                if "user_role" in scope.get("state", {}):
                    user_role = scope["state"]["user_role"]

                MetricsCollector.record_api_request(
                    endpoint=path,
                    method=method,
                    status_code=status_code,
                    user_role=user_role,
                    duration=duration,
                )

            await send(message)

        await self.app(scope, receive, send_wrapper)


def get_metrics():
    """获取当前所有指标"""
    return generate_latest()


def get_metrics_content_type():
    """获取指标内容类型"""
    return CONTENT_TYPE_LATEST
