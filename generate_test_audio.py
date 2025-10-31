#!/usr/bin/env python3
"""
Generate test audio file for transcription testing
"""

import numpy as np
import wave
import os
from pathlib import Path

def generate_test_audio():
    """Generate a simple test audio file"""

    # Audio parameters
    sample_rate = 16000  # 16kHz for speech
    duration = 2.0  # 2 seconds
    frequency = 440  # A4 note

    # Generate sine wave
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t)

    # Convert to 16-bit integers
    audio_data = (audio_data * 32767).astype(np.int16)

    # Create input directory if it doesn't exist
    input_dir = Path("input")
    input_dir.mkdir(exist_ok=True)

    # Save as WAV file
    output_file = input_dir / "sample.wav"

    with wave.open(str(output_file), 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes per sample
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())

    print(f"Test audio file created: {output_file}")
    print(f"Duration: {duration} seconds")
    print(f"Sample rate: {sample_rate} Hz")

if __name__ == "__main__":
    try:
        generate_test_audio()
    except ImportError:
        print("NumPy not installed. Installing...")
        import subprocess
        subprocess.run(["pip", "install", "numpy"], check=True)
        generate_test_audio()
