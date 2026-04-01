@echo off
REM Uninstall all Assistant services
REM Run as Administrator

echo ============================================
echo     Uninstalling Assistant Services
echo ============================================
echo.

echo This will stop and remove all Assistant services.
echo Press Ctrl+C to cancel, or
pause

echo.
echo Stopping services first...
call stop-services.bat

echo.
echo Removing services...

nssm remove assistant-backend confirm
nssm remove mcp-tasks confirm
nssm remove mcp-browser confirm
nssm remove mcp-email confirm
nssm remove mcp-terminal confirm
nssm remove mcp-filesystem confirm

echo Removing Screen MCP startup entry...
del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\start-screen-mcp.vbs" 2>nul

echo.
echo ============================================
echo    All services have been uninstalled.
echo ============================================
