# Build Spec Amendment — SRU RockMail via Playwright
# This document amends CLAUDE_CODE_BUILD_SPEC_FINAL.md
# Read this alongside the main build spec. Where this document conflicts with the
# main spec on anything SRU-email related, this document takes precedence.

---

## What Changed and Why

The original build spec used Microsoft Graph API with OAuth2 for SRU RockMail.
This approach requires registering an Azure AD application, which SRU's tenant
configuration blocks for external accounts.

The replacement approach uses Playwright to scrape outlook.office.com — the same
browser automation tool already used for D2L. Since D2L and RockMail share the same
SRU credentials and MFA flow, the Playwright session established for D2L can be
reused for RockMail. No new authentication infrastructure is needed.

This approach provides full read and send capability from the SRU address.

---

## What To Remove From The Main Build Spec

Remove or ignore all references to:
- SRU_TENANT_ID in config.py
- SRU_CLIENT_ID in config.py
- SRU_SCOPES in config.py
- SRU_TOKEN_REFRESH_MARGIN in config.py
- SRU_GRAPH_BASE in config.py
- msal Python package (do not install)
- Any Microsoft Graph API endpoints or token refresh logic
- The sru_oauth_access and sru_oauth_refresh entries in the credentials table
- The GET /sru/auth/start and POST /sru/auth/callback endpoints
- The SRU OAuth2 authorization flow in the Settings > Accounts tab
- The "SRU Token expiry" display in Settings

---

## config.py — Replacement SRU Section

Replace the entire SRU Microsoft 365 block in config.py with:

```python
# Email — SRU RockMail (Playwright via outlook.office.com)
SRU_OUTLOOK_URL    = "https://outlook.office.com"
SRU_LOGIN_URL      = "https://login.microsoftonline.com"
# Credentials stored in SQLite credentials table under service='sru_outlook'
# Stored as: {email, password} — same credentials used for D2L and MySRU
```

Remove SRU_TOKEN_REFRESH_MARGIN entirely.

---

## Database Schema Amendment

In the credentials table, the relevant service names for SRU are now:

| Service key | Contents |
|---|---|
| sru_outlook | {email: str, password: str} |
| d2l | {email: str, password: str} (unchanged) |

Remove sru_oauth_access and sru_oauth_refresh from your mental model of the
credentials table. They are no longer used.

No schema change is required — the credentials table structure is the same.

---

## Browser / D2L MCP Amendment — Port 8013

The Browser MCP server now handles both D2L and SRU Outlook in the same process,
sharing a single Playwright browser instance and SRU session.

### Shared SRU Session Manager

Add a SRUSessionManager class to the Browser MCP:

```python
# C:\assistant\mcp\browser\session.py

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from auth import get_credential
import asyncio
import logging

logger = logging.getLogger(__name__)

class SRUSessionManager:
    """
    Manages a single shared Playwright browser session for both D2L and Outlook.
    SRU uses the same credentials and MFA for both services.
    One login covers both.
    """
    def __init__(self):
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        self._lock = asyncio.Lock()
        self._logged_in = False

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

    async def get_authenticated_page(self, target_url: str) -> Page:
        async with self._lock:
            page = await self.context.new_page()
            await page.goto(target_url)

            # Check if we landed on a login page
            if "login.microsoftonline.com" in page.url or "login" in page.url:
                await self._perform_login(page)

            return page

    async def _perform_login(self, page: Page):
        creds = get_credential("sru_outlook")
        if not creds:
            raise ValueError("SRU credentials not found. Set them in Settings > Accounts.")

        email = creds["email"]
        password = creds["password"]

        # Enter email
        await page.fill('input[type="email"]', email)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # Enter password
        await page.fill('input[type="password"]', password)
        await page.click('input[type="submit"]')
        await page.wait_for_load_state("networkidle")

        # Handle MFA prompt if present
        if "mysignins" in page.url or "MFA" in await page.title():
            # Emit notification to dashboard to complete MFA on phone
            # The session manager waits up to 60 seconds for MFA completion
            logger.info("MFA prompt detected. Waiting for user to approve on phone...")
            await page.wait_for_url("**/inbox**", timeout=60000)

        # Handle "Stay signed in?" prompt
        try:
            stay_signed_in = page.locator('input[id="idBtn_Back"]')  # "No" button
            if await stay_signed_in.is_visible(timeout=3000):
                await stay_signed_in.click()
        except Exception:
            pass

        self._logged_in = True
        logger.info("SRU login successful")

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()


# Module-level singleton — shared across all requests
sru_session = SRUSessionManager()
```

