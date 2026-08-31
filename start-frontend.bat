@echo off
chcp 65001 >nul
echo ========================================
echo   启动前端服务
echo ========================================

cd /d "%~dp0frontend"

REM 安装依赖
if not exist "node_modules" (
    echo [1/2] 安装依赖...
    npm install --registry=https://registry.npmmirror.com
)

REM 启动开发服务器
echo [2/2] 启动 Vite 开发服务器...
echo 前端地址: http://localhost:3000
echo ========================================
npm run dev
pause
