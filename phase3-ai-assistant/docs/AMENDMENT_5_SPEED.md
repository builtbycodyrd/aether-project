# Amendment 5 — Response Speed Improvements
# Read alongside all previous amendments.
# This amendment takes precedence on anything related to
# streaming, latency, routing speed, or loading indicators.

---

## Overview

1. Immediate typing indicator — UI shows Aether is thinking within 100ms
   of sending, before any API response arrives.

2. Fast-tier routing verification — Ensure Haiku is actually handling
   simple requests. Add keyword pre-classification before the Haiku
   router call to skip the API round trip entirely for obvious intents.

3. Streaming optimization — Reduce time-to-first-token by flushing
   the WebSocket buffer immediately instead of batching.

4. ChromaDB query timeout — Cap memory retrieval at 500ms so a slow
   ChromaDB query never blocks the response.

5. Parallel context assembly — Run memory query, task lookup, and
   preference fetch simultaneously instead of sequentially.

---

## Part 1: Immediate Typing Indicator (Frontend)

### Update AssistantPanel.tsx

When the user sends a message, immediately add a placeholder assistant
message to the message list BEFORE the API call returns anything.
Do not wait for the first WebSocket token.

```typescript
const handleSend = async (text: string) => {
  if (!text.trim()) return;

  // Add user message immediately
  addMessage({ role: "user", content: text, timestamp: Date.now() });
  setInputValue("");
  setIsGenerating(true);

  // Add placeholder assistant message IMMEDIATELY (within one render cycle)
  // This shows the typing indicator before any network response
  appendToMessages({
    role: "assistant",
    content: "",           // empty — will fill as tokens arrive
    isPlaceholder: true,   // flag to show typing animation
    timestamp: Date.now()
  });

  // Then send to backend
  try {
    await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId })
    });
  } catch (err) {
    console.error("Send failed:", err);
    setIsGenerating(false);
  }
};
```

### Typing Indicator Component

When a message has isPlaceholder: true AND content is empty, show a
pulsing dots animation instead of blank space:

```typescript
// In the message render function:
if (message.isPlaceholder && !message.content) {
  return (
    <div className="assistant-message typing-indicator">
      <span className="dot" style={{ animationDelay: "0ms" }} />
      <span className="dot" style={{ animationDelay: "150ms" }} />
      <span className="dot" style={{ animationDelay: "300ms" }} />
    </div>
  );
}
```

```css
/* Add to styles */
.typing-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 16px;
  min-height: 52px;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  opacity: 0.6;
  animation: typing-pulse 1.2s ease-in-out infinite;
}

@keyframes typing-pulse {
  0%, 100% { opacity: 0.3; transform: scale(0.8); }
  50%       { opacity: 1.0; transform: scale(1.1); }
}
```

Once the first token arrives via WebSocket, replace the placeholder content
with the streaming text. The dots disappear and text starts flowing.

---

## Part 2: Keyword Pre-Classification (Backend)

Before calling Haiku for intent classification, run a fast local keyword
check. This eliminates the API round trip for obvious intents and makes
simple requests feel nearly instant.

### Update backend/router.py

Add a keyword_classify function above classify_intent_api:

