@echo off
REM Check status of all Assistant services

echo ============================================
echo       Assistant Services Status
echo ============================================
echo.

for %%s in (mcp-filesystem mcp-terminal mcp-email mcp-browser mcp-tasks assistant-backend) do (
    echo %%s:
    nssm status %%s 2>nul || echo   Not installed
    echo.
)

echo mcp-screen (user session):
netstat -ano | findstr ":8014.*LISTENING" >nul 2>&1 && echo   SERVICE_RUNNING || echo   SERVICE_STOPPED
echo.

echo ============================================
echo            Port Check
echo ============================================
echo.

echo Checking ports...
netstat -an | findstr ":8000 :8010 :8011 :8012 :8013 :8014 :8015" | findstr LISTENING

echo.
echo ============================================
