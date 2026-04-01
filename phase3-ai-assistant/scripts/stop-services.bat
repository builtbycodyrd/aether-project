@echo off
REM Stop all Assistant services
REM Run as Administrator

echo ============================================
echo        Stopping Assistant Services
echo ============================================
echo.

echo Stopping Backend API...
nssm stop assistant-backend

echo Stopping MCP Tasks...
nssm stop mcp-tasks

echo Stopping MCP Screen (user session)...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8014.*LISTENING"') do taskkill /F /PID %%a 2>nul

echo Stopping MCP Browser...
nssm stop mcp-browser

echo Stopping MCP Email...
nssm stop mcp-email

echo Stopping MCP Terminal...
nssm stop mcp-terminal

echo Stopping MCP Filesystem...
nssm stop mcp-filesystem

echo.
echo ============================================
echo       All services stopped.
echo ============================================
