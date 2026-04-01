# Claude Code — Complete Build Specification
# Personal Operating Assistant for Windows 11

---

## Instructions For Claude Code

Read this entire document before writing a single line of code or running any command.
Understand the complete system before beginning Phase 1.

You are building a serious, production-quality personal operating assistant. Every
decision must reflect that. Do not simplify architecture to move faster. Do not skip
steps to show progress. Do not substitute easier alternatives unless a blocker is
explicitly unresolvable.

After completing each phase, run the verification checklist for that phase before
proceeding. Do not move to the next phase until all checks pass.

Commit working code to git after each phase with a descriptive commit message.
Write a brief PHASE_N_COMPLETE.md file in C:\assistant\docs\ after each phase.

---

## Target Machine

- OS: Windows 11
- CPU: Intel i7 11th Gen KF
- GPU: NVIDIA RTX 3060 OC 12GB VRAM (CUDA capable)
- RAM: 32GB DDR4 3200MHz
- Storage C: SSD ~300GB available
- Storage D: HDD ~4TB available
- Email 1: Yahoo Mail (IMAP/SMTP with App Password)
- Email 2: Gmail (IMAP/SMTP with App Password)
- Email 3: SRU RockMail (Microsoft 365, OAuth2 via Microsoft Graph API)
- School LMS: D2L RockOnline at sru.desire2learn.com
- Phone: iPhone — access via Tailscale PWA
- Tailscale: already installed

---

## Absolute Rules

1. AI models are stored on D: drive only. Never install models to C:.
2. Models unload from VRAM after 3 minutes idle. This is mandatory — non-negotiable.
3. Only one model loads at a time. The system never holds two models in VRAM simultaneously.
4. Zero recurring cost in the runtime system. No paid API calls after setup.
5. All credentials stored encrypted in SQLite. Never in plaintext config files or
   environment variables.
6. Destructive operations (file delete, system-altering terminal commands) are always
   blocked until user confirms via the UI confirmation gate.
7. Docker sandbox is mandatory for all assistant-generated code execution. Never run
   assistant code directly on the host OS.
8. All MCP servers bind to localhost only. They are never exposed externally.
9. Only FastAPI port 8000 is accessible over Tailscale.
10. All services start automatically on Windows boot via NSSM.
11. Build phases are executed in order. No skipping.

---

## Project Structure

Create this directory structure as the very first action:

```
C:\assistant\
├── backend\
├── mcp\
│   ├── filesystem\
│   ├── terminal\
│   ├── email\
│   ├── browser\
│   ├── screen\
│   └── tasks\
├── shell\
├── pwa\
├── data\
├── sandbox\
├── voice\
├── logs\
└── docs\
```

Also create:
```
D:\ollama\
D:\ollama\models\
D:\docker\
```

Initialize git in C:\assistant\ and create an initial commit.
Create C:\assistant\.gitignore with entries for: data/, logs/, **/node_modules/,
**/__pycache__/, **/venv/, *.pyc, .env

---

## Prerequisites — Install Exactly In This Order

Use PowerShell (run as Administrator) for all installation commands.
Verify each prerequisite before moving to the next.

### Step 1: Python 3.11

```powershell
winget install Python.Python.3.11
# Close and reopen PowerShell after install
python --version  # Must return 3.11.x
pip install --upgrade pip
```

### Step 2: Node.js 20 LTS

```powershell
winget install OpenJS.NodeJS.LTS
node --version   # Must return 20.x.x
npm --version
```

### Step 3: Rust and Cargo

```powershell
winget install Rustlang.Rustup
# Close and reopen PowerShell
rustup default stable
rustup target add x86_64-pc-windows-msvc
rustc --version  # Must succeed
cargo --version  # Must succeed
```

### Step 4: Visual Studio Build Tools (required by Tauri)

```powershell
winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
```

Verify by opening "x64 Native Tools Command Prompt for VS 2022" from Start Menu.

### Step 5: Tauri CLI

```powershell
cargo install tauri-cli --version "^2.0"
cargo tauri --version  # Must succeed
```

### Step 6: Ollama for Windows

Download installer from https://ollama.ai/download/windows and run it.
After installation:

```powershell
# Set model storage to D: drive
[Environment]::SetEnvironmentVariable("OLLAMA_MODELS", "D:\ollama\models", "Machine")

# Set idle unload timeout to 3 minutes
[Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE", "3m", "Machine")

# Verify Ollama is running
ollama list  # Should return empty list (no models yet)
```

### Step 7: Pull Ollama Models

This will take significant time. Run each pull and wait for completion before the next.

```powershell
ollama pull phi3:mini
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:14b
ollama pull llava:7b
```

Verify all four models loaded and respond correctly:

```powershell
ollama run phi3:mini "Reply with only the word: READY"
ollama run llama3.1:8b "Reply with only the word: READY"
ollama run qwen2.5-coder:14b "Reply with only the word: READY"
ollama run llava:7b "Reply with only the word: READY"
```

All must return READY. If any fail, resolve before continuing.

After pulling all models, open Task Manager, go to Performance > GPU, note baseline
VRAM usage. Wait 4 minutes. Confirm VRAM returns to near-baseline (models unloaded).

### Step 8: WSL2

```powershell
wsl --install
```

Restart Windows when prompted. After restart:

```powershell
wsl --set-default-version 2
wsl --status  # Must show: Default Version: 2
```

### Step 9: Docker Desktop

Download Docker Desktop from https://www.docker.com/products/docker-desktop/
During installation: select WSL2 backend.
After installation:

```powershell
docker --version
docker run hello-world  # Must succeed
```

Configure Docker to store images on D: drive:
Open Docker Desktop > Settings > Resources > Advanced > Disk image location
Change to D:\docker\

### Step 10: NSSM

```powershell
winget install NSSM.NSSM
nssm version  # Must succeed
```

### Step 11: Git

```powershell
winget install Git.Git
# Close and reopen PowerShell
git --version
git config --global core.autocrlf false
git config --global user.name "Assistant Build"
git config --global user.email "build@assistant.local"
```

### Prerequisites Complete

Run a final verification:
```powershell
python --version    # 3.11.x
node --version      # 20.x.x
cargo --version     # any
ollama list         # 4 models listed
docker ps           # no error
nssm version        # no error
git --version       # any
```

All must pass before Phase 1 begins.

---

## Phase 1: Backend Foundation

### 1.1 Create Virtual Environment and Install Dependencies

```powershell
cd C:\assistant\backend
python -m venv venv
.\venv\Scripts\Activate.ps1

pip install fastapi==0.115.0
pip install "uvicorn[standard]==0.30.0"
pip install httpx==0.27.0
pip install "pydantic[email]==2.7.0"
pip install sqlalchemy==2.0.30
pip install aiosqlite==0.20.0
pip install chromadb==0.5.0
pip install sentence-transformers==3.0.0
pip install APScheduler==3.10.4
pip install python-multipart==0.0.9
pip install cryptography==42.0.0
pip install imaplib2==3.6
pip install "msal==1.28.0"
pip install beautifulsoup4==4.12.3
pip install playwright==1.44.0
pip install pillow==10.3.0
pip install python-dotenv==1.0.1
pip install websockets==12.0
pip install pywin32==306
pip install plyer==2.1.0
pip install pyautogui==0.9.54

playwright install chromium
```

