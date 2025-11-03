"""
File Manager for Audio Transcriber API
Handles file monitoring, result management, and file operations
"""

import asyncio
import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from dataclasses import dataclass

# Import TaskStatus locally in functions to avoid circular imports


@dataclass
class TranscriptionResult:
    """Dataclass for transcription results"""
    filename: str
    text: str
    status: str
    timestamp: datetime
    model_used: str
    language: str
    confidence: float
    duration: float
    file_size: int


class FileManagerMixin:
    """Mixin class providing file management functionality"""
    
    async def load_result(self, filename: str) -> Optional[TranscriptionResult]:
        """
        Load transcription result from .result file

        Args:
            filename: Name of the audio file

        Returns:
            TranscriptionResult object or None if not found
        """
        try:
            base_name = Path(filename).stem
            result_file = self.shared_directory / f"{base_name}.result"
            
            if not result_file.exists():
                return None

            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            result = TranscriptionResult(
                filename=data["filename"],
                text=data["text"], 
                status=data["status"],
                model_used=data["model_used"],
                language=data["language"],
                confidence=data["confidence"],
                duration=data["duration"],
                file_size=data["file_size"],
                timestamp=datetime.fromisoformat(data["timestamp"])
            )

            return result

        except Exception as e:
            self.logger.error(f"Error loading result for '{filename}': {e}")
            return None

    async def result_exists(self, filename: str) -> bool:
        """
        Check if result file exists for a given filename

        Args:
            filename: Name of the audio file

        Returns:
            True if result file exists
        """
        base_name = Path(filename).stem
        result_file = self.shared_directory / f"{base_name}.result"
        return result_file.exists()

    async def delete_all_related_files(
        self,
        filename: str,
        force: bool = False
    ) -> List[str]:
        """
        Delete all files related to a given filename

        Args:
            filename: Base filename
            force: Force deletion even if processing

        Returns:
            List of deleted file paths
        """
        base_name = Path(filename).stem
        deleted_files = []

        # Files to delete: original, .in_progress, .result, and any temporary files
        patterns = [
            filename,  # Original file
            f"{base_name}.in_progress",
            f"{base_name}.result",
            f"{base_name}.txt",
            f"{base_name}.json",
            f"{base_name}.srt",
            f"{base_name}.vtt"
        ]

        for pattern in patterns:
            file_path = self.shared_directory / pattern
            if file_path.exists():
                try:
                    file_path.unlink()
                    deleted_files.append(str(file_path))
                    self.logger.info(f"Deleted file: {file_path}")
                except Exception as e:
                    self.logger.error(f"Error deleting {file_path}: {e}")

        # Clear from cache
        if filename in self._status_cache:
            del self._status_cache[filename]

        return deleted_files

    async def get_processing_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get processing information from .in_progress file

        Args:
            filename: Name of the audio file

        Returns:
            Processing info dictionary or None
        """
        base_name = Path(filename).stem
        in_progress_file = self.shared_directory / f"{base_name}.in_progress"

        if not in_progress_file.exists():
            return None

        try:
            with open(in_progress_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading processing info for '{filename}': {e}")
            return None

    async def get_result_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get basic result information without full content

        Args:
            filename: Name of the audio file

        Returns:
            Result info dictionary or None
        """
        base_name = Path(filename).stem
        result_file = self.shared_directory / f"{base_name}.result"

        if not result_file.exists():
            return None

        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Return basic info only
            return {
                "processing_time": data.get("processing_time"),
                "word_count": data.get("word_count"),
                "duration": data.get("duration"),
                "model_used": data.get("model_used"),
                "timestamp": data.get("timestamp")
            }

        except Exception as e:
            self.logger.error(f"Error reading result info for '{filename}': {e}")
            return None

    async def get_debug_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get debug information for a file

        Args:
            filename: Name of the audio file

        Returns:
            Debug info dictionary or None
        """
        debug_info = {}

        # File existence
        debug_info["file_exists"] = await self.file_exists(filename)

        # File size
        if debug_info["file_exists"]:
            file_path = self.shared_directory / filename
            debug_info["file_size"] = file_path.stat().st_size
            debug_info["file_modified"] = datetime.fromtimestamp(
                file_path.stat().st_mtime
            ).isoformat()

        # Status file content
        processing_info = await self.get_processing_info(filename)
        if processing_info:
            debug_info["processing_info"] = processing_info

        # Result file info
        result_info = await self.get_result_info(filename)
        if result_info:
            debug_info["result_info"] = result_info

        return debug_info if debug_info else None


class AudioFileHandler(FileSystemEventHandler):
    """
    File system event handler for monitoring new audio files
    """

    def __init__(self, file_manager):
        self.file_manager = file_manager
        from core.logger import get_logger
        self.logger = get_logger(__name__)

        # Supported audio formats
        self.audio_extensions = {
            '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma',
            '.aac', '.opus', '.mp4', '.avi', '.mov', '.mkv'
        }

    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix.lower() in self.audio_extensions:
            # Skip files with "sample" in the name (case-insensitive)
            if "sample" in file_path.name.lower():
                self.logger.debug(f"Skipping sample file: {file_path.name}")
                return

            self.logger.info(f"New audio file detected: {file_path.name}")
            # Schedule async task
            asyncio.create_task(self.file_manager.handle_new_file(file_path.name))

    def on_moved(self, event):
        """Handle file moves (also triggers for renames)"""
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)
        if dest_path.suffix.lower() in self.audio_extensions:
            # Skip files with "sample" in the name (case-insensitive)
            if "sample" in dest_path.name.lower():
                self.logger.debug(f"Skipping sample file: {dest_path.name}")
                return

            self.logger.info(f"Audio file moved/renamed: {dest_path.name}")
            # Schedule async task
            asyncio.create_task(self.file_manager.handle_new_file(dest_path.name))


class FileManager:
    """
    Manages file operations and shared directory monitoring
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        from core.logger import get_logger
        self.logger = get_logger(__name__)

        # Directory paths
        self.shared_directory = Path(config.get("shared_directory", "./shared"))
        self.temp_directory = Path(config.get("temp_directory", "./temp"))

        # Ensure directories exist
        self.shared_directory.mkdir(parents=True, exist_ok=True)
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        # File monitoring
        self.observer = None
        self.monitoring_active = False

        # Status file cache
        self._status_cache: Dict[str, Dict[str, Any]] = {}

        # Valid audio extensions
        self.audio_extensions = {
            '.mp3', '.wav', '.flac', '.m4a', '.ogg', '.wma',
            '.aac', '.opus', '.mp4', '.avi', '.mov', '.mkv'
        }

    async def start_monitoring(self):
        """
        Start monitoring the shared directory for new files
        """
        if self.monitoring_active:
            self.logger.warning("File monitoring is already active")
            return

        try:
            # Set up file system observer
            self.observer = Observer()
            handler = AudioFileHandler(self)

            self.observer.schedule(
                handler,
                str(self.shared_directory),
                recursive=False
            )

            self.observer.start()
            self.monitoring_active = True

            self.logger.info(f"Started monitoring directory: {self.shared_directory}")

            # Perform initial scan for existing files
            await self.scan_existing_files()

        except Exception as e:
            self.logger.error(f"Failed to start file monitoring: {e}")
            raise

    async def stop(self):
        """Stop file monitoring"""
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
            self.monitoring_active = False
            self.logger.info("File monitoring stopped")

    async def scan_existing_files(self):
        """
        Scan shared directory for existing audio files that need processing
        """
        from api.models import TaskStatus

        self.logger.info("Scanning for existing audio files...")

        try:
            processed_count = 0

            for file_path in self.shared_directory.iterdir():
                if (file_path.is_file() and
                    file_path.suffix.lower() in self.audio_extensions):

                    # Skip files with "sample" in the name (case-insensitive)
                    if "sample" in file_path.name.lower():
                        self.logger.debug(f"Skipping sample file: {file_path.name}")
                        continue

                    # Check if file already has a result or is being processed
                    status = await self.get_file_status(file_path.name)

                    if status is None or status == TaskStatus.ERROR:
                        # File needs processing
                        await self.handle_new_file(file_path.name, auto_scan=True)
                        processed_count += 1

            self.logger.info(f"Found {processed_count} files needing processing")

        except Exception as e:
            self.logger.error(f"Error scanning existing files: {e}")

    async def handle_new_file(self, filename: str, auto_scan: bool = False):
        """
        Handle a new audio file that needs processing

        Args:
            filename: Name of the audio file
            auto_scan: Whether this is from auto-scan (lower priority)
        """
        try:
            # Import here to avoid circular imports
            from core.task_manager import get_task_manager
            from api.models import TaskPriority

            task_manager = get_task_manager()

            # Determine priority
            priority = TaskPriority.AUTO_SCAN if auto_scan else TaskPriority.API

            # Add to processing queue
            task_id = await task_manager.add_task(
                filename=filename,
                priority=priority
            )

            self.logger.info(f"Added new file '{filename}' to queue with priority {priority.name}")

        except Exception as e:
            self.logger.error(f"Error handling new file '{filename}': {e}")

    async def file_exists(self, filename: str) -> bool:
        """
        Check if a file exists in the shared directory

        Args:
            filename: Name of the file to check

        Returns:
            True if file exists
        """
        file_path = self.shared_directory / filename
        return file_path.exists() and file_path.is_file()

    async def get_file_status(self, filename: str) -> Optional['TaskStatus']:
        """
        Get the current processing status of a file

        Args:
            filename: Name of the file

        Returns:
            Current task status or None if unknown
        """
        from api.models import TaskStatus

        # Check cache first
        if filename in self._status_cache:
            cached_data = self._status_cache[filename]
            status_str = cached_data.get("status")
            if status_str:
                try:
                    return TaskStatus(status_str)
                except ValueError:
                    pass

        # Check for status files
        base_name = Path(filename).stem

        # Check for .in_progress file
        in_progress_file = self.shared_directory / f"{base_name}.in_progress"
        if in_progress_file.exists():
            try:
                with open(in_progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    status_str = data.get("status", "processing")
                    self._status_cache[filename] = data
                    return TaskStatus(status_str)
            except Exception as e:
                self.logger.warning(f"Error reading in_progress file for {filename}: {e}")

        # Check for .result file
        result_file = self.shared_directory / f"{base_name}.result"
        if result_file.exists():
            self._status_cache[filename] = {"status": "completed"}
            return TaskStatus.COMPLETED

        # Check queue in TaskManager for pending tasks
        try:
            from core.task_manager import get_task_manager
            task_manager = get_task_manager()
            task_info = await task_manager.get_task_info(filename)
            if task_info:
                # File is in queue
                return TaskStatus.PENDING
        except Exception as e:
            self.logger.warning(f"Error checking task manager for {filename}: {e}")

        # Final check: does the file exist in shared directory?
        if await self.file_exists(filename):
            # File exists but no status information - it should be processed
            return TaskStatus.PENDING

        # No status information found and file doesn't exist
        return None

    async def update_status_file(
        self,
        filename: str,
        status,  # Remove type hint to avoid circular import
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Update or create status file for a processing task

        Args:
            filename: Name of the audio file
            status: Current processing status
            additional_data: Additional data to include in status file
        """
        base_name = Path(filename).stem
        status_file = self.shared_directory / f"{base_name}.in_progress"

        # Prepare status data
        status_data = {
            "filename": filename,
            "status": status.value,
            "updated_at": datetime.now().isoformat()
        }

        if additional_data:
            status_data.update(additional_data)

        try:
            # Save status file
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2, ensure_ascii=False)

            # Update cache
            self._status_cache[filename] = status_data

            self.logger.debug(f"Updated status file for '{filename}': {status.value}")

        except Exception as e:
            self.logger.error(f"Error updating status file for '{filename}': {e}")

    async def get_debug_info(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Get debug information for a file

        Args:
            filename: Name of the audio file

        Returns:
            Debug info dictionary or None
        """
        debug_info = {}

        # File existence
        debug_info["file_exists"] = await self.file_exists(filename)

        # File size and modification time
        if debug_info["file_exists"]:
            file_path = self.shared_directory / filename
            try:
                stat = file_path.stat()
                debug_info["file_size"] = stat.st_size
                debug_info["file_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except Exception as e:
                debug_info["file_stat_error"] = str(e)

        # Processing info
        processing_info = await self.get_processing_info(filename)
        if processing_info:
            debug_info["processing_info"] = processing_info

        # Result file info
        result_info = await self.get_result_info(filename)
        if result_info:
            debug_info["result_info"] = result_info

        # Cache info
        if filename in self._status_cache:
            debug_info["cached_status"] = self._status_cache[filename]

        return debug_info if debug_info else None


# Global file manager instance
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """Get the global file manager instance"""
    global _file_manager
    if _file_manager is None:
        from core.config_loader import get_config
        _file_manager = FileManager(get_config())
    return _file_manager
