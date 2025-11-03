# 📋 Статусные файлы Audio Transcriber

## 📁 Обзор системы статусных файлов

Система использует файлы в shared директории для отслеживания состояния обработки аудиофайлов:

- **`.in_progress`** - файлы в процессе обработки
- **`.result`** - завершенные результаты транскрипции
- **Исходные аудиофайлы** - входные файлы для обработки

## 🔄 .in_progress файлы

### Назначение
Создаются при начале обработки аудиофайла и содержат информацию о текущем прогрессе и статусе задачи.

### Формат имени файла
```
{audio_filename_without_extension}.in_progress
```

**Примеры:**
- `audio.mp3` → `audio.in_progress`
- `interview.wav` → `interview.in_progress`
- `podcast_episode_1.flac` → `podcast_episode_1.in_progress`

### Структура JSON
```json
{
  "filename": "audio.mp3",
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-03T10:32:00.123456",
  "priority": "API",
  "progress": 45.5,
  "model_used": "small",
  "language": "en",
  "estimated_completion": "2025-11-03T10:35:00.000000",
  "current_stage": "transcription",
  "retry_count": 0,
  "client_id": "client-550e8400",
  "debug_info": {
    "whisperx_process_id": 12345,
    "memory_usage_mb": 512.3,
    "temp_files": ["/tmp/whisperx_temp_abc123"]
  }
}
```

### Описание полей

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `filename` | string | ✅ | Имя исходного аудиофайла |
| `status` | string | ✅ | Статус: "processing" или "error" |
| `task_id` | string | ✅ | Уникальный идентификатор задачи |
| `started_at` | string | ✅ | ISO 8601 timestamp начала обработки |
| `priority` | string | ✅ | Приоритет: "DELETE", "API", "AUTO_SCAN" |
| `progress` | float | ❌ | Прогресс обработки (0.0-100.0) |
| `model_used` | string | ❌ | Используемая модель Whisper |
| `language` | string | ❌ | Определенный/заданный язык |
| `estimated_completion` | string | ❌ | Ожидаемое время завершения |
| `current_stage` | string | ❌ | Текущий этап обработки |
| `retry_count` | integer | ❌ | Количество повторных попыток |
| `client_id` | string | ❌ | Идентификатор клиента |
| `debug_info` | object | ❌ | Отладочная информация |

### Возможные значения полей

**status:**
- `"processing"` - файл обрабатывается
- `"error"` - произошла ошибка обработки

**priority:**
- `"DELETE"` - задача удаления (наивысший приоритет)
- `"API"` - запрос через API
- `"AUTO_SCAN"` - автоматическое сканирование

**current_stage:**
- `"initialization"` - инициализация обработки
- `"audio_loading"` - загрузка аудиофайла
- `"transcription"` - процесс транскрипции
- `"post_processing"` - постобработка результата
- `"saving_result"` - сохранение результата

### Примеры .in_progress файлов

**Успешная обработка в процессе:**
```json
{
  "filename": "interview.mp3",
  "status": "processing",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2025-11-03T10:32:00.123456",
  "priority": "API",
  "progress": 67.3,
  "model_used": "small",
  "language": "en",
  "estimated_completion": "2025-11-03T10:35:00.000000",
  "current_stage": "transcription"
}
```

**Обработка с ошибкой:**
```json
{
  "filename": "corrupted.wav",
  "status": "error",
  "task_id": "660f9511-f3ac-52e5-b827-557766551111",
  "started_at": "2025-11-03T10:30:00.456789",
  "priority": "API",
  "progress": 15.0,
  "model_used": "base",
  "current_stage": "audio_loading",
  "retry_count": 2,
  "error_message": "Unable to load audio file: format not supported",
  "debug_info": {
    "error_code": "AUDIO_LOAD_FAILED",
    "ffmpeg_output": "Error: Invalid data found when processing input"
  }
}
```

## ✅ .result файлы

### Назначение
Создаются при успешном завершении транскрипции и содержат полный результат обработки.

### Формат имени файла
```
{audio_filename_without_extension}.result
```