### 1.2 config.py

```python
# C:\assistant\backend\config.py
from pathlib import Path

BASE_DIR = Path("C:/assistant")
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
SANDBOX_DIR = BASE_DIR / "sandbox"
DOCS_DIR = BASE_DIR / "docs"

for d in [DATA_DIR, LOGS_DIR, SANDBOX_DIR, DOCS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 180

# Model assignments (can be overridden by SQLite preferences at runtime)
MODEL_ROUTER    = "phi3:mini"
MODEL_GENERAL   = "llama3.1:8b"
MODEL_CODE      = "qwen2.5-coder:14b"
MODEL_VISION    = "llava:7b"

# MCP server ports
MCP_FILESYSTEM  = "http://localhost:8010"
MCP_TERMINAL    = "http://localhost:8011"
MCP_EMAIL       = "http://localhost:8012"
MCP_BROWSER     = "http://localhost:8013"
MCP_SCREEN      = "http://localhost:8014"
MCP_TASKS       = "http://localhost:8015"

# Storage
SQLITE_PATH    = DATA_DIR / "assistant.db"
CHROMADB_PATH  = str(DATA_DIR / "chromadb")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
MEMORY_TOP_K   = 5

# Email — Yahoo
YAHOO_IMAP_HOST = "imap.mail.yahoo.com"
YAHOO_IMAP_PORT = 993
YAHOO_SMTP_HOST = "smtp.mail.yahoo.com"
YAHOO_SMTP_PORT = 587

# Email — Gmail
GMAIL_IMAP_HOST = "imap.gmail.com"
GMAIL_IMAP_PORT = 993
GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587

# Email — SRU Microsoft 365 (Microsoft Graph API)
SRU_GRAPH_BASE         = "https://graph.microsoft.com/v1.0"
SRU_TENANT_ID          = "common"
SRU_CLIENT_ID          = "YOUR_AZURE_APP_CLIENT_ID"
SRU_SCOPES             = ["Mail.Read", "Mail.Send", "Mail.ReadWrite",
                          "Calendars.Read", "Calendars.ReadWrite", "offline_access"]
SRU_TOKEN_REFRESH_MARGIN = 600  # Refresh token if within 10 minutes of expiry

# D2L
D2L_BASE_URL = "https://sru.desire2learn.com"

# Scheduler intervals (seconds)
INTERVAL_REMINDER_CHECK  = 60
INTERVAL_MAIL_SYNC       = 900
INTERVAL_D2L_SYNC        = 14400
MEMORY_EXTRACTION_DELAY  = 120

# FastAPI
API_HOST = "0.0.0.0"
API_PORT = 8000
```

### 1.3 database.py — Full SQLite Schema

```python
# C:\assistant\backend\database.py
import sqlite3
from config import SQLITE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    category TEXT DEFAULT 'general',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    body TEXT,
    due_datetime DATETIME,
    recurrence TEXT,
    status TEXT DEFAULT 'pending',
    priority INTEGER DEFAULT 2,
    source TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    start_datetime DATETIME,
    end_datetime DATETIME,
    location TEXT,
    notes TEXT,
    source TEXT DEFAULT 'user',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course TEXT,
    title TEXT NOT NULL,
    due_datetime DATETIME,
    description TEXT,
    status TEXT DEFAULT 'pending',
    url TEXT,
    d2l_id TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL,
    account TEXT NOT NULL,
    sender TEXT,
    subject TEXT,
    received_at DATETIME,
    read INTEGER DEFAULT 0,
    flagged INTEGER DEFAULT 0,
    snippet TEXT,
    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(uid, account)
);

CREATE TABLE IF NOT EXISTS conversation_index (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at DATETIME,
    ended_at DATETIME,
    summary TEXT,
    topics TEXT,
    memory_extracted INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS habit_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT,
    description TEXT NOT NULL,
    observed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    confidence REAL DEFAULT 0.5
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    path TEXT,
    language TEXT,
    last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS command_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    command_type TEXT,
    command TEXT,
    output TEXT,
    exit_code INTEGER,
    executed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT
);

CREATE TABLE IF NOT EXISTS credentials (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT UNIQUE NOT NULL,
    encrypted_data TEXT NOT NULL,
    token_expiry DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_datetime, status);
CREATE INDEX IF NOT EXISTS idx_assignments_due ON assignments(due_datetime, status);
CREATE INDEX IF NOT EXISTS idx_emails_account ON emails(account, received_at);
CREATE INDEX IF NOT EXISTS idx_emails_read ON emails(account, read);
"""

def init_db():
    conn = sqlite3.connect(SQLITE_PATH)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    print(f"Database initialized at {SQLITE_PATH}")

if __name__ == "__main__":
    init_db()
```

### 1.4 auth.py — Credential Encryption

```python
# C:\assistant\backend\auth.py
"""
Credentials are encrypted with Fernet symmetric encryption.
The encryption key is stored in the Windows Credential Store (keyring),
not in any file or environment variable.
"""
import keyring
import secrets
import base64
import sqlite3
import json
from datetime import datetime
from cryptography.fernet import Fernet
from config import SQLITE_PATH

SERVICE_NAME = "PersonalAssistant"
KEY_NAME = "encryption_key"

def get_or_create_key() -> bytes:
    key = keyring.get_password(SERVICE_NAME, KEY_NAME)
    if not key:
        key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        keyring.set_password(SERVICE_NAME, KEY_NAME, key)
    return key.encode()

def encrypt(data: dict) -> str:
    f = Fernet(get_or_create_key())
    return f.encrypt(json.dumps(data).encode()).decode()

def decrypt(encrypted: str) -> dict:
    f = Fernet(get_or_create_key())
    return json.loads(f.decrypt(encrypted.encode()).decode())

def store_credential(service: str, data: dict, token_expiry: datetime = None):
    encrypted = encrypt(data)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        INSERT INTO credentials (service, encrypted_data, token_expiry, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(service) DO UPDATE SET
            encrypted_data = excluded.encrypted_data,
            token_expiry = excluded.token_expiry,
            updated_at = CURRENT_TIMESTAMP
    """, (service, encrypted, token_expiry.isoformat() if token_expiry else None))
    conn.commit()
    conn.close()

def get_credential(service: str) -> dict | None:
    conn = sqlite3.connect(SQLITE_PATH)
    row = conn.execute(
        "SELECT encrypted_data FROM credentials WHERE service = ?", (service,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    return decrypt(row[0])
```

### 1.5 memory.py — ChromaDB + SQLite Memory Interface

Build a memory module that:

- Initializes ChromaDB client at CHROMADB_PATH with four collections:
  conversation_memory, user_preferences, project_context, knowledge_base
- Loads sentence-transformers all-MiniLM-L6-v2 at startup (once, cached)
- Exposes these functions:

