@echo off
REM Control Screen MCP (user session process)
REM Usage: screen-mcp-control.bat [start|stop|status|restart]

set ACTION=%1

if "%ACTION%"=="" (
    echo Usage: screen-mcp-control.bat [start^|stop^|status^|restart]
    echo.
    echo   start   - Start the Screen MCP server
    echo   stop    - Stop the Screen MCP server
    echo   status  - Check if Screen MCP is running
    echo   restart - Stop and start the Screen MCP server
    exit /b 1
)

if /i "%ACTION%"=="start" goto :start
if /i "%ACTION%"=="stop" goto :stop
if /i "%ACTION%"=="status" goto :status
if /i "%ACTION%"=="restart" goto :restart

echo Unknown action: %ACTION%
exit /b 1

:start
echo Starting Screen MCP...
wscript "C:\assistant\scripts\start-screen-mcp.vbs"
timeout /t 2 /nobreak >nul
goto :status

:stop
echo Stopping Screen MCP...
taskkill /F /FI "WINDOWTITLE eq *uvicorn*8014*" 2>nul
REM Also try killing by command line match
for /f "tokens=2" %%i in ('wmic process where "commandline like '%%uvicorn%%8014%%'" get processid 2^>nul ^| findstr /r "[0-9]"') do (
    taskkill /F /PID %%i 2>nul
)
REM Kill any python process running on port 8014
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8014.*LISTENING"') do (
    taskkill /F /PID %%a 2>nul
)
echo Screen MCP stopped.
exit /b 0

:status
echo.
echo Checking Screen MCP status...
netstat -ano | findstr ":8014.*LISTENING" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [RUNNING] Screen MCP is listening on port 8014
    curl -s http://localhost:8014/health 2>nul
) else (
    echo [STOPPED] Screen MCP is not running
)
echo.
exit /b 0

:restart
call :stop
timeout /t 1 /nobreak >nul
call :start
exit /b 0
