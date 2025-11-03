# 🔧 Структуры данных и алгоритмы

## 📊 Основные структуры данных

### ProcessingTask (упрощенная версия)
```python
@dataclass
class ProcessingTask:
    filename: str
    priority: str  # "api" or "auto"
    settings: dict  # Includes debug parameter from request
    created_at: datetime
    attempt: int = 1
```

### Статусные файлы

#### .in_progress файл (упрощенная версия)
```json
{
  "filename": "audio.mp3",
  "status": "processing",
  "start_time": "2024-01-01T10:00:00Z",
  "attempt": 1,
  "settings": {
    "model_size": "base",
    "language": "ru",
    "debug": false
  },
  "error": null
}
```

#### .result файл (упрощенная версия)
```json
{
  "filename": "audio.mp3",
  "processing_time_seconds": 27.1,
  "transcription": {
    "text": "Full transcription text...",
    "segments": [{
      "start": 0.0,
      "end": 5.2, 
      "text": "Segment text"
    }]
  },
  "metadata": {
    "duration_seconds": 135.5,
    "confidence": 0.89,
    "word_count": 156
  }
}
```

## 🚀 Ключевые алгоритмы

### Проверка файла с повторами
```python
def check_file_exists(filename: str) -> bool:
    """Check if file exists with 3 attempts and 1 second interval"""
    for attempt in range(3):  # Updated from 5 to 3 attempts
        if os.path.exists(f"shared/{filename}"):
            return True
        time.sleep(1)
    return False
```

### Определение статуса файла
```python
def check_file_status(filename: str) -> str:
    """Determine file processing status based on existing files"""
    file_exists = os.path.exists(f"shared/{filename}")
    in_progress_exists = os.path.exists(f"shared/{filename}.in_progress")
    result_exists = os.path.exists(f"shared/{filename}.result")
    
    if not file_exists:
        return "file_not_found"
    elif result_exists and not in_progress_exists:
        return "completed"
    elif in_progress_exists:
        return "processing"
    else:
        return "pending"
```

