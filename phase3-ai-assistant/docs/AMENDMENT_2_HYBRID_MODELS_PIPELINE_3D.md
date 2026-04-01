# Amendment 2 — Hybrid Models, Stacking Pipeline, and 3D Scripting
# This document amends CLAUDE_CODE_BUILD_SPEC_FINAL.md
# Read alongside the main spec and AMENDMENT_SRU_EMAIL.md
# This amendment takes precedence where it conflicts with the main spec.

---

## Overview of Changes

This amendment makes three significant improvements:

1. **Hybrid Model Stack** — Replace local phi3:mini and llama3.1:8b with Claude
   Haiku 3.5 (routing + fast tasks) and Claude Sonnet 4.5 (general conversation).
   Keep Qwen2.5-Coder 14B local for code and LLaVA 7B local for vision.

2. **Multi-Agent Stacking Pipeline** — For HEAVY coding tasks, implement a
   Planner→Builder→Reviewer chain where Sonnet plans, Qwen builds and runs in
   sandbox, and Haiku reviews the output before delivery.

3. **3D Scripting MCP** — New MCP server on port 8016 that generates and executes
   Python scripts for Fusion 360 and Blender via their APIs.

---

## Part 1: Hybrid Model Stack

### Remove From config.py

Remove these entries:
```python
MODEL_ROUTER  = "phi3:mini"
MODEL_GENERAL = "llama3.1:8b"
```

### Add To config.py

```python
# Anthropic API models
ANTHROPIC_API_KEY    = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_BASE_URL   = "https://api.anthropic.com/v1/messages"
MODEL_HAIKU          = "claude-haiku-3-5-20251001"
MODEL_SONNET         = "claude-sonnet-4-5"

# Local models (kept for code and vision only)
MODEL_CODE           = "qwen2.5-coder:14b"   # unchanged
MODEL_VISION         = "llava:7b"             # unchanged

# Model tier assignments
MODEL_ROUTER         = MODEL_HAIKU    # Haiku handles all routing
MODEL_FAST           = MODEL_HAIKU    # Haiku handles fast tasks
MODEL_GENERAL        = MODEL_SONNET   # Sonnet handles conversation
```

### Updated Intent to Model Routing Table

| Intent | Model | Provider | Tools |
|---|---|---|---|
| chat | claude-sonnet-4-5 | Anthropic API | None |
| task_lookup | claude-haiku-3-5 | Anthropic API | Tasks MCP |
| reminder_set | claude-haiku-3-5 | Anthropic API | Tasks MCP |
| schedule | claude-haiku-3-5 | Anthropic API | Tasks MCP |
| weather | claude-haiku-3-5 | Anthropic API | Browser MCP |
| email | claude-sonnet-4-5 | Anthropic API | Email MCP |
| d2l | claude-sonnet-4-5 | Anthropic API | Browser MCP |
| file_action | claude-sonnet-4-5 | Anthropic API | Filesystem MCP |
| terminal | qwen2.5-coder:14b | Ollama (local) | Terminal MCP |
| code | STACKING PIPELINE | Mixed | Filesystem + Terminal |
| screen | llava:7b | Ollama (local) | Screen MCP |
| search | claude-haiku-3-5 | Anthropic API | Browser MCP |
| threed | STACKING PIPELINE | Mixed | ThreeD MCP |

### New Anthropic API Call Function

Replace the existing Ollama call logic in main.py with a unified call function
that routes to either Anthropic API or Ollama based on the model:

