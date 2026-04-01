# Amendment 4 — Aether Rebrand and Purple Theme
# Read alongside all previous amendments.
# This amendment takes precedence on anything related to naming,
# wake words, colors, or orb color.

---

## Overview

1. Rename the assistant from "ASSISTANT" to "AETHER" throughout
2. Change wake words to "Hey Aether" and "Aether"
3. Replace the blue color theme with the purple/grey theme from the reference image
4. Change the orb particle color to purple to match

---

## Exact Colors (extracted from reference image)

```css
--bg-primary:     #212121;   /* Main background - dark charcoal */
--bg-secondary:   #2a2a2a;   /* Slightly lighter dark grey */
--bg-panel:       #303030;   /* Panel and input surface */
--bg-panel-hover: #383838;   /* Hover state */
--bg-input:       #303030;   /* Input field background */
--border-subtle:  rgba(255, 255, 255, 0.08);
--border-accent:  rgba(117, 76, 180, 0.4);  /* Purple border */

--accent:         #754cb4;   /* Primary purple - from button */
--accent-bright:  #8b5cf6;   /* Brighter purple for highlights */
--accent-dim:     rgba(117, 76, 180, 0.5);
--accent-glow:    rgba(117, 76, 180, 0.15);
--accent-bg:      rgba(117, 76, 180, 0.12);

--text-primary:   #f0f0f0;
--text-secondary: #a0a0a0;
--text-muted:     #505050;
--text-accent:    #a78bfa;   /* Light purple for accent text */

--status-ok:      #68d391;   /* Keep green for success */
--status-warn:    #f6ad55;   /* Keep amber for warnings */
--status-error:   #fc8181;   /* Keep red for errors */
--status-info:    #754cb4;   /* Purple for info (replaces blue) */

--user-bubble-bg:     rgba(117, 76, 180, 0.15);
--user-bubble-border: rgba(117, 76, 180, 0.35);
```

---

## Part 1: Rename to Aether

### Files to update:

**shell/src/App.tsx or Sidebar component:**
Change any text "ASSISTANT" to "AETHER"
Change any title/branding text to "AETHER"

**shell/src-tauri/tauri.conf.json:**
Change "title" from "Assistant" to "Aether"
Change "identifier" from "com.assistant.personal" to "com.aether.personal"

**shell/index.html:**
Change <title> from "Assistant" or "Tauri + React + Typescript" to "Aether"

**shell/src/App.tsx:**
Any "Assistant" text in the UI → "Aether"

**pwa/public/manifest.json:**
Change "name" from "Assistant" to "Aether"
Change "short_name" from "Assistant" to "Aether"

**backend/main.py system prompt:**
Change all references to "assistant" in the system prompt personality section
to use the name "Aether":
"You are Aether, a personal AI assistant running locally on Cody's PC..."

**All NSSM service display names** (no functional change needed, just internal):
These can stay as-is since they're internal service names.

---

## Part 2: Update Wake Words

**backend/voice_pipeline.py:**

Change WAKE_WORDS list from:
```python
WAKE_WORDS = ["hey jarvis", "jarvis", "hey friday", "friday"]
```

To:
```python
WAKE_WORDS = ["hey aether", "aether"]
```

---

## Part 3: Update Color Theme

**shell/src/styles/tokens.css:**

Replace the entire :root block with the new Aether purple theme:

```css
:root {
  --bg-primary:     #212121;
  --bg-secondary:   #2a2a2a;
  --bg-tertiary:    #1a1a1a;
  --bg-panel:       #303030;
  --bg-panel-hover: #383838;
  --bg-input:       #303030;
  --border-subtle:  rgba(255, 255, 255, 0.08);
  --border-accent:  rgba(117, 76, 180, 0.4);

  --accent:         #754cb4;
  --accent-bright:  #8b5cf6;
  --accent-dim:     rgba(117, 76, 180, 0.5);
  --accent-glow:    rgba(117, 76, 180, 0.15);
  --accent-bg:      rgba(117, 76, 180, 0.12);

  --text-primary:   #f0f0f0;
  --text-secondary: #a0a0a0;
  --text-muted:     #505050;
  --text-accent:    #a78bfa;

  --status-ok:      #68d391;
  --status-warn:    #f6ad55;
  --status-error:   #fc8181;
  --status-info:    #754cb4;

  --user-bubble-bg:     rgba(117, 76, 180, 0.15);
  --user-bubble-border: rgba(117, 76, 180, 0.35);

  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', Consolas, monospace;

  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;

  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.5);

  --t-fast:   150ms ease;
  --t-normal: 250ms ease;
  --t-slow:   400ms ease;
}

* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: var(--bg-primary);
  color: var(--text-primary);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
}
```

