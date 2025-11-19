# Speech Recognition App - Code Analysis Report

**File:** `speech_recognition_app.py`
**Date:** 2025-11-19
**Environment:** Linux (Anaconda Edition)

---

## Executive Summary

This is a Terminal User Interface (TUI) application built with Textual that provides real-time speech recognition with optional AI-powered responses via Ollama. The application is specifically optimized for Anaconda Python environments and handles ALSA audio system complexities on Linux.

---

## Architecture Overview

### Core Technologies
- **UI Framework:** Textual (Terminal UI)
- **Speech Recognition:** `speech_recognition` library with Google Speech Recognition API
- **AI Integration:** Ollama (optional) for conversational AI responses
- **Audio System:** PyAudio/ALSA (Linux audio layer)
- **Concurrency:** Threading for non-blocking audio processing

### Key Components

1. **Speech Recognition Engine** (`speech_recognition` library)
2. **TUI Interface** (Textual framework)
3. **Ollama AI Integration** (conversational context)
4. **Audio Device Management** (microphone detection and cycling)
5. **Multi-language Support** (Indonesian/English)

---

## Feature Analysis

### 1. Speech Recognition
**Location:** Lines 651-733 (`listen_once_blocking`)

**Features:**
- Google Speech Recognition API integration
- Configurable energy threshold (300) with dynamic adjustment
- Pause threshold: 0.8 seconds
- Timeout: 10 seconds, phrase limit: 60 seconds
- Ambient noise adjustment (0.3s duration)

**Error Handling:**
- `UnknownValueError`: Audio not understood
- `RequestError`: API connection issues
- `WaitTimeoutError`: No speech detected
- Debug mode: saves unrecognized audio to WAV files

### 2. Continuous Listening Mode
**Location:** Lines 461-478, 620-650

**Mechanism:**
- Press `L` to start continuous listening
- Press `L` again (or any key) to stop
- Runs in separate daemon thread
- 0.3s pause between recognition cycles
- Thread-safe with mutex locks

### 3. Microphone Management
**Location:** Lines 294-369

**Capabilities:**
- Auto-detection of available microphones
- Prioritization: ALC294 Analog devices first
- Filters out HDMI devices (unless analog)
- Cycle through microphones with `M` key
- Multi-sample rate support: 44100Hz, 48000Hz, 16000Hz, auto

**Initialization Strategy:**
```
1. Try device at 44100Hz
2. Fallback to 48000Hz
3. Fallback to 16000Hz
4. Fallback to auto-detect
```

### 4. Ollama AI Integration
**Location:** Lines 563-618

**Features:**
- Conversational context with history (10 messages max)
- System prompt configuration via JSON
- Configurable model selection (default: `qwen3:8b`)
- Temperature and token limit controls
- Asynchronous processing in daemon thread

**Configuration:** `prompt_llm_SR.json`
```json
{
  "default_language": "id-ID",
  "model": "qwen3:8b",
  "system_prompt": "...",
  "temperature": 0.7,
  "max_tokens": 500
}
```

### 5. Multi-language Support
**Location:** Lines 227-232, 795-812

**Languages:**
- Indonesian (`id-ID`) - Default
- English (`en-US`)

**Toggle:** `G` key or "Toggle Lang" button

### 6. Audio Visualization
**Location:** Lines 485-504, 548-561

**Display:**
- 20-character audio level bar
- Real-time animation during listening
- Visual states: Idle (░), Listening (█)
- Simulated audio levels (0-20 scale)

---

## ALSA Error Suppression Strategy

### Problem
Anaconda Python environments on Linux produce verbose ALSA (Advanced Linux Sound Architecture) warnings that clutter the terminal output.

### Solution (Lines 19-74)
1. **Environment Variables:**
   - `PYTHONWARNINGS='ignore'`
   - `ALSA_CARD='Generic_1'`

2. **C-Level Error Handler:**
   - Loads `libasound.so.2` via ctypes
   - Installs custom error handler that suppresses messages

3. **Stream Suppression:**
   - Custom `SuppressStream` class filters stderr
   - Blocks messages containing: 'ALSA', 'alsa', 'pcm', 'dlmisc'

4. **Context-Specific Suppression:**
   - Microphone detection (lines 296-299)
   - Microphone initialization (lines 330-331)
   - Audio recording (lines 661-664)

---

## User Interface Layout

