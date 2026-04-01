# Personal Operating Assistant — Final Architecture Plan

**Hardware:** Intel i7-11th Gen KF | RTX 3060 OC 12GB VRAM | 32GB DDR4 3200MHz
**OS:** Windows 11
**Storage:** 300GB SSD (C:) + 4TB HDD (D:)
**Email:** Yahoo Mail + Gmail + SRU RockMail (Microsoft 365)
**Phone:** iPhone (iOS)
**Network:** Tailscale (already installed)
**School:** Slippery Rock University of Pennsylvania
**LMS:** D2L / RockOnline (sru.desire2learn.com)

---

## What This System Is

A local-first, zero-recurring-cost personal operating assistant that lives on your main PC.
It controls your computer, manages your files, reads all three of your email accounts, tracks
your SRU assignments and schedule, writes and runs code, and learns your preferences over
time. It is accessible from your PC natively, and from your laptop and iPhone through
Tailscale.

This is not a chatbot. It is not a dashboard. It is a personal operating system layer — a
capable agent that runs on your machine, costs nothing after setup, and gets more useful the
more you use it.

---

## Hardware Allocation Strategy

The RTX 3060 12GB is the most important resource to manage. The entire model strategy is
built around keeping the GPU completely free when you are gaming, rendering, or doing
anything else — and loading models on demand only when the assistant is actively used.

### VRAM Budget

| Model Role | Model | VRAM (Q4) | Behavior |
|---|---|---|---|
| Fast / Router | Phi-3 Mini 3.8B | ~2.3GB | Loads on first request of session |
| General / Conversation | Llama 3.1 8B | ~4.7GB | Loads on demand |
| Code Specialist | Qwen2.5-Coder 14B | ~8.3GB | Loads on demand |
| Vision / Screen | LLaVA 7B | ~4.2GB | Loads only when screen task triggered |

Only one model loads at a time. All models unload from VRAM after 3 minutes of idle.
When you are not actively using the assistant, the GPU is 100% free.
First response after idle: 5–10 second load delay. This is the correct tradeoff for a
personal machine where the GPU serves multiple purposes.

Your 32GB RAM handles all non-inference processes (FastAPI, SQLite, ChromaDB, MCP servers,
background jobs, the Tauri shell) with a combined footprint under 1.5GB.

### Storage Allocation

| What | Where | Reason |
|---|---|---|
| AI models (Ollama) | D:\ollama\models | Large files, no SSD speed required |
| System codebase | C:\assistant\ | Active files, fast access needed |
| SQLite database | C:\assistant\data\ | Frequent small reads and writes |
| ChromaDB vector store | C:\assistant\data\ | Frequent similarity queries |
| Docker images | D:\docker\ | Large, infrequently accessed |
| Logs | C:\assistant\logs\ | Moderate volume |
| Code sandbox workspace | C:\assistant\sandbox\ | Active during coding tasks |

SSD footprint for the system: approximately 3–5GB.
HDD footprint for models: approximately 25–40GB.

---

## System Layer Diagram

```
+------------------------------------------------------------------+
|                   LAYER 4 — Desktop Shell                        |
|                 Tauri v2 + React (Windows 11)                    |
|   Assistant Panel | Dashboard | Agent Monitor | Settings         |
+------------------------------------------------------------------+
|               LAYER 5 — Cross-Device Access                      |
|          React PWA served by FastAPI over Tailscale              |
|              iPhone (Safari) + Laptop (any browser)              |
+------------------------------------------------------------------+
|             LAYER 1 — Orchestration Backend                      |
|                    FastAPI + Python 3.11                         |
|  Intent Router | Tool Dispatch | Session Manager | Scheduler     |
+---------------------+--------------------------------------------+
|  LAYER 2            |  LAYER 3                                   |
|  Memory &           |  Computer Control                          |
|  Personalization    |  MCP Tool Servers                          |
|                     |                                            |
|  SQLite             |  Filesystem MCP    :8010                   |
|  ChromaDB           |  Terminal MCP      :8011                   |
|  APScheduler        |  Email MCP         :8012                   |
|                     |  Browser/D2L MCP   :8013                   |
|                     |  Screen MCP        :8014                   |
|                     |  Tasks MCP         :8015                   |
+---------------------+--------------------------------------------+
|                LAYER 0 — Local Inference                         |
|                       Ollama (Windows)                           |
|        Models on D: HDD | Inference on RTX 3060 GPU             |
|  Phi-3 Mini | Llama 3.1 8B | Qwen2.5-Coder 14B | LLaVA 7B       |
+------------------------------------------------------------------+
```

---

## Layer 0: Local Inference Engine

**Technology:** Ollama for Windows
**Model storage:** D:\ollama\models
**Inference:** RTX 3060 12GB via CUDA
**Idle policy:** All models unload after 3 minutes with no active requests
**API:** localhost:11434 (internal only, not exposed over Tailscale)

Ollama runs as a Windows background service. It starts automatically on boot, runs
silently, and is never visible to the user. The orchestration backend is the only process
that communicates with it.

### Model Roster

