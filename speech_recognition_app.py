import speech_recognition as sr 
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Button, Static, RichLog, Label
from textual.binding import Binding
from textual.message import Message
from textual import events
from datetime import datetime
import threading
import queue
import sys
import subprocess
import os
import warnings
from ctypes import *
import asyncio
import json

# Suppress ALSA warnings more aggressively for Anaconda environments
import os
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['ALSA_CARD'] = 'Generic_1'  # Use the ALC294 card

# Try to suppress ALSA errors
try:
    # Try to load ALSA library and suppress errors
    ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
    def py_error_handler(filename, line, function, err, fmt):
        pass
    c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
    
    # Try different ALSA library names
    asound = None
    for lib_name in ['libasound.so.2', 'libasound.so', 'asound']:
        try:
            asound = cdll.LoadLibrary(lib_name)
            break
        except:
            continue
    
    if asound:
        asound.snd_lib_error_set_handler(c_error_handler)
except:
    pass

# Redirect stderr to suppress ALSA messages
class SuppressStream:
    def write(self, data):
        # Suppress ALSA error messages
        if not any(x in str(data) for x in ['ALSA', 'alsa', 'pcm', 'dlmisc']):
            sys.__stderr__.write(data)
    def flush(self):
        pass

# Temporarily suppress ALSA errors during import
old_stderr = sys.stderr
sys.stderr = SuppressStream()

# Try to import ollama
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# TTS removed - not needed

# Restore stderr after imports
sys.stderr = old_stderr

# Suppress other warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*ALSA.*")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


# Removed espeak check - TTS not needed


class UpdateLog(Message):
    """Message to update logs from threads."""
    def __init__(self, log_type: str, text: str, is_error: bool = False):
        super().__init__()
        self.log_type = log_type
        self.text = text
        self.is_error = is_error


class UpdateStatus(Message):
    """Message to update status from threads."""
    def __init__(self, message: str, status_class: str = "status-ready"):
        super().__init__()
        self.message = message
        self.status_class = status_class


class UpdateAudioLevel(Message):
    """Message to update audio level indicator."""
    def __init__(self, level: int):
        super().__init__()
        self.level = level  # 0-10 scale


