"""
Audio processor module for Audio Transcriber
Handles WhisperX integration and audio file processing
"""

import subprocess
import json
import os
import psutil
import tempfile
import shutil
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any


class AudioProcessor:
    """Handles audio processing using WhisperX command line tool"""

    def __init__(self, config: dict, logger):
        """
        Initialize audio processor with configuration

        Args:
            config: Configuration dictionary
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.whisperx_config = config.get('whisperx', {})
        self.output_dir = Path(config['output_directory'])

        # Check if WhisperX is available
        self._check_whisperx_available()

    def _check_whisperx_available(self) -> None:
        """Check if WhisperX command is available"""
        # Check ffmpeg availability first
        self._check_ffmpeg_available()

        try:
            result = subprocess.run(
                [sys.executable, '-m', 'whisperx', '--help'],
                capture_output=True,
                text=True,
                timeout=30  # Increased timeout for WhisperX help command
            )
            if result.returncode != 0:
                raise Exception(f"WhisperX module failed. Output: {result.stdout}\nError: {result.stderr}")

        except subprocess.TimeoutExpired:
            # WhisperX help can be slow, let's try a simpler check
            self.logger.warning("WhisperX --help timed out, trying alternative check", "AudioProcessor")
            try:
                result = subprocess.run(
                    [sys.executable, '-c', 'import whisperx; print("WhisperX available")'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode != 0:
                    raise Exception(f"WhisperX import failed: {result.stderr}")
                self.logger.info("WhisperX is available (confirmed via import)", "AudioProcessor")
            except Exception as e:
                raise Exception(f"WhisperX check failed: {e}")
        except FileNotFoundError:
            raise Exception("Python not found in PATH")
        except Exception as e:
            raise Exception(f"WhisperX check failed: {e}")

    def _check_ffmpeg_available(self) -> None:
        """Check if ffmpeg command is available"""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed. Error: {result.stderr}")
        except subprocess.TimeoutExpired:
            raise Exception("FFmpeg command timed out")
        except FileNotFoundError:
            raise Exception("FFmpeg not found in PATH. Please install ffmpeg and add it to PATH.")
        except Exception as e:
            raise Exception(f"FFmpeg check failed: {e}")

    def _check_whisperx_processes(self) -> bool:
        """
        Check if any WhisperX processes are currently running

        Returns:
            True if WhisperX processes found
        """
        try:
            for process in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if process.info['cmdline']:
                        cmdline = ' '.join(process.info['cmdline']).lower()
                        # Check for both direct whisperx and python -m whisperx
                        if ('whisperx' in cmdline and 'python' in cmdline) or 'whisperx' in cmdline:
                            self.logger.warning("WhisperX process already running", "AudioProcessor")
                            return True

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

        except Exception as e:
            self.logger.warning(f"Could not check running processes: {e}", "AudioProcessor")

        return False

    def process_audio_file(self, audio_file: Path, processing_time: str = "неизвестно") -> bool:
        """
        Process audio file using WhisperX

        Args:
            audio_file: Path to audio file to process
            processing_time: Time taken to process the file

        Returns:
            True if processing successful
        """
        # Check if WhisperX is already running
        if self._check_whisperx_processes():
            self.logger.error("WhisperX is already running. Please wait for it to finish.", "AudioProcessor")
            return False

        # Check if audio file exists and is not empty
        if not audio_file.exists():
            self.logger.error(f"Audio file not found: {audio_file}", "AudioProcessor")
            return False

        if audio_file.stat().st_size == 0:
            self.logger.error(f"Audio file is empty: {audio_file}", "AudioProcessor")
            return False

        self.logger.info(f"Starting WhisperX processing for: {audio_file.name}", "AudioProcessor")

        # Create temporary directory for WhisperX output
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Run WhisperX
                success = self._run_whisperx(audio_file, temp_path)

                if success:
                    # Parse results and create output file
                    return self._process_whisperx_results(audio_file, temp_path, processing_time)
                else:
                    return False

            except Exception as e:
                self.logger.error(f"Error processing {audio_file.name}: {e}", "AudioProcessor")
                return False

    def _run_whisperx(self, audio_file: Path, temp_dir: Path) -> bool:
        """
        Run WhisperX command line tool

        Args:
            audio_file: Path to audio file
            temp_dir: Temporary directory for output

        Returns:
            True if WhisperX completed successfully
        """
        model_size = self.whisperx_config.get('model_size', 'medium')
        language = self.whisperx_config.get('language', 'ru')
        temperature = self.whisperx_config.get('temperature', 0.98)
        compute_type = self.whisperx_config.get('compute_type', 'float32')
        device = self.whisperx_config.get('device', 'cpu')

        # Build WhisperX command
        cmd = [
            sys.executable, '-m', 'whisperx',
            str(audio_file),
            '--model', model_size,
            '--language', language,
            '--temperature', str(temperature),
            '--compute_type', compute_type,
            '--device', device,
            '--output_dir', str(temp_dir),
            '--output_format', 'json'
        ]

        self.logger.info(f"Running WhisperX command: {' '.join(cmd)}", "AudioProcessor")

        # Set environment variables for proper encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

        try:
            # Run WhisperX with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600,  # 1 hour timeout
                env=env
            )

            if result.returncode == 0:
                self.logger.info(f"WhisperX completed successfully for {audio_file.name}", "AudioProcessor")
                return True
            else:
                self.logger.error(f"WhisperX failed with code {result.returncode}: {result.stderr}", "AudioProcessor")
                return False

        except subprocess.TimeoutExpired:
            self.logger.error(f"WhisperX timed out for {audio_file.name}", "AudioProcessor")
            return False
        except Exception as e:
            self.logger.error(f"WhisperX execution failed: {e}", "AudioProcessor")
            return False

    def _process_whisperx_results(self, audio_file: Path, temp_dir: Path, processing_time: str = "неизвестно") -> bool:
        """
        Process WhisperX JSON results and create final text file

        Args:
            audio_file: Original audio file
            temp_dir: Directory containing WhisperX results
            processing_time: Time taken to process the file

        Returns:
            True if processing successful
        """
        # Find JSON result file
        json_files = list(temp_dir.glob("*.json"))

        if not json_files:
            self.logger.error(f"No JSON results found for {audio_file.name}", "AudioProcessor")
            return False

        json_file = json_files[0]

        try:
            # Load JSON results
            with open(json_file, 'r', encoding='utf-8') as f:
                results = json.load(f)

            # Validate JSON structure
            if not self._validate_whisperx_json(results):
                self.logger.error(f"Invalid WhisperX JSON format for {audio_file.name}", "AudioProcessor")
                return False

            # Create formatted text file
            output_file = self.output_dir / f"{audio_file.stem}.txt"
            self._create_text_output(audio_file, results, output_file, processing_time)

            self.logger.info(f"Created text output: {output_file.name}", "AudioProcessor")
            return True

        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON from WhisperX: {e}", "AudioProcessor")
            return False
        except Exception as e:
            self.logger.error(f"Error processing WhisperX results: {e}", "AudioProcessor")
            return False

    def _validate_whisperx_json(self, data: Dict[Any, Any]) -> bool:
        """
        Validate WhisperX JSON output structure

        Args:
            data: Parsed JSON data

        Returns:
            True if valid structure
        """
        try:
            if 'segments' not in data:
                return False

            segments = data['segments']
            if not isinstance(segments, list):
                return False

            # Check first few segments have required fields
            for segment in segments[:3]:  # Check first 3 segments
                if not isinstance(segment, dict):
                    return False
                if 'start' not in segment or 'end' not in segment or 'text' not in segment:
                    return False

            return True

        except Exception:
            return False

    def _create_text_output(self, audio_file: Path, results: Dict[Any, Any], output_file: Path, processing_time: str = "неизвестно") -> None:
        """
        Create formatted text output file

        Args:
            audio_file: Original audio file
            results: WhisperX JSON results
            output_file: Output text file path
            processing_time: Time taken to process the file
        """
        # Calculate duration
        segments = results.get('segments', [])
        duration = 0
        if segments:
            last_segment = segments[-1]
            duration = last_segment.get('end', 0)

        duration_str = self._format_duration(duration)
        process_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Create output content
        content = f"""=== РАСШИФРОВКА АУДИОЗАПИСИ ===
