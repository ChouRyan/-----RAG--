@echo off
chcp 65001 >nul
echo ========================================
echo   启动后端服务
echo ========================================

cd /d "%~dp0backend"

REM 检查虚拟环境
if not exist "venv" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo [2/3] 安装依赖...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

REM 检查 .env 文件
if not exist ".env" (
    echo [提示] 未找到 .env 文件，正在从模板创建...
    copy .env.example .env
    echo [提示] 请编辑 backend\.env 文件，填入你的 OpenAI API Key
    pause
    exit /b
)

REM 启动服务
echo [3/3] 启动 FastAPI 服务...
echo 后端地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo ========================================
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