```python
def add_memory(collection: str, text: str, metadata: dict) -> None
    # Embed text and store in the specified ChromaDB collection

def query_memory(collection: str, query_text: str, n_results: int = 5) -> list[dict]
    # Embed query_text, return top n_results from collection with metadata

def query_all_collections(query_text: str, n_per_collection: int = 2) -> list[dict]
    # Query all four collections, return merged results sorted by relevance

def inject_context(request_text: str) -> str
    # Query all collections, format top results as a clean context block string
    # Format: "- [type] content (confidence: 0.87)"

def add_preference(text: str, confidence: float = 0.8) -> None
    # Shorthand for add_memory("user_preferences", ...)

def add_conversation_summary(session_id: str, summary: str) -> None
    # Shorthand for add_memory("conversation_memory", ...)

def add_knowledge(text: str) -> None
    # Shorthand for add_memory("knowledge_base", ...) — permanent, never auto-deleted
```

Use cosine similarity for deduplication. When adding new memory, first query the
same collection for similar content. If any result has similarity > 0.85, skip the
new entry to avoid duplication.

### 1.6 router.py — Intent Classifier

```python
# C:\assistant\backend\router.py
import httpx
from config import OLLAMA_BASE_URL, MODEL_ROUTER

INTENTS = [
    "chat", "task_lookup", "reminder_set", "email", "file_action",
    "terminal", "code", "screen", "d2l", "schedule", "weather", "search"
]

TIER_MAP = {
    "chat": "MEDIUM", "task_lookup": "FAST", "reminder_set": "FAST",
    "email": "MEDIUM", "file_action": "MEDIUM", "terminal": "MEDIUM",
    "code": "HEAVY", "screen": "FAST", "d2l": "MEDIUM",
    "schedule": "FAST", "weather": "FAST", "search": "FAST",
}

MODEL_MAP = {
    "chat": "llama3.1:8b", "task_lookup": "phi3:mini", "reminder_set": "phi3:mini",
    "email": "llama3.1:8b", "file_action": "llama3.1:8b", "terminal": "qwen2.5-coder:14b",
    "code": "qwen2.5-coder:14b", "screen": "llava:7b", "d2l": "llama3.1:8b",
    "schedule": "phi3:mini", "weather": "phi3:mini", "search": "llama3.1:8b",
}

MCP_MAP = {
    "chat": [], "task_lookup": ["tasks"], "reminder_set": ["tasks"],
    "email": ["email"], "file_action": ["filesystem"], "terminal": ["terminal"],
    "code": ["filesystem", "terminal"], "screen": ["screen"],
    "d2l": ["browser"], "schedule": ["tasks"], "weather": ["browser"],
    "search": ["browser"],
}

ROUTER_PROMPT = """You are an intent classifier for a personal assistant.
Classify the user message into exactly one of these categories:
chat, task_lookup, reminder_set, email, file_action, terminal, code, screen,
d2l, schedule, weather, search

Rules:
- task_lookup: asking about existing tasks, reminders, or to-do items
- reminder_set: creating a new reminder or task
- schedule: asking about calendar, today's plan, upcoming events
- d2l: anything about school assignments, courses, grades, D2L
- code: writing, debugging, building, or running software
- terminal: running system commands, scripts, installations
- file_action: reading, finding, editing, or managing files
- screen: looking at or analyzing screen content
- email: reading, writing, or managing email
- weather: current weather or forecast
- search: looking up information on the web
- chat: everything else

Reply with ONLY the single category word. No explanation, no punctuation."""

async def classify_intent(message: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json={
                "model": MODEL_ROUTER,
                "messages": [
                    {"role": "system", "content": ROUTER_PROMPT},
                    {"role": "user", "content": message}
                ],
                "stream": False,
                "options": {"temperature": 0.0, "num_predict": 10}
            }
        )
        raw = resp.json()["message"]["content"].strip().lower()
        intent = raw if raw in INTENTS else "chat"
        return {
            "intent": intent,
            "tier": TIER_MAP[intent],
            "model": MODEL_MAP[intent],
            "tools": MCP_MAP[intent],
        }
```

### 1.7 main.py — FastAPI Application

Build the main FastAPI app with:

**Lifespan startup:**
- Call database.init_db()
- Initialize ChromaDB and load embedding model
- Initialize APScheduler and add all background jobs (see scheduler.py)
- Start APScheduler
- Mount PWA static files at /

**Endpoints to implement:**

POST /chat
- Accept: {message: str, session_id: str}
- Call classify_intent(message) to get routing
- Call inject_context(message) to get memory context
- Pull active tasks from SQLite (due in next 7 days, status=pending)
- Pull upcoming assignments from SQLite (due in next 7 days)
- Pull relevant preferences from SQLite
- Build system prompt using the template from the architecture doc
- Emit step event via WebSocket: "Classified as {intent} ({tier})"
- Emit step event: "Loading {model}..."
- Call Ollama API with streaming enabled
- Stream tokens back to client via StreamingResponse
- After streaming completes: update conversation_index in SQLite

WS /stream
- WebSocket endpoint for Tauri shell
- Handles: streaming chat responses, step events for Agent Monitor,
  dashboard refresh events, confirmation gate events, notification events

GET /tasks, POST /tasks, PUT /tasks/{id}, DELETE /tasks/{id}
- Full CRUD for SQLite tasks table

GET /tasks/today — tasks where date(due_datetime) = date('now')
GET /tasks/upcoming — tasks where due_datetime between now and now+7days

GET /assignments — all assignments ordered by due_datetime
GET /assignments/overdue — due_datetime < now AND status != 'complete'

GET /email/inbox — merged inbox from all three accounts from SQLite email table,
  ordered by received_at desc, limit 50
GET /email/inbox/{account} — filtered by account (yahoo|gmail|sru)
GET /email/message/{account}/{uid} — fetch full body via Email MCP if not cached
POST /email/send — {account, to, subject, body, reply_to_uid?}

GET /status — current active job info: {active: bool, task: str, steps: list, elapsed: int}
GET /memory/recent — last 20 ChromaDB entries across all collections
DELETE /memory/{collection}/{id} — delete specific memory entry
GET /health — check Ollama reachable, all MCP servers reachable, SQLite connected,
  ChromaDB connected; return status for each

**Confirmation gate implementation:**
When a tool call returns {requires_confirmation: true, token: str, description: str,
details: str}, the backend:
1. Stores the pending action in memory with the token
2. Emits a confirmation_required WebSocket event with description and details
3. Waits (non-blocking) for POST /confirm/{token} or DELETE /confirm/{token}
4. On POST (approve): executes the stored action and streams the result
5. On DELETE (deny): discards the action and informs the model

### 1.8 scheduler.py — Background Jobs

Implement APScheduler with these jobs. Each job must handle its own exceptions
internally and log errors to C:\assistant\logs\scheduler.log without crashing.