Файл: {audio_file.name}
Дата обработки: {process_time}
Продолжительность: {duration_str}
Расшифровка заняла: {processing_time}

=== ТРАНСКРИПЦИЯ ===
"""

        # Add transcription segments
        for segment in segments:
            start_time = self._format_timestamp(segment.get('start', 0))
            text = segment.get('text', '').strip()

            if text:  # Only add non-empty segments
                content += f"[{start_time}] {text}\n"

        # Write output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

    def _format_timestamp(self, seconds: float) -> str:
        """
        Format timestamp from seconds to HH:MM:SS

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        try:
            td = timedelta(seconds=int(seconds))
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception:
            return "00:00:00"

    def _get_processing_time(self, audio_file: Path) -> str:
        """
        Get processing time from .in_process file

        Args:
            audio_file: Original audio file

        Returns:
            Processing time string
        """
        base_name = audio_file.stem
        in_process_file = self.output_dir / f"{base_name}.in_process"

        try:
            if in_process_file.exists():
                with open(in_process_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Find the processing time line
                for line in content.split('\n'):
                    if line.startswith('Processing time:'):
                        # Extract time from "Processing time: 1m 30.5s"
                        time_part = line.split(':', 1)[1].strip()
                        return time_part

            return "неизвестно"

        except Exception as e:
            self.logger.warning(f"Could not read processing time from {in_process_file.name}: {e}", "AudioProcessor")
            return "неизвестно"

    def _format_duration(self, seconds: float) -> str:
        """
        Format duration from seconds to HH:MM:SS

        Args:
            seconds: Duration in seconds

        Returns:
            Formatted duration string
        """
        return self._format_timestamp(seconds)