**Phi-3 Mini 3.8B — The Router**
Every single request hits this model first. It classifies intent in under 2 seconds,
determines which tier and model should handle the request, and returns a routing decision.
It never generates the final user-facing response — it only routes.
Use cases: intent classification, quick factual answers, weather, reminder queries,
simple schedule checks.

**Llama 3.1 8B — The Conversationalist**
The primary assistant model for daily use. Handles everything conversational, planning-
oriented, and non-code. Fits comfortably in 12GB VRAM at Q4.
Use cases: assistant conversation, email drafting and triage, schedule planning,
assignment discussion, D2L content explanation, general reasoning.

**Qwen2.5-Coder 14B — The Engineer**
The code specialist. At Q4 quantization this sits at approximately 8.3GB — fits cleanly
in 12GB with headroom. This is the highest-capability code model your GPU can run well.
Use cases: writing code, debugging, building applications, PowerShell scripting,
file editing, technical builds, automation scripts.

**LLaVA 7B — The Eyes**
Vision-capable model. Loaded only when a screen-aware task is triggered. Receives
screenshots and returns natural language analysis to the orchestration layer.
Use cases: "look at my screen", "what is on my screen", "help me with this"
when the context implies a visual reference.

---

## Layer 1: Orchestration Backend

**Technology:** FastAPI (Python 3.11)
**Process manager:** NSSM (Non-Sucking Service Manager) — registers FastAPI as a
Windows service that starts on boot and runs silently in the background
**Exposed port:** 8000 — accessible locally and over the Tailscale network
**Internal only:** All MCP servers on ports 8010–8015 bind to localhost only

This is the central brain of the entire system. Every request from the Tauri desktop
shell, the Tailscale PWA, and all background jobs enters this layer and is handled here.

### Intent Classification and Tier Routing

Every incoming request is classified by Phi-3 Mini into one of three tiers and one of
twelve intent categories before any other processing occurs.

**TIER: FAST** — Target response time: 3–8 seconds end to end
Simple lookups, status checks, reminder management, weather.
Routes to Phi-3 Mini. No heavy model loading required.
Examples: "what do I have due today", "set a reminder for 8pm", "what's the weather",
"do I have any emails from my professor"

**TIER: MEDIUM** — Target response time: 15–60 seconds
Multi-step tasks, email handling, file work, code explanation, D2L detail.
Routes to Llama 3.1 8B with relevant MCP tools active.
Examples: "draft a reply to this email", "check my D2L for the assignment description",
"find that file I was editing yesterday", "explain what this code does"

**TIER: HEAVY** — No fixed target. Progress shown live in Agent Monitor.
Complex builds, large automation, substantial coding work.
Routes to Qwen2.5-Coder 14B. Agent Monitor surface activates automatically.
Examples: "build me a web scraper", "write a full Python app that does X",
"refactor this entire codebase", "automate my weekly workflow"

### Intent to Model and Tool Routing Table

| Intent Category | Model | MCP Tools Activated |
|---|---|---|
| chat | Llama 3.1 8B | None |
| task_lookup | Phi-3 Mini | Tasks MCP |
| reminder_set | Phi-3 Mini | Tasks MCP |
| schedule | Phi-3 Mini | Tasks MCP |
| weather | Phi-3 Mini | Browser MCP |
| email | Llama 3.1 8B | Email MCP |
| d2l | Llama 3.1 8B | Browser/D2L MCP |
| file_action | Llama 3.1 8B | Filesystem MCP |
| terminal | Qwen2.5-Coder 14B | Terminal MCP |
| code | Qwen2.5-Coder 14B | Filesystem MCP + Terminal MCP |
| screen | LLaVA 7B | Screen MCP |
| search | Llama 3.1 8B | Browser MCP |

### Memory Injection Pipeline

Before every model call the orchestration layer runs this sequence:
1. Embed the request text using sentence-transformers all-MiniLM-L6-v2 (CPU only)
2. Query ChromaDB for the 5 most semantically similar memory chunks across all collections
3. Pull any active tasks, reminders, and assignments from SQLite relevant to the request
4. Query SQLite preferences for any stored user preferences relevant to the request
5. Assemble a structured context block and inject it into the system prompt

The model always has relevant personal context without the user ever needing to re-explain
anything about themselves, their projects, or their preferences.

### System Prompt Template

```
You are a personal operating assistant running locally on the user's PC.
You are capable, direct, and genuinely useful. You do not over-explain or pad your
responses. You act when asked to act. You ask for clarification only when genuinely
necessary — not as a habit.

Current date and time: {datetime}
Day of week: {weekday}

Memory context (most relevant to this request):
{memory_context}

Active reminders and tasks:
{active_tasks}

Upcoming assignment deadlines:
{upcoming_assignments}

User preferences:
{preferences}
```

### Background Jobs (APScheduler embedded in FastAPI process)

**Reminder check** — runs every 60 seconds
Queries SQLite tasks table for items where due_datetime <= now AND status = pending.
For each match: updates status to notified, fires a Windows toast notification via
plyer, emits a WebSocket event to update the dashboard in real time.

**Yahoo mail sync** — runs every 15 minutes
Connects via IMAP with stored App Password. Fetches last 50 message headers.
Stores sender, subject, received timestamp, read status, snippet in SQLite.
Does not download full message bodies — metadata only for fast dashboard display.