**Job: reminder_check (IntervalTrigger, seconds=60)**
```python
def reminder_check():
    conn = sqlite3.connect(SQLITE_PATH)
    due = conn.execute("""
        SELECT id, title, body FROM tasks
        WHERE due_datetime <= datetime('now')
        AND status = 'pending'
    """).fetchall()
    for task_id, title, body in due:
        conn.execute("UPDATE tasks SET status='notified' WHERE id=?", (task_id,))
        # Fire Windows toast notification using plyer
        notification.notify(title="Assistant Reminder", message=title, timeout=10)
        # Emit WebSocket event for dashboard update
        emit_ws_event("reminder_fired", {"id": task_id, "title": title})
    conn.commit()
    conn.close()
```

**Job: yahoo_mail_sync (IntervalTrigger, seconds=900)**
Using imaplib2:
- Connect to imap.mail.yahoo.com:993 with SSL
- Authenticate with stored Yahoo App Password from credentials table
- SELECT INBOX
- Search for messages in the last 7 days (SINCE date)
- For each message UID not already in emails table:
  - Fetch envelope (FROM, SUBJECT, DATE, FLAGS)
  - Fetch first 200 bytes of body for snippet
  - Insert into emails table with account='yahoo'
- Emit ws event "email_synced" with new message count
- On auth failure: log error, emit ws event "auth_error" with account='yahoo'

**Job: gmail_sync (IntervalTrigger, seconds=900)**
Same as yahoo_mail_sync but connecting to imap.gmail.com:993 with account='gmail'.

**Job: sru_mail_sync (IntervalTrigger, seconds=900)**
Using Microsoft Graph API via httpx:
- Get access token from credentials table
- Check if token expires within SRU_TOKEN_REFRESH_MARGIN seconds
- If so: use refresh token to get new access token via MSAL, update credentials table
- If refresh fails: emit ws event "auth_error" with account='sru', skip sync
- Call GET https://graph.microsoft.com/v1.0/me/messages?$top=50&$orderby=receivedDateTime desc
- For each message not in emails table: insert with account='sru'
- Emit ws event "email_synced"

**Job: d2l_sync (IntervalTrigger, seconds=14400)**
Using Playwright:
- Launch headless Chromium
- Navigate to sru.desire2learn.com
- Authenticate with stored D2L credentials (handle MFA if needed)
- Navigate to each course's assignments page
- Extract: course name, assignment title, due date, description URL, D2L ID
- Upsert each assignment (INSERT OR REPLACE based on d2l_id)
- Emit ws event "d2l_synced" with new assignment count
- Close browser

**Memory extraction:** Not a scheduled interval job. Instead, main.py tracks the
last message time per session. When a session has been idle for MEMORY_EXTRACTION_DELAY
seconds, main.py triggers extract_session_memory(session_id) asynchronously.

```python
async def extract_session_memory(session_id: str):
    # Get full conversation from conversation_index
    # Send to llama3.1:8b with extraction prompt
    extraction_prompt = """
    Extract any user preferences, habits, project updates, or explicit facts from
    this conversation. Return ONLY a JSON array. Each item must have:
    - "type": one of "preference", "habit", "project", "fact"
    - "content": the observation as a clear statement
    - "confidence": float 0.0 to 1.0

    Example: [{"type":"preference","content":"prefers concise code comments","confidence":0.9}]
    Return only the JSON array with no other text.
    """
    # Parse response JSON
    # For each item: add_memory(item.type_to_collection, item.content, {confidence})
    # High confidence facts (>0.8) also written to SQLite preferences
    # Mark session memory_extracted=1 in conversation_index
```

### Phase 1 Verification

```powershell
cd C:\assistant\backend
.\venv\Scripts\Activate.ps1
python database.py        # "Database initialized"
python -c "from memory import init_memory; init_memory(); print('ChromaDB OK')"
python -c "import asyncio; from router import classify_intent; print(asyncio.run(classify_intent('what do i have due today')))"
# Must return intent='schedule', tier='FAST', model='phi3:mini'
python -c "import asyncio; from router import classify_intent; print(asyncio.run(classify_intent('write a python script to rename files')))"
# Must return intent='code', tier='HEAVY', model='qwen2.5-coder:14b'
uvicorn main:app --port 8000
# In another terminal:
curl http://localhost:8000/health
# Must return all systems green
```

All checks must pass before Phase 2.

---

## Phase 2: MCP Servers

Each MCP server is a standalone FastAPI app. Each has its own requirements.txt and
runs in its own virtual environment. Each is registered as a Windows service via NSSM.

Standard MCP server structure for each:
```
C:\assistant\mcp\{name}\
├── main.py
├── requirements.txt
└── venv\
```

Standard requirements for all MCP servers:
```
fastapi==0.115.0
uvicorn[standard]==0.30.0
httpx==0.27.0
pydantic==2.7.0
```

### 2.1 Filesystem MCP — Port 8010

Additional requirements: none

Endpoints:

GET /list?path=
Returns: {path, entries: [{name, type, size, modified}]}
Validates path exists. Returns 400 for invalid paths.

GET /read?path=&max_bytes=102400
Returns: {path, content, truncated: bool}
Text files only. Returns 400 for binary files. Truncates at max_bytes.

POST /write
Body: {path: str, content: str, create_dirs: bool = false}
Returns: {success, path}
Creates parent directories if create_dirs is true.

POST /search
Body: {root: str, name_pattern: str = "", content_search: str = "", max_results: int = 50}
Returns: {results: [{path, match_type}]}
Uses glob for name search, line-by-line scan for content search.

POST /move
Body: {source: str, destination: str}
Returns: {success, destination}

POST /copy
Body: {source: str, destination: str}
Returns: {success, destination}

DELETE /delete?path=
Returns: {requires_confirmation: true, token: str, description: str, details: str}
NEVER deletes immediately. Always returns confirmation request.

POST /confirm/{token}
Executes the pending delete associated with the token.

GET /metadata?path=
Returns: {path, size, created, modified, type, extension}

Path validation: reject paths containing ".." (directory traversal prevention).
All paths normalized to Windows format.

### 2.2 Terminal MCP — Port 8011

Additional requirements:
```
pywin32==306
```

Destructive patterns list (must require confirmation):
```python
DESTRUCTIVE_PATTERNS = [
    "Remove-Item", "rm ", "rmdir", "del ", "rd ",
    "format ", "Format-Volume",
    "reg delete", "reg add",
    "net user", "net localgroup",
    "Stop-Service", "Disable-ComputerRestore",
    "Uninstall-", "Remove-AppxPackage",
    "Clear-RecycleBin", "Reset-ComputerMachinePassword",
]
```

POST /powershell
Body: {command: str, working_dir: str = "C:\\assistant\\sandbox", timeout: int = 60}
- Check command against DESTRUCTIVE_PATTERNS
- If match: return {requires_confirmation: true, token: uuid, description, details: command}
- Else: log to SQLite command_log, execute via subprocess, return {stdout, stderr, exit_code, duration}

POST /cmd
Same as /powershell but runs cmd.exe /c {command}

POST /python
Body: {script_path: str, args: list = [], working_dir: str}
Executes python {script_path} in a subprocess.

POST /docker_run
Body: {command: str, working_dir: str = "/workspace"}
Runs command inside the assistant-sandbox Docker container.
Mounts C:\assistant\sandbox to /workspace inside container.
Uses: docker run --rm -v C:/assistant/sandbox:/workspace --memory=4g --cpus=2 assistant-sandbox {command}

