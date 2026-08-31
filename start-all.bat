@echo off
chcp 65001 >nul
echo ========================================
echo   企业知识库 RAG 系统 - 一键启动
echo ========================================
echo.

REM 启动后端（新窗口）
start "RAG后端" cmd /k "cd /d %~dp0 && call start-backend.bat"

REM 等待后端启动
echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

REM 启动前端（新窗口）
start "RAG前端" cmd /k "cd /d %~dp0 && call start-frontend.bat"

echo.
echo ========================================
echo   服务已启动！
echo   后端: http://localhost:8000
echo   前端: http://localhost:3000
echo   API文档: http://localhost:8000/docs
echo ========================================
pause
