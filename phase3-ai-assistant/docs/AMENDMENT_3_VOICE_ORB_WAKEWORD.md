# Amendment 3 — Voice, Orb, and Wake Word
# This document amends CLAUDE_CODE_BUILD_SPEC_FINAL.md
# Read alongside the main spec, AMENDMENT_SRU_EMAIL.md, and AMENDMENT_2.
# This amendment takes precedence on anything related to voice, TTS, STT, or the orb.

---

## Overview

1. Three.js Particle Orb — Audio-reactive orb in the Assistant Panel.
   Pulses during speech, breathes when idle, spikes during generation.
   Adapted from ethanplusai/jarvis orb.ts, ported to React.

2. Kokoro TTS — Local text-to-speech. Jarvis speaks responses aloud only
   when the user initiated via voice. Silent when the user types.

3. faster-whisper STT — Local speech-to-text, CUDA-accelerated on the RTX 3060.

4. Voice Activation — Both wake word (Hey Jarvis) and push-to-talk simultaneously.

5. Voice Settings Tab — Change voice, test voice, toggle wake word, adjust speed.

---

## Part 1: Backend Voice Pipeline

### Install Dependencies

```powershell
cd C:\assistant\backend
.\venv\Scripts\Activate.ps1
pip install faster-whisper==1.0.3
pip install sounddevice==0.4.6
pip install soundfile==0.12.1
pip install numpy==1.26.4
pip install kokoro-onnx==0.4.9
pip install onnxruntime-gpu==1.18.0
```

### Download Kokoro Model

```powershell
mkdir C:\assistant\voice
cd C:\assistant\voice
python -c "from kokoro_onnx import Kokoro; k = Kokoro('kokoro-v0_19.onnx', 'voices.bin'); print('Kokoro ready')"
```

### Create backend/voice_pipeline.py

Build a voice pipeline module with these components:

AVAILABLE_VOICES dict mapping voice IDs to display names:
- af_heart: Heart (American Female) — default
- af_bella: Bella (American Female)
- af_nicole: Nicole (American Female)
- af_sarah: Sarah (American Female)
- am_adam: Adam (American Male)
- am_michael: Michael (American Male)
- bf_emma: Emma (British Female)
- bf_isabella: Isabella (British Female)
- bm_george: George (British Male)
- bm_lewis: Lewis (British Male)

Functions to implement:

get_whisper_model() — Load faster-whisper WhisperModel("medium", device="cuda",
compute_type="float16"). Cache after first load.

get_kokoro_model() — Load Kokoro from C:\assistant\voice\. Cache after first load.

set_voice(voice_id: str) -> bool — Change active voice, return True if valid.

get_current_voice() -> dict — Return {id, name} of current voice.

get_available_voices() -> list — Return [{id, name}] for all voices.

async transcribe_audio(audio_data: np.ndarray) -> str — Run faster-whisper in
thread pool. Convert int16 to float32, use vad_filter=True.

async synthesize_speech(text: str, voice_id: str = None, speed: float = 1.0) -> bytes
— Run Kokoro in thread pool. Return WAV bytes via io.BytesIO + soundfile.

detect_wake_word(text: str) -> bool — Check if text contains any of:
"hey jarvis", "jarvis", "hey friday", "friday"

strip_wake_word(text: str) -> str — Remove wake word from start of text.

WakeWordListener class:
- __init__(self, on_wake_word, on_speech) — callbacks for events
- start() — begin background thread with sounddevice InputStream
- stop() — stop thread
- Background loop: collect 1.5s audio chunks, skip silence (energy < 200),
  transcribe with faster-whisper, check for wake word, call appropriate callback
- If command is in same utterance as wake word, call on_wake_word(command)
- If wake word only, set flag to treat next utterance as command

### Add Voice Endpoints to main.py

