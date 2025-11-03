"""
Task Manager for Audio Transcriber
Implements priority queue system for processing audio transcription tasks
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from queue import PriorityQueue
from threading import Lock

from api.models import TaskPriority, TaskStatus, TaskInfo, TranscribeRequest
from core.logger import get_logger


@dataclass
class ProcessingTask:
    """
    Task object for processing queue with priority support
    """
    task_id: str
    filename: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    transcribe_request: Optional[TranscribeRequest] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    client_id: Optional[str] = None

    def __lt__(self, other):
        """Priority comparison for queue ordering"""
        # Lower priority number = higher priority
        if self.priority != other.priority:
            return self.priority < other.priority
        # If same priority, older tasks first
        return self.created_at < other.created_at


class TaskManager:
    """
    Manages processing tasks with priority queue system
    Priorities: DELETE(0) > API(1) > AUTO-SCAN(2)
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        # Priority queue for tasks
        self._task_queue = PriorityQueue()
        self._queue_lock = Lock()

        # Task tracking
        self._active_tasks: Dict[str, ProcessingTask] = {}
        self._completed_tasks: Dict[str, ProcessingTask] = {}
        self._processing_task: Optional[ProcessingTask] = None

        # Processing control
        self._processing_active = False
        self._stop_processing = False
        self._current_process = None

        # Statistics
        self._stats = {
            "total_processed": 0,
            "total_errors": 0,
            "avg_processing_time": 0.0
        }

    async def add_task(
        self,
        filename: str,
        priority: TaskPriority,
        transcribe_request: Optional[TranscribeRequest] = None,
        client_id: Optional[str] = None
    ) -> str:
        """
        Add task to priority queue

        Args:
            filename: Name of the audio file
            priority: Task priority level
            transcribe_request: Optional request parameters
            client_id: Optional client identifier

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task = ProcessingTask(
            task_id=task_id,
            filename=filename,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=datetime.now(),
            transcribe_request=transcribe_request,
            client_id=client_id
        )

        # Remove any existing task for this filename
        await self.remove_task(filename)

        # Add to queue and tracking
        with self._queue_lock:
            self._task_queue.put(task)
            self._active_tasks[filename] = task

        self.logger.info(f"Added task {task_id} for file '{filename}' with priority {priority.name}")
        return task_id

    async def remove_task(self, filename: str) -> bool:
        """
        Remove task from queue and tracking

        Args:
            filename: Name of the file

        Returns:
            True if task was removed, False if not found
        """
        with self._queue_lock:
            if filename in self._active_tasks:
                task = self._active_tasks.pop(filename)
                self.logger.info(f"Removed task {task.task_id} for file '{filename}'")
                return True
        return False

    async def get_highest_priority_task(self) -> Optional[ProcessingTask]:
        """
        Get the highest priority task from queue

        Returns:
            Next task to process or None if queue is empty
        """
        with self._queue_lock:
            # Clean up invalid tasks from queue
            valid_tasks = []

            while not self._task_queue.empty():
                task = self._task_queue.get()
                # Only include tasks that are still active
                if task.filename in self._active_tasks:
                    valid_tasks.append(task)

            # Put valid tasks back and get the highest priority one
            next_task = None
            for task in valid_tasks:
                if next_task is None:
                    next_task = task
                else:
                    self._task_queue.put(task)

            return next_task

    async def start_processing(self):
        """
        Start the background task processing loop
        """
        if self._processing_active:
            self.logger.warning("Task processing is already active")
            return

        self._processing_active = True
        self._stop_processing = False
        self.logger.info("Started task processing loop")

        while not self._stop_processing:
            try:
                # Get next task
                task = await self.get_highest_priority_task()

                if task is None:
                    # No tasks available, wait a bit
                    await asyncio.sleep(1)
                    continue

                # Process the task
                await self._process_task(task)

            except Exception as e:
                self.logger.error(f"Error in processing loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying

        self._processing_active = False
        self.logger.info("Stopped task processing loop")

    async def stop(self):
        """Stop the task processing"""
        self.logger.info("Stopping task manager...")
        self._stop_processing = True

        # Interrupt current processing if active
        if self._current_process:
            await self.interrupt_processing(self._processing_task.filename)

        # Wait for processing to stop
        timeout = 30  # 30 seconds timeout
        while self._processing_active and timeout > 0:
            await asyncio.sleep(1)
            timeout -= 1

        if self._processing_active:
            self.logger.warning("Task processing did not stop gracefully")
        else:
            self.logger.info("Task manager stopped successfully")

    async def _process_task(self, task: ProcessingTask):
        """
        Process a single task

        Args:
            task: Task to process
        """
        self.logger.info(f"Starting processing of task {task.task_id} for file '{task.filename}'")

        # Update task status
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.now()
        self._processing_task = task

        try:
            # Import here to avoid circular imports
            from core.transcriber import WhisperXTranscriber
            from core.file_manager import get_file_manager

            # Create transcriber instance
            transcriber = WhisperXTranscriber(self.config)
            file_manager = get_file_manager()

            # Update status file
            await file_manager.update_status_file(task.filename, TaskStatus.PROCESSING, {
                "task_id": task.task_id,
                "started_at": task.started_at.isoformat(),
                "progress": 0
            })

            # Execute transcription
            result = await transcriber.transcribe_file(
                task.filename,
                task.transcribe_request
            )

            # Save result
            await file_manager.save_result(task.filename, result)

            # Update task completion
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()

            # Update status file
            await file_manager.update_status_file(task.filename, TaskStatus.COMPLETED, {
                "task_id": task.task_id,
                "completed_at": task.completed_at.isoformat(),
                "progress": 100
            })

            # Move to completed tasks
            with self._queue_lock:
                if task.filename in self._active_tasks:
                    self._active_tasks.pop(task.filename)
                self._completed_tasks[task.filename] = task

            # Update statistics
            processing_time = (task.completed_at - task.started_at).total_seconds()
            self._update_stats(processing_time, success=True)

            self.logger.info(f"Successfully completed task {task.task_id} in {processing_time:.2f}s")

        except Exception as e:
            self.logger.error(f"Error processing task {task.task_id}: {e}")

            # Handle retry logic
            task.retry_count += 1
            task.error_message = str(e)

            max_retries = self.config.get("max_retries", 3)
            if task.retry_count < max_retries:
                # Retry with exponential backoff
                delay = 2 ** task.retry_count
                self.logger.info(f"Retrying task {task.task_id} in {delay} seconds (attempt {task.retry_count + 1})")

                # Reset status and re-queue
                task.status = TaskStatus.PENDING
                task.started_at = None

                await asyncio.sleep(delay)

                with self._queue_lock:
                    self._task_queue.put(task)
            else:
                # Max retries exceeded
                task.status = TaskStatus.ERROR
                task.completed_at = datetime.now()

                # Update status file with error
                from core.file_manager import get_file_manager
                file_manager = get_file_manager()
                await file_manager.update_status_file(task.filename, TaskStatus.ERROR, {
                    "task_id": task.task_id,
                    "error": task.error_message,
                    "retry_count": task.retry_count,
                    "completed_at": task.completed_at.isoformat()
                })

                # Move to completed tasks
                with self._queue_lock:
                    if task.filename in self._active_tasks:
                        self._active_tasks.pop(task.filename)
                    self._completed_tasks[task.filename] = task

                self._update_stats(0, success=False)

                self.logger.error(f"Task {task.task_id} failed after {max_retries} retries")

        finally:
            self._processing_task = None
            self._current_process = None

    async def interrupt_processing(self, filename: str) -> bool:
        """
        Interrupt processing of a specific file

        Args:
            filename: Name of the file being processed

        Returns:
            True if processing was interrupted
        """
        if (self._processing_task and
            self._processing_task.filename == filename and
            self._current_process):

            self.logger.info(f"Interrupting processing of file '{filename}'")

            try:
                # Terminate the current process
                self._current_process.terminate()
                await asyncio.sleep(2)

                if self._current_process.poll() is None:
                    # Force kill if still running
                    self._current_process.kill()

                return True
            except Exception as e:
                self.logger.error(f"Error interrupting process: {e}")

        return False

    async def get_task_info(self, filename: str) -> Optional[TaskInfo]:
        """
        Get task information for a file

        Args:
            filename: Name of the file

        Returns:
            Task information or None if not found
        """
        # Check active tasks
        if filename in self._active_tasks:
            task = self._active_tasks[filename]
        elif filename in self._completed_tasks:
            task = self._completed_tasks[filename]
        else:
            return None

        return TaskInfo(
            task_id=task.task_id,
            filename=task.filename,
            priority=task.priority,
            status=task.status,
            created_at=task.created_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            retry_count=task.retry_count,
            client_id=task.client_id
        )

    async def get_queue_position(self, filename: str) -> Optional[int]:
        """
        Get position in queue for a file

        Args:
            filename: Name of the file

        Returns:
            Queue position (1-based) or None if not in queue
        """
        if filename not in self._active_tasks:
            return None

        target_task = self._active_tasks[filename]
        if target_task.status != TaskStatus.PENDING:
            return None

        # Count pending tasks with higher priority or earlier creation time
        position = 1

        for task_filename, task in self._active_tasks.items():
            if (task.status == TaskStatus.PENDING and
                task_filename != filename):

                # Higher priority comes first
                if task.priority.value < target_task.priority.value:
                    position += 1
                # Same priority, earlier creation time comes first
                elif (task.priority.value == target_task.priority.value and
                      task.created_at < target_task.created_at):
                    position += 1


        return position

    async def get_estimated_wait_time(self, task_id: str) -> Optional[float]:
        """
        Estimate wait time for a task

        Args:
            task_id: Task identifier

        Returns:
            Estimated wait time in seconds or None
        """
        # Find the task
        task = None
        for t in self._active_tasks.values():
            if t.task_id == task_id:
                task = t
                break

        if not task or task.status != TaskStatus.PENDING:
            return None

        queue_position = await self.get_queue_position(task.filename)
        if queue_position is None:
            return None

        # Estimate based on average processing time and queue position
        avg_time = self._stats.get("avg_processing_time", 60.0)  # Default 1 minute
        return (queue_position - 1) * avg_time

    async def get_estimated_completion_time(self, task_id: str) -> Optional[datetime]:
        """
        Get estimated completion time for a task

        Args:
            task_id: Task identifier

        Returns:
            Estimated completion datetime or None
        """
        wait_time = await self.get_estimated_wait_time(task_id)
        if wait_time is None:
            return None

        return datetime.now() + timedelta(seconds=wait_time)

    async def get_queue_info(self) -> Dict[str, Any]:
        """
        Get current queue information

        Returns:
            Dictionary with queue statistics
        """
        pending_tasks = [t for t in self._active_tasks.values() if t.status == TaskStatus.PENDING]
        processing_tasks = [t for t in self._active_tasks.values() if t.status == TaskStatus.PROCESSING]

        return {
            "length": len(pending_tasks),
            "processing": len(processing_tasks),
            "completed_today": len([t for t in self._completed_tasks.values()
                                  if t.completed_at and t.completed_at.date() == datetime.now().date()]),
            "tasks": [
                {
                    "task_id": t.task_id,
                    "filename": t.filename,
                    "priority": t.priority.name,
                    "status": t.status.value,
                    "created_at": t.created_at.isoformat()
                }
                for t in pending_tasks[:10]  # Show first 10 pending tasks
            ],
            "stats": self._stats
        }

    def _update_stats(self, processing_time: float, success: bool):
        """Update processing statistics"""
        if success:
            self._stats["total_processed"] += 1
            # Update average processing time
            total = self._stats["total_processed"]
            current_avg = self._stats["avg_processing_time"]
            self._stats["avg_processing_time"] = ((current_avg * (total - 1)) + processing_time) / total
        else:
            self._stats["total_errors"] += 1


# Global task manager instance
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """Get the global task manager instance"""
    global _task_manager
    if _task_manager is None:
        from core.config_loader import get_config
        _task_manager = TaskManager(get_config())
    return _task_manager
