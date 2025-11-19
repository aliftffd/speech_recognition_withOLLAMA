#!/usr/bin/env python
"""
Audio Diagnostic Tool for Anaconda Environments
Tests microphone setup and speech recognition capabilities
"""

import sys
import os
import platform
import subprocess

def print_header(text):
    print("\n" + "="*50)
    print(f" {text}")
    print("="*50)

def check_environment():
    """Check if running in conda environment"""
    print_header("Environment Check")
    
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    
    # Check if in conda environment
    conda_env = os.environ.get('CONDA_DEFAULT_ENV', 'Not in conda environment')
    print(f"Conda environment: {conda_env}")
    
    if 'conda' in sys.executable or 'anaconda' in sys.executable.lower():
        print("✓ Running in Anaconda/Conda environment")
    else:
        print("⚠ Not running in Anaconda environment")
        print("  Run: conda activate speech_recognition_env")
    
    return 'conda' in sys.executable or 'anaconda' in sys.executable.lower()

def check_packages():
    """Check if required packages are installed"""
    print_header("Package Check")
    
    packages = {
        'pyaudio': 'PyAudio',
        'speech_recognition': 'SpeechRecognition',
        'textual': 'Textual',
        'ollama': 'Ollama (optional)'
    }
    
    missing = []
    
    for module, name in packages.items():
        try:
            __import__(module)
            print(f"✓ {name} installed")
        except ImportError:
            print(f"✗ {name} NOT installed")
            missing.append(module)
    
    if missing:
        print(f"\nInstall missing packages:")
        for pkg in missing:
            if pkg == 'pyaudio':
                print(f"  conda install -c conda-forge {pkg}")
            else:
                print(f"  pip install {pkg}")
    
    return len(missing) == 0

def check_microphone():
    """Check microphone availability"""
    print_header("Microphone Check")
    
    try:
        import speech_recognition as sr
        
        # List all microphones
        mic_list = sr.Microphone.list_microphone_names()
        
        if not mic_list:
            print("✗ No microphones detected!")
            print("\nTroubleshooting:")
            print("  1. Check if microphone is connected")
            print("  2. Check system audio settings")
            print("  3. On Linux: sudo usermod -a -G audio $USER")
            return False
        
        print(f"✓ Found {len(mic_list)} microphone(s):\n")
        for i, name in enumerate(mic_list):
            print(f"  [{i}] {name}")
            if 'default' in name.lower():
                print(f"      ^ This is likely your default microphone")
        
        # Test microphone initialization
        print("\nTesting microphone initialization...")
        try:
            # Try different sample rates
            sample_rates = [16000, 44100, 48000]
            working_rate = None
            
            for rate in sample_rates:
                try:
                    mic = sr.Microphone(sample_rate=rate)
                    with mic as source:
                        r = sr.Recognizer()
                        r.adjust_for_ambient_noise(source, duration=0.1)
                    working_rate = rate
                    break
                except:
                    continue
            
            if working_rate:
                print(f"✓ Microphone works with sample rate: {working_rate} Hz")
                return True
            else:
                print("✗ Could not initialize microphone with any sample rate")
                return False
                
        except Exception as e:
            print(f"✗ Microphone initialization failed: {str(e)}")
            return False
            
    except ImportError:
        print("✗ speech_recognition not installed")
        print("  Run: pip install SpeechRecognition")
        return False

def test_speech_recognition():
    """Test actual speech recognition"""
    print_header("Speech Recognition Test")
    
    try:
        import speech_recognition as sr
        
        r = sr.Recognizer()
        
        # Ask user if they want to test
        response = input("\nDo you want to test speech recognition? (y/n): ").lower()
        if response != 'y':
            print("Skipping speech recognition test")
            return
        
        print("\nPreparing to listen...")
        print("When you see 'Listening...', speak clearly into your microphone")
        print("The test will listen for 5 seconds maximum")
        
        try:
            with sr.Microphone() as source:
                print("\nAdjusting for ambient noise...")
                r.adjust_for_ambient_noise(source, duration=1)
                
                print("LISTENING... Speak now!")
                audio = r.listen(source, timeout=5, phrase_time_limit=5)
                
                print("Processing speech...")
                
                # Try multiple recognition engines
                try:
                    text = r.recognize_google(audio)
                    print(f"✓ Google Speech Recognition heard: '{text}'")
                except sr.UnknownValueError:
                    print("✗ Could not understand audio")
                except sr.RequestError as e:
                    print(f"✗ Google API error: {e}")
                
        except sr.WaitTimeoutError:
            print("✗ No speech detected within timeout period")
        except Exception as e:
            print(f"✗ Error during recording: {str(e)}")
            
    except ImportError:
        print("✗ speech_recognition not installed")

def check_ollama():
    """Check if Ollama is available"""
    print_header("Ollama Check (Optional)")
    
    # Check if ollama module is installed
    try:
        import ollama
        print("✓ Ollama Python module installed")
        
        # Check if Ollama service is running
        try:
            models = ollama.list()
            print(f"✓ Ollama service is running")
            if models['models']:
                print(f"  Available models:")
                for model in models['models']:
                    print(f"    - {model['name']}")
            else:
                print("  No models installed. Run: ollama pull qwen2.5:3b")
        except:
            print("✗ Ollama service not running")
            print("  Start with: ollama serve")
            
    except ImportError:
        print("ℹ Ollama not installed (optional)")
        print("  Install with: pip install ollama")

def system_audio_check():
    """Check system audio configuration"""
    print_header("System Audio Configuration")
    
    system = platform.system()
    
    if system == "Linux":
        # Check ALSA
        try:
            result = subprocess.run(['arecord', '-l'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=2)
            if result.returncode == 0:
                print("✓ ALSA audio system working")
                print("\nRecording devices:")
                print(result.stdout)
            else:
                print("✗ ALSA issue detected")
        except:
            print("⚠ Could not check ALSA status")
            
        # Check PulseAudio
        try:
            result = subprocess.run(['pactl', 'info'], 
                                  capture_output=True, 
                                  text=True,
                                  timeout=2)
            if result.returncode == 0:
                print("✓ PulseAudio is running")
            else:
                print("⚠ PulseAudio may not be running")
        except:
            pass
            
    elif system == "Darwin":  # macOS
        print("macOS audio system")
        print("If microphone isn't working:")
        print("  1. System Preferences > Security & Privacy > Microphone")
        print("  2. Allow Terminal/Python access to microphone")
        
    elif system == "Windows":
        print("Windows audio system")
        print("If microphone isn't working:")
        print("  1. Settings > Privacy > Microphone")
        print("  2. Allow apps to access microphone")

def generate_report():
    """Generate a summary report"""
    print_header("Diagnostic Summary")
    
    all_good = True
    
    # Check each component
    in_conda = check_environment()
    if not in_conda:
        print("\n⚠ Not in conda environment - some features may not work")
        all_good = False
    
    has_packages = check_packages()
    if not has_packages:
        all_good = False
    
    has_mic = check_microphone()
    if not has_mic:
        all_good = False
    
    check_ollama()
    system_audio_check()
    
    if all_good:
        print("\n✓✓✓ System is ready for speech recognition! ✓✓✓")
        test_speech_recognition()
    else:
        print("\n⚠ Please fix the issues above before running the main app")
    
    print("\n" + "="*50)
    print(" Diagnostic Complete")
    print("="*50)

if __name__ == "__main__":
    print("\nSpeech Recognition Diagnostic Tool for Anaconda")
    print("This will check your system configuration")
    
    generate_report()
    
    print("\nTo run the main app:")
    print("  python speech_recognition_fixed.py")