```python
import re

# Keyword patterns for fast pre-classification
# These are checked before making any API call
KEYWORD_PATTERNS = {
    "reminder_set": [
        r"\bremind\b", r"\breminder\b", r"\bset an alarm\b",
        r"\bdon't forget\b", r"\balert me\b"
    ],
    "task_lookup": [
        r"\bwhat do i have\b", r"\bmy tasks\b", r"\bmy reminders\b",
        r"\bwhat's due\b", r"\bdue today\b", r"\bdue tomorrow\b",
        r"\bwhat's on my\b"
    ],
    "schedule": [
        r"\bmy schedule\b", r"\bwhat's today\b", r"\bwhat do i have today\b",
        r"\bmy calendar\b", r"\bthis week\b", r"\bupcoming\b"
    ],
    "weather": [
        r"\bweather\b", r"\btemperature\b", r"\brain\b", r"\bsnow\b",
        r"\bforecast\b", r"\bhow cold\b", r"\bhow hot\b", r"\bwindy\b"
    ],
    "screen": [
        r"\blook at my screen\b", r"\bwhat's on my screen\b",
        r"\bsee my screen\b", r"\bwhat do you see\b", r"\bmy screen\b"
    ],
    "d2l": [
        r"\bd2l\b", r"\brockonline\b", r"\bmy assignments\b",
        r"\bcourse\b.*\bassignment\b", r"\bclass\b.*\bdue\b",
        r"\bhomework\b", r"\bprofessor\b"
    ],
}

def keyword_classify(message: str) -> dict | None:
    """
    Fast local keyword pre-classification.
    Returns routing dict if confident, None if should fall through to API.
    Only classifies high-confidence obvious cases.
    """
    msg_lower = message.lower()

    for intent, patterns in KEYWORD_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, msg_lower):
                return {
                    "intent": intent,
                    "tier": TIER_MAP[intent],
                    "model": MODEL_MAP[intent],
                    "tools": MCP_MAP[intent],
                    "classified_by": "keyword"
                }

    return None  # Fall through to Haiku API classification


async def classify_intent(message: str) -> dict:
    """
    Two-stage classification:
    1. Fast local keyword check (no API call)
    2. Haiku API classification (if keyword check inconclusive)
    """
    # Stage 1: keyword pre-check
    keyword_result = keyword_classify(message)
    if keyword_result:
        return keyword_result

    # Stage 2: Haiku API (for ambiguous requests)
    return await classify_intent_api(message)
```

This means reminder_set, task_lookup, schedule, weather, screen, and d2l
requests never wait for an API round trip for classification. They start
processing within milliseconds.

---

## Part 3: Parallel Context Assembly (Backend)

### Update backend/main.py

Currently context assembly runs sequentially:
1. Classify intent (wait)
2. Query ChromaDB (wait)
3. Query SQLite tasks (wait)
4. Query SQLite preferences (wait)
5. Build system prompt (wait)
6. Call model (wait)

Change steps 2-4 to run in parallel using asyncio.gather:

```python
@app.post("/chat")
async def chat(request: ChatRequest):
    session_id = request.session_id
    message = request.message

    # Emit immediate acknowledgment so frontend knows request was received
    await manager.emit_event("thinking", {"message": "..."})

    # Stage 1: classify intent (keyword check first, then Haiku if needed)
    routing = await classify_intent(message)
    await manager.emit_event("step", {
        "content": f"Classified as {routing['intent']} ({routing['tier']})"
    })

    # Stage 2: gather all context IN PARALLEL
    async def get_memory():
        try:
            return await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, inject_context, message
                ),
                timeout=0.5  # 500ms cap on memory retrieval
            )
        except asyncio.TimeoutError:
            return ""  # Skip memory if too slow, don't block

    async def get_tasks():
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            tasks = conn.execute("""
                SELECT title, due_datetime, priority FROM tasks
                WHERE status = 'pending'
                AND (due_datetime IS NULL OR due_datetime >= datetime('now', '-1 day'))
                ORDER BY due_datetime ASC LIMIT 5
            """).fetchall()
            conn.close()
            if not tasks:
                return "No active tasks."
            return "\n".join(
                f"- {t[0]}" + (f" (due {t[1]})" if t[1] else "")
                for t in tasks
            )
        except Exception:
            return ""

    async def get_prefs():
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            prefs = conn.execute(
                "SELECT key, value FROM preferences LIMIT 20"
            ).fetchall()
            conn.close()
            return "\n".join(f"{k}: {v}" for k, v in prefs) if prefs else ""
        except Exception:
            return ""

    async def get_assignments():
        try:
            conn = sqlite3.connect(SQLITE_PATH)
            assignments = conn.execute("""
                SELECT course, title, due_datetime FROM assignments
                WHERE status != 'complete'
                AND due_datetime >= datetime('now')
                ORDER BY due_datetime ASC LIMIT 5
            """).fetchall()
            conn.close()
            if not assignments:
                return "No upcoming assignments."
            return "\n".join(
                f"- {a[1]} ({a[0]}) due {a[2]}" for a in assignments
            )
        except Exception:
            return ""

    # Run all context queries simultaneously
    memory_context, active_tasks, preferences, upcoming_assignments = (
        await asyncio.gather(
            get_memory(),
            get_tasks(),
            get_prefs(),
            get_assignments()
        )
    )

    # Stage 3: tool context if needed (MCP calls)
    tool_results = ""
    if routing["tools"]:
        await manager.emit_event("step", {"content": "Gathering context..."})
        tool_results = await gather_tool_context(routing["tools"], message)

    # Stage 4: build system prompt and call model
    # ... rest of existing chat logic
```