**Gmail sync** — runs every 15 minutes
Same as Yahoo but uses Gmail IMAP with stored App Password.

**SRU RockMail sync** — runs every 15 minutes
Uses Microsoft Graph API with stored OAuth2 token. Fetches inbox metadata.
If token is within 10 minutes of expiry, triggers silent refresh automatically.
If refresh fails (password expired after 90-day SRU policy), emits a re-auth
notification to the dashboard rather than failing silently.

**D2L assignment sync** — runs every 4 hours
Launches headless Playwright browser. Authenticates to sru.desire2learn.com using
stored SRU credentials with MFA token. Navigates course list, scrapes all assignments
with due dates, descriptions, course names, and D2L IDs. Upserts into SQLite
assignments table. Emits dashboard WebSocket event if new assignments are found.

**Memory extraction** — triggered 2 minutes after a session goes idle
Sends completed conversation to Llama 3.1 8B with an extraction prompt.
Extracts new preferences, habits, project updates, explicit facts.
Deduplicates against existing ChromaDB entries.
Writes novel observations to ChromaDB. Writes explicit facts to SQLite preferences.
Marks session as memory_extracted in conversation_index table.

### FastAPI Endpoint Surface

```
POST   /chat                  Primary conversation endpoint (streaming)
POST   /command               Direct tool execution
WS     /stream                WebSocket for Tauri shell real-time communication
GET    /tasks                 All tasks with optional filters
POST   /tasks                 Create task or reminder
PUT    /tasks/{id}            Update task
DELETE /tasks/{id}            Delete task
GET    /tasks/today           Tasks due today
GET    /tasks/upcoming        Tasks due in next 7 days
GET    /assignments           All assignments sorted by due date
GET    /assignments/overdue   Overdue assignments
GET    /email/inbox           Unified inbox summary across all three accounts
GET    /email/inbox/{account} Single account inbox (yahoo | gmail | sru)
GET    /email/message/{id}    Full message body (fetches live if not cached)
POST   /email/send            Send email from specified account
GET    /status                Active job status for Agent Monitor
GET    /memory/recent         Recent memory extractions
DELETE /memory/{id}           Delete a specific memory entry
GET    /health                Full system health check
GET    /                      Serves PWA (React app for Tailscale access)
```

---

## Layer 2: Memory and Personalization

**No Postgres. No external database server of any kind.**
SQLite is a file. ChromaDB is a folder. Both run inside the application process with
zero server overhead, zero maintenance, and zero configuration. Both are perfectly
appropriate for a single-user personal assistant and outperform server-based alternatives
on single-user read/write workloads.

### SQLite — Structured Storage
**Location:** C:\assistant\data\assistant.db

**preferences** — Explicit and inferred user settings
(key, value, category, created_at, updated_at)

**tasks** — Reminders and to-do items
(id, title, body, due_datetime, recurrence, status, priority, source, created_at)

**calendar_events** — Schedule items
(id, title, start_datetime, end_datetime, location, notes, source)

**assignments** — D2L coursework from RockOnline
(id, course, title, due_datetime, description, status, url, d2l_id, created_at)

**emails** — Unified metadata index across all three accounts
(id, uid, account, sender, subject, received_at, read, flagged, snippet, fetched_at)

**conversation_index** — Session metadata
(id, session_id, started_at, ended_at, summary, topics, memory_extracted)

**habit_observations** — Usage pattern observations
(id, pattern_type, description, observed_at, confidence)

**projects** — Active projects the assistant knows about
(id, name, description, path, language, last_active, created_at)

**command_log** — Full audit trail of all terminal/tool operations
(id, command_type, command, output, exit_code, executed_at, session_id)

**credentials** — All auth tokens and passwords, stored encrypted
(id, service, encrypted_data, token_expiry, created_at)
Services stored: yahoo_imap, yahoo_smtp, gmail_imap, gmail_smtp,
sru_oauth_access, sru_oauth_refresh, d2l_session

### ChromaDB — Vector / Semantic Memory
**Location:** C:\assistant\data\chromadb\
**Embedding model:** all-MiniLM-L6-v2 via sentence-transformers (CPU, ~80MB RAM)

**conversation_memory**
Summaries of past sessions. The assistant remembers what you worked on, what you
discussed, what you decided, and what was left unfinished.

**user_preferences**
Learned behavior embeddings extracted from interaction patterns.
Examples stored here: "prefers concise responses to simple questions",
"likes inline comments in code", "tends to work late at night",
"prefers to be shown options rather than given a single answer"

**project_context**
Per-project observations, notes, and summaries. Automatically retrieved when the
context of a request matches a known project. Means the assistant picks up where
it left off on a project without being re-briefed.

**knowledge_base**
Permanent explicit facts the user has stated directly.
Examples: "Remember my D2L username is X", "Remember I prefer Python over JavaScript",
"Remember my roommate's name is Y". These never expire and are never auto-deleted.

### The Learning Loop (Runs automatically after every session)

1. APScheduler triggers 2 minutes after conversation goes idle
2. Llama 3.1 8B receives the full conversation with this extraction prompt:
   "Extract any user preferences, habits, project updates, or explicit facts from
   this conversation. Return as a JSON array where each item has: type
   (preference | habit | project | fact), content (string), confidence (0.0–1.0)"