Initialize the session manager in the Browser MCP's FastAPI lifespan startup event:
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    await sru_session.start()
    yield
    await sru_session.close()
```

### New SRU Outlook Endpoints

Add these endpoints to the Browser MCP alongside the existing D2L endpoints:

**GET /sru/inbox?limit=20**

```python
@app.get("/sru/inbox")
async def sru_inbox(limit: int = 20):
    page = await sru_session.get_authenticated_page(
        "https://outlook.office.com/mail/inbox"
    )
    await page.wait_for_selector('[aria-label="Message list"]', timeout=15000)

    messages = []
    items = await page.query_selector_all('[role="option"]')

    for item in items[:limit]:
        try:
            sender = await item.query_selector('[data-testid="SenderName"]')
            subject = await item.query_selector('[data-testid="Subject"]')
            preview = await item.query_selector('[data-testid="Preview"]')
            time_el = await item.query_selector("time")
            is_read = await item.get_attribute("aria-describedby")

            messages.append({
                "uid": await item.get_attribute("data-convid") or "",
                "account": "sru",
                "sender": await sender.inner_text() if sender else "",
                "subject": await subject.inner_text() if subject else "",
                "snippet": await preview.inner_text() if preview else "",
                "received_at": await time_el.get_attribute("datetime") if time_el else "",
                "read": "unread" not in str(is_read).lower(),
            })
        except Exception:
            continue

    await page.close()

    # Upsert into SQLite emails table
    conn = sqlite3.connect(SQLITE_PATH)
    for msg in messages:
        conn.execute("""
            INSERT INTO emails (uid, account, sender, subject, received_at, read, snippet)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(uid, account) DO UPDATE SET read = excluded.read
        """, (msg["uid"], "sru", msg["sender"], msg["subject"],
              msg["received_at"], msg["read"], msg["snippet"]))
    conn.commit()
    conn.close()

    return {"messages": messages}
```

**GET /sru/message/{uid}**

```python
@app.get("/sru/message/{uid}")
async def sru_message(uid: str):
    page = await sru_session.get_authenticated_page(
        "https://outlook.office.com/mail/inbox"
    )
    # Click the message matching the conversation ID
    await page.click(f'[data-convid="{uid}"]')
    await page.wait_for_selector('[aria-label="Message body"]', timeout=10000)

    body_el = await page.query_selector('[aria-label="Message body"]')
    body = await body_el.inner_text() if body_el else ""

    # Mark as read in SQLite
    conn = sqlite3.connect(SQLITE_PATH)
    conn.execute("UPDATE emails SET read=1 WHERE uid=? AND account='sru'", (uid,))
    conn.commit()
    conn.close()

    await page.close()
    return {"uid": uid, "body": body}
```

**POST /sru/send**

```python
@app.post("/sru/send")
async def sru_send(payload: dict):
    # payload: {to: str, subject: str, body: str, reply_to_uid: str = ""}
    page = await sru_session.get_authenticated_page(
        "https://outlook.office.com/mail/inbox"
    )

    if payload.get("reply_to_uid"):
        # Click the original message and use Reply
        await page.click(f'[data-convid="{payload["reply_to_uid"]}"]')
        await page.wait_for_selector('[aria-label="Reply"]', timeout=5000)
        await page.click('[aria-label="Reply"]')
    else:
        # New message
        await page.click('[aria-label="New mail"]')

    await page.wait_for_selector('[aria-label="To"]', timeout=5000)

    if not payload.get("reply_to_uid"):
        await page.fill('[aria-label="To"]', payload["to"])
        await page.fill('[aria-label="Subject"]', payload["subject"])

    # Click body area and type message
    await page.click('[aria-label="Message body"]')
    await page.keyboard.type(payload["body"])

    # Send
    await page.click('[aria-label="Send"]')
    await page.wait_for_timeout(2000)  # Wait for send to complete

    await page.close()
    return {"success": True}
