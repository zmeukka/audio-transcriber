# 📊 Структуры данных Audio Transcriber

## 🔧 Конфигурация системы

### config.yaml
```yaml
# Directory paths - simplified to single shared directory
shared_directory: "./shared"

# Processing settings
processing_timeout: 180  # 3 minutes
max_retries: 3
log_level: "INFO"

# API configuration
api:
  host: "0.0.0.0"
  port: 8000
  debug: false

# WhisperX settings
whisperx:
  default_model: "small"
  default_compute_type: "float32" 
  default_language: null  # Auto-detect
  batch_size: 16
  device: "cpu"  # or "cuda" if GPU available

# File monitoring
monitoring:
  enabled: true
  scan_interval: 60  # seconds
```

## 📋 API модели данных

### Запросы (Requests)

#### TranscribeRequest
```python
{
  "filename": str,                    # Имя аудиофайла (обязательно)
  "language": str | null,             # Код языка или null для автоопределения
  "model": "tiny|base|small|medium|large",  # Модель Whisper
  "compute_type": "float16|float32|int8",   # Тип вычислений
  "output_format": "json|txt|srt|vtt|tsv", # Формат вывода
  "debug": bool,                      # Режим отладки
  "temperature": float,               # Температура семплирования (0.0-1.0)
  "beam_size": int,                   # Размер луча для декодирования
  "best_of": int,                     # Количество кандидатов
  "patience": float,                  # Терпение для beam search
  "word_timestamps": bool             # Временные метки слов
}
```

#### DeleteRequest
```python
{
  "filename": str,     # Имя файла для удаления
  "force": bool        # Принудительное удаление даже при обработке
}
```

### Ответы (Responses)

#### TranscribeResponse
```python
{
  "status": "pending|processing|completed|error|file_not_found",
  "filename": str,
  "task_id": str | null,              # ID задачи
  "message": str,                     # Описание статуса
  "debug_info": dict | null,          # Отладочная информация
  "estimated_wait_time": float | null, # Ожидаемое время ожидания
  "queue_position": int | null        # Позиция в очереди
}
```

#### StatusResponse
```python
{
  "status": "pending|processing|completed|error|file_not_found",
  "filename": str,
  "progress": float | null,           # Прогресс обработки (0-100)
  "message": str,
  "queue_position": int | null,
  "priority": str | null,             # Приоритет задачи
  "estimated_completion": datetime | null,
  "processing_time": float | null,    # Время обработки в секундах
  "debug_info": dict | null
}
```

#### ResultResponse
```python
{
  "status": "success|not_found|error",
  "filename": str,
  "result": TranscriptionResult | null,
  "message": str
}
```

#### TranscriptionResult
```python
{
  "filename": str,
  "language": str,                    # Определенный язык
  "duration": float,                  # Длительность аудио в секундах
  "text": str,                        # Полный транскрибированный текст
  "segments": [TranscriptionSegment], # Сегменты с временными метками
  "word_count": int,                  # Количество слов
  "confidence_avg": float | null,     # Средняя уверенность
  "model_used": str,                  # Использованная модель
  "processing_time": float,           # Время обработки
  "timestamp": datetime               # Время создания результата
}
```

#### TranscriptionSegment
```python
{
  "start": float,                     # Время начала в секундах
  "end": float,                       # Время окончания в секундах
  "text": str,                        # Текст сегмента
  "confidence": float | null,         # Уверенность сегмента
  "words": [dict] | null              # Детали уровня слов
}
```

## 🔄 Системы приоритетов

### TaskPriority (Enum)
```python
DELETE = 0      # Немедленное удаление (наивысший приоритет)
API = 1         # Запросы через API
AUTO_SCAN = 2   # Автоматическое сканирование файлов
```

### TaskStatus (Enum)
```python
PENDING = "pending"           # Ожидает обработки
PROCESSING = "processing"     # В процессе обработки
COMPLETED = "completed"       # Обработка завершена
ERROR = "error"              # Ошибка обработки
FILE_NOT_FOUND = "file_not_found"  # Файл не найден
```

## 📁 Форматы файлов состояния

### .in_progress файлы
```json
{
  "filename": "audio.mp3",
  "status": "processing",
  "task_id": "uuid-string",
  "started_at": "2025-11-03T10:30:00",
  "priority": "API",
  "progress": 45.5,
  "model_used": "small",
  "language": "en",
  "estimated_completion": "2025-11-03T10:33:00"
}
```

### .result файлы
```json
{
  "filename": "audio.mp3",
  "text": "Полный транскрибированный текст...",
  "status": "completed",
  "timestamp": "2025-11-03T10:32:15",
  "model_used": "small",
  "language": "en",
  "confidence": 0.92,
  "duration": 120.5,
  "file_size": 2048576,
  "processing_time": 45.2,
  "word_count": 234,
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "Первый сегмент текста",
      "confidence": 0.95
    }
  ]
}
```

## 🏗️ Внутренние структуры данных

### ProcessingTask
```python
{
  "task_id": str,                     # Уникальный ID задачи
  "filename": str,                    # Имя файла
  "priority": TaskPriority,           # Приоритет задачи
  "status": TaskStatus,               # Текущий статус
  "created_at": datetime,             # Время создания
  "transcribe_request": TranscribeRequest | None,
  "started_at": datetime | None,      # Время начала обработки
  "completed_at": datetime | None,    # Время завершения
  "error_message": str | None,        # Сообщение об ошибке
  "retry_count": int,                 # Количество попыток
  "client_id": str | None             # ID клиента
}
```

### TaskInfo  
```python
{
  "task_id": str,
  "filename": str,
  "priority": TaskPriority,
  "status": TaskStatus,
  "created_at": datetime,
  "started_at": datetime | None,
  "completed_at": datetime | None,
  "error_message": str | None,
  "retry_count": int,
  "client_id": str | None
}
```

## 🎯 Поддерживаемые форматы

### Аудиоформаты
- MP3
- WAV  
- FLAC
- M4A
- OGG
- WMA

### Модели Whisper
- tiny (39 MB)
- base (74 MB)
- small (244 MB)
- medium (769 MB)
- large (1550 MB)

### Типы вычислений
- float16 (быстрее, меньше точности)
- float32 (баланс скорости и точности)
- int8 (самый быстрый, наименьшая точность)

### Форматы вывода
- json (структурированные данные)
- txt (только текст)
- srt (субтитры)
- vtt (веб-субтитры)
- tsv (табулированные данные)

---

**Дата обновления:** 3 ноября 2025  
**Версия:** 1.0