```python
# backend/api_client.py

import httpx
import json
from config import (
    ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL,
    MODEL_HAIKU, MODEL_SONNET,
    OLLAMA_BASE_URL, OLLAMA_TIMEOUT
)

ANTHROPIC_MODELS = {MODEL_HAIKU, MODEL_SONNET}

async def call_model(
    model: str,
    messages: list,
    system_prompt: str,
    stream_callback=None,
    max_tokens: int = 2048
) -> str:
    """
    Unified model caller. Routes to Anthropic API or Ollama based on model name.
    If stream_callback is provided, calls it with each token chunk.
    Returns the full response string.
    """
    if model in ANTHROPIC_MODELS:
        return await call_anthropic(model, messages, system_prompt,
                                    stream_callback, max_tokens)
    else:
        return await call_ollama(model, messages, system_prompt,
                                 stream_callback)


async def call_anthropic(
    model: str,
    messages: list,
    system_prompt: str,
    stream_callback=None,
    max_tokens: int = 2048
) -> str:
    """Call Anthropic API with optional streaming."""
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system_prompt,
        "messages": messages,
        "stream": stream_callback is not None
    }

    full_response = ""

    async with httpx.AsyncClient(timeout=120) as client:
        if stream_callback:
            async with client.stream("POST", ANTHROPIC_BASE_URL,
                                     headers=headers,
                                     json=payload) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            event = json.loads(data)
                            if event.get("type") == "content_block_delta":
                                chunk = event["delta"].get("text", "")
                                full_response += chunk
                                await stream_callback(chunk)
                        except json.JSONDecodeError:
                            pass
        else:
            response = await client.post(ANTHROPIC_BASE_URL,
                                         headers=headers,
                                         json={**payload, "stream": False})
            data = response.json()
            full_response = data["content"][0]["text"]

    return full_response


async def call_ollama(
    model: str,
    messages: list,
    system_prompt: str,
    stream_callback=None
) -> str:
    """Call local Ollama model with optional streaming."""
    ollama_messages = [{"role": "system", "content": system_prompt}] + messages
    full_response = ""

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        if stream_callback:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": ollama_messages, "stream": True}
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                chunk = data["message"]["content"]
                                full_response += chunk
                                await stream_callback(chunk)
                        except json.JSONDecodeError:
                            pass
        else:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={"model": model, "messages": ollama_messages, "stream": False}
            )
            full_response = response.json()["message"]["content"]

    return full_response


async def classify_intent_api(message: str) -> dict:
    """
    Use Haiku to classify intent. Much more reliable than phi3:mini.
    Returns {intent, tier, model, tools}
    """
    from router import INTENTS, TIER_MAP, MODEL_MAP, MCP_MAP, ROUTER_PROMPT

    response = await call_anthropic(
        model=MODEL_HAIKU,
        messages=[{"role": "user", "content": message}],
        system_prompt=ROUTER_PROMPT,
        stream_callback=None,
        max_tokens=10
    )

    intent = response.strip().lower()
    if intent not in INTENTS:
        intent = "chat"

    return {
        "intent": intent,
        "tier": TIER_MAP[intent],
        "model": MODEL_MAP[intent],
        "tools": MCP_MAP[intent],
    }
```

### Update router.py MODEL_MAP

```python
from config import MODEL_HAIKU, MODEL_SONNET, MODEL_CODE, MODEL_VISION

MODEL_MAP = {
    "chat":         MODEL_SONNET,
    "task_lookup":  MODEL_HAIKU,
    "reminder_set": MODEL_HAIKU,
    "schedule":     MODEL_HAIKU,
    "weather":      MODEL_HAIKU,
    "email":        MODEL_SONNET,
    "file_action":  MODEL_SONNET,
    "terminal":     MODEL_CODE,
    "code":         "PIPELINE",   # handled by stacking pipeline
    "screen":       MODEL_VISION,
    "d2l":          MODEL_SONNET,
    "search":       MODEL_HAIKU,
    "threed":       "PIPELINE",   # handled by stacking pipeline
}
```

### Update main.py

Replace all direct Ollama calls with calls to api_client.call_model().
Replace classify_intent() calls with classify_intent_api() from api_client.
The stream_callback for the chat endpoint should be:
```python
async def stream_callback(chunk: str):
    await manager.emit_event("token", {"content": chunk})
```

### Update Frontend Model Badge

