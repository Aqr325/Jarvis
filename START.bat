@echo off
chcp 65001 >nul
title J.A.R.V.I.S. Agent

echo ========================================
echo    J.A.R.V.I.S. Agent 快速启动
echo ========================================
echo.

cd /d "%~dp0jarvis-agent-app"

echo [1/3] 检查Python环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或未加入PATH
    pause
    exit /b 1
)
echo [OK] Python 已安装

echo [2/3] 启动服务器...
python -m uvicorn server:app --host 0.0.0.0 --port 8000

if errorlevel 1 (
    echo.
    echo [错误] 服务器启动失败
    echo 请检查:
    echo   1. 端口8000是否被占用 (netstat -ano ^| findstr :8000)
    echo   2. 依赖是否完整 (pip install -r requirements.txt)
    pause
    exit /b 1
)

pause