### Структура JSON
```json
{
  "filename": "audio.mp3",
  "text": "Complete transcribed text from the audio file...",
  "status": "completed",
  "timestamp": "2025-11-03T10:33:18.789012",
  "model_used": "small",
  "language": "en",
  "confidence": 0.923,
  "duration": 120.5,
  "file_size": 2048576,
  "processing_time": 78.4,
  "word_count": 234,
  "segments": [
    {
      "start": 0.0,
      "end": 3.5,
      "text": "This is the first segment",
      "confidence": 0.95,
      "words": [
        {
          "start": 0.0,
          "end": 0.4,
          "text": "This",
          "confidence": 0.98
        },
        {
          "start": 0.5,
          "end": 0.7,
          "text": "is",
          "confidence": 0.92
        }
      ]
    }
  ],
  "metadata": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "priority": "API",
    "client_id": "client-550e8400",
    "whisperx_version": "3.1.1",
    "compute_type": "float32",
    "device": "cpu"
  }
}
```

### Описание полей

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `filename` | string | ✅ | Имя исходного аудиофайла |
| `text` | string | ✅ | Полный транскрибированный текст |
| `status` | string | ✅ | Всегда "completed" |
| `timestamp` | string | ✅ | ISO 8601 timestamp завершения |
| `model_used` | string | ✅ | Использованная модель Whisper |
| `language` | string | ✅ | Определенный язык аудио |
| `confidence` | float | ✅ | Средняя уверенность (0.0-1.0) |
| `duration` | float | ✅ | Длительность аудио в секундах |
| `file_size` | integer | ✅ | Размер исходного файла в байтах |
| `processing_time` | float | ✅ | Время обработки в секундах |
| `word_count` | integer | ✅ | Количество слов в тексте |
| `segments` | array | ✅ | Массив сегментов с временными метками |
| `metadata` | object | ❌ | Дополнительные метаданные |

### Структура segments
```json
{
  "start": 0.0,              // Время начала в секундах
  "end": 3.5,                // Время окончания в секундах  
  "text": "Segment text",     // Текст сегмента
  "confidence": 0.95,        // Уверенность сегмента
  "words": [                 // Массив слов (опционально)
    {
      "start": 0.0,
      "end": 0.4,
      "text": "Word",
      "confidence": 0.98
    }
  ]
}
```

### Примеры .result файлов

**Короткий аудиофайл:**
```json
{
  "filename": "greeting.wav",
  "text": "Hello, how are you today?",
  "status": "completed",
  "timestamp": "2025-11-03T10:33:18.789012",
  "model_used": "tiny",
  "language": "en",
  "confidence": 0.987,
  "duration": 2.3,
  "file_size": 147456,
  "processing_time": 5.2,
  "word_count": 6,
  "segments": [
    {
      "start": 0.0,
      "end": 2.3,
      "text": "Hello, how are you today?",
      "confidence": 0.987,
      "words": [
        {"start": 0.0, "end": 0.5, "text": "Hello,", "confidence": 0.99},
        {"start": 0.6, "end": 0.9, "text": "how", "confidence": 0.98},
        {"start": 1.0, "end": 1.2, "text": "are", "confidence": 0.99},
        {"start": 1.3, "end": 1.5, "text": "you", "confidence": 0.98},
        {"start": 1.6, "end": 2.3, "text": "today?", "confidence": 0.99}
      ]
    }
  ],
  "metadata": {
    "task_id": "123e4567-e89b-12d3-a456-426614174000",
    "priority": "API",
    "whisperx_version": "3.1.1",
    "compute_type": "float32",
    "device": "cpu"
  }
}
```

**Длинный аудиофайл с множественными сегментами:**
```json
{
  "filename": "podcast_episode.mp3",
  "text": "Welcome to our podcast. Today we're discussing artificial intelligence and its impact on society. Machine learning has revolutionized many industries...",
  "status": "completed", 
  "timestamp": "2025-11-03T10:45:22.123456",
  "model_used": "large",
  "language": "en",
  "confidence": 0.912,
  "duration": 1800.0,
  "file_size": 25165824,
  "processing_time": 245.7,
  "word_count": 2847,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Welcome to our podcast.",
      "confidence": 0.96
    },
    {
      "start": 5.8,
      "end": 12.1,
      "text": "Today we're discussing artificial intelligence and its impact on society.",
      "confidence": 0.94
    },
    {
      "start": 13.0,
      "end": 18.5,
      "text": "Machine learning has revolutionized many industries.",
      "confidence": 0.89
    }
  ],
  "metadata": {
    "task_id": "789f0123-4567-8901-b234-567890123456",
    "priority": "AUTO_SCAN",
    "whisperx_version": "3.1.1",
    "compute_type": "float16",
    "device": "cuda"
  }
}
```