In AssistantPanel.tsx, update the model badge display names:
```typescript
const MODEL_DISPLAY: Record<string, string> = {
    "claude-haiku-3-5-20251001": "FAST · Haiku",
    "claude-sonnet-4-5":         "SONNET",
    "qwen2.5-coder:14b":         "CODE · Qwen",
    "llava:7b":                  "VISION · LLaVA",
    "PIPELINE":                  "PIPELINE · Multi-Agent",
}
```

### Ollama Models That Can Be Retired

phi3:mini and llama3.1:8b are no longer used in the runtime system.
They can remain installed but will not be loaded.
Do NOT delete them — keep as fallback if API is unavailable.

Add a fallback in api_client.py: if Anthropic API call fails with a network
error, fall back to Ollama llama3.1:8b for the same request and log the fallback.

---

## Part 2: Multi-Agent Stacking Pipeline

This pipeline activates for `code` and `threed` intent tiers only.
All other intents use direct single-model calls.

### Pipeline Architecture

```
User Request
     │
     ▼
[Stage 1: PLANNER — Claude Sonnet 4.5]
     │  Receives: user request + memory context + project context
     │  Produces: structured technical spec (JSON)
     │
     ▼
[Stage 2: BUILDER — Qwen2.5-Coder 14B (local)]
     │  Receives: technical spec from Planner
     │  Produces: code, writes to sandbox, runs it
     │  Iterates: up to 3 times on errors
     │
     ▼
[Stage 3: REVIEWER — Claude Haiku 3.5]
     │  Receives: final code + execution results
     │  Produces: brief quality check + delivery summary
     │
     ▼
User receives: code + explanation + test results
```

### Implement pipeline.py

