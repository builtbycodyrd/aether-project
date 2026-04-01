' Start Screen MCP in user session (for screenshot access)
' This script runs silently at user login via Startup folder

Set WshShell = CreateObject("WScript.Shell")

' Set working directory and start the Screen MCP server
WshShell.CurrentDirectory = "C:\assistant\mcp\screen"

' Run uvicorn silently (0 = hidden window)
WshShell.Run "C:\assistant\mcp\screen\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8014", 0, False

Set WshShell = Nothing