GET /voice/voices — Return {voices: [...], current: {...}}
POST /voice/set — {voice_id: str} — Change voice, save to SQLite preferences
POST /voice/synthesize — {text: str, voice_id?: str, speed?: float}
  Return {audio_base64: str, format: "wav"}
POST /voice/transcribe — {audio_base64: str}
  Decode base64 to int16 numpy array, transcribe, return {text: str}
POST /voice/wake_word — {enabled: bool} — Toggle wake word, save to SQLite

Add response_complete WebSocket event at end of stream_ollama_response:
After emitting "done", emit:
{type: "response_complete", text: full_response, synthesize: True}

### Load Preferences on Startup

In lifespan startup after db init:
- Load tts_voice from SQLite preferences, call set_voice()
- Load wake_word_enabled from SQLite, start WakeWordListener if true
- Load tts_speed from SQLite for default speed

### Wake Word Processing

When wake word detected, call process_chat_message(command, "voice_wake_word")
which is a helper that runs the full chat pipeline for a given message and
session_id, used by both the /chat endpoint and wake word triggers.

---

## Part 2: Frontend Orb Component

### Install Three.js

```powershell
cd C:\assistant\shell
npm install three@0.165.0
npm install @types/three@0.165.0
```

### Create shell/src/components/JarvisOrb.tsx

A React component that renders a Three.js particle sphere.

Props:
- isGenerating: boolean
- isSpeaking: boolean
- isListening: boolean
- audioLevel: number (0-1)

