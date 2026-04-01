@echo off
REM Start all Assistant services
REM Run as Administrator

echo ============================================
echo       Starting Assistant Services
echo ============================================
echo.

echo [1/7] Starting MCP Filesystem...
nssm start mcp-filesystem
timeout /t 2 /nobreak >nul

echo [2/7] Starting MCP Terminal...
nssm start mcp-terminal
timeout /t 2 /nobreak >nul

echo [3/7] Starting MCP Email...
nssm start mcp-email
timeout /t 2 /nobreak >nul

echo [4/7] Starting MCP Browser...
nssm start mcp-browser
timeout /t 2 /nobreak >nul

echo [5/7] Starting MCP Screen (user session)...
wscript "C:\assistant\scripts\start-screen-mcp.vbs"
timeout /t 2 /nobreak >nul

echo [6/7] Starting MCP Tasks...
nssm start mcp-tasks
timeout /t 2 /nobreak >nul

echo [7/7] Starting Backend API...
nssm start assistant-backend
timeout /t 3 /nobreak >nul

echo.
echo ============================================
echo          Checking Service Status
echo ============================================
echo.

for %%s in (mcp-filesystem mcp-terminal mcp-email mcp-browser mcp-tasks assistant-backend) do (
    echo %%s:
    nssm status %%s
    echo.
)

echo mcp-screen (user session):
netstat -ano | findstr ":8014.*LISTENING" >nul 2>&1 && echo SERVICE_RUNNING || echo SERVICE_STOPPED
echo.

echo ============================================
echo    All services should be running now!
echo ============================================
echo.
echo Backend API: http://localhost:8000
echo PWA:         http://localhost:8000
echo Health:      http://localhost:8000/health