## 🔄 Жизненный цикл файлов

### Создание файлов
1. **Появление аудиофайла** в shared директории
2. **Создание .in_progress** при начале обработки
3. **Обновление .in_progress** по мере выполнения
4. **Создание .result** при успешном завершении
5. **Удаление .in_progress** после создания .result

### Состояния и переходы
```
[audio.mp3] → [audio.in_progress] → [audio.result]
                      ↓
              (при ошибке остается .in_progress с status: "error")
```

### Очистка файлов
При DELETE запросе удаляются все связанные файлы:
- Исходный аудиофайл
- .in_progress файл
- .result файл
- Любые временные файлы

## 🛠️ Утилиты для работы с файлами

### Проверка статуса файла
```python
async def get_file_status(filename: str) -> TaskStatus:
    """
    Определяет статус файла по наличию файлов:
    1. Проверка .result (COMPLETED)
    2. Проверка .in_progress (PROCESSING/ERROR)
    3. Проверка исходного файла (FILE_NOT_FOUND)
    4. Проверка очереди задач (PENDING)
    """
    base_name = Path(filename).stem
    
    # Проверка результата
    if (shared_dir / f"{base_name}.result").exists():
        return TaskStatus.COMPLETED
    
    # Проверка обработки
    in_progress_file = shared_dir / f"{base_name}.in_progress"
    if in_progress_file.exists():
        try:
            with open(in_progress_file) as f:
                data = json.load(f)
                return TaskStatus.ERROR if data.get("status") == "error" else TaskStatus.PROCESSING
        except:
            return TaskStatus.PROCESSING
    
    # Проверка исходного файла
    if not (shared_dir / filename).exists():
        return TaskStatus.FILE_NOT_FOUND
    
    # Проверка очереди
    if await task_manager.has_task(filename):
        return TaskStatus.PENDING
    
    return None
```

### Чтение статусных файлов
```python
async def read_in_progress_file(filename: str) -> Optional[dict]:
    """Чтение .in_progress файла"""
    base_name = Path(filename).stem
    file_path = shared_dir / f"{base_name}.in_progress"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading .in_progress file: {e}")
        return None

async def read_result_file(filename: str) -> Optional[dict]:
    """Чтение .result файла"""
    base_name = Path(filename).stem
    file_path = shared_dir / f"{base_name}.result"
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading .result file: {e}")
        return None
```

### Обновление статусных файлов
```python
async def update_in_progress_file(filename: str, data: dict):
    """Обновление .in_progress файла"""
    base_name = Path(filename).stem
    file_path = shared_dir / f"{base_name}.in_progress"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error updating .in_progress file: {e}")
        raise

async def create_result_file(filename: str, result_data: dict):
    """Создание .result файла"""
    base_name = Path(filename).stem
    file_path = shared_dir / f"{base_name}.result"
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, indent=2, ensure_ascii=False)
        
        # Удаление .in_progress файла после успешного создания .result
        in_progress_path = shared_dir / f"{base_name}.in_progress"
        if in_progress_path.exists():
            in_progress_path.unlink()
            
    except Exception as e:
        logger.error(f"Error creating .result file: {e}")
        raise
```

## 🔍 Мониторинг и отладка

### Поиск проблемных файлов
```bash
# Поиск зависших .in_progress файлов (старше 1 часа)
find ./shared -name "*.in_progress" -mtime +1h

# Поиск файлов с ошибками
grep -l '"status": "error"' ./shared/*.in_progress

# Статистика по статусам
echo "Processing files:"; ls ./shared/*.in_progress | wc -l
echo "Completed files:"; ls ./shared/*.result | wc -l
```

### Проверка валидности JSON
```python
def validate_status_files(shared_dir: Path):
    """Проверка всех статусных файлов на корректность JSON"""
    for file_path in shared_dir.glob("*.in_progress"):
        try:
            with open(file_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {e}")
    
    for file_path in shared_dir.glob("*.result"):
        try:
            with open(file_path) as f:
                json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON in {file_path}: {e}")
```

---

**Дата обновления:** 3 ноября 2025  
**Версия:** 1.0
