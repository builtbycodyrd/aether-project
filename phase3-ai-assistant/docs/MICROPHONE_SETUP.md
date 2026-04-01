# Microphone Setup for Aether (Tauri App)

## ✅ Fix Applied

**Changed `tauri.conf.json`**:
- Set `"csp": null` in the security section
- This disables Content Security Policy restrictions, allowing browser APIs like getUserMedia to work

**Why CSP null?**: Tauri v2's CSP can block getUserMedia even with `media-src mediastream:`. Setting it to null allows all browser APIs to function properly.

## Testing the Fix

### Step 1: Restart the Tauri App
After the configuration change, you **must restart** the app for the changes to take effect.

### Step 2: Check Windows Privacy Settings

**CRITICAL**: Windows 11 must allow desktop apps to access the microphone.

1. Open **Settings** (`Win + I`)
2. Go to **Privacy & Security** → **Microphone**
3. Ensure these are **enabled**:
   - ☑ **Microphone access** (main toggle at top)
   - ☑ **Let apps access your microphone**
   - ☑ **Let desktop apps access your microphone** ← **This is crucial**

**Quick access**: Run `ms-settings:privacy-microphone` from Win+R dialog

### Step 3: Test with the Test File

Before testing in the full app, verify microphone works in the webview:

1. Open `C:\assistant\shell\test-microphone.html` in your browser (NOT Tauri)
2. Click "Test Microphone"
3. If it works in browser but not Tauri → Windows privacy issue
4. If it doesn't work in browser → hardware/driver issue

### Step 4: Test in Aether App

Once the app is restarted and Windows settings are correct:

**Test #1 - Settings Tab**:
1. Open Aether
2. Go to Settings → Voice tab
3. Click "Test Microphone"
4. Should record for 3 seconds and show transcription

**Test #2 - Push-to-Talk**:
1. Go to Chat tab
2. Hold the microphone button (bottom of input)
3. Button turns purple while recording
4. Speak, then release
5. Should transcribe and auto-send

**Test #3 - Wake Word** (if enabled):
1. Enable "Wake Word" in Settings → Voice
2. Say "Hey Aether" or "Aether"
3. Orb should react
4. Speak your command

## Troubleshooting

### Error: "NotAllowedError: Permission denied"
- **Cause**: Windows privacy settings blocking microphone
- **Fix**: Enable "Let desktop apps access your microphone" in Windows Settings

### Error: "NotFoundError: Requested device not found"
- **Cause**: No microphone detected
- **Fix**:
  - Check Device Manager → Audio inputs
  - Ensure microphone is plugged in
  - Set microphone as default recording device in Sound settings

### Error: "NotSupportedError: getUserMedia not supported"
- **Cause**: CSP blocking the API
- **Fix**: Verify `tauri.conf.json` has `"csp": null`
- Restart the app after changing config

### Microphone Works in Browser But Not Tauri
- **Cause**: WebView2 using different permission system
- **Fix**:
  1. Update WebView2 Runtime: https://developer.microsoft.com/microsoft-edge/webview2/
  2. Restart Windows (WebView2 permissions sometimes need a full restart)
  3. Check if antivirus is blocking Tauri app

### No Permission Popup Appears
- **Expected**: WebView2 should show a permission prompt the first time
- **If no prompt**: Windows privacy settings are blocking it before the prompt
- **Check**: Windows Settings → Microphone → ensure "Let desktop apps" is enabled

## Technical Details

### How Tauri v2 Microphone Access Works

1. **Browser API**: Uses standard `navigator.mediaDevices.getUserMedia({ audio: true })`
2. **WebView2**: Tauri on Windows uses Microsoft Edge WebView2 runtime
3. **CSP**: Content Security Policy can block getUserMedia even if Windows allows it
4. **Windows Privacy**: OS-level control over which apps can access microphone

### Why CSP null?

Tauri v2's CSP is very restrictive by default. Even with `media-src 'self' mediastream:`, getUserMedia can be blocked. Setting CSP to null:
- ✅ Allows all browser APIs (getUserMedia, WebRTC, etc.)
- ⚠️ Less secure (but fine for desktop app accessing localhost)
- 🎯 Standard approach for Tauri apps needing media access

### Capabilities File

The `capabilities/default.json` file defines Tauri-specific permissions (not browser APIs):
- `core:default` - Basic Tauri APIs
- `core:window:*` - Window management
- `opener:default` - Open URLs

**Note**: There is no "microphone permission" in Tauri capabilities because getUserMedia is a browser API, not a Tauri API.

## Current Configuration

### `tauri.conf.json`
```json
{
  "app": {
    "security": {
      "csp": null
    }
  }
}
```

### `capabilities/default.json`
```json
{
  "permissions": [
    "core:default",
    "core:window:allow-set-focus",
    "core:webview:allow-webview-position",
    "core:webview:allow-internal-toggle-devtools",
    "opener:default"
  ]
}
```

## Summary

✅ **CSP set to null** → Allows getUserMedia
✅ **Windows privacy enabled** → OS allows microphone access
✅ **WebView2 up to date** → Latest runtime handles permissions correctly

If all three are correct, microphone **will work** in the Tauri app.