---

## Part 4: Streaming Flush Optimization (Backend)

### Update stream_ollama_response and call_anthropic in api_client.py

For Anthropic streaming, ensure tokens are emitted to the WebSocket
immediately without any buffering:

```python
async def stream_callback(chunk: str):
    # Emit immediately — no batching, no delay
    await manager.emit_event("token", {"content": chunk})
    # Small yield to allow WebSocket to flush
    await asyncio.sleep(0)
```

The `await asyncio.sleep(0)` yields control back to the event loop after
each token emission, allowing the WebSocket send to complete before the
next token is processed. This reduces time between tokens in the UI.

For Ollama streaming (code model), same pattern — emit each chunk
immediately as it arrives.

---

## Part 5: Add Thinking Event to Frontend

### Update AssistantPanel.tsx WebSocket handler

Add handling for the new "thinking" event type:

```typescript
case "thinking":
  // This fires as soon as the backend receives the request
  // Ensures the placeholder/typing indicator is definitely showing
  setIsGenerating(true);
  break;

case "token":
  // First token — replace placeholder with actual content
  setIsGenerating(true);
  if (lastMessageIsPlaceholder()) {
    replaceLastMessageContent(event.content);
  } else {
    appendToLastMessage(event.content);
  }
  break;

case "done":
  setIsGenerating(false);
  break;
```

---

## Part 6: Health Check Fast Path

The health check currently queries all 7 MCP servers every 30 seconds
and blocks if any are slow. Change it to run health checks in parallel
with a 2-second timeout per server:

### Update backend/main.py GET /health

```python
@app.get("/health")
async def health():
    async def check_mcp(url: str, name: str) -> tuple[str, bool]:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                r = await client.get(f"{url}/health")
                return name, r.status_code == 200
        except Exception:
            return name, False

    # Check all MCP servers in parallel with 2s timeout each
    checks = await asyncio.gather(
        check_mcp(MCP_FILESYSTEM, "mcp_filesystem"),
        check_mcp(MCP_TERMINAL, "mcp_terminal"),
        check_mcp(MCP_EMAIL, "mcp_email"),
        check_mcp(MCP_BROWSER, "mcp_browser"),
        check_mcp(MCP_SCREEN, "mcp_screen"),
        check_mcp(MCP_TASKS, "mcp_tasks"),
        check_ollama(),
        return_exceptions=True
    )

    result = {name: status for name, status in checks if isinstance(checks, tuple)}
    result["sqlite"] = check_sqlite()
    result["chromadb"] = check_chromadb()

    return result
```

This prevents a slow MCP server from blocking the health check and
making the UI show "Offline" unnecessarily.

---

## Implementation Order

1. Update router.py — add keyword_classify and update classify_intent
2. Update main.py chat endpoint — parallel context assembly with asyncio.gather
3. Add ChromaDB 500ms timeout to memory retrieval
4. Add "thinking" event emission at start of chat endpoint
5. Update api_client.py — add asyncio.sleep(0) after each token emit
6. Update /health endpoint to use parallel checks with timeout
7. Update AssistantPanel.tsx:
   - Add placeholder message on send (before API response)
   - Add typing indicator dots CSS animation
   - Handle "thinking" WebSocket event
   - Handle first token replacing placeholder
8. Restart backend: nssm restart assistant-backend
9. Restart frontend: restart npm run tauri dev
10. Test response times:
    - "What do I have due today?" — should start responding in under 1 second
      (keyword classified, no API round trip, Haiku handles it)
    - "Hey what's the weather?" — same, keyword classified
    - "Tell me about machine learning" — Sonnet, should show dots within
      100ms then start streaming within 2 seconds
    - "Write me a Python script" — pipeline, Agent Monitor should show steps
      immediately
    - Typing indicator dots should ALWAYS appear before any text

---

## Expected Improvements After This Amendment

| Request Type | Before | After |
|---|---|---|
| Simple tasks/reminders | 2-4 seconds | Under 1 second |
| Weather/schedule | 2-4 seconds | Under 1 second |
| General conversation | 3-5 seconds to first token | 1-2 seconds to first token |
| Typing indicator appearance | After first token | Immediately on send |
| Code pipeline | Same | Same (network bound) |
| Health check | Blocks on slow MCP | Always returns within 2s |