POST /confirm/{token}
Executes the stored destructive command.

GET /log?limit=50
Returns last N entries from command_log table.

### 2.3 Email MCP — Port 8012

Additional requirements:
```
imaplib2==3.6
msal==1.28.0
```

This server manages all three email accounts. It imports auth.py from the backend
by adding C:\assistant\backend to sys.path.

**Yahoo endpoints:**
GET /yahoo/inbox?limit=20 — query SQLite emails table where account='yahoo'
GET /yahoo/message/{uid} — fetch full body via IMAP if not cached, cache in SQLite
POST /yahoo/send — {to, subject, body, reply_to_uid?} via smtplib STARTTLS
POST /yahoo/flag — {uid, flagged: bool}
POST /yahoo/move — {uid, folder}
GET /yahoo/search?q= — IMAP SEARCH command

**Gmail endpoints:** (identical structure, account='gmail', different IMAP host)
GET /gmail/inbox, GET /gmail/message/{uid}, POST /gmail/send,
POST /gmail/flag, POST /gmail/move, GET /gmail/search

**SRU endpoints (Microsoft Graph API):**
GET /sru/inbox?limit=20 — GET {SRU_GRAPH_BASE}/me/messages with auth header
GET /sru/message/{id} — GET {SRU_GRAPH_BASE}/me/messages/{id}
POST /sru/send — POST {SRU_GRAPH_BASE}/me/sendMail
POST /sru/flag — PATCH {SRU_GRAPH_BASE}/me/messages/{id}
GET /sru/search?q= — GET {SRU_GRAPH_BASE}/me/messages?$search="{q}"
GET /sru/auth/status — returns {connected: bool, expiry: str, needs_reauth: bool}
GET /sru/auth/start — returns OAuth2 authorization URL for browser popup
POST /sru/auth/callback — {code: str} — exchange code for tokens, store encrypted

**Unified endpoint:**
GET /inbox?limit=50 — merge all three accounts from SQLite, sorted by received_at desc,
return with account label on each message

### 2.4 Browser / D2L MCP — Port 8013

Additional requirements:
```
playwright==1.44.0
beautifulsoup4==4.12.3
```

playwright install chromium (run after pip install)

**D2L endpoints:**
POST /d2l/sync — trigger immediate D2L scrape (same logic as scheduler job)
GET /d2l/assignments — return from SQLite assignments table
GET /d2l/assignment/{id} — full assignment detail; trigger live scrape if record >4hrs old
GET /d2l/courses — list all enrolled courses

D2L login flow using Playwright:
1. Launch headless Chromium
2. Navigate to D2L_BASE_URL/d2l/login
3. Fill username and password from credentials table (service='d2l')
4. Handle MFA if prompted (look for MFA challenge page, may need manual intervention
   on first run — emit ws event to notify user)
5. Verify login success by checking for user dashboard URL
6. Preserve cookies/session for subsequent requests

**Web endpoints:**
POST /fetch — {url: str} — fetch URL with httpx, clean HTML with BeautifulSoup,
return plain text content (remove scripts, styles, nav, footer)
POST /search — {query: str} — DuckDuckGo search via their JSON API or lite HTML,
return [{title, url, snippet}] top 5 results
POST /weather — {location: str = "Slippery Rock, PA"} — fetch weather from
wttr.in/{location}?format=j1 JSON API, parse and return current conditions + forecast

### 2.5 Screen MCP — Port 8014

Additional requirements:
```
pillow==10.3.0
pyautogui==0.9.54
httpx==0.27.0
```

POST /capture
- Use pyautogui.screenshot() to capture primary monitor
- Save to C:\assistant\data\last_screenshot.png (overwrite each time)
- Return {width, height, image_base64: str (PNG base64)}

POST /capture/window
Body: {window_title: str}
- Use pygetwindow to find window by title
- Capture that window region using pyautogui.screenshot(region=...)
- Return same format as /capture

POST /analyze
Body: {image_base64: str, question: str}
- Send to Ollama llava:7b via multimodal chat endpoint
- Payload: {model: "llava:7b", messages: [{role:"user", content:[
    {type:"image_url", image_url:{url:"data:image/png;base64,{image_base64}"}},
    {type:"text", text: question}
  ]}], stream: false}
- Return {analysis: str}

POST /capture_and_analyze
Body: {question: str, window_title: str = ""}
- Calls /capture or /capture/window then /analyze in sequence
- Convenience endpoint for "look at my screen" requests

### 2.6 Tasks / Calendar MCP — Port 8015

All endpoints read from and write to C:\assistant\data\assistant.db.
This server imports from config.py by adding C:\assistant\backend to sys.path.

GET /tasks — optional query params: status, priority, due_before, due_after
GET /tasks/today — due today
GET /tasks/upcoming?days=7 — due in next N days
POST /tasks — create task {title, body?, due_datetime?, priority?, recurrence?}
PUT /tasks/{id} — update task fields
DELETE /tasks/{id} — delete task (no confirmation required — tasks are user-owned)

GET /assignments — all assignments ordered by due_datetime asc
GET /assignments/overdue — due_datetime < now AND status != 'complete'
GET /assignments/today — due today
PUT /assignments/{id}/status — update status field only

GET /calendar — optional start and end datetime params
POST /calendar — create event {title, start_datetime, end_datetime, location?, notes?}
DELETE /calendar/{id}

GET /summary — combined "what do I have" view:
Returns: {
    overdue_tasks: [...],
    today_tasks: [...],
    today_assignments: [...],
    upcoming_7_days: {date: [items]},
    unread_email_counts: {yahoo: N, gmail: N, sru: N}
}
This is the endpoint the Dashboard calls for its full view.

### Register All MCP Servers as Windows Services

For each MCP server (filesystem, terminal, email, browser, screen, tasks):

```powershell
# Example for filesystem — repeat pattern for all others
nssm install AssistantMCP_Filesystem "C:\assistant\mcp\filesystem\venv\Scripts\python.exe"
nssm set AssistantMCP_Filesystem AppParameters "-m uvicorn main:app --host 127.0.0.1 --port 8010"
nssm set AssistantMCP_Filesystem AppDirectory "C:\assistant\mcp\filesystem"
nssm set AssistantMCP_Filesystem Start SERVICE_AUTO_START
nssm set AssistantMCP_Filesystem AppStdout "C:\assistant\logs\mcp_filesystem.log"
nssm set AssistantMCP_Filesystem AppStderr "C:\assistant\logs\mcp_filesystem_err.log"
nssm start AssistantMCP_Filesystem
```

Ports:
- filesystem: 8010, terminal: 8011, email: 8012, browser: 8013, screen: 8014, tasks: 8015

### Phase 2 Verification

