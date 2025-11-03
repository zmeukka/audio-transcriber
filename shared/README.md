# Shared Directory

This directory is used for file exchange between the Audio Transcriber Docker container and the host system.

## How it works

1. Place audio files in this directory
2. They will be automatically detected by the file monitor
3. Use API endpoints to process them
4. Results will appear as `.result` files
5. Processing status is tracked in `.in_progress` files

## Supported Audio Formats

- **Audio:** MP3, WAV, FLAC, M4A, OGG, AAC, WMA, OPUS
- **Video:** MP4, AVI, MOV, MKV, WEBM (audio track will be extracted)

## Test File Generation

Use `create_sample_mp3.py` to generate test audio files for development and testing.

## File Status

- `filename.ext` - Original audio file
- `filename.in_progress` - Processing status (JSON)
- `filename.result` - Transcription result (JSON)

## Sample Files

Files containing "sample" in the name are excluded from automatic scanning but can be processed via API requests.