3. JSON response is parsed. Each item is embedded and compared to existing ChromaDB
   entries using cosine similarity
4. Items with similarity below 0.85 threshold are treated as novel and stored
5. Items above threshold are considered duplicates and discarded
6. Facts with confidence > 0.8 are also written to SQLite preferences table
7. Session is marked memory_extracted = 1 in conversation_index

Result: the assistant builds a personalized model of the user over time. Preferences,
habits, ongoing work, and explicit knowledge accumulate silently and are injected
into every future session automatically.

---

## Layer 3: Computer Control

**Architecture:** MCP (Model Context Protocol) servers
**Safety policy:**
- READ operations: unrestricted, no confirmation needed
- WRITE operations: allowed, logged to SQLite command_log
- DESTRUCTIVE operations: blocked until user confirms via UI confirmation gate

Each MCP server is a standalone Python FastAPI microservice running on its own localhost
port. The orchestration backend dispatches tool calls to them over HTTP. Each server is
independently restartable, testable, and replaceable without touching any other component.

Adding a new capability = writing a new MCP server and registering it. Nothing else changes.

All MCP servers are registered as Windows services via NSSM and start automatically on boot.

### Filesystem MCP — localhost:8010

READ (unrestricted):
- List directory contents with metadata (size, modified date, type)
- Read file contents (text files; preview truncated for files over 100KB)
- Search by filename pattern across any path
- Search by content string across text files
- Get file metadata

WRITE (logged):
- Write or overwrite file
- Create new file
- Create directory
- Move file or directory
- Copy file or directory

DESTRUCTIVE (confirmation gate):
- Delete file
- Delete directory recursively

Operates on both C: and D: drives. All paths validated to prevent directory traversal.
Windows path conventions (backslash, drive letters) throughout.

### Terminal MCP — localhost:8011

EXECUTE (logged, destructive patterns gated):
- Run PowerShell command with working directory
- Run CMD command with working directory
- Run Python script file
- Run batch file
- Returns: stdout, stderr, exit code, execution time

All commands are written to SQLite command_log before execution.
Destructive pattern detection flags commands matching: Remove-Item, del, rmdir, format,
reg delete, net user, Stop-Service, Uninstall, and similar system-altering patterns.
Flagged commands return a confirmation_required response. The orchestration layer holds
the pending command and presents it in the UI confirmation gate before re-issuing.

Execution uses subprocess with configurable timeout (60s standard, 3600s for heavy builds).

### Email MCP — localhost:8012

Manages all three email accounts. Each account has its own connection handler.
All credentials retrieved from encrypted SQLite credentials table.

**Yahoo Mail**
Protocol: IMAP (imap.mail.yahoo.com:993, SSL) + SMTP (smtp.mail.yahoo.com:587, STARTTLS)
Auth: App Password (standard password field, no OAuth required for Yahoo)
Operations: list inbox, read message body, send email, reply, forward, move, flag,
delete, search by sender/subject/date

**Gmail**
Protocol: IMAP (imap.gmail.com:993, SSL) + SMTP (smtp.gmail.com:587, STARTTLS)
Auth: App Password (generated in Google Account > Security > App Passwords)
Operations: same full set as Yahoo

**SRU RockMail (Microsoft 365)**
Protocol: Microsoft Graph API (REST, not IMAP)
Auth: OAuth2 with automatic token refresh
Initial auth: one-time browser popup flow generates access token + refresh token,
both stored encrypted in SQLite credentials table
Token refresh: silent background refresh when access token is within 10 minutes of expiry
Token expiry recovery: if refresh token fails (SRU 90-day password policy), the system
emits a re-authentication notification to the dashboard rather than failing silently.
The user clicks Re-authenticate in the UI, completes the browser OAuth flow once,
and normal operation resumes.
Operations: list inbox, read message, send email, reply, forward, move, flag, delete,
search, read calendar events, create calendar events

**Unified inbox endpoint:**
The Email MCP exposes a unified inbox that merges recent messages across all three
accounts, sorted by received_at descending, with an account label on each message.
The assistant can filter by account when asked ("check my school email" routes to SRU only).

### Browser / D2L MCP — localhost:8013

**D2L RockOnline Integration**
URL: sru.desire2learn.com
Auth: Playwright headless Chromium, logs in with SRU credentials + MFA
Session is preserved across requests (does not re-login on every call)
Session expiry is handled gracefully with automatic re-login

Operations:
- Get full course list
- Get all assignments across all courses with due dates
- Get individual assignment details (full description, submission requirements, rubric)
- Get grades per course
- Get course materials and announcements
- Navigate to specific course content

**General Web Operations**
- Fetch and clean any URL's text content
- DuckDuckGo web search, return top results with titles and snippets
- Extract structured data from web pages

### Screen MCP — localhost:8014

Operations:
- Capture full screenshot of primary monitor
- Capture specific monitor by index (multi-monitor aware)
- Capture specific application window by title
- Pass screenshot to LLaVA 7B via Ollama API
- Return vision model's natural language analysis

Triggered exclusively by explicit user request. Never runs passively or automatically.
No continuous screen monitoring of any kind.

