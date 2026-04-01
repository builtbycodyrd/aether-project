# Personal Assistant System

A comprehensive AI-powered personal assistant with local LLM inference, MCP servers, desktop shell, and mobile PWA.

## Architecture

```
C:\assistant\
├── backend\          # FastAPI main backend (port 8000)
├── mcp\              # MCP servers
│   ├── filesystem\   # File operations (port 8010)
│   ├── terminal\     # Command execution (port 8011)
│   ├── email\        # Email integration (port 8012)
│   ├── browser\      # Web/D2L scraping (port 8013)
│   ├── screen\       # Screenshot/vision (port 8014)
│   └── tasks\        # Tasks/calendar (port 8015)
├── pwa\              # Progressive Web App
├── shell\            # Tauri desktop shell
├── sandbox\          # Docker sandbox config
├── data\             # SQLite + ChromaDB
├── logs\             # Service logs
└── scripts\          # Management scripts
```

## Services

All services run as Windows services via NSSM and start automatically on boot.

| Service | Port | Description |
|---------|------|-------------|
| assistant-backend | 8000 | Main FastAPI backend, serves PWA |
| mcp-filesystem | 8010 | File read/write/search with confirmation gate |
| mcp-terminal | 8011 | PowerShell/cmd execution with safety checks |
| mcp-email | 8012 | Yahoo, Gmail, SRU email integration |
| mcp-browser | 8013 | D2L scraping, web fetch, weather |
| mcp-screen | 8014 | Screenshot capture, Ollama vision |
| mcp-tasks | 8015 | Tasks, assignments, calendar |

## Management

### Start All Services
```cmd
C:\assistant\scripts\start-services.bat
```

### Stop All Services
```cmd
C:\assistant\scripts\stop-services.bat
```

### Check Status
```cmd
C:\assistant\scripts\status-services.bat
```

### Health Check
```
http://localhost:8000/health
```

## Access

- **PWA (Mobile)**: http://localhost:8000 or http://<PC-IP>:8000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Ollama Models

- `llama3.1:8b` - General conversation (Tier 1)
- `phi3:mini` - Quick tasks (Tier 0)
- `qwen2.5-coder:14b` - Code generation (Tier 2)
- `llava:7b` - Vision/screenshots

## iPhone Installation

See `pwa\INSTALL_ON_IPHONE.txt` for detailed instructions.

Quick steps:
1. Ensure PC and iPhone on same WiFi
2. Open Safari on iPhone
3. Navigate to http://<PC-IP>:8000
4. Tap Share > Add to Home Screen

## Features

- **Multi-model routing**: Automatically selects best model for task
- **Memory system**: ChromaDB for conversation context
- **Confirmation gates**: Approve destructive operations
- **Real-time streaming**: WebSocket for live responses
- **Offline support**: PWA caches for offline access
- **Docker sandbox**: Isolated code execution

## Logs

Service logs are in `C:\assistant\logs\`:
- `backend.log` - Main backend
- `mcp-*.log` - Individual MCP servers
- `scheduler.log` - Background scheduler

## Troubleshooting

### Service won't start
```cmd
nssm status <service-name>
nssm restart <service-name>
```

### Check port conflicts
```cmd
netstat -an | findstr ":800"
```

### View service logs
```cmd
type C:\assistant\logs\backend.log
```

### Reinstall services
```cmd
C:\assistant\scripts\uninstall-services.bat
C:\assistant\scripts\register-services.bat
C:\assistant\scripts\start-services.bat
```