```python
# backend/pipeline.py
"""
Multi-agent stacking pipeline for heavy coding and 3D tasks.
"""
import json
import httpx
from api_client import call_anthropic, call_ollama
from config import MODEL_SONNET, MODEL_HAIKU, MODEL_CODE, MCP_TERMINAL, MCP_FILESYSTEM

PLANNER_SYSTEM = """You are a senior software architect. Your job is to take a
user's coding request and produce a clear, precise technical specification that
a code-generation model can implement directly.

Output ONLY a JSON object with these fields:
{
    "task_summary": "one sentence description",
    "language": "python|javascript|powershell|other",
    "approach": "brief description of the implementation approach",
    "steps": ["step 1", "step 2", ...],
    "filename": "suggested_filename.py",
    "dependencies": ["any pip/npm packages needed"],
    "edge_cases": ["edge case to handle"],
    "expected_output": "description of what success looks like"
}

Be specific and technical. Do not write any code yourself."""

BUILDER_SYSTEM = """You are an expert programmer. You receive a technical
specification and implement it completely. Write production-quality code with
error handling and comments. Output ONLY the complete code, nothing else."""

REVIEWER_SYSTEM = """You are a code reviewer. You receive code and its execution
results. Provide a brief, clear summary for the user:
1. What was built
2. How to use it
3. Any important notes or limitations
Be concise and helpful. Do not reprint the code."""


async def run_coding_pipeline(
    user_request: str,
    memory_context: str,
    emit_step,
    sandbox_path: str = "C:/assistant/sandbox"
) -> dict:
    """
    Run the full Planner→Builder→Reviewer pipeline.
    emit_step: async function to emit step events to the UI
    Returns: {code, filename, execution_result, review}
    """

    # Stage 1: Planner
    await emit_step("🧠 Planning implementation with Sonnet...")
    await emit_step("Model: claude-sonnet-4-5")

    planner_messages = [{
        "role": "user",
        "content": f"User request: {user_request}\n\nContext: {memory_context}"
    }]

    spec_raw = await call_anthropic(
        model=MODEL_SONNET,
        messages=planner_messages,
        system_prompt=PLANNER_SYSTEM,
        max_tokens=1024
    )

    try:
        # Strip markdown fences if present
        spec_clean = spec_raw.replace("```json", "").replace("```", "").strip()
        spec = json.loads(spec_clean)
    except json.JSONDecodeError:
        spec = {
            "task_summary": user_request,
            "language": "python",
            "approach": "direct implementation",
            "steps": ["implement the requested functionality"],
            "filename": "solution.py",
            "dependencies": [],
            "edge_cases": [],
            "expected_output": "working solution"
        }

    await emit_step(f"📋 Plan ready: {spec.get('task_summary', '')}")
    await emit_step(f"📝 File: {spec.get('filename', 'solution.py')}")

    # Stage 2: Builder (with retry loop)
    await emit_step("⚙️ Building with Qwen2.5-Coder...")

    builder_prompt = f"""Technical Specification:
{json.dumps(spec, indent=2)}

Original request: {user_request}

Write the complete, working implementation."""

    builder_messages = [{"role": "user", "content": builder_prompt}]

    code = await call_ollama(
        model=MODEL_CODE,
        messages=builder_messages,
        system_prompt=BUILDER_SYSTEM
    )

    # Clean code if wrapped in markdown
    if "```" in code:
        lines = code.split("\n")
        code_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```"):
                in_block = not in_block
                continue
            if in_block:
                code_lines.append(line)
        code = "\n".join(code_lines)

    filename = spec.get("filename", "solution.py")
    filepath = f"{sandbox_path}/{filename}"

    await emit_step(f"💾 Writing {filename}...")

    # Write code to sandbox via Filesystem MCP
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(f"{MCP_FILESYSTEM}/write", json={
            "path": filepath,
            "content": code,
            "create_dirs": True
        })

    # Install dependencies if needed
    deps = spec.get("dependencies", [])
    if deps:
        await emit_step(f"📦 Installing dependencies: {', '.join(deps)}")
        async with httpx.AsyncClient(timeout=120) as client:
            await client.post(f"{MCP_TERMINAL}/docker_run", json={
                "command": f"pip install {' '.join(deps)}"
            })

    # Run code in sandbox with retry
    execution_result = ""
    success = False

    for attempt in range(1, 4):
        await emit_step(f"🚀 Running in sandbox (attempt {attempt}/3)...")

        async with httpx.AsyncClient(timeout=120) as client:
            run_response = await client.post(f"{MCP_TERMINAL}/docker_run", json={
                "command": f"python /workspace/{filename}"
            })
            result = run_response.json()

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        exit_code = result.get("exit_code", 1)

        if exit_code == 0:
            execution_result = stdout
            success = True
            await emit_step(f"✅ Execution successful")
            break
        else:
            await emit_step(f"⚠️ Error on attempt {attempt}: {stderr[:100]}")

            if attempt < 3:
                # Ask builder to fix the error
                await emit_step(f"🔧 Fixing error with Qwen2.5-Coder...")
                fix_messages = [
                    {"role": "user", "content": builder_prompt},
                    {"role": "assistant", "content": f"```python\n{code}\n```"},
                    {"role": "user", "content": f"This produced an error:\n{stderr}\n\nFix the code. Output only the corrected code."}
                ]
                code = await call_ollama(
                    model=MODEL_CODE,
                    messages=fix_messages,
                    system_prompt=BUILDER_SYSTEM
                )
                if "```" in code:
                    lines = code.split("\n")
                    code_lines = []
                    in_block = False
                    for line in lines:
                        if line.startswith("```"):
                            in_block = not in_block
                            continue
                        if in_block:
                            code_lines.append(line)
                    code = "\n".join(code_lines)

                async with httpx.AsyncClient(timeout=30) as client:
                    await client.post(f"{MCP_FILESYSTEM}/write", json={
                        "path": filepath,
                        "content": code,
                        "create_dirs": True
                    })
            else:
                execution_result = f"Failed after 3 attempts. Last error:\n{stderr}"

    # Stage 3: Reviewer
    await emit_step("🔍 Reviewing output with Haiku...")

    review_messages = [{
        "role": "user",
        "content": f"""Original request: {user_request}

Code written ({filename}):
```
{code[:3000]}
```

Execution result:
{execution_result[:1000] if execution_result else 'Did not execute successfully'}

Success: {success}

Provide a brief user-friendly summary."""
    }]

    review = await call_anthropic(
        model=MODEL_HAIKU,
        messages=review_messages,
        system_prompt=REVIEWER_SYSTEM,
        max_tokens=512
    )

    await emit_step("✨ Pipeline complete")

    return {
        "code": code,
        "filename": filename,
        "filepath": filepath,
        "execution_result": execution_result,
        "review": review,
        "success": success,
        "spec": spec
    }