### Tasks / Calendar MCP — localhost:8015

Operations:
- Get all tasks with optional filters (status, priority, due_before, due_after)
- Get today's tasks
- Get upcoming tasks (next N days)
- Create task or reminder with title, body, due_datetime, priority, recurrence
- Update task (status, due date, priority, content)
- Delete task
- Get all calendar events
- Create calendar event
- Get assignments from SQLite (D2L-synced data)
- Get overdue assignments
- Query "what do I have this week" — returns merged view of tasks, events, assignments

### Code Execution Sandbox — Docker + WSL2

When the assistant writes and runs code during a coding task, execution happens inside
a Docker container. The host OS is never directly touched by assistant-generated code.

Container configuration:
- Base image: Python 3.11 slim with Node.js, git, common build tools pre-installed
- Mounted path: C:\assistant\sandbox (the only host directory accessible)
- Memory limit: 4GB
- CPU limit: 2 cores
- Network: bridge (internet access for pip/npm installs during builds)
- No access to: C:\Users, C:\Windows, D:, or any system path

Workflow for a coding task:
1. Assistant writes code to C:\assistant\sandbox via Filesystem MCP
2. Terminal MCP runs the code inside Docker container
3. stdout/stderr returned to the model for evaluation
4. Model iterates — edits code, runs again — until the result is correct
5. When complete and the user wants it deployed, assistant moves files from
   sandbox to the target path with explicit user approval

---

## Layer 4: Desktop Shell

**Technology:** Tauri v2 (Rust) + React + TypeScript
**Distribution:** Native Windows .exe — not a browser tab, not Electron
**WebView2:** Ships with Windows 11, no install required
**System tray:** Assistant lives in the tray at all times, accessible with one click
**Startup:** Optionally starts with Windows (configurable in Settings)

### UI Surface: Assistant Panel

The primary interaction surface. The face of the assistant.

Layout:
- Message history fills the main area with smooth scroll-to-bottom on new messages
- User messages: right-aligned, accent-colored background bubble
- Assistant messages: left-aligned, glass panel background
- Streaming display: text renders character by character as the model generates,
  never dumped all at once
- Code blocks: syntax highlighted with language label, one-click copy button,
  line numbers for blocks over 10 lines
- File path references: rendered as clickable chips — clicking opens the file or
  folder in Windows Explorer
- Model tier badge: subtle indicator in the top-right of each assistant message
  showing which model handled it ("FAST · phi3", "CODE · qwen2.5", etc.)
- Input area: full-width, auto-expanding text field with send button
- Voice button: placeholder for Phase 8, non-functional but present in the UI
- Active generation state: soft blue breathing animation pulses on the input
  border while the model is generating a response
- Confirmation gate: when a DESTRUCTIVE action is pending approval, a dismissible
  banner appears above the input showing the action description, the exact command
  or file path involved, and two buttons — Approve (green) and Deny (red).
  The assistant pauses and waits. Nothing executes until a button is pressed.

### UI Surface: Dashboard

The ambient presence surface. Always shows the user their world at a glance.

Left column — Time and status:
- Current time displayed large and clean
- Today's date and day of week
- Weather widget: current conditions and today's high/low, fetched on load

Center column — Today and upcoming:
- TODAY section: all tasks and assignments due today, sorted chronologically
  Each item shows: title, course name (for assignments), due time, status
  Overdue items are highlighted amber
- UPCOMING section: next 7 days grouped by day label
- QUICK ADD: inline reminder creation without opening settings

Right column — Communications and projects:
- Unified email summary: unread count per account with account labels
  (Yahoo: 3 unread | Gmail: 1 unread | RockMail: 7 unread)
  Most recent 3 messages shown with sender and subject
- Active projects: list with path and last-active timestamp
- Quick action buttons: Check D2L, Check All Email, New Reminder

Auto-refresh behavior:
- Tasks and reminders: every 60 seconds
- Email counts: every 15 minutes
- D2L assignments: reflects most recent sync (timestamp shown)
- Items that change state pulse softly to signal the update

### UI Surface: Agent Monitor

The transparency surface. Activates automatically during MEDIUM and HEAVY tasks.
This is what makes the assistant feel like it is working rather than frozen.

Display:
- Task title derived from the original request
- Elapsed time counter (live, ticking)
- Step feed: a scrolling log of recent steps emitted by the backend in real time
  Examples: "Classifying intent...", "Loading Qwen2.5-Coder...", "Calling Filesystem
  MCP...", "Reading file C:\project\main.py...", "Writing code...", "Running in
  sandbox...", "Fixing error on line 42...", "Build successful"
- Current model indicator
- Live token preview: last 2 lines of what the model is currently generating
- Cancel button: sends cancellation signal to the backend, cleanly stops the task
- When idle: shows the last completed task with a summary and timestamp

Every MCP call, model switch, file read, command execution, and generation milestone
emits a step event over the WebSocket. The Agent Monitor receives and displays them live.

### UI Surface: Settings

Tabbed configuration interface.

Models tab:
- Table of all intent categories and their currently assigned model
- Each row has a dropdown to reassign the model
- Save writes to SQLite preferences table
- Changes take effect on the next request (no restart required)

