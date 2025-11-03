"""
API routes for Audio Transcriber
Implements all REST endpoints according to specification
"""

import asyncio
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse

from api.models import (
    TranscribeRequest, TranscribeResponse, DeleteRequest, DeleteResponse,
    StatusResponse, ResultResponse, HealthCheckResponse, TaskStatus,
    TaskPriority, ErrorResponse
)
from core.logger import get_logger
from core.config_loader import get_config
from core.task_manager import get_task_manager
from core.file_manager import get_file_manager
from core.transcriber import WhisperXTranscriber


router = APIRouter()
logger = get_logger(__name__)


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Enhanced health check endpoint with system information
    Checks WhisperX availability, loaded models, and system resources
    """
    try:
        config = get_config()
        file_manager = get_file_manager()

        # Check WhisperX availability
        transcriber = WhisperXTranscriber(config)
        whisperx_available = await transcriber.check_availability()

        # Get loaded models
        models_loaded = await transcriber.get_available_models()

        # Get system information
        import psutil
        import shutil

        system_info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
        }

        # Check disk space for shared directory
        shared_path = config.get("shared_directory", "./shared")
        disk_usage = shutil.disk_usage(shared_path)
        disk_space = {
            "total_gb": disk_usage.total / (1024**3),
            "used_gb": disk_usage.used / (1024**3),
            "free_gb": disk_usage.free / (1024**3),
            "free_percent": (disk_usage.free / disk_usage.total) * 100
        }

        # Calculate uptime (placeholder - would need app start time)
        uptime = 0.0  # Will be implemented with global app state

        return HealthCheckResponse(
            status="healthy",
            service="Audio Transcriber API",
            version="1.0.0",
            uptime=uptime,
            whisperx_available=whisperx_available,
            models_loaded=models_loaded,
            system_info=system_info,
            disk_space=disk_space
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "service": "Audio Transcriber API",
                "error": str(e)
            }
        )


@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """
    Submit audio file for transcription
    Implements priority queue logic and file existence checking
    """
    try:
        logger.info(f"Received transcription request for file: {request.filename}")

        file_manager = get_file_manager()
        task_manager = get_task_manager()

        # Check file existence with 3 attempts (1 second interval)
        file_exists = False
        for attempt in range(3):
            if await file_manager.file_exists(request.filename):
                file_exists = True
                break
            if attempt < 2:  # Don't wait after the last attempt
                await asyncio.sleep(1)

        if not file_exists:
            return TranscribeResponse(
                status=TaskStatus.FILE_NOT_FOUND,
                filename=request.filename,
                message=f"File '{request.filename}' not found after 3 attempts"
            )

        # Check current file status
        current_status = await file_manager.get_file_status(request.filename)

        # Implement status logic according to specification matrix
        if current_status == TaskStatus.COMPLETED:
            return TranscribeResponse(
                status=TaskStatus.COMPLETED,
                filename=request.filename,
                message="File already processed. Use /result endpoint to get results."
            )

        elif current_status == TaskStatus.PROCESSING:
            # Get current task info
            task_info = await task_manager.get_task_info(request.filename)
            queue_position = await task_manager.get_queue_position(request.filename)

            return TranscribeResponse(
                status=TaskStatus.PROCESSING,
                filename=request.filename,
                task_id=task_info.task_id if task_info else None,
                message="File is currently being processed",
                queue_position=queue_position
            )

        elif current_status in [TaskStatus.PENDING, TaskStatus.ERROR, None]:
            # Create new task with API priority
            task_id = await task_manager.add_task(
                filename=request.filename,
                priority=TaskPriority.API,
                transcribe_request=request
            )

            queue_position = await task_manager.get_queue_position(request.filename)
            estimated_wait = await task_manager.get_estimated_wait_time(task_id)

            debug_info = None
            if request.debug:
                debug_info = await file_manager.get_debug_info(request.filename)

            return TranscribeResponse(
                status=TaskStatus.PENDING,
                filename=request.filename,
                task_id=task_id,
                message="Task added to processing queue",
                queue_position=queue_position,
                estimated_wait_time=estimated_wait,
                debug_info=debug_info
            )

    except Exception as e:
        logger.error(f"Error processing transcribe request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/transcribe", response_model=DeleteResponse)
async def delete_transcription(request: DeleteRequest):
    """
    Delete transcription files immediately (priority 0)
    Interrupts current processing if necessary
    """
    try:
        logger.info(f"Received delete request for file: {request.filename}")

        file_manager = get_file_manager()
        task_manager = get_task_manager()

        # Remove from queue immediately
        await task_manager.remove_task(request.filename)

        # Interrupt processing if currently being processed
        await task_manager.interrupt_processing(request.filename)

        # Delete all related files
        deleted_files = await file_manager.delete_all_related_files(
            request.filename,
            force=request.force
        )

        return DeleteResponse(
            status="success",
            filename=request.filename,
            message=f"Successfully deleted {len(deleted_files)} files",
            files_deleted=deleted_files
        )

    except Exception as e:
        logger.error(f"Error processing delete request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{filename}", response_model=StatusResponse)
async def get_transcription_status(
    filename: str,
    debug: bool = Query(False, description="Enable debug mode")
):
    """
    Get current transcription status for a file
    """
    try:
        logger.info(f"Status check requested for file: {filename}")

        file_manager = get_file_manager()
        task_manager = get_task_manager()

        # Get current status
        status = await file_manager.get_file_status(filename)

        if status is None:
            return StatusResponse(
                status=TaskStatus.FILE_NOT_FOUND,
                filename=filename,
                message="No processing information found for this file"
            )

        # Get additional information based on status
        queue_position = None
        priority = None
        estimated_completion = None
        processing_time = None
        debug_info = None

        if status == TaskStatus.PENDING:
            # Get task info for priority and queue position
            task_info = await task_manager.get_task_info(filename)
            if task_info:
                priority = task_info.priority.value
                queue_position = await task_manager.get_queue_position(filename)
                estimated_completion = await task_manager.get_estimated_completion_time(task_info.task_id)

        elif status == TaskStatus.PROCESSING:
            processing_info = await file_manager.get_processing_info(filename)
            if processing_info:
                processing_time = processing_info.get("processing_time")
                priority = processing_info.get("priority", "UNKNOWN")

        elif status == TaskStatus.COMPLETED:
            result_info = await file_manager.get_result_info(filename)
            if result_info:
                processing_time = result_info.get("processing_time")

        if debug:
            debug_info = await file_manager.get_debug_info(filename)

        return StatusResponse(
            status=status,
            filename=filename,
            message=f"File status: {status.value}",
            queue_position=queue_position,
            priority=priority,
            estimated_completion=estimated_completion,
            processing_time=processing_time,
            debug_info=debug_info
        )

    except Exception as e:
        logger.error(f"Error getting status for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/result/{filename}", response_model=ResultResponse)
async def get_transcription_result(filename: str):
    """
    Get transcription result for a completed file
    """
    try:
        logger.info(f"Result requested for file: {filename}")

        file_manager = get_file_manager()

        # Check if result exists
        if not await file_manager.result_exists(filename):
            return ResultResponse(
                status="not_found",
                filename=filename,
                message="No result found for this file"
            )

        # Get the result
        result = await file_manager.get_result(filename)

        return ResultResponse(
            status="success",
            filename=filename,
            result=result,
            message="Result retrieved successfully"
        )

    except Exception as e:
        logger.error(f"Error getting result for {filename}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Additional utility endpoints

@router.get("/queue")
async def get_queue_status():
    """
    Get current processing queue status
    """
    try:
        task_manager = get_task_manager()
        queue_info = await task_manager.get_queue_info()

        return {
            "status": "success",
            "queue_length": queue_info.get("length", 0),
            "processing_count": queue_info.get("processing", 0),
            "tasks": queue_info.get("tasks", [])
        }

    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """
    Get list of available WhisperX models
    """
    try:
        config = get_config()
        transcriber = WhisperXTranscriber(config)
        models = await transcriber.get_available_models()

        return {
            "status": "success",
            "models": models
        }

    except Exception as e:
        logger.error(f"Error getting available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))
