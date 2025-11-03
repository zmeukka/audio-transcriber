"""
Pydantic models for API requests and responses
Defines data validation and serialization for the Audio Transcriber API
"""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime


class TaskPriority(int, Enum):
    """Task priority levels"""
    DELETE = 0
    API = 1
    AUTO_SCAN = 2


class TaskStatus(str, Enum):
    """Task processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    FILE_NOT_FOUND = "file_not_found"


class AudioFormat(str, Enum):
    """Supported audio formats"""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"
    WMA = "wma"


class WhisperModel(str, Enum):
    """Available Whisper models"""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"


class ComputeType(str, Enum):
    """Compute types for model inference"""
    FLOAT16 = "float16"
    FLOAT32 = "float32"
    INT8 = "int8"


class OutputFormat(str, Enum):
    """Output format options"""
    JSON = "json"
    TXT = "txt"
    SRT = "srt"
    VTT = "vtt"
    TSV = "tsv"


class TranscribeRequest(BaseModel):
    """Request model for transcription API"""
    filename: str = Field(..., description="Name of the audio file to transcribe")
    language: Optional[str] = Field(None, description="Language code (e.g., 'en', 'ru') or None for auto-detection")
    model: WhisperModel = Field(WhisperModel.SMALL, description="Whisper model to use")
    compute_type: ComputeType = Field(ComputeType.FLOAT32, description="Compute precision type")
    output_format: OutputFormat = Field(OutputFormat.JSON, description="Output format")
    debug: bool = Field(False, description="Enable debug mode for detailed responses")
    temperature: float = Field(0.0, description="Sampling temperature", ge=0.0, le=1.0)
    beam_size: int = Field(5, description="Beam size for decoding", ge=1)
    best_of: int = Field(5, description="Number of candidates to consider", ge=1)
    patience: float = Field(1.0, description="Patience for beam search", ge=0.0)
    word_timestamps: bool = Field(True, description="Include word-level timestamps")

    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename format"""
        if not v or len(v.strip()) == 0:
            raise ValueError("Filename cannot be empty")

        # Check for invalid characters
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Filename contains invalid characters: {invalid_chars}")

        return v.strip()


class TranscribeResponse(BaseModel):
    """Response model for transcription API"""
    status: TaskStatus
    filename: str
    task_id: Optional[str] = None
    message: str
    debug_info: Optional[Dict[str, Any]] = None
    estimated_wait_time: Optional[float] = None
    queue_position: Optional[int] = None


class DeleteRequest(BaseModel):
    """Request model for deletion API"""
    filename: str = Field(..., description="Name of the file to delete")
    force: bool = Field(False, description="Force deletion even if processing")


class DeleteResponse(BaseModel):
    """Response model for deletion API"""
    status: str
    filename: str
    message: str
    files_deleted: List[str] = Field(default_factory=list)


class StatusResponse(BaseModel):
    """Response model for status check API"""
    status: TaskStatus
    filename: str
    progress: Optional[float] = Field(None, description="Processing progress (0-100)")
    message: str
    queue_position: Optional[int] = None
    priority: Optional[str] = Field(None, description="Task priority (API/AUTO_SCAN)")
    estimated_completion: Optional[datetime] = None
    processing_time: Optional[float] = None
    debug_info: Optional[Dict[str, Any]] = None


class TranscriptionSegment(BaseModel):
    """Individual transcription segment"""
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text")
    confidence: Optional[float] = Field(None, description="Confidence score")
    words: Optional[List[Dict[str, Any]]] = Field(None, description="Word-level details")


class TranscriptionResult(BaseModel):
    """Complete transcription result"""
    filename: str
    language: str
    duration: float = Field(..., description="Audio duration in seconds")
    text: str = Field(..., description="Full transcribed text")
    segments: List[TranscriptionSegment]
    word_count: int
    confidence_avg: Optional[float] = None
    model_used: str
    processing_time: float
    timestamp: datetime


class ResultResponse(BaseModel):
    """Response model for result retrieval API"""
    status: str
    filename: str
    result: Optional[TranscriptionResult] = None
    message: str


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    service: str
    version: str
    uptime: Optional[float] = None
    whisperx_available: bool
    models_loaded: List[str] = Field(default_factory=list)
    system_info: Optional[Dict[str, Any]] = None
    disk_space: Optional[Dict[str, float]] = None


class ErrorResponse(BaseModel):
    """Standard error response model"""
    status: str = "error"
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskInfo(BaseModel):
    """Task information model"""
    task_id: str
    filename: str
    priority: TaskPriority
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    client_id: Optional[str] = None