Memory tab:
- Scrollable list of recent ChromaDB memory entries with timestamp and category
- Delete button per entry
- Clear all memory button (requires typed confirmation: "DELETE ALL MEMORY")
- Knowledge base section: add and remove permanent explicit memories
- View raw SQLite preferences

Accounts tab:
- Yahoo Mail: email address + App Password fields. Test Connection button.
- Gmail: email address + App Password fields. Test Connection button.
  Link to Google App Password generation page.
- SRU RockMail: shows connected/disconnected status and token expiry date.
  Authorize button triggers OAuth2 browser flow. Re-authorize button for 90-day resets.
- D2L: SRU username + password. Test Connection button. Last sync timestamp.
  Manual Sync Now button.

System tab:
- Model idle timeout slider (1–15 minutes, default 3)
- GPU memory display (shows current VRAM usage)
- Start with Windows toggle
- Minimize to tray on close toggle
- Sandbox path configuration
- Log viewer (last 100 lines of backend log)
- Export settings (JSON backup of all SQLite preferences)

### Visual Design Language

Color palette:
- Background primary: #0d0d0f (near black, not pure black)
- Background secondary: #141416
- Panel background: rgba(255, 255, 255, 0.04) with 1px border rgba(255,255,255,0.08)
- Panel hover: rgba(255, 255, 255, 0.07)
- Accent: #63b3ed (electric blue) used sparingly — active states, key highlights only
- Accent glow: rgba(99, 179, 237, 0.12) for subtle glow effects
- Text primary: #f0f0f0
- Text secondary: #a0a0a0
- Text muted: #505050
- Status processing: #63b3ed
- Status complete: #68d391
- Status warning: #f6ad55
- Status error: #fc8181

Typography:
- UI font: Inter (loaded locally)
- Code font: JetBrains Mono (loaded locally)
- Clear hierarchy: large for headers, comfortable for body, smaller for metadata

Motion:
- All panel transitions: 250ms ease — crossfade between surfaces
- Message appearance: 150ms slide-up fade-in
- Generating state: 2s infinite breathing pulse on input border (opacity 0.4 → 1.0)
- Dashboard item update: 300ms highlight pulse on changed items
- Nothing snaps. Everything transitions.

Glassmorphism:
- Used structurally on panels, not as decoration
- Panels have backdrop-filter blur (8px) and a subtle border
- Not overused — dark background with bright content, not frosted glass everywhere

Overall feel: a product someone designed with intention. Not a developer utility panel.
Not a generic React dashboard. Something you would be comfortable showing other people.

---

## Layer 5: Cross-Device Access

**Technology:** React PWA + FastAPI static serving + Tailscale

The Tauri application is the full desktop experience. Phone and laptop access comes from
a Progressive Web App served by the FastAPI backend, reachable over Tailscale.

### How It Works

1. FastAPI serves the built React PWA as static files at the root route /
2. Tailscale assigns your main PC a stable internal IP (e.g., 100.x.x.x)
3. On iPhone: open Safari → navigate to http://100.x.x.x:8000 → Share → Add to Home Screen
4. The assistant icon appears on your iPhone home screen
5. Opens full-screen like a native app (no browser chrome visible)
6. Same WebSocket connection and same orchestration backend as the desktop

### PWA Capabilities

Included:
- Full conversation interface with streaming display
- Dashboard: today's tasks, assignments, email summary
- Task and reminder creation and management
- D2L assignment list with due dates
- Email inbox across all three accounts with read and reply
- Voice input via iOS Safari Web Speech API (built-in, no install)
- Push notifications for reminders via Web Push API

Not included (desktop only):
- Computer control (filesystem, terminal, screen) — requires the host PC
- Agent Monitor — heavy tasks initiated from mobile route to the desktop monitor
- Full settings panel — basic preferences accessible, advanced settings desktop only

### Tailscale Configuration

Only one port needs to be reachable over Tailscale: port 8000 (FastAPI).
All MCP servers are localhost-only and never exposed.
Ollama is localhost-only and never exposed.
Tailscale handles the encrypted tunnel — no port forwarding, no dynamic DNS required.

---

## Layer 6: Voice (Phase 8 — Future)

**Speech to Text:** faster-whisper
Local implementation of OpenAI's Whisper model. Runs CUDA-accelerated on your 3060.
Transcribes speech to text with high accuracy at near-real-time speed on your hardware.

**Text to Speech:** Kokoro
The highest quality open-source local TTS model currently available.
Produces natural, non-robotic speech. Runs efficiently on CPU, leaving GPU free for
the active language model.

**Integration:**
- Push-to-talk button added to the Tauri Assistant Panel
- Voice input is transcribed by faster-whisper and submitted identically to typed input
- The assistant's text response is passed to Kokoro and played through system audio
- No special code paths, no special models — voice is just another I/O modality
- Wake word detection is a Phase 9 consideration, not included in Phase 8

**Cost:** Zero. Both run entirely locally on your hardware.

---

## Email Account Configuration Reference

### Yahoo Mail
- IMAP: imap.mail.yahoo.com, port 993, SSL/TLS
- SMTP: smtp.mail.yahoo.com, port 587, STARTTLS
- Auth: App Password (generate at myaccount.yahoo.com > Security > App Passwords)
- Standard IMAP — no OAuth required