```powershell
# Test each MCP server
curl http://localhost:8010/list?path=C:\
curl http://localhost:8011/log
curl http://localhost:8012/inbox?limit=5
curl http://localhost:8013/weather
curl http://localhost:8014/capture
curl http://localhost:8015/tasks/today

# Test confirmation gate
curl -X DELETE "http://localhost:8010/delete?path=C:\assistant\sandbox\test.txt"
# Must return requires_confirmation: true — MUST NOT delete anything

# Test from FastAPI backend (tool dispatch)
curl -X POST http://localhost:8000/command -H "Content-Type: application/json" \
  -d '{"tool":"filesystem","action":"list","params":{"path":"C:\\"}}'
```

---

## Phase 3: Docker Sandbox

### 3.1 Create Sandbox Docker Image

```dockerfile
# C:\assistant\sandbox\Dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    nodejs npm git curl wget build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    requests httpx pandas numpy matplotlib \
    scipy scikit-learn pillow

WORKDIR /workspace

CMD ["/bin/bash"]
```

```powershell
cd C:\assistant\sandbox
docker build -t assistant-sandbox .
docker run --rm assistant-sandbox python --version  # Must succeed
```

### 3.2 Integrate Sandbox Into Terminal MCP

The /docker_run endpoint in Terminal MCP uses:
```
docker run --rm \
  -v C:/assistant/sandbox:/workspace \
  --network bridge \
  --memory 4g \
  --cpus 2 \
  --user 1000:1000 \
  assistant-sandbox \
  {command}
```

---

## Phase 4: Desktop Shell

### 4.1 Initialize Tauri v2 Project

```powershell
cd C:\assistant\shell
npm create tauri-app@latest . -- --template react-ts --manager npm
npm install
```

### 4.2 Install Frontend Dependencies

```powershell
npm install zustand@4.5.0
npm install react-markdown@9.0.0
npm install highlight.js@11.9.0
npm install react-syntax-highlighter@15.5.0
npm install framer-motion@11.0.0
npm install lucide-react@0.383.0
npm install @radix-ui/react-dialog
npm install @radix-ui/react-tooltip
npm install @radix-ui/react-select
npm install @radix-ui/react-tabs
npm install @radix-ui/react-slider
npm install tailwindcss@3.4.0 postcss autoprefixer
npx tailwindcss init -p

# Download Inter and JetBrains Mono fonts to C:\assistant\shell\src\assets\fonts\
```

### 4.3 Design Tokens

```css
/* C:\assistant\shell\src\styles\tokens.css */
:root {
  --bg-primary:     #0d0d0f;
  --bg-secondary:   #141416;
  --bg-tertiary:    #1a1a1e;
  --bg-panel:       rgba(255, 255, 255, 0.04);
  --bg-panel-hover: rgba(255, 255, 255, 0.07);
  --bg-input:       rgba(255, 255, 255, 0.06);
  --border-subtle:  rgba(255, 255, 255, 0.08);
  --border-accent:  rgba(99, 179, 237, 0.35);

  --accent:         #63b3ed;
  --accent-dim:     rgba(99, 179, 237, 0.5);
  --accent-glow:    rgba(99, 179, 237, 0.12);
  --accent-bg:      rgba(99, 179, 237, 0.1);

  --text-primary:   #f0f0f0;
  --text-secondary: #a0a0a0;
  --text-muted:     #505050;
  --text-accent:    #63b3ed;

  --status-ok:      #68d391;
  --status-warn:    #f6ad55;
  --status-error:   #fc8181;
  --status-info:    #63b3ed;

  --user-bubble-bg: rgba(99, 179, 237, 0.15);
  --user-bubble-border: rgba(99, 179, 237, 0.3);

  --font-sans:  'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono:  'JetBrains Mono', 'Fira Code', Consolas, monospace;

  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --radius-xl:  24px;

  --shadow-sm:  0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md:  0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-lg:  0 8px 32px rgba(0, 0, 0, 0.5);

  --t-fast:     150ms ease;
  --t-normal:   250ms ease;
  --t-slow:     400ms ease;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}
```

### 4.4 Application Shell (App.tsx)

Build a single-window layout:

```
+------------------+------------------------------------------+
|   Sidebar        |   Main Content Area                      |
|   (220px fixed)  |   (fills remaining width)                |
|                  |                                          |
|   [Logo/Name]    |   <AssistantPanel />  (default)          |
|                  |   <Dashboard />                          |
|   [Chat icon]    |   <AgentMonitor />                       |
|   [Dashboard]    |   <Settings />                           |
|   [Monitor]      |                                          |
|   [Settings]     |                                          |
|                  |                                          |
|   ─────────      |                                          |
|   [Status dot]   |                                          |
|   [Minimize]     |                                          |
+------------------+------------------------------------------+
```

Sidebar:
- Logo area at top: small geometric icon + "ASSISTANT" text
- Nav icons with labels, active state highlighted with accent color and left border
- Bottom: green/red status dot indicating Ollama online/offline (polls /health every 30s)
- Minimize to tray button

Panel switching: framer-motion AnimatePresence with opacity + slight Y translateY
transition (0 → -8px on exit, 8px → 0 on enter), 250ms.

### 4.5 AssistantPanel.tsx

```
+--------------------------------------------------+
| Model badge (top right): "FAST · phi3"           |
|--------------------------------------------------|
|                                                  |
|  [Message history scrollable area]               |
|                                                  |
|  User message (right-aligned):                   |
|  ┌─────────────────────────────┐                 |
|  │ message text               │ accent border    |
|  └─────────────────────────────┘                 |
|                                                  |
|  Assistant message (left-aligned):               |
|  ┌─────────────────────────────────────────┐     |
|  │ streamed text renders here in real time │     |
|  │                                         │     |
|  │ ```python                               │     |
|  │ def example():  # syntax highlighted    │     |
|  │     pass        [copy button] [lang]    │     |
|  │ ```                                     │     |
|  └─────────────────────────────────────────┘     |
|                                                  |
|  [Confirmation gate banner — amber — when active]|
|  "Delete C:\file.txt? [Approve] [Deny]"          |
|                                                  |
|--------------------------------------------------|
|  [text input area ─────────────────] [Send] [🎤]  |
|  ← breathing border animation when generating    |
+--------------------------------------------------+
```

State management (Zustand):
- messages: array of {role, content, model, timestamp}
- isGenerating: boolean
- pendingConfirmation: {token, description, details} | null
- activeModel: string
- sessionId: string

WebSocket connection:
- Connect to ws://localhost:8000/stream on mount
- Receive: {type: "token", content: str} → append to current assistant message
- Receive: {type: "step", content: str} → forward to AgentMonitor store
- Receive: {type: "confirmation_required", token, description, details} → set pendingConfirmation
- Receive: {type: "model_changed", model: str} → update activeModel badge
- Receive: {type: "done"} → set isGenerating to false

Confirmation gate component:
- Renders as an amber-bordered banner above the input when pendingConfirmation is not null
- Shows action description in text, command/path in monospace
- Approve button (green): POST /confirm/{token}, clear pendingConfirmation
- Deny button (red): DELETE /confirm/{token}, clear pendingConfirmation

Breathing animation (CSS):
```css
@keyframes breathe {
  0%, 100% { border-color: rgba(99, 179, 237, 0.3); }
  50%       { border-color: rgba(99, 179, 237, 1.0); }
}
.input-area.generating { animation: breathe 2s ease-in-out infinite; }
```

