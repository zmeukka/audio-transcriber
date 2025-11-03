"""
WhisperX Transcriber Integration
Handles subprocess execution of WhisperX with proper error handling and timeouts
"""

import asyncio
import json
import logging
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from api.models import TranscribeRequest, TranscriptionResult, TranscriptionSegment
from core.logger import get_logger


class WhisperXTranscriber:
    """
    Manages WhisperX subprocess execution for audio transcription
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        # Configuration
        self.shared_directory = Path(config.get("shared_directory", "./shared"))
        self.model_directory = Path(config.get("model_directory", "./models"))
        self.temp_directory = Path(config.get("temp_directory", "./temp"))
        self.timeout = config.get("processing_timeout", 600)  # 10 minutes default

        # Ensure directories exist
        self.temp_directory.mkdir(parents=True, exist_ok=True)

    async def check_availability(self) -> bool:
        """
        Check if WhisperX is available and working

        Returns:
            True if WhisperX is available
        """
        try:
            # Run a simple WhisperX command to check availability
            cmd = ["python", "-m", "whisperx", "--help"]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)

            if process.returncode == 0:
                self.logger.info("WhisperX is available and working")
                return True
            else:
                self.logger.error(f"WhisperX check failed: {stderr.decode()}")
                return False

        except asyncio.TimeoutError:
            self.logger.error("WhisperX availability check timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking WhisperX availability: {e}")
            return False

    async def get_available_models(self) -> List[str]:
        """
        Get list of available models

        Returns:
            List of available model names
        """
        models = []

        # Check for local models
        if self.model_directory.exists():
            for model_dir in self.model_directory.iterdir():
                if model_dir.is_dir() and model_dir.name.startswith("faster-whisper-"):
                    model_name = model_dir.name.replace("faster-whisper-", "")
                    models.append(model_name)

        # Add default models
        default_models = ["tiny", "base", "small", "medium", "large"]
        for model in default_models:
            if model not in models:
                models.append(model)

        return sorted(models)

    async def transcribe_file(
        self,
        filename: str,
        request: Optional[TranscribeRequest] = None
    ) -> TranscriptionResult:
        """
        Transcribe an audio file using WhisperX

        Args:
            filename: Name of the audio file
            request: Transcription request parameters

        Returns:
            Transcription result

        Raises:
            FileNotFoundError: If audio file doesn't exist
            subprocess.TimeoutExpired: If processing times out
            subprocess.CalledProcessError: If WhisperX fails
        """
        start_time = datetime.now()

        # Default request if none provided
        if request is None:
            from api.models import WhisperModel, ComputeType, OutputFormat
            request = TranscribeRequest(
                filename=filename,
                model=WhisperModel.SMALL,
                compute_type=ComputeType.FLOAT32,
                output_format=OutputFormat.JSON
            )

        # Validate input file
        input_file = self.shared_directory / filename
        if not input_file.exists():
            raise FileNotFoundError(f"Audio file not found: {input_file}")

        self.logger.info(f"Starting transcription of '{filename}' with model '{request.model}'")

        # Create temporary directory for this transcription
        with tempfile.TemporaryDirectory(dir=self.temp_directory) as temp_dir:
            temp_path = Path(temp_dir)
            output_dir = temp_path / "output"
            output_dir.mkdir(exist_ok=True)

            # Build WhisperX command
            cmd = await self._build_whisperx_command(
                input_file=input_file,
                output_dir=output_dir,
                request=request
            )

            # Execute WhisperX
            result_data = await self._execute_whisperx(cmd, temp_path)

            # Parse and format result
            result = await self._parse_whisperx_output(
                filename=filename,
                output_dir=output_dir,
                request=request,
                raw_data=result_data,
                processing_time=(datetime.now() - start_time).total_seconds()
            )

            self.logger.info(f"Successfully transcribed '{filename}' in {result.processing_time:.2f}s")
            return result

    async def _build_whisperx_command(
        self,
        input_file: Path,
        output_dir: Path,
        request: TranscribeRequest
    ) -> List[str]:
        """
        Build WhisperX command line arguments

        Args:
            input_file: Path to input audio file
            output_dir: Path to output directory
            request: Transcription request parameters

        Returns:
            Command line arguments list
        """
        cmd = [
            "python", "-m", "whisperx",
            str(input_file),
            "--output_dir", str(output_dir),
            "--output_format", request.output_format.value,
            "--model", request.model.value,
            "--compute_type", request.compute_type.value,
            "--device", "cpu",  # Force CPU for now
            "--batch_size", "16"
        ]

        # Add language if specified
        if request.language:
            cmd.extend(["--language", request.language])

        # Add model directory if available
        model_path = self.model_directory / f"faster-whisper-{request.model.value}"
        if model_path.exists():
            cmd.extend(["--model_dir", str(model_path)])

        # Add optional parameters
        if request.temperature > 0:
            cmd.extend(["--temperature", str(request.temperature)])

        cmd.extend(["--beam_size", str(request.beam_size)])
        cmd.extend(["--best_of", str(request.best_of)])
        cmd.extend(["--patience", str(request.patience)])

        if request.word_timestamps:
            cmd.append("--word_timestamps")

        # Add alignment and diarization flags
        cmd.append("--align_model")

        self.logger.debug(f"WhisperX command: {' '.join(cmd)}")
        return cmd

    async def _execute_whisperx(
        self,
        cmd: List[str],
        working_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Execute WhisperX subprocess with timeout and error handling

        Args:
            cmd: Command line arguments
            working_dir: Working directory for the process

        Returns:
            Raw output data from WhisperX

        Raises:
            subprocess.TimeoutExpired: If process times out
            subprocess.CalledProcessError: If process fails
        """
        try:
            # Create subprocess
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )

            # Store process reference for potential interruption
            # This would be set in the task manager
            # self._current_process = process

            # Wait for completion with timeout
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout
            )

            # Check return code
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace')
                self.logger.error(f"WhisperX failed with return code {process.returncode}: {error_msg}")
                raise subprocess.CalledProcessError(process.returncode, cmd, stderr=error_msg)

            # Log successful execution
            self.logger.debug("WhisperX execution completed successfully")

            # Return stdout for potential parsing
            return {"stdout": stdout.decode('utf-8', errors='replace')}

        except asyncio.TimeoutError:
            self.logger.error(f"WhisperX process timed out after {self.timeout} seconds")
            # Kill the process if it's still running
            if process.returncode is None:
                process.kill()
                await process.wait()
            raise subprocess.TimeoutExpired(cmd, self.timeout)

        except Exception as e:
            self.logger.error(f"Error executing WhisperX: {e}")
            raise

    async def _parse_whisperx_output(
        self,
        filename: str,
        output_dir: Path,
        request: TranscribeRequest,
        raw_data: Optional[Dict[str, Any]],
        processing_time: float
    ) -> TranscriptionResult:
        """
        Parse WhisperX output files and create structured result

        Args:
            filename: Original filename
            output_dir: Directory containing output files
            request: Original request parameters
            raw_data: Raw output from WhisperX
            processing_time: Time taken to process

        Returns:
            Structured transcription result
        """
        # Find the JSON output file
        base_name = Path(filename).stem
        json_file = None

        # Look for JSON output
        for ext in ['.json']:
            potential_file = output_dir / f"{base_name}{ext}"
            if potential_file.exists():
                json_file = potential_file
                break

        if not json_file:
            # If no JSON file, create basic result from other formats
            return await self._create_fallback_result(
                filename, output_dir, request, processing_time
            )

        try:
            # Parse JSON result
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Extract segments
            segments = []
            full_text = ""
            word_count = 0
            confidence_scores = []

            if isinstance(data, dict) and "segments" in data:
                for seg_data in data["segments"]:
                    segment = TranscriptionSegment(
                        start=seg_data.get("start", 0.0),
                        end=seg_data.get("end", 0.0),
                        text=seg_data.get("text", "").strip(),
                        confidence=seg_data.get("confidence"),
                        words=seg_data.get("words", [])
                    )
                    segments.append(segment)

                    # Accumulate text and statistics
                    if segment.text:
                        full_text += segment.text + " "
                        word_count += len(segment.text.split())

                    if segment.confidence is not None:
                        confidence_scores.append(segment.confidence)

            # Calculate average confidence
            confidence_avg = None
            if confidence_scores:
                confidence_avg = sum(confidence_scores) / len(confidence_scores)

            # Get audio duration
            duration = 0.0
            if segments:
                duration = max(seg.end for seg in segments)
            elif isinstance(data, dict) and "duration" in data:
                duration = data["duration"]

            # Detect language
            language = request.language or "auto"
            if isinstance(data, dict) and "language" in data:
                language = data["language"]

            # Create result
            result = TranscriptionResult(
                filename=filename,
                language=language,
                duration=duration,
                text=full_text.strip(),
                segments=segments,
                word_count=word_count,
                confidence_avg=confidence_avg,
                model_used=request.model.value,
                processing_time=processing_time,
                timestamp=datetime.now()
            )

            self.logger.info(f"Parsed transcription result: {word_count} words, {len(segments)} segments")
            return result

        except Exception as e:
            self.logger.error(f"Error parsing WhisperX JSON output: {e}")
            # Fallback to basic result
            return await self._create_fallback_result(
                filename, output_dir, request, processing_time
            )

    async def _create_fallback_result(
        self,
        filename: str,
        output_dir: Path,
        request: TranscribeRequest,
        processing_time: float
    ) -> TranscriptionResult:
        """
        Create a basic result when JSON parsing fails

        Args:
            filename: Original filename
            output_dir: Directory containing output files
            request: Original request parameters
            processing_time: Time taken to process

        Returns:
            Basic transcription result
        """
        base_name = Path(filename).stem

        # Try to read text file
        text_content = ""
        for ext in ['.txt', '.srt', '.vtt']:
            text_file = output_dir / f"{base_name}{ext}"
            if text_file.exists():
                try:
                    with open(text_file, 'r', encoding='utf-8') as f:
                        text_content = f.read().strip()
                    break
                except Exception as e:
                    self.logger.warning(f"Could not read {text_file}: {e}")

        # Create basic segment if we have text
        segments = []
        if text_content:
            # For SRT/VTT files, we could parse timestamps, but for now just create one segment
            segments.append(TranscriptionSegment(
                start=0.0,
                end=0.0,  # Unknown duration
                text=text_content,
                confidence=None
            ))

        return TranscriptionResult(
            filename=filename,
            language=request.language or "unknown",
            duration=0.0,  # Unknown duration
            text=text_content,
            segments=segments,
            word_count=len(text_content.split()) if text_content else 0,
            confidence_avg=None,
            model_used=request.model.value,
            processing_time=processing_time,
            timestamp=datetime.now()
        )
