# J.A.R.V.I.S. Agent - 智能 AI 助手系统

> **2026-06-19** | v2.0 全面审计版 | 58 个文件，~8,500 行代码

---

## 📊 代码库规模

| 指标 | 数值 |
|------|------|
| Python 文件 | 58 个 |
| HTML 前端 | 3 个 |
| API 端点 | 21+ 个 |
| 可用工具 | 23 个 |
| NLP 意图类别 | 26 个 |
| 代码总行数 | ~8,500 行 |
| 测试文件 | 9 个 |
| 测试用例 | 100+ 个 |
| 模块数 | 7 个 (core, modules, agents, plugins, auth, schemas, monitoring) |

---

## 🏗️ 核心架构

```
┌─────────────────────────────────────────────────────┐
│                   Server (server.py)                 │
│   FastAPI + CORS + RateLimit + Timeout + WS + Log   │
├──────────────┬──────────────┬───────────────────────┤
│    core/     │   modules/   │      agents/          │
│  engine.py   │  builtins.py │  多 Agent 协作框架    │
│  sentry.py   │  nlp.py      │  coordinator/research │
│  timeout.py  │  custom_llm  │  coder/writer         │
│  ws_mgr.py   │  public_apis │                       │
├──────────────┼──────────────┼───────────────────────┤
│  plugins/    │   auth/      │    monitoring/        │
│  热插拔系统  │  JWT + RBAC  │  Prometheus 指标      │
└──────────────┴──────────────┴───────────────────────┘
```

---

## 🎯 功能特性

### 核心功能
- **NLP 意图识别**: 26 个意图类别，中英文支持
- **状态机路由**: 多步推理 + 规则引擎
- **自定义 LLM**: OpenAI / Ollama 外部模型接入
- **WebSocket**: 实时双向通信
- **公共 API**: 加密货币、汇率、词典、节假日、笑话、书籍

### 高级功能
- **多 Agent 系统**: 角色分工、任务分配、结果聚合
- **插件系统**: 动态加载、热插拔、第三方扩展
- **权限系统**: JWT 认证 + RBAC 权限管理
- **监控系统**: Prometheus 指标 + Grafana 仪表盘
- **异常追踪**: Sentry 集成
- **Docker 支持**: 多阶段构建 + Compose 编排

---

## 📁 项目结构

```
jarvis-agent-app/
├── server.py                    # 主服务器 (810 行)
├── requirements.txt             # 生产依赖
├── requirements-dev.txt         # 开发依赖
├── Dockerfile                   # 多阶段构建
├── docker-compose.yml           # 编排配置
├── prometheus.yml               # Prometheus 配置
├── .env.example                 # 环境变量模板
│
├── core/                        # 核心引擎 (5 文件)
│   ├── engine.py                # 决策引擎 (796 行) ★
│   ├── rate_limiter.py          # 令牌桶限流
│   ├── timeout.py               # 超时控制 + 熔断器
│   ├── websocket_manager.py     # WebSocket 管理
│   └── sentry_integration.py    # Sentry 集成
│
├── modules/                     # 功能模块 (4 文件)
│   ├── builtins.py              # 内置工具
│   ├── nlp.py                   # NLP 处理器 ★
│   ├── public_apis.py           # 公共 API 封装
│   └── custom_llm.py            # 自定义 LLM
│
├── agents/                      # 多 Agent 系统 (8 文件)
│   ├── interface.py             # Agent 接口定义
│   ├── base.py                  # Agent 基类
│   ├── registry.py              # 注册表
│   ├── manager.py               # 管理器
│   └── examples/                # 示例 (4 Agent)
│
├── plugins/                     # 插件系统 (10 文件)
│   ├── interface.py             # 插件接口
│   ├── base.py                  # 插件基类
│   ├── registry.py              # 注册表
│   ├── manager.py               # 管理器
│   └── examples/                # 示例 (3 插件)
│
├── auth/                        # 认证授权 (5 文件)
│   ├── models.py                # User/Role/Permission
│   ├── jwt_handler.py           # JWT 处理
│   └── middleware.py            # 认证中间件
│
├── schemas/                     # Pydantic Schema (12 文件)
│
├── monitoring/                  # 监控 (Prometheus)
│
├── tests/                       # 测试套件 (7 文件)
│
└── public/
    └── index.html               # 前端控制台 (1,365 行)
```

---

## 🚀 快速启动

### 方式一：直接启动

```bash
cd jarvis-agent-app
pip install -r requirements.txt
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

### 方式二：Docker

```bash
docker-compose up -d
```

### 方式三：Windows 脚本

双击运行 `START.bat`

### 访问

| 页面 | URL |
|------|-----|
| 前端控制台 | http://localhost:8000 |
| 设置界面 | http://localhost:8000/jarvis-interface.html |
| API 文档 (Swagger) | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 |

---

## 🧪 运行测试

```bash
cd jarvis-agent-app
pip install -r requirements-dev.txt
pytest tests/ -v --cov=core --cov=modules --cov=schemas
```

---

## 🔗 GitHub

https://github.com/Aqr325/Jarvis

---

## 📋 审计历史

| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-06-19 | v1.0 审计 | 16 项问题修复 (P0×3, P1×5, P2×8) |
| 2026-06-19 | v2.0 审计 | 全面检查 + 新增模块验证 |
