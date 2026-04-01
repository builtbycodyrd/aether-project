@echo off
REM Register all Assistant services with NSSM
REM Run as Administrator

echo ============================================
echo    Registering Assistant Windows Services
echo ============================================
echo.

REM Set base paths
set BASE=C:\assistant
set BACKEND_PYTHON=%BASE%\backend\venv\Scripts\python.exe
set BACKEND_MAIN=%BASE%\backend\main.py

REM Register MCP Filesystem Service (Port 8010)
echo [1/7] Registering MCP Filesystem...
nssm install mcp-filesystem "%BASE%\mcp\filesystem\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8010
nssm set mcp-filesystem AppDirectory "%BASE%\mcp\filesystem"
nssm set mcp-filesystem DisplayName "Assistant MCP - Filesystem"
nssm set mcp-filesystem Description "File operations MCP server for Assistant"
nssm set mcp-filesystem Start SERVICE_AUTO_START
nssm set mcp-filesystem AppStdout "%BASE%\logs\mcp-filesystem.log"
nssm set mcp-filesystem AppStderr "%BASE%\logs\mcp-filesystem.log"
nssm set mcp-filesystem AppRotateFiles 1
nssm set mcp-filesystem AppRotateBytes 1048576

REM Register MCP Terminal Service (Port 8011)
echo [2/7] Registering MCP Terminal...
nssm install mcp-terminal "%BASE%\mcp\terminal\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8011
nssm set mcp-terminal AppDirectory "%BASE%\mcp\terminal"
nssm set mcp-terminal DisplayName "Assistant MCP - Terminal"
nssm set mcp-terminal Description "Command execution MCP server for Assistant"
nssm set mcp-terminal Start SERVICE_AUTO_START
nssm set mcp-terminal AppStdout "%BASE%\logs\mcp-terminal.log"
nssm set mcp-terminal AppStderr "%BASE%\logs\mcp-terminal.log"
nssm set mcp-terminal AppRotateFiles 1
nssm set mcp-terminal AppRotateBytes 1048576

REM Register MCP Email Service (Port 8012)
echo [3/7] Registering MCP Email...
nssm install mcp-email "%BASE%\mcp\email\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8012
nssm set mcp-email AppDirectory "%BASE%\mcp\email"
nssm set mcp-email DisplayName "Assistant MCP - Email"
nssm set mcp-email Description "Email operations MCP server for Assistant"
nssm set mcp-email Start SERVICE_AUTO_START
nssm set mcp-email AppStdout "%BASE%\logs\mcp-email.log"
nssm set mcp-email AppStderr "%BASE%\logs\mcp-email.log"
nssm set mcp-email AppRotateFiles 1
nssm set mcp-email AppRotateBytes 1048576

REM Register MCP Browser Service (Port 8013)
echo [4/7] Registering MCP Browser...
nssm install mcp-browser "%BASE%\mcp\browser\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8013
nssm set mcp-browser AppDirectory "%BASE%\mcp\browser"
nssm set mcp-browser DisplayName "Assistant MCP - Browser"
nssm set mcp-browser Description "Web/D2L scraping MCP server for Assistant"
nssm set mcp-browser Start SERVICE_AUTO_START
nssm set mcp-browser AppStdout "%BASE%\logs\mcp-browser.log"
nssm set mcp-browser AppStderr "%BASE%\logs\mcp-browser.log"
nssm set mcp-browser AppRotateFiles 1
nssm set mcp-browser AppRotateBytes 1048576

REM SKIP Screen MCP - runs in user session for desktop access
REM Screen MCP is started via Startup folder (start-screen-mcp.vbs)
REM See: C:\assistant\scripts\install-screen-startup.bat
echo [5/7] Skipping MCP Screen (runs in user session)...

REM Register MCP Tasks Service (Port 8015)
echo [6/7] Registering MCP Tasks...
nssm install mcp-tasks "%BASE%\mcp\tasks\venv\Scripts\python.exe" -m uvicorn main:app --host 0.0.0.0 --port 8015
nssm set mcp-tasks AppDirectory "%BASE%\mcp\tasks"
nssm set mcp-tasks DisplayName "Assistant MCP - Tasks"
nssm set mcp-tasks Description "Tasks/calendar MCP server for Assistant"
nssm set mcp-tasks Start SERVICE_AUTO_START
nssm set mcp-tasks AppStdout "%BASE%\logs\mcp-tasks.log"
nssm set mcp-tasks AppStderr "%BASE%\logs\mcp-tasks.log"
nssm set mcp-tasks AppRotateFiles 1
nssm set mcp-tasks AppRotateBytes 1048576

REM Register Backend Service (Port 8000)
echo [7/7] Registering Backend API...
nssm install assistant-backend "%BACKEND_PYTHON%" "%BACKEND_MAIN%"
nssm set assistant-backend AppDirectory "%BASE%\backend"
nssm set assistant-backend DisplayName "Assistant Backend API"
nssm set assistant-backend Description "Main FastAPI backend for Personal Assistant"
nssm set assistant-backend Start SERVICE_AUTO_START
nssm set assistant-backend AppStdout "%BASE%\logs\backend.log"
nssm set assistant-backend AppStderr "%BASE%\logs\backend.log"
nssm set assistant-backend AppRotateFiles 1
nssm set assistant-backend AppRotateBytes 1048576
nssm set assistant-backend DependOnService mcp-filesystem mcp-terminal mcp-email mcp-browser mcp-tasks

echo.
echo ============================================
echo    All services registered successfully!
echo ============================================
echo.
echo Run 'start-services.bat' to start all services.
