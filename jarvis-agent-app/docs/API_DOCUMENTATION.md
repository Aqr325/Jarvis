# J.A.R.V.I.S. Agent API 文档

**版本:** 0.2.0  
**最后更新:** 2026-06-19  
**Base URL:** `http://localhost:8000`

---

## 目录

- [认证](#认证)
- [核心 API](#核心-api)
- [模型配置 API](#模型配置-api)
- [公共服务 API](#公共服务-api)
- [系统 API](#系统-api)
- [WebSocket](#websocket)
- [错误代码](#错误代码)

---

## 认证

当前版本为开发版，所有接口无需认证。未来版本将引入 OAuth2/JWT 认证。

---

## 核心 API

### 智能对话

#### POST `/api/chat`

发送聊天消息并获取 Agent 响应。

**请求体:**

```json
{
  "message": "string (required, 1-4096 chars)",
  "modality": "text|image|audio|video (default: text)",
  "session_id": "string (optional, max 64 chars)",
  "context": "object (optional)"
}
```

**响应:**

```json
{
  "success": true,
  "session_id": "sess_abc123",
  "timestamp": "2026-06-19T12:00:00",
  "output": "Agent 响应内容",
  "reasoning": {
    "output": "响应内容",
    "reasoning": "推理过程",
    "confidence": 0.95,
    "tools_used": ["weather", "search"]
  },
  "nlp": {
    "intent": "weather_query",
    "entities": {"city": "北京"},
    "sentiment": "neutral",
    "confidence": 0.92
  }
}
```

**示例:**

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "今天北京天气怎么样？",
    "session_id": "my_session"
  }'
```

---

### 工具调用

#### POST `/api/tool`

直接调用指定工具。

**请求体:**

```json
{
  "tool": "string (required, 字母开头)",
  "args": "object (optional)"
}
```

**示例:**

```bash
curl -X POST http://localhost:8000/api/tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "weather",
    "args": {"city": "上海"}
  }'
```

#### GET `/api/tools`

获取所有可用工具列表。

**响应:**

```json
{
  "available_tools": [
    {
      "name": "weather",
      "description": "查询天气信息",
      "category": "external"
    }
  ],
  "total": 1
}
```

---

### 任务调度

#### POST `/api/scheduler/task`

创建新任务。

**请求体:**

```json
{
  "title": "string (required, 1-256 chars)",
  "due_date": "string (required, ISO 8601)",
  "priority": "low|medium|high|urgent (default: medium)",
  "description": "string (optional, max 2048 chars)",
  "tags": ["string"] (optional, max 10 items)
}
```

#### GET `/api/scheduler/tasks`

获取任务列表和统计信息。

**查询参数:**

- `status`: 筛选状态 (pending/completed)

---

## 模型配置 API

### POST `/api/model/config`

配置外部 LLM 模型。

**请求体:**

```json
{
  "provider": "openai|ollama|anthropic|gemini|azure|custom (required)",
  "api_base_url": "string (optional)",
  "model_name": "string (required, 1-128 chars)",
  "api_key": "string (required for remote models, min 10 chars)",
  "temperature": "float [0, 2] (default: 0.7)",
  "max_tokens": "int [1, 100000] (default: 4096)",
  "timeout": "int [5, 300] (default: 60)",
  "extra_params": "object (optional)"
}
```

**示例 (OpenAI):**

```bash
curl -X POST http://localhost:8000/api/model/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "api_base_url": "https://api.openai.com/v1",
    "model_name": "gpt-4o",
    "api_key": "sk-your_api_key_here",
    "temperature": 0.7,
    "max_tokens": 4096
  }'
```

**示例 (Ollama 本地):**

```bash
curl -X POST http://localhost:8000/api/model/config \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "ollama",
    "api_base_url": "http://localhost:11434",
    "model_name": "llama3",
    "api_key": "",
    "temperature": 0.5
  }'
```

### GET `/api/model/status`

获取当前模型配置状态。

### POST `/api/model/test`

测试模型连接。

### POST `/api/model/reset`

清除外部模型配置。

---

## 公共服务 API

### 加密货币

#### POST `/api/public/crypto`

获取加密货币价格。

```bash
curl -X POST http://localhost:8000/api/public/crypto \
  -H "Content-Type: application/json" \
  -d '{"coin_id": "bitcoin", "vs_currency": "usd"}'
```

### 汇率

#### POST `/api/public/exchange`

获取汇率信息。

```bash
curl -X POST http://localhost:8000/api/public/exchange \
  -H "Content-Type: application/json" \
  -d '{"from_currency": "USD", "to_currency": "CNY", "amount": 100}'
```

### 词典

#### POST `/api/public/dictionary`

词典查询。

```bash
curl -X POST http://localhost:8000/api/public/dictionary \
  -H "Content-Type: application/json" \
  -d '{"word": "serendipity"}'
```

### 节假日

#### POST `/api/public/holidays`

获取节假日信息。

```bash
curl -X POST http://localhost:8000/api/public/holidays \
  -H "Content-Type: application/json" \
  -d '{"year": 2026, "country_code": "CN"}'
```

### 书籍搜索

#### POST `/api/public/books/search`

搜索书籍。

```bash
curl -X POST http://localhost:8000/api/public/books/search \
  -H "Content-Type: application/json" \
  -d '{"query": "Python programming", "limit": 10}'
```

---

## 系统 API

### GET `/health`

健康检查。

**响应:**

```json
{
  "status": "healthy",
  "service": "J.A.R.V.I.S. Agent",
  "version": "0.2.0",
  "websocket_enabled": true,
  "rate_limiting": "active"
}
```

### GET `/api/status`

获取系统状态。

### GET `/api/admin/circuit-breaker`

获取断路器状态。

---

## WebSocket

### `ws://localhost:8000/ws`

实时双向通信。

**消息格式:**

```json
{
  "type": "chat|tool_call|ping",
  "data": {
    "message": "string",
    "session_id": "string"
  }
}
```

**示例:**

```python
import asyncio
import websockets

async def chat():
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        await ws.send_json({
            "type": "chat",
            "data": {"message": "你好"}
        })
        
        async for message in ws:
            data = json.loads(message)
            print(data)

asyncio.run(chat())
```

---

## 错误代码

| HTTP 状态码 | 错误代码 | 说明 |
|------------|---------|------|
| 400 | BAD_REQUEST | 请求格式错误 |
| 401 | UNAUTHORIZED | 未授权 (未来功能) |
| 403 | FORBIDDEN | 禁止访问 (未来功能) |
| 404 | NOT_FOUND | 资源未找到 |
| 422 | VALIDATION_ERROR | 验证失败 |
| 429 | RATE_LIMIT_EXCEEDED | 超过速率限制 |
| 500 | INTERNAL_ERROR | 内部服务器错误 |
| 502 | UPSTREAM_ERROR | 上游服务错误 |
| 503 | SERVICE_UNAVAILABLE | 服务不可用 |
| 504 | TIMEOUT | 网关超时 |

---

## 速率限制

- **默认限制:** 100 请求/分钟 (general)
- **聊天限制:** 30 请求/分钟 (chat)
- **工具限制:** 50 请求/分钟 (tool)

响应头包含:
- `X-RateLimit-Limit`: 总限制数
- `X-RateLimit-Remaining`: 剩余请求数
- `X-RateLimit-Reset`: 重置时间 (Unix 时间戳)

---

## 环境配置

| 变量名 | 说明 | 默认值 |
|-------|------|-------|
| `LOG_LEVEL` | 日志级别 | INFO |
| `SENTRY_DSN` | Sentry DSN | (空) |
| `SENTRY_ENVIRONMENT` | 环境 | development |
| `OPENAI_API_KEY` | OpenAI API 密钥 | (空) |
| `REDIS_URL` | Redis 连接 | redis://localhost:6379 |

---

## 生成 OpenAPI 文档

```bash
# 查看 Swagger UI
python -m uvicorn server:app
# 访问 http://localhost:8000/docs

# 下载 OpenAPI Schema
curl http://localhost:8000/openapi.json > openapi.json
```