Implementation:
- useEffect to initialize Three.js scene on mount
- 3000 particles distributed on sphere surface using spherical coordinates
- Particle color: electric blue (#63b3ed range) with slight per-particle variation
- PointsMaterial with vertexColors, size 0.015, transparent opacity 0.85
- Ambient glow: large transparent sphere behind particles, color #1a6bb5
- Animation loop using requestAnimationFrame:
  - Base idle breathing: sin(elapsed * 0.8) * 0.02 per particle
  - Slow rotation: elapsed * 0.05 on Y axis
  - Audio reactive displacement when isSpeaking or isListening:
    audioLevel * 0.4 * sin(elapsed * 8 + i * 0.05)
  - Generation pulse when isGenerating: sin(elapsed * 4) * 0.08
  - Listening pulse: sin(elapsed * 6) * 0.05
  - Glow opacity: 0.03 idle, 0.05 listening, 0.06+ speaking (scales with audioLevel)
- Pass state via data attributes on container div to avoid re-mounting Three.js
- Handle window resize
- Cleanup on unmount: cancel animation, dispose renderer, remove canvas
- Container div: width 100%, height 280px, transparent background

### Create shell/src/components/VoiceInput.tsx

Push-to-talk button component.

Props:
- onTranscription(text: string)
- onListeningChange(listening: boolean)
- onAudioLevel(level: number)

Implementation:
- onMouseDown/onTouchStart: getUserMedia, create AudioContext analyser for
  level tracking, create MediaRecorder, start recording, setIsListening(true)
- onMouseUp/onTouchEnd: stop MediaRecorder, stop tracks, cancel animation frame,
  collect Blob, convert to base64, POST to /voice/transcribe, call onTranscription
- Render: circular button (44x44px, border-radius 50%)
  - Border: accent blue when active, subtle white when idle
  - Background: accent blue 20% opacity when active
  - Microphone SVG icon inside
  - Title: "Hold to talk"
  - Disabled and shows wait cursor while processing transcription

### Update AssistantPanel.tsx

1. Import JarvisOrb and VoiceInput

2. Add state:
   - isSpeaking: boolean
   - isListening: boolean
   - audioLevel: number
   - voiceSessionActive: boolean
   - currentAudioRef: useRef for HTMLAudioElement

3. Layout change: Place JarvisOrb above the message history area.
   The panel structure becomes:
   [JarvisOrb - 280px]
   [Message history - flex 1, scrollable]
   [Confirmation gate banner - conditional]
   [Input area with VoiceInput button]

4. Replace existing placeholder voice button with VoiceInput component.
   On transcription:
   - setVoiceSessionActive(true)
   - Set input value to transcribed text
   - Auto-send the message

5. WebSocket message handler additions:
   - On wake_word_detected: setIsListening(true), setVoiceSessionActive(true)
     If has_command is true, setIsListening(false)
   - On response_complete AND voiceSessionActive is true:
     a. setVoiceSessionActive(false)
     b. POST /voice/synthesize with event.text
     c. Create Audio from base64 WAV response
     d. Set up AudioContext analyser on the audio element
     e. On audio play: setIsSpeaking(true), start level tracking loop
     f. On audio end: setIsSpeaking(false), setAudioLevel(0), revoke object URL
     g. Play the audio
     h. Store in currentAudioRef for potential cancellation

---

## Part 3: Voice Settings Tab

Add a "Voice" tab to Settings.tsx:

Voice selector:
- Fetch GET /voice/voices on mount
- Render select dropdown with all available voices
- On change: POST /voice/set, update local state
- Label: "Assistant Voice"

Test voice button:
- POST /voice/synthesize with text "Hello, I am your personal assistant.
  How can I help you today?" and current voice
- Play returned audio immediately
- Label: "Test Voice"

Wake word toggle:
- Switch/checkbox labeled "Wake Word (say Hey Jarvis)"
- On toggle: POST /voice/wake_word {enabled: bool}
- Load current state from GET /voice/voices response

Speech speed slider:
- Range 0.5 to 2.0, step 0.1, default 1.0
- Label shows current value: "Speed: 1.0x"
- On change: POST /voice/set with speed value (update backend default speed)
- Save to SQLite preferences as tts_speed

Microphone test:
- Button "Test Microphone"
- Records 3 seconds, transcribes, shows result text
- Label: "Microphone Test"

---

## Implementation Order

1. Install Python deps in backend venv
2. Download Kokoro model
3. Create backend/voice_pipeline.py
4. Add voice endpoints to main.py
5. Add response_complete event to stream function
6. Integrate WakeWordListener into startup
7. Test all voice endpoints manually:
   curl GET /voice/voices
   curl POST /voice/synthesize {"text": "Hello"} -> save and play WAV
   curl POST /voice/set {"voice_id": "bm_george"}
   curl POST /voice/synthesize {"text": "Hello"} -> should sound different
8. Install Three.js npm packages
9. Create JarvisOrb.tsx
10. Create VoiceInput.tsx
11. Update AssistantPanel.tsx
12. Add Voice tab to Settings.tsx
13. Restart backend: nssm restart assistant-backend
14. Restart frontend: restart npm run tauri dev
15. Verify:
    - Orb renders and animates (idle breathing visible)
    - Hold mic button, speak, release -> text appears in input, auto-sends
    - Response streams -> orb shows generation pulse
    - Audio plays back -> orb reacts to audio level in real time
    - Say "Hey Jarvis" -> wake word event received, isListening state activates
    - Settings Voice tab: dropdown works, Test Voice plays audio
    - Type a message -> no audio plays (voiceSessionActive stays false)
    - Change voice to George (British Male) -> Test Voice sounds different
    - Change back to default, verify saved on restart

---

## Notes

- faster-whisper downloads the medium Whisper model (~1.5GB) on first transcribe
  to the HuggingFace cache. This is expected and only happens once.
- If CUDA fails for faster-whisper, fall back: WhisperModel("medium",
  device="cpu", compute_type="int8")
- The orb must be clearly visible at 280px height — not too small
- Do not make the orb full screen or replace the chat interface
- Wake word detection requires continuous microphone access — Windows will
  show a microphone indicator in the taskbar while it is active
- The WakeWordListener thread is daemonized so it dies with the process
- Test voice synthesis before wiring it to chat — audio quality check first
