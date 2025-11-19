# Speech Recognition TUI Application

A modern Text User Interface (TUI) application for real-time speech recognition using Python. Built with the `textual` framework and Google's Speech Recognition API.

## Features

- **Interactive TUI**: Beautiful terminal-based user interface
- **Listen Once Mode**: Capture single voice commands
- **Continuous Listening**: Real-time transcription mode
- **Timestamped Transcripts**: All recognized text is timestamped
- **Keyboard Shortcuts**: Quick access to all features
- **Error Handling**: Graceful handling of recognition errors

## Screenshots

The app features:
- Header with application title
- Control buttons for different modes
- Status indicator showing current state
- Scrollable transcript log with timestamps
- Footer with keyboard shortcuts

## Installation

### 1. System Dependencies

#### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install python3-pyaudio portaudio19-dev
```

#### Fedora/RHEL
```bash
sudo dnf install python3-pyaudio portaudio-devel
```

#### macOS
```bash
brew install portaudio
```

### 2. Python Dependencies

Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Running the Application

```bash
python speech_recognition_app.py
```

### Controls

#### Buttons
- **Listen Once**: Record and transcribe a single phrase
- **Start Continuous**: Begin continuous listening mode
- **Stop**: Stop continuous listening
- **Clear**: Clear the transcript log

#### Keyboard Shortcuts
- `l` - Listen once
- `s` - Toggle continuous listening
- `c` - Clear transcript
- `q` - Quit application

### Features Explained

#### Listen Once Mode
Click "Listen Once" or press `l` to record a single phrase. The app will:
1. Listen for up to 5 seconds
2. Wait for you to speak (up to 10 seconds of speech)
3. Transcribe and display the text

#### Continuous Mode
Click "Start Continuous" or press `s` to enable continuous listening. The app will:
- Continuously listen and transcribe speech
- Display all recognized phrases with timestamps
- Run until you click "Stop" or press `s` again

#### Status Indicators
- **Green (Ready)**: Ready to listen
- **Yellow (Listening)**: Actively listening or processing
- **Red (Error)**: An error occurred

## Requirements

- Python 3.8+
- Working microphone
- Internet connection (for Google Speech Recognition API)

## Troubleshooting

### Microphone Not Detected
```bash
# Test your microphone
arecord -l  # Linux
# or
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

### PyAudio Installation Issues

If you encounter errors installing PyAudio:

**Linux:**
```bash
sudo apt-get install python3-dev
pip install --upgrade pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install --upgrade pyaudio
```

**Windows:**
Download the appropriate wheel from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio) and install:
```bash
pip install PyAudio‑0.2.11‑cp39‑cp39‑win_amd64.whl
```

### Permission Denied Errors
Make the script executable:
```bash
chmod +x speech_recognition_app.py
```

### API Errors
The app uses Google's free Speech Recognition API. If you encounter rate limiting:
- Wait a few moments between requests
- Consider implementing a different recognition engine (options available in SpeechRecognition library)

## Technical Details

### Architecture
- **UI Framework**: Textual (modern TUI framework)
- **Speech Recognition**: SpeechRecognition library with Google Speech Recognition
- **Audio Input**: PyAudio for microphone access
- **Threading**: Background threads for non-blocking audio processing

### How It Works
1. Microphone captures audio using PyAudio
2. Audio is sent to Google's Speech Recognition API
3. Transcribed text is displayed in the TUI with timestamps
4. All operations run asynchronously to keep the UI responsive

## License

MIT License - Feel free to use and modify for your projects

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Future Enhancements

Potential features to add:
- Save transcripts to file
- Support for multiple languages
- Offline recognition options
- Custom wake words
- Voice commands for app control
- Export transcripts in various formats (JSON, TXT, CSV)