```

**GET /sru/search?q=**

```python
@app.get("/sru/search")
async def sru_search(q: str):
    page = await sru_session.get_authenticated_page(
        "https://outlook.office.com/mail/inbox"
    )
    await page.fill('[aria-placeholder="Search"]', q)
    await page.keyboard.press("Enter")
    await page.wait_for_load_state("networkidle")
    await page.wait_for_selector('[role="option"]', timeout=10000)

    results = []
    items = await page.query_selector_all('[role="option"]')
    for item in items[:20]:
        try:
            sender = await item.query_selector('[data-testid="SenderName"]')
            subject = await item.query_selector('[data-testid="Subject"]')
            results.append({
                "uid": await item.get_attribute("data-convid") or "",
                "sender": await sender.inner_text() if sender else "",
                "subject": await subject.inner_text() if subject else "",
            })
        except Exception:
            continue

    await page.close()
    return {"results": results}
```

**GET /sru/auth/status**
```python
@app.get("/sru/auth/status")
async def sru_auth_status():
    creds = get_credential("sru_outlook")
    return {
        "connected": creds is not None,
        "email": creds["email"] if creds else None,
        "session_active": sru_session._logged_in
    }
```

### D2L Integration — Reuse SRU Session

The D2L scraping code already in the Browser MCP should be updated to use the same
SRUSessionManager instead of creating its own Playwright session. D2L and Outlook
both authenticate through the same Microsoft login, so a session established for
Outlook will generally work for D2L too (same cookies, same tenant auth).

Update the D2L sync function:
```python
async def scrape_d2l():
    page = await sru_session.get_authenticated_page(
        "https://sru.desire2learn.com/d2l/home"
    )
    # ... rest of D2L scraping logic unchanged
    await page.close()
```

This means one login handles both D2L and RockMail. If the user needs to re-authenticate
(session expired, password changed), one re-login restores both services simultaneously.

---

## Email MCP Amendment — Port 8012

The Email MCP (port 8012) no longer handles SRU email directly.
SRU email is now handled entirely by the Browser MCP (port 8013).

Update config.py MCP routing:
```python
# SRU email routes to Browser MCP, not Email MCP
MCP_EMAIL_SRU = "http://localhost:8013"  # Browser MCP handles SRU
```

The unified /email/inbox endpoint in FastAPI main.py should call:
- Email MCP (:8012) for Yahoo and Gmail
- Browser MCP (:8013/sru/inbox) for SRU

```python
@app.get("/email/inbox")
async def unified_inbox(limit: int = 50):
    async with httpx.AsyncClient() as client:
        yahoo_task  = client.get(f"{MCP_EMAIL}/yahoo/inbox?limit=20")
        gmail_task  = client.get(f"{MCP_EMAIL}/gmail/inbox?limit=20")
        sru_task    = client.get(f"{MCP_EMAIL_SRU}/sru/inbox?limit=20")

        yahoo_res, gmail_res, sru_res = await asyncio.gather(
            yahoo_task, gmail_task, sru_task,
            return_exceptions=True
        )

    messages = []
    for res, account in [(yahoo_res, "yahoo"), (gmail_res, "gmail"), (sru_res, "sru")]:
        if isinstance(res, Exception):
            continue  # Account unavailable, skip silently
        data = res.json()
        messages.extend(data.get("messages", []))

    messages.sort(key=lambda x: x.get("received_at", ""), reverse=True)
    return {"messages": messages[:limit]}
```

---

## Scheduler Amendment

Remove the sru_mail_sync job from scheduler.py (the one using Microsoft Graph API).

Replace with:

```python
# In scheduler.py — replace Graph API sync with Playwright-based sync

@scheduler.scheduled_job('interval', seconds=900, id='sru_mail_sync')
async def sru_mail_sync():
    """
    Trigger the SRU mail sync via the Browser MCP.
    The Browser MCP handles its own Playwright session.
    """
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            await client.get(f"{MCP_EMAIL_SRU}/sru/inbox?limit=50")
        emit_ws_event("email_synced", {"account": "sru"})
    except Exception as e:
        logger.error(f"SRU mail sync failed: {e}")
        # Do not crash — just log and continue
