# J.A.R.V.I.S. Agent 启动指南

## 问题诊断

你已经运行了 `python -m uvicorn server:app --host 0.0.0.0 --port 8000`，但无法访问。以下是可能的原因和解决方案：

---

## 1. 确认服务器在运行

打开新的终端窗口（PowerShell 或 CMD），执行：

```powershell
netstat -ano | findstr :8000
```

如果看到类似输出说明服务器在运行：
```
  TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       71264
```

如果没有输出，说明服务器**没有启动**或**已退出**。

---

## 2. 手动启动服务器

在 **PowerShell** 中执行：

```powershell
cd "D:\workbuddy workspace\2026-06-19-12-04-01\jarvis-agent-app"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
```

你应该看到：
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 3. 验证访问

在**浏览器**中访问：

| 页面 | URL |
|------|-----|
| 主界面 | http://localhost:8000 |
| 设置界面 | http://localhost:8000/jarvis-interface.html |
| API文档 | http://localhost:8000/docs |
| 健康检查 | http://localhost:8000/health |

---

## 4. 常见问题排查

### 问题：端口已被占用

```powershell
# 查找占用8000端口的进程
netstat -ano | findstr :8000

# 终止进程（替换PID为你的进程ID）
taskkill /F /PID <PID>

# 重新启动服务器
```

### 问题：启动后立即退出

检查错误日志：
1. 确保已安装所有依赖：`pip install -r requirements.txt`
2. 查看启动时的错误信息

### 问题：仍然无法访问

尝试访问：`http://127.0.0.1:8000`（某些网络配置下host和127.0.0.1行为不同）

---

## 快速启动脚本

创建 `start.bat`：

```batch
@echo off
cd /d "D:\workbuddy workspace\2026-06-19-12-04-01\jarvis-agent-app"
python -m uvicorn server:app --host 0.0.0.0 --port 8000
pause
```

双击运行即可启动。
