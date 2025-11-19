#!/usr/bin/env python3
"""
Test script to verify speech recognition setup
"""

import sys


def test_imports():
    """Test if all required modules can be imported."""
    print("Testing imports...")

    try:
        import speech_recognition as sr
        print("✓ SpeechRecognition imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import SpeechRecognition: {e}")
        return False

    try:
        import textual
        print("✓ Textual imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import Textual: {e}")
        return False

    try:
        import pyaudio
        print("✓ PyAudio imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PyAudio: {e}")
        print("  Note: PyAudio requires system dependencies. See README.md")
        return False

    return True


def test_microphone():
    """Test if microphone is available."""
    print("\nTesting microphone...")

    try:
        import speech_recognition as sr

        # List available microphones
        mics = sr.Microphone.list_microphone_names()
        print(f"✓ Found {len(mics)} microphone(s):")
        for i, mic in enumerate(mics):
            print(f"  {i}: {mic}")

        # Try to initialize default microphone
        mic = sr.Microphone()
        print("✓ Default microphone initialized successfully")
        return True

    except Exception as e:
        print(f"✗ Microphone test failed: {e}")
        return False


def test_recognizer():
    """Test if speech recognizer can be initialized."""
    print("\nTesting speech recognizer...")

    try:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        print("✓ Speech recognizer initialized successfully")

        # Test ambient noise adjustment
        with sr.Microphone() as source:
            print("  Adjusting for ambient noise (1 second)...")
            recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✓ Ambient noise adjustment complete")

        return True

    except Exception as e:
        print(f"✗ Recognizer test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Speech Recognition App - Setup Test")
    print("=" * 50)

    all_passed = True

    if not test_imports():
        all_passed = False
        print("\n⚠ Import test failed. Install dependencies:")
        print("  pip install -r requirements.txt")

    if all_passed and not test_microphone():
        all_passed = False
        print("\n⚠ Microphone test failed. Check your audio setup.")

    if all_passed and not test_recognizer():
        all_passed = False
        print("\n⚠ Recognizer test failed.")

    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! You're ready to run the app:")
        print("  python speech_recognition_app.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("  See README.md for troubleshooting help.")
        sys.exit(1)


if __name__ == "__main__":
    main()
