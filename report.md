# Report: Speech Recognition + Ollama AI TUI

## 1. Project Overview

This project is a Terminal User Interface (TUI) application built with Python and the Textual framework. It provides a user-friendly interface for real-time speech recognition. The application captures audio from a microphone, transcribes it to text using a speech recognition service, and can optionally forward the transcribed text to a local Ollama Large Language Model (LLM) to generate conversational responses.

The application is specifically designed with optimizations for Linux-based Anaconda environments, incorporating several workarounds for common issues related to ALSA audio drivers.

## 2. Key Features

- **Real-time Speech-to-Text:** Listens for voice input and transcribes it into text.
- **Ollama Integration:** Connects to a local Ollama instance to function as a conversational AI. The AI's persona, model, and other parameters are configurable.
- **Rich TUI:** A clean, organized terminal interface that separates user speech (transcript) from AI responses.
- **Anaconda Audio Fixes:** Includes specific workarounds to suppress ALSA warnings and errors that are common in Conda environments on Linux.
- **Dynamic Microphone Management:** Automatically detects available microphones and attempts to select the best one. Users can manually cycle through available microphones.
- **External LLM Configuration:** AI behavior is controlled via an external `prompt_llm_SR.json` file, allowing for easy customization without modifying the source code.
- **Debug Mode:** A toggleable debug mode that provides more detailed logs. When recognition fails, it saves the audio clip to a `.wav` file for inspection.

## 3. Dependencies

The application relies on the following core Python libraries:

- `textual`: For building the Terminal User Interface.
- `speech_recognition`: For capturing microphone input and performing speech-to-text.
  - Requires `PyAudio` for microphone access.
- `ollama` (Optional): For connecting to the Ollama LLM.

These can be installed via `pip` or from the provided `environment.yml` / `requirements.txt` files.

## 4. Setup and Usage

### a. Environment Setup

It is recommended to use a virtual environment (like Conda or venv) to manage dependencies.

**Using Conda:**
```bash
# Create a new conda environment
conda create --name speech_app python=3.9

# Activate the environment
conda activate speech_app

# Install dependencies
pip install textual speechrecognition "ollama>=0.2.0" PyAudio
```

### b. Running the Application

Once the environment is set up and dependencies are installed, you can run the application using the provided shell script or by directly invoking the Python script.

```bash
# Make the script executable (if needed)
chmod +x run_speech_app.sh

# Run the app
./run_speech_app.sh
```
*Alternatively:*
```bash
python speech_recognition_app.py
```

## 5. Configuration

### a. LLM Configuration (`prompt_llm_SR.json`)

The interaction with the Ollama LLM is controlled by the `prompt_llm_SR.json` file.

```json
{
  "model": "qwen3:8b",
  "temperature": 0.5,
  "max_tokens": 256,
  "system_prompt": "Kamu adalah asisten...",
  "default_language": "id-ID"
}
```
- `model`: The name of the Ollama model to use (e.g., `qwen3:8b`). Make sure you have pulled this model using `ollama pull <model_name>`.
- `temperature`: Controls the creativity of the AI's responses (e.g., `0.5`).
- `max_tokens`: The maximum length of the AI's response.
- `system_prompt`: A description of the AI's persona and instructions on how it should behave. This is crucial for setting the tone and context of the conversation.
- `default_language`: The language code for the speech recognition service (e.g., `id-ID` for Indonesian).

### b. Microphone

The application attempts to find the best available microphone on startup. If you are having issues, you can press the `M` key to cycle through all detected microphones.

## 6. Key Bindings

The application uses the following keyboard shortcuts:

| Key | Action               | Description                                           |
|-----|----------------------|-------------------------------------------------------|
| `L` | Listen Once          | Starts a single recording session.                    |
| `C` | Clear                | Clears the transcript and Ollama response logs.       |
| `M` | Cycle Microphone     | Switches to the next available microphone.            |
| `D` | Toggle Debug Mode    | Toggles verbose logging for troubleshooting.          |
| `Q` | Quit                 | Exits the application.                                |

## 7. Troubleshooting

- **Microphone Not Working:** The application includes several fixes for audio issues on Linux. If you have problems, first try cycling the microphone with the `M` key. Ensure your system's microphone is not muted and is correctly configured.
- **"Tidak dapat memahami audio" Error:** This means the speech recognition service could not understand the audio it received.
  - **Solution:** Activate Debug Mode (`D` key) and try again. The app will save the unrecognized audio as a `.wav` file. Listen to this file to check for issues like low volume, excessive noise, or silence.
- **Ollama Errors:** Ensure the Ollama service is running on your local machine. Verify that the model specified in `prompt_llm_SR.json` has been downloaded with `ollama pull <model_name>`.