class SpeechRecognitionApp(App):
    """A Textual app for speech recognition with TUI - Anaconda Optimized."""

    CSS = """
    Screen {
        background: $surface;
    }

    #status-panel {
        height: 3;
        border: solid $accent;
        background: $panel;
        padding: 0 1;
    }

    #audio-level {
        height: 3;
        border: solid $success;
        background: $panel;
        padding: 0 1;
    }

    #info-panel {
        height: 5;
        border: solid $primary;
        background: $panel;
        padding: 0 1;
    }

    #controls {
        height: 5;
        dock: top;
        background: $panel;
    }

    #transcript-panel {
        border: solid $primary;
        background: $surface;
        height: 1fr;
        padding: 1;
    }

    .status-ready {
        color: $success;
    }

    .status-listening {
        color: $warning;
    }

    .status-error {
        color: $error;
    }

    Button {
        margin: 1 2;
    }

    Button.primary {
        background: $success;
    }

    Button.danger {
        background: $error;
    }

    Button.secondary {
        background: $accent;
    }

    #transcript-log {
        border: solid $primary;
        background: $surface-darken-1;
        height: 1fr;
    }

    #ollama-panel {
        border: solid $success;
        background: $surface;
        height: 1fr;
        padding: 1;
    }

    #ollama-log {
        border: solid $success;
        background: $surface-darken-1;
        height: 1fr;
    }

    .timestamp {
        color: $accent;
    }

    .transcript-text {
        color: $text;
    }

    .ollama-response {
        color: $success;
    }
    
    .info-text {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        # L key handled via on_key for press/release detection
        Binding("c", "clear", "Clear"),
        ("m", "cycle_microphone", "Cycle Mic"),
        ("g", "toggle_language", "Toggle Lang"),
        ("d", "toggle_debug", "Toggle Debug"),
    ]

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.microphone = None
        self.microphone_error = None
        # Multi-language support
        self.languages = {
            "id-ID": "Indonesian",
            "en-US": "English"
        }
        self.language = "id-ID"  # Default: Bahasa Indonesia
        self.mic_lock = threading.Lock()
        
        # Anaconda-specific settings
        self.available_mics = []
        self.selected_mic_index = None
        self.sample_rate = 44100  # Default for ALC294
        self.debug_mode = False
        
        # Ollama settings
        self.ollama_enabled = OLLAMA_AVAILABLE
        self.ollama_model = "qwen3:8b"
        self.conversation_history = []
        self.llm_config = {}

        # Audio visualization
        self.audio_level = 0
        self.is_listening = False

        # Continuous listening mode
        self.continuous_mode = False
        self.l_key_pressed = False
        self.listening_thread = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()

        with Container(id="controls"):
            yield Static("Speech Recognition + Ollama AI (Anaconda Edition)", classes="title")
            with Horizontal():
                yield Button("Listen Once [L]", id="btn-listen", variant="primary")
                yield Button("Clear [C]", id="btn-clear", variant="default")
                yield Button("Cycle Mic [M]", id="btn-mic", variant="default")
                yield Button("Lang: ID [G]", id="btn-lang", variant="success")
                if OLLAMA_AVAILABLE:
                    yield Button("Toggle Ollama", id="btn-ollama", variant="success")

        with Container(id="audio-level"):
            yield Label("Audio Level: [░░░░░░░░░░░░░░░░░░░░]", id="audio-bar", classes="status-ready")

        with Container(id="status-panel"):
            ollama_status = "ON" if self.ollama_enabled else "OFF" if OLLAMA_AVAILABLE else "N/A"
            lang_name = self.languages.get(self.language, self.language)
            yield Label(f"Status: Ready | Lang: {lang_name} | Ollama: {ollama_status} | Mic: Not Set",
                       id="status-label", classes="status-ready")

        with Container(id="info-panel"):
            yield Static("System Info:", classes="title")
            yield Label("Initializing...", id="info-label", classes="info-text")

        with Horizontal():
            with Container(id="transcript-panel"):
                yield Static("Transcript (Your Speech):", classes="title")
                yield RichLog(id="transcript-log", highlight=True, markup=True)

            with Container(id="ollama-panel"):
                yield Static("Ollama AI Response:", classes="title")
                yield RichLog(id="ollama-log", highlight=True, markup=True)

        yield Footer()

    def detect_microphones(self):
        """Detect available microphones with Anaconda-specific handling."""
        # Suppress ALSA errors during detection
        old_stderr = sys.stderr
        sys.stderr = SuppressStream()
        
        try:
            self.available_mics = []
            mic_list = sr.Microphone.list_microphone_names()
            
            # Filter and prioritize microphones
            for idx, name in enumerate(mic_list):
                # Skip HDMI devices and prefer analog
                if 'hdmi' in name.lower() and 'analog' not in name.lower():
                    continue
                    
                # Prioritize ALC294 Analog
                if 'alc294' in name.lower() or 'analog' in name.lower():
                    self.available_mics.insert(0, (idx, name))
                else:
                    self.available_mics.append((idx, name))
            
            # If no mics after filtering, add all
            if not self.available_mics:
                self.available_mics = [(i, n) for i, n in enumerate(mic_list)]
            
            return True
            
        except Exception as e:
            self.post_message(UpdateLog("info", f"Microphone detection error: {str(e)}", True))
            return False
        finally:
            sys.stderr = old_stderr

    def initialize_microphone(self, device_index=None):
        """Initialize microphone with Anaconda-specific error handling."""
        old_stderr = sys.stderr
        sys.stderr = SuppressStream()
        
        try:
            # Try different configurations
            configs = [
                (device_index, 44100),
                (device_index, 48000),
                (device_index, 16000),
                (device_index, None),  # Let system choose
            ]
            
            for dev_idx, rate in configs:
                try:
                    if rate:
                        self.microphone = sr.Microphone(
                            device_index=dev_idx,
                            sample_rate=rate
                        )
                    else:
                        self.microphone = sr.Microphone(device_index=dev_idx)
                    
                    # Test the microphone
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                    
                    self.sample_rate = rate or "auto"
                    self.selected_mic_index = dev_idx
                    return True
                    
                except:
                    continue
            
            return False
            
        except Exception as e:
            self.post_message(UpdateLog("info", f"Mic init error: {str(e)}", True))
            return False
        finally:
            sys.stderr = old_stderr

    def load_llm_prompt_config(self, config_path="prompt_llm_SR.json"):
        """Loads LLM prompt configuration from a JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.llm_config = json.load(f)

            self.language = self.llm_config.get("default_language", self.language)
            self.ollama_model = self.llm_config.get("model", self.ollama_model)

            if self.llm_config.get("system_prompt"):
                self.conversation_history = [{
                    "role": "system",
                    "content": self.llm_config["system_prompt"]
                }]

            self.add_transcript(f"✓ LLM config loaded from '{config_path}'")

        except FileNotFoundError:
            self.add_transcript(f"✗ LLM config '{config_path}' not found. Using defaults.", is_error=True)
        except Exception as e:
            self.add_transcript(f"✗ Error loading LLM config: {e}", is_error=True)

    def on_mount(self) -> None:
        """Initialize on mount with better Anaconda handling."""
        info_text = []
        
        # Detect Python environment
        if 'conda' in sys.executable or 'anaconda' in sys.executable.lower():
            info_text.append("✓ Anaconda environment detected")
        
        # Detect available microphones
        if self.detect_microphones():
            info_text.append(f"✓ Found {len(self.available_mics)} microphone(s)")
            
            # Try to initialize with the first (preferred) microphone
            if self.available_mics:
                mic_idx, mic_name = self.available_mics[0]
                
                # Shorten the mic name for display
                short_name = mic_name.split(':')[-1].strip() if ':' in mic_name else mic_name
                info_text.append(f"Trying: {short_name}")
                
                if self.initialize_microphone(mic_idx):
                    self.microphone_error = None
                    info_text.append(f"✓ Using: {short_name} @ {self.sample_rate}Hz")
                    self.post_message(UpdateStatus(
                        f"Ready | Mic: {short_name}", 
                        "status-ready"
                    ))
                else:
                    self.microphone_error = "Failed to initialize microphone"
                    info_text.append("✗ Microphone initialization failed")
                    self.post_message(UpdateStatus("Error: Mic init failed", "status-error"))
            else:
                self.microphone_error = "No microphones available"
                info_text.append("✗ No microphones found")
        else:
            self.microphone_error = "Microphone detection failed"
            info_text.append("✗ Could not detect microphones")
        
        # Update info panel
        info_label = self.query_one("#info-label", Label)
        info_label.update(" | ".join(info_text))

        # Show installation warnings
        if not OLLAMA_AVAILABLE:
            self.add_transcript("ℹ Ollama not installed. Install with: pip install ollama")

        self.load_llm_prompt_config()

    def on_update_log(self, message: UpdateLog) -> None:
        """Handle log update messages from threads."""
        if message.log_type == "info":
            info_label = self.query_one("#info-label", Label)
            current = info_label.renderable
            info_label.update(f"{current} | {message.text}")
        elif message.log_type == "transcript":
            self.add_transcript(message.text, message.is_error)
        elif message.log_type == "ollama":
            self.add_ollama_response(message.text, message.is_error)

    def on_update_status(self, message: UpdateStatus) -> None:
        """Handle status update messages from threads."""
        self.update_status(message.message, message.status_class)

    def on_update_audio_level(self, message: UpdateAudioLevel) -> None:
        """Handle audio level update messages from threads."""
        self.audio_level = message.level
        self.update_audio_bar()

    def on_key(self, event: events.Key) -> None:
        """Handle key press for continuous listening."""
        # Press L to start, press L again (or any key) to stop
        if event.key == "l" or event.key == "L":
            if not self.continuous_mode and not self.is_listening:
                # Start continuous listening
                self.continuous_mode = True
                self.l_key_pressed = True
                self.start_continuous_listening()
                event.prevent_default()
                event.stop()
            elif self.continuous_mode:
                # Stop continuous listening
                self.stop_continuous_listening()
                self.add_transcript("Continuous listening stopped")
                event.prevent_default()
                event.stop()

    def stop_continuous_listening(self):
        """Stop continuous listening mode."""
        self.continuous_mode = False
        self.l_key_pressed = False
        self.post_message(UpdateStatus("Ready - Stopped listening", "status-ready"))

    def update_audio_bar(self):
        """Update the audio level visualization bar."""
        audio_bar = self.query_one("#audio-bar", Label)

        # Create visual bar based on audio level (0-20 blocks)
        bar_length = 20
        filled = min(self.audio_level, bar_length)

        if self.is_listening:
            # Animated listening indicator
            bar = "█" * filled + "░" * (bar_length - filled)
            audio_bar.update(f"🎤 Listening: [{bar}]")
            audio_bar.remove_class("status-ready", "status-error")
            audio_bar.add_class("status-listening")
        else:
            # Idle state
            bar = "░" * bar_length
            audio_bar.update(f"Audio Level: [{bar}]")
            audio_bar.remove_class("status-listening", "status-error")
            audio_bar.add_class("status-ready")

    def update_status(self, message: str, status_class: str = "status-ready"):
        """Update the status label."""
        status_label = self.query_one("#status-label", Label)

        # Add language and Ollama status
        lang_name = self.languages.get(self.language, self.language)
        ollama_status = "ON" if self.ollama_enabled else "OFF" if OLLAMA_AVAILABLE else "N/A"

        # Add mic info if available
        if self.selected_mic_index is not None and self.available_mics:
            for idx, name in self.available_mics:
                if idx == self.selected_mic_index:
                    short_name = name.split(':')[-1].strip() if ':' in name else name
                    status_text = f"{message} | Lang: {lang_name} | Ollama: {ollama_status} | Mic: {short_name}"
                    break
        else:
            status_text = f"{message} | Lang: {lang_name} | Ollama: {ollama_status}"

        status_label.update(status_text)
        status_label.remove_class("status-ready", "status-listening", "status-error")
        status_label.add_class(status_class)

    def add_transcript(self, text: str, is_error: bool = False):
        """Add a transcript entry to the log."""
        log = self.query_one("#transcript-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if is_error:
            log.write(f"[red][{timestamp}] Error: {text}[/red]")
        else:
            log.write(f"[cyan][{timestamp}][/cyan] [white]{text}[/white]")

    def add_ollama_response(self, text: str, is_error: bool = False):
        """Add an Ollama response to the log."""
        log = self.query_one("#ollama-log", RichLog)
        timestamp = datetime.now().strftime("%H:%M:%S")

        if is_error:
            log.write(f"[red][{timestamp}] Error: {text}[/red]")
        else:
            log.write(f"[green][{timestamp}][/green] [white]{text}[/white]")

    def simulate_audio_level(self, duration: float = 2.0):
        """Simulate audio level animation during listening."""
        import random
        import time

        start_time = time.time()
        while time.time() - start_time < duration and self.is_listening:
            # Random audio level simulation (0-20)
            level = random.randint(5, 20)
            self.post_message(UpdateAudioLevel(level))
            time.sleep(0.1)  # Update every 100ms

        # Reset to 0 when done
        self.post_message(UpdateAudioLevel(0))

    def process_with_ollama(self, user_text: str):
        """Process user speech with Ollama in a separate thread."""
        if not OLLAMA_AVAILABLE:
            self.post_message(UpdateLog("ollama", "Ollama not available", True))
            return
            
        def ollama_worker():
            try:
                self.post_message(UpdateStatus("Thinking...", "status-listening"))

                # Add user message to history
                self.conversation_history.append({
                    "role": "user",
                    "content": user_text
                })

                # Limit history, but preserve system prompt if it exists
                history_limit = 10 
                if len(self.conversation_history) > history_limit:
                    if self.conversation_history[0].get("role") == "system":
                        self.conversation_history = [self.conversation_history[0]] + self.conversation_history[-(history_limit - 1):]
                    else:
                        self.conversation_history = self.conversation_history[-history_limit:]
                
                # Prepare Ollama options
                options = {}
                if "temperature" in self.llm_config:
                    options["temperature"] = self.llm_config["temperature"]
                if "max_tokens" in self.llm_config:
                    options["num_predict"] = self.llm_config["max_tokens"]

                # Call Ollama
                response = ollama.chat(
                    model=self.ollama_model,
                    messages=self.conversation_history,
                    options=options if options else None,
                )

                assistant_message = response['message']['content']

                # Add response to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": assistant_message
                })

                # Display response
                self.post_message(UpdateLog("ollama", assistant_message))

                self.post_message(UpdateStatus("Ready", "status-ready"))

            except Exception as e:
                self.post_message(UpdateLog("ollama", f"Error: {str(e)}", True))
                self.post_message(UpdateStatus("Ready", "status-ready"))

        threading.Thread(target=ollama_worker, daemon=True).start()

    def start_continuous_listening(self):
        """Start continuous listening in a separate thread."""
        if self.microphone_error:
            self.add_transcript("Cannot listen: Microphone error", is_error=True)
            self.stop_continuous_listening()
            return

        if self.listening_thread and self.listening_thread.is_alive():
            return  # Already listening

        self.listening_thread = threading.Thread(target=self.continuous_listening_loop, daemon=True)
        self.listening_thread.start()

    def continuous_listening_loop(self):
        """Continuously listen while L key is held."""
        self.add_transcript("Hold L to listen, release to stop")

        while self.continuous_mode:
            try:
                self.listen_once_blocking()

                # Small pause between recognitions
                if self.continuous_mode:
                    import time
                    time.sleep(0.3)
            except Exception as e:
                self.post_message(UpdateLog("transcript", f"Continuous mode error: {str(e)}", True))
                break

        self.stop_continuous_listening()

    def listen_once_blocking(self):
        """Listen for speech once with Anaconda-optimized error handling."""
        if not self.microphone:
            self.post_message(UpdateLog("transcript", "Microphone not initialized", True))
            return

        if not self.mic_lock.acquire(blocking=False):
            self.post_message(UpdateLog("transcript", "Microphone busy", True))
            return

        # Suppress ALSA errors during recording
        old_stderr = sys.stderr
        sys.stderr = SuppressStream()

        try:
            self.is_listening = True
            self.post_message(UpdateStatus("Listening...", "status-listening"))
            self.post_message(UpdateAudioLevel(0))

            # Start audio level animation in background
            animation_thread = threading.Thread(target=self.simulate_audio_level, args=(3.0,), daemon=True)
            animation_thread.start()

            with self.microphone as source:
                # Adjust for noise with shorter duration
                self.recognizer.adjust_for_ambient_noise(source, duration=0.3)

                # Listen with reasonable timeout
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=60)

            self.is_listening = False
            self.post_message(UpdateAudioLevel(0))
            self.post_message(UpdateStatus("Recognizing...", "status-listening"))

            try:
                # Try recognition
                text = self.recognizer.recognize_google(audio, language=self.language)
                self.post_message(UpdateLog("transcript", text))

                # Process with Ollama if enabled
                if self.ollama_enabled:
                    self.process_with_ollama(text)
                else:
                    self.post_message(UpdateStatus("Ready", "status-ready"))
                    
            except sr.UnknownValueError:
                self.post_message(UpdateLog("transcript", "Tidak dapat memahami audio", True))
                if self.debug_mode:
                    self.post_message(UpdateLog("transcript", 
                        f"Debug: Audio length={len(audio.frame_data)} bytes", False))
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"unrecognized_audio_{timestamp}.wav"
                        with open(filename, "wb") as f:
                            f.write(audio.get_wav_data())
                        self.post_message(UpdateLog("transcript", 
                            f"Debug: Unrecognized audio saved to '{filename}'", False))
                    except Exception as e:
                        self.post_message(UpdateLog("transcript", 
                            f"Debug: Failed to save audio file: {e}", True))
                self.post_message(UpdateStatus("Ready", "status-ready"))
                
            except sr.RequestError as e:
                self.post_message(UpdateLog("transcript", f"API error: {str(e)}", True))
                self.post_message(UpdateStatus("Ready", "status-ready"))

        except sr.WaitTimeoutError:
            self.is_listening = False
            self.post_message(UpdateAudioLevel(0))
            self.post_message(UpdateLog("transcript", "Timeout - no speech detected", True))
            self.post_message(UpdateStatus("Ready", "status-ready"))

        except Exception as e:
            self.is_listening = False
            self.post_message(UpdateAudioLevel(0))
            self.post_message(UpdateLog("transcript", f"Error: {str(e)}", True))
            self.post_message(UpdateStatus("Ready", "status-ready"))

        finally:
            self.is_listening = False
            sys.stderr = old_stderr
            self.mic_lock.release()



    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "btn-listen":
            self.action_listen_once()
        elif button_id == "btn-clear":
            self.action_clear()
        elif button_id == "btn-ollama":
            self.action_toggle_ollama()
        elif button_id == "btn-lang":
            self.action_toggle_language()
        elif button_id == "btn-mic":
            self.action_cycle_microphone()

    def action_listen_once(self):
        """Listen for speech once."""
        if self.microphone_error:
            self.add_transcript("Cannot listen: Microphone error", is_error=True)
            return

        threading.Thread(target=self.listen_once_blocking, daemon=True).start()

    def action_clear(self):
        """Clear logs."""
        transcript_log = self.query_one("#transcript-log", RichLog)
        ollama_log = self.query_one("#ollama-log", RichLog)
        transcript_log.clear()
        ollama_log.clear()
        
        # Reset conversation history, keeping system prompt if it exists
        if self.llm_config and self.llm_config.get("system_prompt"):
            self.conversation_history = [{
                "role": "system",
                "content": self.llm_config["system_prompt"]
            }]
        else:
            self.conversation_history = []

        self.add_transcript("Logs cleared")

    def action_toggle_ollama(self):
        """Toggle Ollama on/off."""
        if not OLLAMA_AVAILABLE:
            self.add_transcript("Ollama not installed", is_error=True)
            return

        self.ollama_enabled = not self.ollama_enabled
        btn = self.query_one("#btn-ollama", Button)

        if self.ollama_enabled:
            btn.variant = "success"
            self.add_transcript("Ollama enabled")
        else:
            btn.variant = "warning"
            self.add_transcript("Ollama disabled")

        self.update_status("Ready", "status-ready")

    def action_toggle_language(self):
        """Toggle between Indonesian and English."""
        # Switch language
        if self.language == "id-ID":
            self.language = "en-US"
            lang_code = "EN"
            lang_name = "English"
        else:
            self.language = "id-ID"
            lang_code = "ID"
            lang_name = "Indonesian"

        # Update button
        btn = self.query_one("#btn-lang", Button)
        btn.label = f"Lang: {lang_code} [G]"

        self.add_transcript(f"Language changed to {lang_name}")
        self.update_status("Ready", "status-ready")


    def action_cycle_microphone(self):
        """Cycle through available microphones."""
        if not self.available_mics:
            self.add_transcript("No microphones available to cycle", is_error=True)
            return
        
        # Find current index
        current_pos = 0
        for i, (idx, _) in enumerate(self.available_mics):
            if idx == self.selected_mic_index:
                current_pos = i
                break
        
        # Move to next microphone
        next_pos = (current_pos + 1) % len(self.available_mics)
        next_idx, next_name = self.available_mics[next_pos]
        
        short_name = next_name.split(':')[-1].strip() if ':' in next_name else next_name
        self.add_transcript(f"Switching to: {short_name}")
        
        if self.initialize_microphone(next_idx):
            self.add_transcript(f"✓ Now using: {short_name}")
            self.update_status("Ready", "status-ready")
            self.microphone_error = None
        else:
            self.add_transcript(f"✗ Failed to initialize: {short_name}", is_error=True)

    def action_toggle_debug(self):
        """Toggle debug mode."""
        self.debug_mode = not self.debug_mode
        self.add_transcript(f"Debug mode: {'ON' if self.debug_mode else 'OFF'}")

    def action_quit(self):
        """Quit the application."""
        self.continuous_mode = False
        self.exit()


def main():
    """Run the speech recognition app."""
    print("Starting Speech Recognition App (Anaconda Edition)...")
    print("Suppressing ALSA warnings...")
    
    # Run the app
    app = SpeechRecognitionApp()
    app.run()


if __name__ == "__main__":
    main()