**Also update any hardcoded color values in component files:**
Search all .tsx and .css files for the old blue accent values and replace:
- #63b3ed → #754cb4
- rgba(99, 179, 237, ...) → rgba(117, 76, 180, ...)
- Any "blue" named variables → purple equivalents

**Tailwind config (if used):**
Update the accent color in tailwind.config.js to use #754cb4

---

## Part 4: Update Orb Color

**shell/src/components/JarvisOrb.tsx (or AetherOrb.tsx — rename the file):**

Rename the component from JarvisOrb to AetherOrb.

Change the particle colors from blue to purple:

Find the particle color initialization loop:
```typescript
// OLD - blue colors:
colors[i * 3] = 0.3 + Math.random() * 0.2;     // R
colors[i * 3 + 1] = 0.6 + Math.random() * 0.3; // G
colors[i * 3 + 2] = 0.9 + Math.random() * 0.1; // B

// NEW - purple colors matching #754cb4 (rgb 117, 76, 180):
colors[i * 3] = 0.4 + Math.random() * 0.2;     // R (0.46 base)
colors[i * 3 + 1] = 0.25 + Math.random() * 0.15; // G (0.30 base)
colors[i * 3 + 2] = 0.65 + Math.random() * 0.2; // B (0.71 base)
```

Change the glow sphere color from blue to purple:
```typescript
// OLD:
color: 0x1a6bb5,

// NEW:
color: 0x754cb4,
```

Change the glow opacity colors to use purple tones.

Update the breathing animation accent color references to purple.

Rename all imports of JarvisOrb to AetherOrb in AssistantPanel.tsx.

---

## Part 5: Update PWA Theme Color

**pwa/public/manifest.json:**
Change theme_color from "#0d0d0f" to "#212121"
Change background_color from "#0d0d0f" to "#212121"

**pwa/index.html:**
Update meta theme-color to "#212121"

---

## Part 6: Update System Prompt Personality

**backend/main.py — SYSTEM_PROMPT_TEMPLATE:**

Update the opening line to establish the Aether name and personality:

```python
SYSTEM_PROMPT_TEMPLATE = """You are Aether, a personal AI assistant running
locally on Cody's PC at Slippery Rock University. You are capable, direct,
and genuinely useful. You have full access to Cody's computer through your
tools and must use them when relevant. You do not over-explain. You act when
asked to act. You refer to yourself as Aether when asked your name.

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

IMPORTANT: You have FULL ACCESS to Cody's computer through MCP tools.
When tool results are provided below, use them directly in your response.
Do not say you lack access to something you just retrieved data from.

{tool_results}"""
```

---

## Implementation Order

1. Update tokens.css with new color palette
2. Search and replace all hardcoded blue hex values in all .tsx files
3. Update tauri.conf.json title and identifier
4. Update index.html title
5. Update all "ASSISTANT" / "Assistant" text in UI components to "AETHER" / "Aether"
6. Update pwa/public/manifest.json name and colors
7. Rename JarvisOrb.tsx to AetherOrb.tsx, update component name
8. Update orb particle colors to purple
9. Update glow sphere color to purple
10. Update all imports of JarvisOrb to AetherOrb
11. Update WAKE_WORDS in voice_pipeline.py
12. Update system prompt in main.py
13. Restart backend: nssm restart assistant-backend
14. Restart frontend: restart npm run tauri dev
15. Verify:
    - App title bar shows "Aether"
    - Sidebar branding shows "AETHER"
    - Background is dark charcoal #212121
    - Accent elements are purple #754cb4
    - Orb particles are purple
    - Orb glow is purple
    - User message bubbles have purple border/tint
    - Active nav item highlight is purple
    - Online status dot uses purple for info states
    - Say "Hey Aether" triggers wake word
    - Say "Jarvis" does NOT trigger wake word
    - System prompt references "Aether" when asked "what is your name"
