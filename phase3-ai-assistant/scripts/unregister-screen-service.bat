@echo off
REM Remove Screen MCP from NSSM Windows Services
REM Run as Administrator

echo ============================================
echo    Removing Screen MCP Windows Service
echo ============================================
echo.

REM Stop the service first
echo Stopping mcp-screen service...
nssm stop mcp-screen 2>nul
timeout /t 2 /nobreak >nul

REM Remove the service
echo Removing mcp-screen from NSSM...
nssm remove mcp-screen confirm

echo.
echo ============================================
echo    Screen MCP service removed!
echo ============================================
echo.
echo The Screen MCP will now run in user session via Startup folder.
echo See: C:\assistant\scripts\start-screen-mcp.vbs
echo.
pause