```

### Integrate Pipeline Into main.py

In the chat endpoint, after intent classification:

```python
if routing["intent"] in ("code", "threed"):
    # Use stacking pipeline instead of direct model call
    from pipeline import run_coding_pipeline

    async def emit_step_fn(step: str):
        await manager.emit_event("step", {"content": step})

    result = await run_coding_pipeline(
        user_request=message,
        memory_context=memory_context,
        emit_step=emit_step_fn
    )

    # Stream the review as the final response
    review = result["review"]
    for i in range(0, len(review), 10):
        chunk = review[i:i+10]
        await manager.emit_event("token", {"content": chunk})
        await asyncio.sleep(0.01)

    # Also emit the code block
    code_block = f"\n\n```{result['spec'].get('language','python')}\n{result['code']}\n```"
    for i in range(0, len(code_block), 10):
        chunk = code_block[i:i+10]
        await manager.emit_event("token", {"content": chunk})
        await asyncio.sleep(0.01)

    await manager.emit_event("done", {"summary": result["review"][:200]})
    return {"status": "pipeline_complete", "model": "PIPELINE"}
```

---

## Part 3: 3D Scripting MCP

**Port:** localhost:8016
**Purpose:** Generate and execute Python scripts for Fusion 360 and Blender

### Add to config.py

```python
MCP_THREED = "http://localhost:8016"

# 3D app paths (update if installed in different location)
FUSION360_SCRIPT_DIR = "C:/Users/{USERNAME}/AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Scripts"
BLENDER_EXECUTABLE   = "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
```

### Add to router.py

```python
# Add to INTENTS list
INTENTS = [...existing..., "threed"]

# Add to TIER_MAP
TIER_MAP["threed"] = "HEAVY"

# Add to MODEL_MAP
MODEL_MAP["threed"] = "PIPELINE"

# Add to MCP_MAP
MCP_MAP["threed"] = ["threed"]

# Update ROUTER_PROMPT to include threed:
# threed: creating, modifying, or automating 3D models in Fusion 360 or Blender,
#         generating 3D geometry, parametric design, 3D printing preparation
```

### Create C:\assistant\mcp\threed\requirements.txt

```
fastapi==0.135.2
uvicorn[standard]==0.42.0
httpx==0.28.1
pydantic==2.12.5
```

### Create C:\assistant\mcp\threed\main.py

```python
# C:\assistant\mcp\threed\main.py
"""
3D Scripting MCP Server - Port 8016
Generates and executes scripts for Fusion 360 and Blender.
"""
import subprocess
import tempfile
import os
import sys
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, "C:/assistant/backend")
from config import FUSION360_SCRIPT_DIR, BLENDER_EXECUTABLE

app = FastAPI(title="3D Scripting MCP", version="1.0.0")


class ScriptRequest(BaseModel):
    script: str
    app: str = "blender"  # "blender" or "fusion360"
    description: str = ""


class ScriptResponse(BaseModel):
    success: bool
    output: str = ""
    error: str = ""
    script_path: str = ""


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "threed"}