### Gmail
- IMAP: imap.gmail.com, port 993, SSL/TLS
- SMTP: smtp.gmail.com, port 587, STARTTLS
- Auth: App Password (generate at myaccount.google.com > Security > 2-Step > App Passwords)
- Standard IMAP — no OAuth required once App Password is set

### SRU RockMail (Microsoft 365)
- Protocol: Microsoft Graph API (not IMAP)
- Endpoint: https://graph.microsoft.com/v1.0/me/messages
- Auth: OAuth2 Authorization Code Flow
  - Client registered in Azure AD (public client, no secret needed)
  - Scopes: Mail.Read, Mail.Send, Mail.ReadWrite, Calendars.Read, Calendars.ReadWrite
  - Initial auth: browser popup → user signs in with SRU credentials + MFA
  - Result: access_token (1 hour) + refresh_token (90 days or until password change)
  - Both tokens stored encrypted in SQLite credentials table
  - Access token silently refreshed when within 10 minutes of expiry
  - If refresh fails (SRU 90-day password reset): dashboard notification prompts re-auth
  - Re-auth is a one-click browser flow, takes under 60 seconds

### SRU Password Expiry Handling
SRU passwords expire every 90 days by policy. The system handles this gracefully:
- Token refresh failure is caught and classified as an auth error (not a crash)
- Dashboard shows: "SRU email needs re-authorization — click to reconnect"
- All other functionality continues normally while SRU email is disconnected
- One click re-authorizes via the browser OAuth flow
- No data is lost during the disconnection period

---

## Full Stack Reference

| Component | Technology | Location |
|---|---|---|
| Inference runtime | Ollama for Windows | D:\ollama |
| Fast/router model | Phi-3 Mini 3.8B Q4 | D:\ollama\models |
| General model | Llama 3.1 8B Q4 | D:\ollama\models |
| Code model | Qwen2.5-Coder 14B Q4 | D:\ollama\models |
| Vision model | LLaVA 7B Q4 | D:\ollama\models |
| Orchestration backend | FastAPI Python 3.11 | C:\assistant\backend |
| Background scheduler | APScheduler (embedded) | C:\assistant\backend |
| Windows service runner | NSSM | System |
| Structured storage | SQLite | C:\assistant\data |
| Vector memory | ChromaDB | C:\assistant\data |
| Embedding model | all-MiniLM-L6-v2 | C:\assistant\backend |
| Filesystem MCP | FastAPI Python | C:\assistant\mcp\filesystem |
| Terminal MCP | FastAPI Python | C:\assistant\mcp\terminal |
| Email MCP | FastAPI Python | C:\assistant\mcp\email |
| Browser / D2L MCP | FastAPI Python + Playwright | C:\assistant\mcp\browser |
| Screen MCP | FastAPI Python + Pillow | C:\assistant\mcp\screen |
| Tasks / Calendar MCP | FastAPI Python | C:\assistant\mcp\tasks |
| Code execution sandbox | Docker + WSL2 | C:\assistant\sandbox |
| Desktop shell | Tauri v2 + React + TypeScript | C:\assistant\shell |
| Mobile / laptop PWA | React + Tailwind | C:\assistant\pwa |
| Device network | Tailscale | Already installed |
| Voice STT (Phase 8) | faster-whisper | C:\assistant\voice |
| Voice TTS (Phase 8) | Kokoro | C:\assistant\voice |

---

## Project Directory Structure

```
C:\assistant\
├── backend\
│   ├── main.py              FastAPI app entry point
│   ├── config.py            All configuration constants
│   ├── database.py          SQLite schema and init
│   ├── memory.py            ChromaDB + SQLite memory interface
│   ├── router.py            Intent classification logic
│   ├── scheduler.py         APScheduler background jobs
│   ├── auth.py              Credential encryption and retrieval
│   ├── models.py            Pydantic request/response schemas
│   └── venv\                Python virtual environment
│
├── mcp\
│   ├── filesystem\          Filesystem MCP server (:8010)
│   ├── terminal\            Terminal MCP server (:8011)
│   ├── email\               Email MCP server (:8012)
│   ├── browser\             Browser + D2L MCP server (:8013)
│   ├── screen\              Screen capture + vision MCP (:8014)
│   └── tasks\               Tasks + calendar MCP server (:8015)
│
├── shell\                   Tauri v2 desktop application
│   ├── src-tauri\           Rust backend
│   │   ├── src\main.rs      Tauri entry point
│   │   └── tauri.conf.json  App configuration
│   └── src\                 React frontend
│       ├── panels\
│       │   ├── AssistantPanel.tsx
│       │   ├── Dashboard.tsx
│       │   ├── AgentMonitor.tsx
│       │   └── Settings.tsx
│       ├── components\      Reusable UI components
│       ├── hooks\           Custom React hooks
│       ├── store\           Zustand application state
│       └── styles\          Design tokens and global CSS
│
├── pwa\                     Progressive web app
│   └── src\
│       ├── views\           Chat, Tasks, Email, Settings
│       └── components\      Mobile-optimized components
│
├── data\                    Never committed to version control
│   ├── assistant.db         SQLite database
│   └── chromadb\            ChromaDB vector store
│
├── sandbox\                 Docker code execution workspace
│   └── Dockerfile
│
├── voice\                   Phase 8 voice pipeline
├── logs\                    Application logs
└── docs\                    Architecture and build documents
```