```
┌─────────────────────────────────────────────────┐
│ Header                                          │
├─────────────────────────────────────────────────┤
│ Controls: [Listen] [Clear] [Cycle Mic] [Lang]  │
├─────────────────────────────────────────────────┤
│ Audio Level: [████████░░░░░░░░░░░░]            │
├─────────────────────────────────────────────────┤
│ Status: Ready | Lang: Indonesian | Ollama: ON  │
├─────────────────────────────────────────────────┤
│ System Info: Anaconda detected | 3 mics found  │
├─────────────────────────────────────────────────┤
│ Transcript (Left)    │ Ollama AI Response (Rt) │
│ [Your speech here]   │ [AI responses here]     │
│                      │                          │
├─────────────────────────────────────────────────┤
│ Footer: Keybindings                            │
└─────────────────────────────────────────────────┘
```

### Color Scheme (Lines 107-208)
- **Ready:** Green (`$success`)
- **Listening:** Yellow (`$warning`)
- **Error:** Red (`$error`)
- **Transcript:** Cyan timestamps, white text
- **Ollama:** Green timestamps, white text

---

## Key Bindings

| Key | Action | Description |
|-----|--------|-------------|
| `L` | Listen | Press to start, press again to stop continuous listening |
| `C` | Clear | Clear transcript and Ollama logs |
| `M` | Cycle Mic | Switch to next available microphone |
| `G` | Toggle Lang | Switch between Indonesian/English |
| `D` | Toggle Debug | Enable/disable debug mode (saves unrecognized audio) |
| `Q` | Quit | Exit application |

---

## Threading Architecture

### Thread Types
1. **Main Thread:** Textual UI event loop
2. **Listening Thread:** Continuous listening mode (lines 630-631)
3. **Audio Animation Thread:** Visual feedback (lines 671-672)
4. **Ollama Worker Thread:** AI processing (line 618)

### Thread Safety
- **Mutex Lock:** `mic_lock` prevents concurrent microphone access (lines 233, 657-660)
- **Daemon Threads:** All background threads marked as daemon for clean shutdown
- **Message Passing:** Custom Textual messages for cross-thread communication:
  - `UpdateLog` (lines 80-86)
  - `UpdateStatus` (lines 89-94)
  - `UpdateAudioLevel` (lines 97-101)

---

## Configuration System

### LLM Configuration (Lines 371-391)
**File:** `prompt_llm_SR.json`

**Loaded Parameters:**
- `default_language`: Sets initial recognition language
- `model`: Ollama model name
- `system_prompt`: Initial conversational context
- `temperature`: AI creativity (0.0-1.0)
- `max_tokens`: Response length limit

**Example:**
```json
{
  "default_language": "id-ID",
  "model": "qwen3:8b",
  "system_prompt": "You are a helpful assistant that speaks Indonesian.",
  "temperature": 0.7,
  "max_tokens": 500
}
```

### Speech Recognizer Settings (Lines 221-224)
```python
energy_threshold = 300          # Minimum audio energy
dynamic_energy_threshold = True # Auto-adjust to ambient noise
pause_threshold = 0.8           # Seconds of silence to end phrase
```

---

## Error Handling Strategy

### Microphone Errors
1. **Detection Failure:** Graceful degradation, shows error in UI
2. **Initialization Failure:** Tries multiple sample rates before failing
3. **Busy Microphone:** Non-blocking check, shows "Microphone busy" message

### Recognition Errors
1. **UnknownValueError:** "Tidak dapat memahami audio" message
2. **RequestError:** Displays API error details
3. **WaitTimeoutError:** "Timeout - no speech detected"

### Debug Mode (Lines 698-710)
- Saves unrecognized audio to timestamped WAV files
- Logs audio data length for diagnostics
- Filename format: `unrecognized_audio_YYYYMMDD_HHMMSS.wav`

---

## Ollama Conversation Management

### History Limits (Lines 580-585)
- Maximum 10 messages retained
- Preserves system prompt (always at index 0)
- FIFO eviction for older messages

### Message Structure
```python
{
  "role": "system" | "user" | "assistant",
  "content": "message text"
}
```

### Processing Flow
1. User speech → Transcript
2. Add user message to history
3. Trim history to 10 messages
4. Call Ollama API with full history
5. Add assistant response to history
6. Display in UI

---

## Anaconda-Specific Optimizations

### Detection (Lines 397-399)
```python
if 'conda' in sys.executable or 'anaconda' in sys.executable.lower():
    info_text.append("✓ Anaconda environment detected")
```

