#!/bin/bash

# Fix ALSA issues for Anaconda Speech Recognition
echo "========================================="
echo "ALSA Audio Fix for Anaconda Environment"
echo "========================================="

# Check if we're in a conda environment
if [ -z "$CONDA_DEFAULT_ENV" ]; then
  echo "⚠ Not in a conda environment!"
  echo "Please run: conda activate speech_recognition_env"
  exit 1
fi

echo "Current environment: $CONDA_DEFAULT_ENV"
echo ""

# Function to check command existence
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# 1. Create ALSA config to bypass problematic configurations
echo "1. Creating ALSA configuration override..."
mkdir -p ~/.config/alsa
cat >~/.config/alsa/asoundrc <<'EOF'
# Minimal ALSA configuration for conda environments
# This bypasses the pipewire errors

pcm.!default {
    type hw
    card 1  # Use card 1 (ALC294 Analog)
}

ctl.!default {
    type hw
    card 1
}
EOF

echo "   ✓ Created ~/.config/alsa/asoundrc"

# 2. Set environment variables
echo ""
echo "2. Setting environment variables..."
cat >~/anaconda_audio_env.sh <<'EOF'
# Environment variables for better audio in Anaconda
export ALSA_CARD=Generic_1
export SDL_AUDIODRIVER=alsa
export AUDIODEV=hw:1,0

# Suppress ALSA warnings
export PYTHONWARNINGS="ignore"

# For conda environments
export LD_LIBRARY_PATH=$CONDA_PREFIX/lib:$LD_LIBRARY_PATH
EOF

echo "   ✓ Created ~/anaconda_audio_env.sh"
echo "   Run: source ~/anaconda_audio_env.sh"

# 3. Test microphone access
echo ""
echo "3. Testing microphone access..."

# Check if arecord is available
if command_exists arecord; then
  echo "   Available recording devices:"
  arecord -l | grep -E "card [0-9]" | while read line; do
    echo "   - $line"
  done
else
  echo "   ⚠ arecord not found - installing alsa-utils recommended"
  echo "   Run: sudo apt-get install alsa-utils"
fi

# 4. Test Python audio
echo ""
echo "4. Testing Python audio access..."
python <<'PYTHON_EOF'
import warnings
warnings.filterwarnings("ignore")

import os
os.environ['PYTHONWARNINGS'] = 'ignore'

# Suppress stderr temporarily
import sys
from io import StringIO
old_stderr = sys.stderr
sys.stderr = StringIO()

try:
    import speech_recognition as sr
    
    # List microphones
    mic_list = sr.Microphone.list_microphone_names()
    
    # Restore stderr
    sys.stderr = old_stderr
    
    print("   ✓ Python can access audio devices")
    print(f"   Found {len(mic_list)} microphone(s)")
    
    # Find ALC294
    for i, name in enumerate(mic_list):
        if 'ALC294' in name or 'Analog' in name:
            print(f"   ✓ Target microphone found at index {i}: {name}")
            break
    
except ImportError:
    sys.stderr = old_stderr
    print("   ✗ speech_recognition not installed")
    print("   Run: pip install SpeechRecognition")
except Exception as e:
    sys.stderr = old_stderr
    print(f"   ✗ Error: {str(e)}")
PYTHON_EOF

# 5. Create test recording script
echo ""
echo "5. Creating test recording script..."
cat >~/test_recording.py <<'PYTHON_EOF'
#!/usr/bin/env python
"""Quick microphone test for Anaconda environments"""

import warnings
warnings.filterwarnings("ignore")

import os
os.environ['PYTHONWARNINGS'] = 'ignore'
os.environ['ALSA_CARD'] = 'Generic_1'

# Suppress ALSA errors
import sys
from io import StringIO

class SuppressStream:
    def write(self, data):
        if not any(x in str(data) for x in ['ALSA', 'alsa', 'pcm']):
            sys.__stderr__.write(data)
    def flush(self):
        pass

sys.stderr = SuppressStream()

try:
    import speech_recognition as sr
    
    print("Testing microphone recording...")
    print("Please speak after you see 'LISTENING'")
    print("-" * 40)
    
    r = sr.Recognizer()
    
    # Find the right microphone
    mic_list = sr.Microphone.list_microphone_names()
    mic_index = None
    
    for i, name in enumerate(mic_list):
        if 'ALC294' in name or ('Analog' in name and 'HDMI' not in name):
            mic_index = i
            print(f"Using microphone: {name}")
            break
    
    if mic_index is None and mic_list:
        mic_index = 1  # Fallback to index 1
        print(f"Using fallback microphone: {mic_list[mic_index]}")
    
    # Initialize microphone
    mic = sr.Microphone(device_index=mic_index, sample_rate=44100)
    
    with mic as source:
        print("Adjusting for ambient noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        print("LISTENING - Speak now!")
        audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
    print("Processing...")
    
    try:
        text = r.recognize_google(audio, language="id-ID")
        print(f"✓ SUCCESS! You said: '{text}'")
    except sr.UnknownValueError:
        print("✗ Could not understand audio")
        print("Tips:")
        print("  - Speak louder and clearer")
        print("  - Check if microphone is not muted")
        print("  - Try: alsamixer (and press F6 to select sound card)")
    except sr.RequestError as e:
        print(f"✗ API Error: {e}")
        print("Check your internet connection")
        
except ImportError:
    print("✗ Missing dependencies")
    print("Run: pip install SpeechRecognition pyaudio")
except Exception as e:
    print(f"✗ Error: {e}")
PYTHON_EOF

chmod +x ~/test_recording.py
echo "   ✓ Created ~/test_recording.py"

# 6. Provide recommendations
echo ""
echo "========================================="
echo "Setup Complete! Next Steps:"
echo "========================================="
echo ""
echo "1. Source the environment variables:"
echo "   source ~/anaconda_audio_env.sh"
echo ""
echo "2. Test microphone recording:"
echo "   python ~/test_recording.py"
echo ""
echo "3. If audio still doesn't work:"
echo "   a) Check microphone volume:"
echo "      alsamixer"
echo "      (Press F6, select your card, adjust levels)"
echo ""
echo "   b) Test with system tools:"
echo "      arecord -d 5 -f cd test.wav"
echo "      aplay test.wav"
echo ""
echo "   c) Restart PulseAudio (if using):"
echo "      pulseaudio --kill && pulseaudio --start"
echo ""
echo "4. Run the main application:"
echo "   python speech_recognition_anaconda.py"
echo ""
echo "========================================="
echo "Common Issues:"
echo "========================================="
echo ""
echo "• ALSA warnings: Now suppressed, safe to ignore"
echo "• No audio captured: Check mic volume in alsamixer"
echo "• Wrong microphone: Press 'M' in app to cycle mics"
echo "• API errors: Check internet connection"
echo ""

# Check if ollama is running
if command_exists ollama; then
  if pgrep -x "ollama" >/dev/null; then
    echo "✓ Ollama is running"
  else
    echo "ℹ Ollama installed but not running"
    echo "  Start with: ollama serve"
  fi
else
  echo "ℹ Ollama not installed (optional)"
fi