```

---

## Settings UI Amendment — Accounts Tab

Replace the SRU OAuth section with a simpler credentials section:

**SRU RockMail section in Settings > Accounts:**
- SRU Email address text input (your SRU email e.g. abc1234@sru.edu)
- SRU Password text input (obscured, toggle show/hide)
- Note: "This is your MySRU / D2L password. The same credentials are used for
  both D2L and RockMail."
- "Save Credentials" button — stores encrypted in SQLite under service='sru_outlook'
  AND updates the d2l credentials entry simultaneously (same email/password)
- Test Connection button — calls GET /sru/auth/status, then triggers a test page load
- Session status indicator: "Session active" (green) or "Not connected" (gray)
- Re-authenticate button — calls sru_session._logged_in = False on the backend,
  forcing a fresh login on the next SRU request
- Note displayed: "If your SRU password changes, update it here and click
  Re-authenticate. SRU passwords expire every 90 days."

Remove:
- Token expiry display
- Authorize / OAuth flow button
- Any mention of Azure or OAuth2

---

## MFA Handling Note

SRU requires MFA (Microsoft Authenticator) on first login from a new session.

When the Playwright session logs in for the first time or after session expiry:
1. The login flow detects the MFA prompt
2. The backend emits a WebSocket event to the Tauri shell:
   {type: "notification", level: "warning", message: "SRU login needs MFA approval —
   check your phone and approve the Microsoft Authenticator prompt"}
3. The Tauri shell displays this as an amber notification banner
4. The user approves on their phone (same as normal SRU login)
5. Playwright detects the successful redirect and continues
6. The session is now established for both D2L and RockMail

After the initial session is established, MFA is not required again until the session
expires (typically several hours to days depending on SRU's session policy).

If the Playwright session is persisted using context.storage_state() between backend
restarts, MFA prompts become infrequent — typically only after a password change or
a very long period of inactivity.

**Persist the browser context between restarts:**

```python
# In SRUSessionManager.start():
import os
STATE_PATH = "C:/assistant/data/sru_browser_state.json"

self.context = await self.browser.new_context(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    storage_state=STATE_PATH if os.path.exists(STATE_PATH) else None
)

# In SRUSessionManager after successful login:
async def _save_state(self):
    await self.context.storage_state(path=STATE_PATH)

# Call _save_state() after _perform_login() completes successfully
```

This means after the first successful login + MFA approval, the session state is
saved to disk. On the next backend restart, the saved cookies are loaded and the
user typically does not need to re-approve MFA.

Add C:/assistant/data/sru_browser_state.json to .gitignore.

---

## Verification Checklist Amendment

Replace the SRU email verification items with:

- [ ] SRU credentials can be saved in Settings > Accounts > SRU RockMail
- [ ] Test Connection shows "Session active" after credentials are saved
- [ ] SRU inbox loads and messages appear (may require MFA approval on phone
      on the very first connection)
- [ ] MFA notification banner appears in the Tauri shell when MFA is needed
- [ ] After MFA approval, inbox loads successfully
- [ ] Browser state is persisted — backend restart does not require MFA again
- [ ] SRU message body loads when a message is clicked
- [ ] Send from SRU address works (test with a message to yourself)
- [ ] SRU search returns results
- [ ] D2L sync uses the same shared session (no second login required after
      SRU Outlook is already authenticated)
- [ ] Re-authenticate button forces a fresh login on the next request
- [ ] Unified /email/inbox returns messages from all three accounts merged

---

## Summary of All Changes

| Area | Original | Amendment |
|---|---|---|
| SRU auth method | Microsoft Graph API OAuth2 | Playwright scraping outlook.office.com |
| Azure AD app | Required | Not needed |
| Python packages | msal required | msal removed |
| SRU session | Token-based, auto-refresh | Playwright browser context, persisted to disk |
| D2L session | Separate Playwright instance | Shared with SRU Outlook session |
| MFA handling | OAuth2 handles it | User approves on phone, Playwright waits |
| Settings UI | OAuth authorize button | Email + password fields |
| Re-auth trigger | Token expiry | Manual button or session expiry |
| SRU email port | Email MCP :8012 | Browser MCP :8013 |
| Inbox merge | Graph API + IMAP | Playwright + IMAP |
ENDOFFILE
echo "done"