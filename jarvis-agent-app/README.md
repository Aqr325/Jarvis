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

## 💡 使用示例

### 场景一：日常助手

```
你: "帮我查询今天比特币价格"
Jarvis: [调用 CoinGecko API] "当前比特币价格：$67,234.56"

你: "写一首关于春天的五言绝句"
Jarvis: [调用 NLP + Writer Agent] "春山暖日和风，杨柳绿窗纱。
         庭院海棠初放，鸟语声声入画。"
```

### 场景二：代码生成

```
你: "用 Python 写一个快速排序"
Jarvis: [调用 Coder Agent]
```python
def quick_sort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quick_sort(left) + middle + quick_sort(right)
```
```

### 场景三：多 Agent 协作

```
你: "分析一下特斯拉的股价，写一份投资报告"
Jarvis: [启动 Research Agent + Analyst Agent + Writer Agent]
        - Research Agent 搜索最新财报
        - Analyst Agent 分析技术指标
        - Writer Agent 撰写报告

输出：完整的 2000 字投资分析报告
```

---

## 🎨 截图展示

### 前端控制台

<div align="center">
  <img src="public/screenshot-dashboard.png" alt="前端控制台" width="80%">
  <p>实时对话界面，支持 Markdown 渲染</p>
</div>

### 设置界面

<div align="center">
  <img src="public/screenshot-settings.png" alt="设置界面" width="80%">
  <p>自定义 LLM 配置、插件管理、权限设置</p>
</div>

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

### 系统要求

| 项 | 要求 |
|----|------|
| **Python** | ≥ 3.11 (推荐 3.13.12) |
| **Node.js** | ≥ 22.x (前端可选) |
| **Docker** | ≥ 24.x (可选) |
| **内存** | ≥ 2GB RAM |
| **磁盘** | ≥ 500MB 可用空间 |

### 安装步骤

#### 方式一：Python 直接启动（推荐新手）

1. **克隆仓库**
   ```bash
   git clone https://github.com/Aqr325/Jarvis.git
   cd Jarvis/jarvis-agent-app
   ```

2. **创建虚拟环境**（可选但推荐）
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，配置自定义 LLM（可选）
   ```

5. **启动服务**
   ```bash
   # 开发模式（带热重载）
   python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

   # 生产模式（性能更好）
   python -m uvicorn server:app --host 0.0.0.0 --port 8000
   ```

#### 方式二：Windows 一键启动

1. **直接运行**
   双击 `START.bat` 即可启动

2. **访问界面**
   - 前端控制台：http://localhost:8000
   - 设置界面：http://localhost:8000/jarvis-interface.html

#### 方式三：Docker 部署

1. **启动服务**
   ```bash
   docker-compose up -d
   ```

2. **验证安装**
   ```bash
   docker ps  # 应该看到 jarvis-agent-app 容器运行中
   ```

### 访问地址

| 功能 | 地址 | 说明 |
|------|------|------|
| 前端控制台 | http://localhost:8000 | 主界面，实时对话 |
| 设置界面 | http://localhost:8000/jarvis-interface.html | 自定义配置 LLM |
| API 文档 | http://localhost:8000/docs | Swagger UI 交互式文档 |
| 健康检查 | http://localhost:8000/health | 服务状态检测 |
| Prometheus | http://localhost:9090 | 指标监控（需手动启动） |
| Grafana | http://localhost:3000 | 仪表盘可视化（默认 admin/admin） |

### 验证安装

在浏览器中访问 http://localhost:8000/health，应该看到：

```json
{
  "status": "healthy",
  "version": "2.0",
  "modules": ["nlp", "custom_llm", "agents", "plugins"]
}
```

---

## ⚙️ 常见问题

### Q1: 启动失败，提示端口被占用

**解决方案**：
```bash
# Windows: 更换端口
python -m uvicorn server:app --host 0.0.0.0 --port 8001

# 或停止占用端口的进程
netstat -ano | findstr :8000
taskkill /PID <进程ID> /F
```

### Q2: 缺少 uvicorn 或 fastapi

**解决方案**：
```bash
pip install uvicorn fastapi pydantic python-dotenv
```

### Q3: NLP 无法识别意图

**检查项**：
1. 查看 `core/nlp.py` 是否正常加载
2. 尝试重启服务
3. 查看日志中的错误信息

### Q4: 自定义 LLM 配置失败

**检查项**：
1. `.env` 文件是否正确配置（OpenAI Key / Ollama URL）
2. 网络是否可访问外网
3. Ollama 是否正常运行

### Q5: 测试用例失败

**解决方案**：
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

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
