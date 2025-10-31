"""
File manager module for Audio Transcriber
Handles file operations, status tracking, and directory management
"""

import os
import shutil
import time
from pathlib import Path
from datetime import datetime
from typing import List, Optional


class FileManager:
    """Manages file operations and status tracking"""

    # Supported audio formats
    SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.oga'}

    def __init__(self, config: dict, logger, test_mode: bool = False):
        """
        Initialize file manager with configuration

        Args:
            config: Configuration dictionary
            logger: Logger instance
            test_mode: Whether to process test files (sample.*)
        """
        self.config = config
        self.logger = logger
        self.test_mode = test_mode
        self.input_dir = Path(config['input_directory'])
        self.output_dir = Path(config['output_directory'])
        self.manual_dir = Path(config['manual_processing_directory'])

        # Ensure directories exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.manual_dir.mkdir(parents=True, exist_ok=True)

    def scan_audio_files(self) -> List[Path]:
        """
        Scan input directory for audio files

        Returns:
            List of audio file paths (excludes sample.* unless in test mode)
        """
        audio_files = []

        for file_path in self.input_dir.glob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                # Filter sample files based on test mode
                if file_path.name.startswith('sample.'):
                    if self.test_mode:
                        self.logger.info(f"Test mode: Including {file_path.name}", "FileManager")
                        audio_files.append(file_path)
                    else:
                        self.logger.info(f"Normal mode: Skipping {file_path.name}", "FileManager")
                else:
                    audio_files.append(file_path)

        self.logger.info(f"Found {len(audio_files)} audio files", "FileManager")
        return audio_files

    def get_file_status(self, audio_file: Path) -> str:
        """
        Determine file processing status

        Args:
            audio_file: Path to audio file

        Returns:
            Status: 'unprocessed', 'in_progress', 'error', 'completed'
        """
        base_name = audio_file.stem

        in_process_file = self.output_dir / f"{base_name}.in_process"
        output_file = self.output_dir / f"{base_name}.txt"

        if output_file.exists() and not in_process_file.exists():
            return 'completed'
        elif in_process_file.exists():
            # Check if file has errors by reading content
            try:
                with open(in_process_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if '=== ERRORS (if any) ===' in content and content.split('=== ERRORS (if any) ===')[1].strip():
                        return 'error'
                    else:
                        return 'in_progress'
            except:
                return 'in_progress'
        else:
            return 'unprocessed'

    def create_in_process_file(self, audio_file: Path, attempt: int = 1) -> Path:
        """
        Create .in_process file for tracking

        Args:
            audio_file: Path to audio file being processed
            attempt: Current attempt number

        Returns:
            Path to created in_process file
        """
        base_name = audio_file.stem
        in_process_file = self.output_dir / f"{base_name}.in_process"

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""Processing started: {timestamp}
File: {audio_file.name}
Attempt: {attempt}
Processing time: 0 seconds
---
[intermediate transcription results saved here during processing]

=== ERRORS (if any) ===
"""

        with open(in_process_file, 'w', encoding='utf-8') as f:
            f.write(content)

        self.logger.info(f"Created in_process file for {audio_file.name}", "FileManager")
        return in_process_file

    def add_error_to_process_file(self, audio_file: Path, error_msg: str, attempt: int) -> None:
        """
        Add error information to .in_process file

        Args:
            audio_file: Path to audio file that failed
            error_msg: Error message
            attempt: Attempt number
        """
        base_name = audio_file.stem
        in_process_file = self.output_dir / f"{base_name}.in_process"

        if not in_process_file.exists():
            # Create in_process file if it doesn't exist
            self.create_in_process_file(audio_file, attempt)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        error_entry = f"""
Error date: {timestamp}
Attempt: {attempt}
Error: {error_msg}
Details: WhisperX process failed
---"""

        try:
            with open(in_process_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Add error to the errors section
            if '=== ERRORS (if any) ===' in content:
                content = content.replace(
                    '=== ERRORS (if any) ===\n',
                    f'=== ERRORS (if any) ==={error_entry}\n'
                )
            else:
                content += f'\n=== ERRORS (if any) ==={error_entry}\n'

            with open(in_process_file, 'w', encoding='utf-8') as f:
                f.write(content)

        except Exception as e:
            self.logger.warning(f"Could not add error to process file: {e}", "FileManager")

        self.logger.error(f"Added error entry for {audio_file.name}: {error_msg}", "FileManager")

    def move_to_manual_processing(self, audio_file: Path) -> None:
        """
        Move problematic files to manual processing directory

        Args:
            audio_file: Path to audio file to move
        """
        base_name = audio_file.stem

        # Files to move
        files_to_move = [
            audio_file,
            self.output_dir / f"{base_name}.in_process"
        ]

        moved_files = []
        for file_path in files_to_move:
            if file_path.exists():
                dest_path = self.manual_dir / file_path.name
                shutil.move(str(file_path), str(dest_path))
                moved_files.append(file_path.name)

        self.logger.warning(f"Moved {len(moved_files)} files to manual processing: {moved_files}", "FileManager")

    def cleanup_temp_files(self, audio_file: Path) -> None:
        """
        Clean up temporary processing files after successful completion

        Args:
            audio_file: Path to audio file that was processed
        """
        base_name = audio_file.stem

        temp_files = [
            self.output_dir / f"{base_name}.in_process"
        ]

        for temp_file in temp_files:
            if temp_file.exists():
                temp_file.unlink()

        self.logger.info(f"Cleaned up temporary files for {audio_file.name}", "FileManager")

    def check_disk_space(self) -> bool:
        """
        Check if there's enough disk space (minimum 0.1GB)

        Returns:
            True if enough space available
        """
        try:
            statvfs = os.statvfs(str(self.output_dir))
            free_bytes = statvfs.f_frsize * statvfs.f_available
            free_gb = free_bytes / (1024 ** 3)

            if free_gb < 0.1:
                self.logger.error(f"Insufficient disk space: {free_gb:.2f}GB available, minimum 0.1GB required", "FileManager")
                return False

            return True

        except Exception as e:
            self.logger.warning(f"Could not check disk space: {e}", "FileManager")
            return True  # Assume OK if we can't check

    def process_file(self, file_path: str, audio_processor) -> bool:
        """
        Process a single file

        Args:
            file_path: Path to file to process
            audio_processor: AudioProcessor instance

        Returns:
            True if processing was successful
        """
        audio_file = Path(file_path)

        if not audio_file.exists():
            self.logger.error(f"File not found: {file_path}", "FileManager")
            return False

        if audio_file.suffix.lower() not in self.SUPPORTED_FORMATS:
            self.logger.error(f"Unsupported file format: {audio_file.suffix}", "FileManager")
            return False

        # Check disk space
        if not self.check_disk_space():
            return False

        # Process the file
        return self._process_single_file(audio_file, audio_processor)

    def process_all_files(self, audio_processor) -> None:
        """
        Process all files in input directory

        Args:
            audio_processor: AudioProcessor instance
        """
        if not self.check_disk_space():
            return

        audio_files = self.scan_audio_files()

        if not audio_files:
            self.logger.info("No audio files found to process", "FileManager")
            return

        processed = 0
        for audio_file in audio_files:
            self.logger.info(f"Processing file {processed + 1}/{len(audio_files)}: {audio_file.name}", "FileManager")

            if self._process_single_file(audio_file, audio_processor):
                processed += 1

        self.logger.info(f"Processing completed: {processed}/{len(audio_files)} files successful", "FileManager")

    def _process_single_file(self, audio_file: Path, audio_processor) -> bool:
        """
        Internal method to process a single file

        Args:
            audio_file: Path to audio file
            audio_processor: AudioProcessor instance

        Returns:
            True if successful
        """
        status = self.get_file_status(audio_file)

        if status == 'completed':
            self.logger.info(f"File already processed: {audio_file.name}", "FileManager")
            return True

        max_attempts = self.config.get('processing', {}).get('max_retry_attempts', 3)

        if status == 'error':
            # Check if max attempts exceeded by reading in_process file
            base_name = audio_file.stem
            in_process_file = self.output_dir / f"{base_name}.in_process"

            if in_process_file.exists():
                try:
                    with open(in_process_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        attempt_count = content.count('Attempt:')

                    if attempt_count >= max_attempts:
                        self.logger.warning(f"Max attempts exceeded for {audio_file.name}, moving to manual processing", "FileManager")
                        self.move_to_manual_processing(audio_file)
                        return False
                except:
                    pass

        # Determine attempt number
        attempt = 1
        if status in ['in_progress', 'error']:
            base_name = audio_file.stem
            in_process_file = self.output_dir / f"{base_name}.in_process"

            if in_process_file.exists():
                try:
                    with open(in_process_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        attempt = content.count('Attempt:') + 1
                except:
                    attempt = 1

        # Create in_process file
        in_process_file = self.create_in_process_file(audio_file, attempt)

        # Start timing
        start_time = time.time()

        # Process with audio processor (pass placeholder time)
        success = audio_processor.process_audio_file(audio_file, "обрабатывается...")

        # Calculate processing time
        processing_time = time.time() - start_time
        processing_time_str = self._format_processing_time(processing_time)

        # Update in_process file with final processing time
        self._update_processing_time(in_process_file, processing_time_str)

        # Update the final output file with correct processing time
        if success:
            output_file = self.output_dir / f"{audio_file.stem}.txt"
            if output_file.exists():
                self._update_output_file_processing_time(output_file, processing_time_str)

        if success:
            self.cleanup_temp_files(audio_file)
            self.logger.info(f"Successfully processed: {audio_file.name} in {processing_time_str}", "FileManager")
            return True
        else:
            # Handle failure
            self.logger.error(f"Failed to process: {audio_file.name} after {processing_time_str}", "FileManager")
            if attempt >= max_attempts:
                self.logger.warning(f"Max attempts reached for {audio_file.name}, moving to manual processing", "FileManager")
                self.move_to_manual_processing(audio_file)
            else:
                self.add_error_to_process_file(audio_file, "Processing failed", attempt)

            return False

    def _format_processing_time(self, seconds: float) -> str:
        """
        Format processing time in human-readable format

        Args:
            seconds: Processing time in seconds

        Returns:
            Formatted time string
        """
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"

    def _update_processing_time(self, in_process_file: Path, processing_time_str: str) -> None:
        """
        Update processing time in the in_process file

        Args:
            in_process_file: Path to in_process file
            processing_time_str: Formatted processing time string
        """
        try:
            if in_process_file.exists():
                with open(in_process_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the processing time line
                updated_content = content.replace(
                    'Processing time: 0 seconds',
                    f'Processing time: {processing_time_str}'
                )

                with open(in_process_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)

        except Exception as e:
            self.logger.warning(f"Could not update processing time in {in_process_file.name}: {e}", "FileManager")

    def _update_output_file_processing_time(self, output_file: Path, processing_time_str: str) -> None:
        """
        Update processing time in the output .txt file

        Args:
            output_file: Path to output .txt file
            processing_time_str: Formatted processing time string
        """
        try:
            if output_file.exists():
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Replace the processing time line
                updated_content = content.replace(
                    'Расшифровка заняла: обрабатывается...',
                    f'Расшифровка заняла: {processing_time_str}'
                )

                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(updated_content)

        except Exception as e:
            self.logger.warning(f"Could not update processing time in {output_file.name}: {e}", "FileManager")