@app.post("/run/blender", response_model=ScriptResponse)
async def run_blender_script(request: ScriptRequest):
    """
    Execute a Python script in Blender in background mode.
    The script receives a fully initialized Blender scene.
    """
    blender_path = Path(BLENDER_EXECUTABLE)
    if not blender_path.exists():
        return ScriptResponse(
            success=False,
            error=f"Blender not found at {BLENDER_EXECUTABLE}. "
                  f"Update BLENDER_EXECUTABLE in config.py."
        )

    # Write script to temp file
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False, dir="C:/assistant/sandbox"
    ) as f:
        f.write(request.script)
        script_path = f.name

    try:
        result = subprocess.run(
            [str(blender_path), "--background", "--python", script_path],
            capture_output=True,
            text=True,
            timeout=120
        )
        success = result.returncode == 0
        return ScriptResponse(
            success=success,
            output=result.stdout[-3000:] if result.stdout else "",
            error=result.stderr[-2000:] if result.stderr else "",
            script_path=script_path
        )
    except subprocess.TimeoutExpired:
        return ScriptResponse(
            success=False,
            error="Script timed out after 120 seconds",
            script_path=script_path
        )
    except Exception as e:
        return ScriptResponse(
            success=False,
            error=str(e),
            script_path=script_path
        )


@app.post("/run/fusion360", response_model=ScriptResponse)
async def run_fusion360_script(request: ScriptRequest):
    """
    Deploy a script to Fusion 360's script directory.
    Fusion 360 scripts must be run manually from within the application
    (API > Scripts and Add-ins). This endpoint writes the script to the
    correct location and returns instructions.
    """
    script_dir = Path(FUSION360_SCRIPT_DIR)

    if not script_dir.exists():
        # Try to find Fusion 360 scripts directory
        possible_paths = [
            Path.home() / "AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Scripts",
            Path("C:/Users") / os.environ.get("USERNAME", "") /
            "AppData/Roaming/Autodesk/Autodesk Fusion 360/API/Scripts"
        ]
        for p in possible_paths:
            if p.exists():
                script_dir = p
                break
        else:
            return ScriptResponse(
                success=False,
                error="Fusion 360 script directory not found. "
                      "Is Fusion 360 installed?"
            )

    # Create script folder
    script_name = "AssistantScript"
    target_dir = script_dir / script_name
    target_dir.mkdir(exist_ok=True)

    script_file = target_dir / f"{script_name}.py"
    script_file.write_text(request.script)

    manifest = target_dir / f"{script_name}.manifest"
    manifest.write_text('{"autodeskProduct": "Fusion", "type": "script", '
                        '"engine": "Python", "id": "AssistantScript", '
                        '"description": "Assistant generated script", '
                        '"version": "1.0.0"}')

    return ScriptResponse(
        success=True,
        output=f"Script written to Fusion 360 scripts directory.\n"
               f"To run: In Fusion 360, go to Utilities > Add-Ins > Scripts "
               f"and Add-Ins, find '{script_name}' and click Run.",
        script_path=str(script_file)
    )


@app.get("/apps/available")
async def available_apps():
    """Check which 3D applications are installed."""
    apps = {}

    blender = Path(BLENDER_EXECUTABLE)
    apps["blender"] = {
        "installed": blender.exists(),
        "path": str(blender),
        "execution": "background_mode"
    }

    fusion_dir = Path(FUSION360_SCRIPT_DIR)
    apps["fusion360"] = {
        "installed": fusion_dir.exists() or any(
            Path(f"C:/Users/{os.environ.get('USERNAME','')}/AppData/Local/"
                 f"Autodesk/webdeploy/production").glob("*/FusionLauncher.exe")
        ),
        "script_dir": str(fusion_dir),
        "execution": "manual_via_ui"
    }

    return {"apps": apps}
```

### Register 3D Scripting MCP as Windows Service

```powershell
nssm install AssistantMCP_ThreeD "C:\assistant\mcp\threed\venv\Scripts\python.exe"
nssm set AssistantMCP_ThreeD AppParameters "-m uvicorn main:app --host 127.0.0.1 --port 8016"
nssm set AssistantMCP_ThreeD AppDirectory "C:\assistant\mcp\threed"
nssm set AssistantMCP_ThreeD Start SERVICE_AUTO_START
nssm set AssistantMCP_ThreeD AppStdout "C:\assistant\logs\mcp_threed.log"
nssm set AssistantMCP_ThreeD AppStderr "C:\assistant\logs\mcp_threed_err.log"
nssm start AssistantMCP_ThreeD
```

### Add ThreeD MCP to health check in main.py

```python
MCP_THREED = config.MCP_THREED  # http://localhost:8016
# Add to health check dict: "mcp_threed": await check_mcp(MCP_THREED)
```

### Update gather_tool_context in main.py

```python
elif "threed" in tools:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            apps_response = await client.get(f"{MCP_THREED}/apps/available")
            apps_data = apps_response.json()
        tool_context += f"\n3D Apps Available: {json.dumps(apps_data['apps'])}"
    except Exception as e:
        tool_context += f"\n3D Apps: Check failed ({e})"