### 4.6 Dashboard.tsx

Calls GET /tasks/summary on mount and every 60 seconds.
Calls GET /email/inbox (all accounts) on mount and every 15 minutes.

Layout: CSS Grid, 3 columns on desktop, 1 column stacked on smaller windows.

Left column (time and weather):
- Large digital clock (live, updates every second)
- Full date line: "Thursday, March 26, 2026"
- Weather card: fetched from /weather on load
  Shows: condition icon (use lucide-react icons), temp, high/low, brief description

Center column (agenda):
- OVERDUE section (amber): tasks and assignments past due — if none, hidden
- TODAY section: tasks and assignments due today, sorted by time
  Each item: colored dot (task=blue, assignment=green) + title + time + course if applicable
- UPCOMING section: next 7 days grouped by "Tomorrow", "Wednesday", etc.
- Quick add button: opens an inline form for creating a reminder without leaving Dashboard

Right column (comms and projects):
- Email summary: three rows, one per account
  "Yahoo  •  {N} unread" with the most recent sender+subject
  "Gmail  •  {N} unread"
  "RockMail  •  {N} unread"
  Each row clickable — switches to Settings > Accounts or triggers email check
- Projects section: list from SQLite projects table, sorted by last_active desc
- Quick actions row: three icon buttons
  [Check D2L] — triggers POST /d2l/sync, then refreshes
  [Check Email] — triggers all three mail syncs
  [+ Reminder] — opens reminder create dialog

Item update animation: when the data refreshes and an item has changed, apply a
300ms highlight pulse using a CSS keyframe that briefly shows accent-bg then fades.

### 4.7 AgentMonitor.tsx

Zustand store for agent state:
- isActive: boolean
- taskTitle: string
- startTime: Date | null
- steps: string[]  (last 30 steps)
- currentModel: string
- liveTokens: string  (last 150 characters of live token stream)
- lastCompleted: {title, summary, endTime} | null

Receives step events from the WebSocket. Activates (isActive = true) when step events
are received, deactivates (isActive = false) on "done" event.

Display when active:
```
┌─────────────────────────────────────────────────────┐
│ TASK: Write file renamer script          00:42 ●    │
│ MODEL: qwen2.5-coder                    [Cancel]    │
│─────────────────────────────────────────────────────│
│ ✓ Classified as CODE (HEAVY)                        │
│ ✓ Loading qwen2.5-coder...                          │
│ ✓ Reading C:\projects\files\ (47 items)             │
│ ● Writing renamer.py...                             │
│ ● Running in sandbox...                             │
│─────────────────────────────────────────────────────│
│ GENERATING:                                         │
│ ...for f in files:                                  │
│     new_name = pattern.format(...)                  │
└─────────────────────────────────────────────────────┘
```

Step icons: ✓ = completed step (accent color), ● = current step (pulsing dot)
Elapsed timer: updates every second while isActive
Cancel button: sends DELETE /confirm/cancel to backend, clears active state

Display when idle (lastCompleted exists):
Shows last task title, completion time, brief summary if available.
Grayed out, no active indicators.

### 4.8 Settings.tsx

Radix UI Tabs component with four tabs:

**Models tab:**
Table of all 12 intent categories. Each row: intent name, current model (dropdown),
FAST/MEDIUM/HEAVY tier label. Available models populated from GET /health (Ollama model list).
Save button: POST /preferences with updated model assignments.

**Memory tab:**
Two sections:
- LEARNED MEMORY: list of recent ChromaDB entries with type badge, content, confidence,
  timestamp, and delete button per entry. Calls GET /memory/recent.
- KNOWLEDGE BASE: form to add explicit permanent memories + list of existing ones.
  Add: POST /memory/knowledge. Delete: DELETE /memory/{collection}/{id}.
- DANGER ZONE: "Clear All Memory" button — requires typing "DELETE ALL MEMORY" in
  a confirmation input before enabling. Calls DELETE /memory/all.

**Accounts tab:**
Three accordion sections, one per account.

Yahoo section:
- Email address text input
- App Password text input (obscured, toggle show/hide)
- Test Connection button → GET /email/yahoo/test → show result
- Instructions link to Yahoo App Password generation

Gmail section:
- Same fields as Yahoo
- Instructions link to Google App Password generation

SRU RockMail section:
- Connected/Disconnected status badge
- Token expiry date if connected
- Authorize button (shows when disconnected): opens OAuth2 URL in system browser
  The browser auth flow redirects to localhost:8000/auth/sru/callback automatically
- Re-authorize button (always visible): same flow, updates existing token
- Connection status note: "SRU passwords expire every 90 days. Re-authorize when prompted."

D2L section:
- Username and password fields (stored encrypted)
- Last sync timestamp
- Manual Sync Now button
- Test Connection button

**System tab:**
- Model idle timeout: Radix Slider (1–15 minutes, default 3)
  On change: update OLLAMA_KEEP_ALIVE env var and restart Ollama service
- GPU memory display: current usage fetched from /health
- Start with Windows: toggle switch
  On enable: creates startup shortcut. On disable: removes it.
- Minimize to tray on close: toggle switch
- Sandbox path: text input showing C:\assistant\sandbox, editable
- Log viewer: last 100 lines of C:\assistant\logs\backend.log, auto-updates every 10s
- Export settings: downloads SQLite preferences as JSON

### 4.9 Tauri Configuration (src-tauri/tauri.conf.json)

```json
{
  "app": {
    "windows": [{
      "title": "Assistant",
      "width": 1200,
      "height": 800,
      "minWidth": 900,
      "minHeight": 600,
      "resizable": true,
      "decorations": true,
      "transparent": false,
      "center": true
    }],
    "trayIcon": {
      "iconPath": "icons/tray.png",
      "iconAsTemplate": false
    }
  },
  "bundle": {
    "active": true,
    "icon": ["icons/icon.ico"],
    "identifier": "com.assistant.personal"
  }
}
```

Tauri Rust backend (src-tauri/src/main.rs) must implement:
- System tray with right-click menu: Show/Hide, and Quit
- Left-click tray icon: toggle window visibility
- "Start minimized" flag: if --tray argument passed, start hidden

### Phase 4 Verification

```powershell
cd C:\assistant\shell
npm run tauri dev
```

Verify manually:
- [ ] All four panels render and switch with smooth transitions
- [ ] Chat messages stream correctly (no dump-all-at-once)
- [ ] Code blocks are syntax highlighted with copy buttons
- [ ] Model badge updates when intent changes between requests
- [ ] Breathing animation shows on input while generating
- [ ] Confirmation gate renders and Approve/Deny buttons work
- [ ] Dashboard shows today's tasks, email counts, quick actions
- [ ] Agent Monitor shows steps during a multi-tool task
- [ ] Settings tabs all render and save correctly
- [ ] System tray icon shows and right-click menu works
- [ ] Window hides/shows on tray icon click

---

## Phase 5: Progressive Web App

### 5.1 Initialize PWA

