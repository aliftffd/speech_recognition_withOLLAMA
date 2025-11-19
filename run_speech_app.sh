#!/bin/bash

# Script to run speech recognition app with ALSA warnings suppressed

# Redirect ALSA errors to /dev/null
export ALSA_CARD=Generic
export ALSA_PCM_CARD=Generic

# Run the application with stderr filtered to remove ALSA warnings
python speech_recognition_app.py 2>&1 | grep -v "ALSA lib"