```

### 3D Scripting System Prompt Addition

Add to the main system prompt when intent is threed:

```
You have access to a 3D Scripting tool that can:
- Write and execute Python scripts in Blender (background mode, instant execution)
- Write Python scripts for Fusion 360 (deployed to script directory, run manually)

For Blender tasks: you can fully automate mesh creation, modifiers, materials,
rendering, and file export. Scripts run immediately and results are returned.

For Fusion 360 tasks: you write the script and it is deployed to the Scripts
directory. The user runs it from within Fusion 360 via Utilities > Add-Ins.

Always use the bpy module for Blender scripts.
Always use the adsk.fusion and adsk.core modules for Fusion 360 scripts.
The pipeline will handle writing and executing — just provide working code.
```

---

## Implementation Order

Claude Code must implement these changes in this exact order:

1. Install anthropic package in backend venv:
   ```powershell
   cd C:\assistant\backend && .\venv\Scripts\Activate.ps1
   pip install anthropic==0.40.0
   ```

2. Create backend/api_client.py with the unified call function

3. Update config.py with Anthropic model constants

4. Update router.py MODEL_MAP to use Anthropic model names

5. Update main.py to use api_client functions throughout

6. Create backend/pipeline.py

7. Integrate pipeline into main.py chat endpoint

8. Update frontend model badge display names in AssistantPanel.tsx

9. Create C:\assistant\mcp\threed\ with requirements.txt and main.py

10. Install threed MCP dependencies and register as Windows service

11. Test each component:
    - Test Haiku routing: send "what time is it" → should route to haiku, respond fast
    - Test Sonnet conversation: send "explain quantum computing" → should use Sonnet
    - Test pipeline: send "write a Python web scraper" → should show planner→builder→reviewer steps in Agent Monitor
    - Test threed: send "write a Blender script to create a cube" → should use threed pipeline
    - Test fallback: temporarily disable API key → should fall back to llama3.1:8b

12. Restart backend and all services after implementation

13. Verify health check returns mcp_threed: true

---

## Cost Management

Add a token usage tracker to main.py:

```python
# Track API usage per session for cost awareness
import sqlite3
from datetime import datetime

def log_api_usage(model: str, input_tokens: int, output_tokens: int):
    """Log API usage to SQLite for cost tracking."""
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            estimated_cost REAL,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Pricing per million tokens
    pricing = {
        "claude-haiku-3-5-20251001": (0.80, 4.00),
        "claude-sonnet-4-5": (3.00, 15.00),
    }
    if model in pricing:
        input_rate, output_rate = pricing[model]
        cost = (input_tokens / 1_000_000 * input_rate +
                output_tokens / 1_000_000 * output_rate)
        conn.execute(
            "INSERT INTO api_usage (model, input_tokens, output_tokens, estimated_cost) VALUES (?,?,?,?)",
            (model, input_tokens, output_tokens, cost)
        )
        conn.commit()
    conn.close()
```

Add a GET /usage endpoint that returns daily and monthly cost estimates from
the api_usage table. Display this in the Settings > System tab.

---

## Fallback Behavior

If the Anthropic API is unreachable or returns an error:
- Log the error to C:\assistant\logs\backend.log
- Fall back to llama3.1:8b via Ollama for the same request
- Emit a step event: "⚠️ API unavailable, using local fallback"
- Do not crash or return an error to the user

This ensures the system remains functional even without internet access.