```powershell
cd C:\assistant\pwa
npx create-react-app . --template typescript
npm install zustand react-markdown framer-motion
npm install @radix-ui/react-tabs
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### 5.2 PWA Manifest (public/manifest.json)

```json
{
  "name": "Assistant",
  "short_name": "Assistant",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0d0d0f",
  "theme_color": "#0d0d0f",
  "orientation": "portrait",
  "icons": [
    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}
  ]
}
```

### 5.3 PWA Views

Four bottom-tab views:

**Chat view** (default):
- Same conversation interface as Tauri shell but full-screen mobile
- Uses the same /stream WebSocket endpoint
- Input area at bottom of screen above the tab bar
- Voice button uses window.SpeechRecognition (iOS Safari Web Speech API)

**Tasks view:**
- Today's tasks and assignments (calls /tasks/today and /assignments/today)
- "Add reminder" button: full-screen form overlay
- Swipe left on task to reveal "Done" and "Delete" actions

**Email view:**
- Three account tabs at top (Yahoo | Gmail | RockMail)
- Message list: sender, subject, time, read/unread indicator
- Tap message: expand to show full body (calls /email/message/{account}/{uid})
- Reply button on expanded message

**Settings view (mobile-only settings):**
- Account connection status (read-only)
- Re-authorize SRU button
- Model idle timeout setting

### 5.4 Service Worker

Register a service worker for offline shell capability:
- Cache-first for all static assets (CSS, JS, fonts, icons)
- Network-first for all API calls (/chat, /tasks, /email, etc.)
- Fallback to cached data if network unavailable (show "offline" indicator)

### 5.5 Build and Serve from FastAPI

```powershell
cd C:\assistant\pwa
npm run build
```

In FastAPI main.py:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="C:/assistant/pwa/build", html=True), name="pwa")
```

Note: Mount the PWA AFTER all API routes are defined, so API routes take precedence.

### 5.6 iOS Installation Instructions

Generate a INSTALL_ON_IPHONE.txt in C:\assistant\docs\:
```
1. Connect your iPhone to the same Tailscale network as your PC
2. Find your PC's Tailscale IP: run "tailscale ip" in PowerShell
3. Open Safari on your iPhone
4. Navigate to: http://[tailscale-ip]:8000
5. Tap the Share button (box with arrow)
6. Tap "Add to Home Screen"
7. Tap "Add"
8. The assistant icon now appears on your home screen
```

### Phase 5 Verification

- [ ] PWA builds without errors
- [ ] PWA is accessible from a second device at http://[tailscale-ip]:8000
- [ ] Chat works over Tailscale from the second device
- [ ] Tasks and email endpoints load correctly
- [ ] Add to Home Screen works on iPhone (standalone mode, no browser chrome)
- [ ] Voice input works in Safari on iOS

---

## Phase 6: Windows Services Final Configuration

### Register FastAPI Backend as Windows Service

```powershell
nssm install AssistantBackend "C:\assistant\backend\venv\Scripts\python.exe"
nssm set AssistantBackend AppParameters "-m uvicorn main:app --host 0.0.0.0 --port 8000"
nssm set AssistantBackend AppDirectory "C:\assistant\backend"
nssm set AssistantBackend Start SERVICE_AUTO_START
nssm set AssistantBackend AppStdout "C:\assistant\logs\backend.log"
nssm set AssistantBackend AppStderr "C:\assistant\logs\backend_err.log"
nssm set AssistantBackend AppRestartDelay 5000
nssm start AssistantBackend
```

### Configure Tauri App to Start With Windows

```powershell
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Assistant.lnk")
$Shortcut.TargetPath = "C:\assistant\shell\src-tauri\target\release\assistant.exe"
$Shortcut.Arguments = "--tray"
$Shortcut.Save()
```

### Final System Verification Checklist

Run after all phases are complete:

**Inference:**
- [ ] All four Ollama models pull and run correctly
- [ ] CUDA acceleration active (GPU usage visible in Task Manager during inference)
- [ ] Models unload from VRAM after 3 minutes idle
- [ ] GPU VRAM returns to baseline after idle (verify in Task Manager > GPU)

**Backend:**
- [ ] GET /health returns all systems green
- [ ] Intent classifier correctly routes test messages:
  - "what do I have due today" → schedule, FAST, phi3:mini
  - "check my email" → email, MEDIUM, llama3.1:8b
  - "write a Python web scraper" → code, HEAVY, qwen2.5-coder:14b
  - "look at my screen" → screen, FAST, llava:7b

**Memory:**
- [ ] Preferences persist correctly across backend restarts
- [ ] Memory injection adds context to system prompts
- [ ] Learning loop extracts and stores observations after a test session
- [ ] Stored memories appear in Settings > Memory tab

**Computer Control:**
- [ ] Filesystem MCP can list C:\ and D:\
- [ ] Filesystem MCP can read and write a test file
- [ ] Filesystem delete returns confirmation_required — does NOT delete immediately
- [ ] Terminal MCP executes Get-Date in PowerShell and returns output
- [ ] Terminal MCP returns confirmation_required for a destructive command pattern
- [ ] Confirmation gate in Tauri UI shows and both buttons work
- [ ] Screen MCP captures a screenshot successfully
- [ ] Screen MCP analyze returns LLaVA description of the screenshot

**Email:**
- [ ] Yahoo inbox loads (after App Password is set in Settings)
- [ ] Gmail inbox loads (after App Password is set in Settings)
- [ ] SRU OAuth flow completes and inbox loads (after authorization)
- [ ] SRU re-auth notification appears when token is manually expired

**D2L:**
- [ ] D2L sync completes and assignments appear in Dashboard
- [ ] Manual sync now button works from Settings

**Productivity:**
- [ ] Creating a reminder from the Dashboard Quick Add works
- [ ] Reminder notification fires at the scheduled time (Windows toast)
- [ ] Overdue items appear highlighted amber in Dashboard
- [ ] "What do I have due today?" returns correct response

**Desktop Shell:**
- [ ] All four panels render and transitions are smooth
- [ ] Streaming responses display correctly (character by character)
- [ ] Agent Monitor shows live steps during a code task
- [ ] Model badge updates correctly per intent
- [ ] System tray icon persists when window is closed
- [ ] App restores from tray on icon click

**Remote Access:**
- [ ] PWA accessible from a second device over Tailscale
- [ ] Chat works from mobile
- [ ] Tasks visible from mobile
- [ ] PWA installs to iPhone home screen and opens in standalone mode

**Startup:**
- [ ] After a full Windows reboot:
  - Ollama service is running
  - All MCP services are running
  - FastAPI backend is running
  - Tauri app opens to tray
  - GET /health returns all green

---

## Security Requirements

- All credentials encrypted with Fernet using key from Windows Credential Store
- No credentials in any file, config, or environment variable at any time
- MCP servers: 127.0.0.1 only — not 0.0.0.0
- FastAPI: 0.0.0.0 (accessible over Tailscale) — only port 8000
- Docker sandbox: no access to host paths except C:\assistant\sandbox
- All file and terminal operations logged to SQLite with full audit trail
- Destructive operations require explicit UI confirmation — no exceptions
