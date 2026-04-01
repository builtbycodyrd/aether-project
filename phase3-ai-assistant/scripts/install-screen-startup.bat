@echo off
REM Install Screen MCP to run at user login
REM Run as your normal user (NOT as Administrator)

echo ============================================
echo    Installing Screen MCP User Startup
echo ============================================
echo.

set STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
set SCRIPT_PATH=C:\assistant\scripts\start-screen-mcp.vbs

REM Copy the VBS script to Startup folder
echo Copying startup script to: %STARTUP_FOLDER%
copy "%SCRIPT_PATH%" "%STARTUP_FOLDER%\start-screen-mcp.vbs" /Y

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================
    echo    Screen MCP startup installed!
    echo ============================================
    echo.
    echo The Screen MCP will now start automatically when you log in.
    echo It runs in your user session so it can capture screenshots.
    echo.
    echo To start it now without rebooting, run:
    echo   wscript "C:\assistant\scripts\start-screen-mcp.vbs"
    echo.
) else (
    echo.
    echo ERROR: Failed to copy startup script.
    echo.
)

pause