### Audio Device Prioritization (Lines 304-318)
1. Filter out HDMI devices
2. Prioritize ALC294 Analog devices
3. Move preferred devices to front of list
4. Fallback to all devices if none match

### Sample Rate Strategy
Anaconda environments may have different default sample rates. The app tries multiple rates to find a working configuration.

---

## Security Considerations

### Potential Concerns
1. **API Keys:** Google Speech Recognition uses default API (rate-limited)
2. **Audio Privacy:** Microphone access requires user interaction
3. **File System:** Debug mode writes audio files to current directory
4. **Network:** Sends audio to Google API and Ollama (if enabled)

### Mitigations
- No persistent storage of audio (except debug mode)
- Clear user indicators when microphone is active
- Local Ollama processing (no cloud)
- Daemon threads ensure clean shutdown

---

## Dependencies

### Required
```
speech_recognition    # Core speech-to-text
textual              # Terminal UI framework
pyaudio              # Audio I/O (implicit via speech_recognition)
```

### Optional
```
ollama               # AI responses (graceful degradation if missing)
```

### System
```
libasound.so.2       # ALSA library (Linux)
```

---

## Installation Requirements

### Python Packages
```bash
pip install speech_recognition textual ollama
```

### System (Linux)
```bash
# ALSA development libraries
sudo pacman -S alsa-lib portaudio

# Or on Debian/Ubuntu
sudo apt-get install libasound2-dev portaudio19-dev
```

### Ollama Setup
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull model
ollama pull qwen3:8b
```

---

## Known Limitations

1. **Google API:** Requires internet connection for speech recognition
2. **Language Support:** Limited to Google's supported languages
3. **Audio Quality:** Depends on microphone hardware quality
4. **ALSA Warnings:** Complete suppression may hide legitimate errors
5. **Ollama Dependency:** Requires local Ollama installation for AI features
6. **Platform:** Linux-specific ALSA handling (may need adjustments for macOS/Windows)

---

## Code Quality Assessment

### Strengths
- Comprehensive error handling with graceful degradation
- Thread-safe microphone access
- Clean separation of UI and business logic
- Extensive ALSA error suppression for better UX
- Configurable via JSON
- Multi-language support
- Debug mode for troubleshooting

### Areas for Improvement
1. **Magic Numbers:** Energy threshold (300), pause threshold (0.8) could be configurable
2. **Hard-coded Paths:** `prompt_llm_SR.json` path not configurable
3. **Error Messages:** Some messages in Indonesian even when English mode active
4. **Testing:** No unit tests visible
5. **Documentation:** Inline comments sparse in some complex sections
6. **Audio Storage:** Debug mode saves to CWD without user confirmation

---

## Performance Characteristics

### Resource Usage
- **CPU:** Low idle, moderate during recognition/Ollama processing
- **Memory:** ~50-100MB (depends on Textual + Ollama)
- **Network:** Bursts during Google API calls
- **Disk:** None (except debug mode WAV files)

### Latency
- **Recognition Start:** ~0.3s (ambient noise adjustment)
- **Recognition:** ~1-3s (network + API processing)
- **Ollama Response:** 2-10s (depends on model and hardware)

---

## Future Enhancement Suggestions

1. **Offline Recognition:** Add support for Vosk/DeepSpeech
2. **Custom Wake Word:** Voice activation instead of key press
3. **Multiple AI Backends:** OpenAI, Anthropic Claude API
4. **Audio Preprocessing:** Noise reduction, echo cancellation
5. **Conversation Export:** Save chat history to file
6. **Config UI:** Interactive configuration instead of JSON
7. **Metrics Dashboard:** Recognition accuracy, latency stats
8. **Plugin System:** Custom audio processors/formatters

---

## Conclusion

This is a well-structured, production-ready speech recognition application with thoughtful error handling and user experience optimizations. The Anaconda-specific ALSA suppression demonstrates deep understanding of Linux audio stack challenges. The Textual UI provides a clean, keyboard-driven interface suitable for terminal environments.

**Primary Use Cases:**
- Voice-controlled terminal applications
- Accessibility tools for hands-free computing
- Voice note-taking with AI assistance
- Language learning (multilingual transcription)
- Prototyping voice interfaces

**Target Users:**
- Developers in Anaconda environments
- Linux users with audio compatibility issues
- Users wanting local AI-powered voice assistants
- Terminal enthusiasts preferring TUI over GUI

---

**Report Generated:** 2025-11-19
**Total Lines of Code:** 865
**Analysis Depth:** Comprehensive architecture and implementation review