---

## Build Phases

### Phase 1 — Inference Foundation
Install Ollama for Windows. Configure model storage to D:\ollama\models. Set CUDA
environment variables. Pull all four models and verify each loads and responds. Confirm
CUDA acceleration is active (watch GPU usage in Task Manager during inference). Confirm
models unload from VRAM after the idle timeout. This phase must be fully verified before
any other phase begins.

### Phase 2 — Orchestration Backend
Build FastAPI backend. Implement intent classifier using Phi-3 Mini. Implement three-tier
routing with the full intent-to-model routing table. Connect to Ollama API. Implement
streaming responses via WebSocket. Add session management. Register as Windows service
via NSSM. Test that model switching works correctly across all intent categories.

### Phase 3 — Memory Layer
Implement complete SQLite schema. Initialize all four ChromaDB collections. Implement
memory injection pipeline (embed → query → format → inject). Implement learning loop as
APScheduler background job. Test that preferences persist correctly and are retrieved
accurately across multiple sessions.

### Phase 4 — Computer Control (MCP Servers)
Build and test MCP servers in this order:
1. Filesystem MCP — read, write, search, confirmation gate for deletes
2. Terminal MCP — PowerShell execution, logging, destructive command detection
3. Tasks MCP — full CRUD for tasks, reminders, assignments
4. Email MCP — all three accounts with correct auth for each
5. Browser/D2L MCP — D2L scraping with Playwright, general web fetch
6. Screen MCP — screenshot capture and LLaVA vision analysis

Test each server independently before wiring into the orchestration layer.
Implement tool dispatch in the orchestration backend. Implement the confirmation gate
(WebSocket event to UI, hold pending command, execute on approval).

### Phase 5 — Desktop Shell
Initialize Tauri v2 + React project. Build all four UI surfaces: Assistant Panel,
Dashboard, Agent Monitor, Settings. Implement the full visual design language including
all color tokens, typography, transitions, and animations. Connect to FastAPI via
WebSocket for streaming. Implement the confirmation gate UI component. Configure system
tray integration with right-click context menu. Configure startup behavior.

### Phase 6 — Productivity and Integrations
Implement all three APScheduler email sync jobs. Implement D2L sync job. Configure
Yahoo SMTP, Gmail SMTP, and SRU Graph API for send operations. Build full reminder
notification system using plyer for Windows toast notifications. Implement SRU OAuth2
flow including token storage, auto-refresh, and expiry recovery UI. Test all workflows
end to end: reminder fires notification, D2L assignments appear in dashboard, email
sync populates inbox surface.

### Phase 7 — Remote Access
Build React PWA with all mobile surfaces. Configure FastAPI to serve built PWA at root
route. Test access via Tailscale from a second device. Optimize all mobile layouts for
iPhone screen sizes. Test Add to Home Screen installation on iPhone. Implement Web Push
notifications for reminders on mobile.

### Phase 8 — Voice
Install faster-whisper with CUDA support. Install Kokoro TTS. Build voice pipeline:
microphone capture → faster-whisper transcription → orchestration backend → Kokoro
playback. Add push-to-talk button to the Tauri Assistant Panel. Test end-to-end
latency and tune for acceptable response time.

---

## Security Model

- All credentials (Yahoo App Password, Gmail App Password, SRU OAuth tokens, D2L
  password) are stored encrypted using Fernet symmetric encryption
- Encryption key is derived from machine-specific entropy and stored in the Windows
  Credential Store — never in a file, never in an environment variable
- MCP servers bind to localhost only — never reachable from outside the machine
- Only FastAPI port 8000 is accessible over Tailscale — all other ports are internal
- All file operations and terminal commands are logged with full audit trail in SQLite
- Destructive operations are blocked until explicit UI confirmation
- The code sandbox has no access to sensitive host paths
- No data ever leaves the Tailscale network

---

## What This System Feels Like When Complete

You open your PC. The assistant is in the system tray — it has been running since
Windows started. You click it or press your hotkey. It already knows you have an
assignment due Thursday. It knows what you were coding last night. It knows you prefer
concise answers for quick questions.

You ask what you have due this week. It pulls from D2L and your reminders and gives you
a clean list in under 5 seconds.

You ask it to help with the Thursday assignment. It fetches the full description from
D2L, reads it, understands what is being asked, and helps you work through it or drafts
a solution with you.

You ask it to look at your screen. It takes a screenshot, runs it through the vision
model, and tells you exactly what it sees or helps you with what is visible.

You ask it to write a Python script to rename 500 files according to a pattern. It
writes the script in the sandbox, runs it, catches the error on line 12, fixes it, runs
it again, confirms it works on a test set, and delivers it to you ready to deploy.

You pick up your iPhone. You open the assistant from the home screen over Tailscale.
You ask what is due tomorrow. It answers in seconds from the same data as your PC.

None of this costs anything to run. It lives entirely on your machine. Every session
it learns a little more about how you work, what you like, and what matters to you.