### Создание .in_progress файла
```python
def create_in_progress_file(filename: str, settings: dict) -> None:
    """Create status file for processing tracking"""
    data = {
        "filename": filename,
        "status": "processing",
        "start_time": datetime.now().isoformat(),
        "attempt": 1,
        "settings": settings,
        "error": None
    }
    
    with open(f"shared/{filename}.in_progress", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### Сохранение результата
```python
def save_result_file(filename: str, transcription_data: dict, metadata: dict, processing_time: float) -> None:
    """Save transcription result and cleanup status file"""
    result = {
        "filename": filename,
        "processing_time_seconds": processing_time,
        "transcription": transcription_data,
        "metadata": metadata
    }
    
    with open(f"shared/{filename}.result", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Remove .in_progress file after successful save
    in_progress_file = f"shared/{filename}.in_progress"
    if os.path.exists(in_progress_file):
        os.remove(in_progress_file)
```

### Debug режим обработки ошибок
```python
def handle_processing_error(task: ProcessingTask, exception: Exception) -> dict:
    """Handle processing errors with optional debug information"""
    error_info = {
        "code": type(exception).__name__,
        "message": str(exception),
        "timestamp": datetime.now().isoformat(),
        "attempt": task.attempt
    }
    
    # Update .in_progress file with error
    update_in_progress_with_error(task.filename, error_info)
    
    # Determine debug mode: request parameter takes priority
    debug_enabled = task.settings.get('debug', False)
    
    if debug_enabled:
        return create_debug_response(task.filename, error_info)
    else:
        return create_standard_error_response(error_info)

def create_debug_response(filename: str, error_info: dict) -> dict:
    """Create detailed error response with .in_progress content"""
    response = {
        "status": "error",
        "filename": filename,
        "error": error_info
    }
    
    # Add debug info with .in_progress content
    in_progress_file = f"shared/{filename}.in_progress"
    if os.path.exists(in_progress_file):
        try:
            with open(in_progress_file, 'r', encoding='utf-8') as f:
                in_progress_content = json.load(f)
            response["debug_info"] = {
                "in_progress_content": in_progress_content
            }
        except Exception as e:
            response["debug_info"] = {
                "error": f"Could not read .in_progress file: {str(e)}"
            }
    
    return response

def create_standard_error_response(error_info: dict) -> dict:
    """Create standard error response without debug details"""
    return {
        "status": "error",
        "error_code": error_info.get("code", "unknown_error"),
        "message": error_info.get("message", "Processing failed"),
        "suggestion": "Check audio file format and try again"
    }
```

### Приоритетная очередь
```python
def add_to_priority_queue(task: ProcessingTask) -> None:
    """Add task to priority queue with correct ordering"""
    # Priority: "api" tasks have higher priority than "auto" tasks
    if task.priority == "api":
        priority_queue.put((1, task.created_at, task))  # Lower number = higher priority
    else:  # "auto" priority
        priority_queue.put((2, task.created_at, task))

def get_highest_priority_task() -> ProcessingTask:
    """Get next task from priority queue"""
    if not priority_queue.empty():
        _, _, task = priority_queue.get()
        return task
    return None

def remove_from_queue(filename: str) -> bool:
    """Remove all tasks with specified filename from queue (for DELETE operations)"""
    # Convert queue to list, filter, and rebuild queue
    remaining_tasks = []
    removed_count = 0
    
    while not priority_queue.empty():
        priority, timestamp, task = priority_queue.get()
        if task.filename != filename:
            remaining_tasks.append((priority, timestamp, task))
        else:
            removed_count += 1
    
    # Rebuild queue with remaining tasks
    for task_tuple in remaining_tasks:
        priority_queue.put(task_tuple)
    
    return removed_count > 0
```

### WhisperX процесс запуска
```python
def run_whisperx_process(filename: str, settings: dict) -> dict:
    """Execute WhisperX transcription process"""
    input_file = f"shared/{filename}"
    output_dir = f"temp/{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Prepare WhisperX command
    cmd = [
        "whisperx",
        input_file,
        "--model", settings.get("model_size", "base"),
        "--language", settings.get("language", "ru"),
        "--temperature", str(settings.get("temperature", 0.1)),
        "--compute_type", settings.get("compute_type", "int8"),
        "--device", settings.get("device", "cpu"),
        "--output_dir", output_dir,
        "--output_format", "json"
    ]
    
    try:
        # Execute WhisperX with timeout
        result = subprocess.run(
            cmd,
            timeout=600,  # 10 minutes timeout
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse JSON output
        json_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.json")
        with open(json_file, 'r', encoding='utf-8') as f:
            transcription_data = json.load(f)
        
        # Cleanup temp directory
        shutil.rmtree(output_dir)
        
        return transcription_data
        
    except subprocess.TimeoutExpired:
        raise Exception("WhisperX process timed out")
    except subprocess.CalledProcessError as e:
        raise Exception(f"WhisperX process failed with exit code {e.returncode}: {e.stderr}")
    except Exception as e:
        raise Exception(f"WhisperX execution error: {str(e)}")
```

## 📋 Конфигурация и константы

### Упрощенная конфигурация (config.yaml)
```yaml
# Directory paths
shared_directory: "shared"

# WhisperX default settings
whisperx:
  model_size: "base"
  language: "ru"
  temperature: 0.1
  compute_type: "int8"
  device: "cpu"
  debug: false

# Processing settings
processing:
  max_retry_attempts: 3
  timeout_minutes: 10
  file_check_attempts: 3
  polling_interval_seconds: 10

# Queue settings
queue:
  immediate_operations: ["DELETE"]
```

### Константы приложения
```python
# File status constants
FILE_STATUS_NOT_FOUND = "file_not_found"
FILE_STATUS_PENDING = "pending"
FILE_STATUS_PROCESSING = "processing"
FILE_STATUS_COMPLETED = "completed"
FILE_STATUS_ERROR = "error"

# Priority constants
PRIORITY_API = "api"
PRIORITY_AUTO = "auto"

# Supported audio formats
SUPPORTED_AUDIO_FORMATS = [".mp3", ".wav", ".m4a", ".ogg", ".flac"]

# Default timeout values
DEFAULT_PROCESSING_TIMEOUT = 600  # 10 minutes
DEFAULT_FILE_CHECK_ATTEMPTS = 3
DEFAULT_POLLING_INTERVAL = 10  # seconds
```

## 🔗 Связанные файлы
- **[План разработки](./development_plan.md)** - этапы реализации
- **[Статусные файлы](./status_files.md)** - детальное описание форматов
- **[API спецификация](./api.md)** - HTTP endpoints
- **[Техническое задание](../specs/technical_specification.md)** - полная спецификация
