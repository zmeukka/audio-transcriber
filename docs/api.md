# 📡 API Спецификация

## 🎯 Базовая информация
- **URL:** `http://localhost:8000`
- **Content-Type:** `application/json`
- **Методы:** POST, DELETE, GET

## 📤 POST /transcribe

### Запрос транскрипции аудиофайла

#### Параметры запроса
```json
{
  "filename": "audio.mp3",           // Обязательно: имя файла в shared директории
  "language": "ru",                  // Опционально: язык (по умолчанию из config)
  "model_size": "base",              // Опционально: размер модели (tiny/base/small/medium/large)
  "temperature": 0.1,                // Опционально: температура модели (0.0-1.0)
  "compute_type": "int8",            // Опционально: тип вычислений (float32/float16/int8)
  "device": "cpu",                   // Опционально: устройство (cpu/cuda)
  "debug": false                     // Опционально: debug режим для этого запроса (по умолчанию false)
}
```

#### Ответ
```json
{
  "status": "started",
  "message": "Transcription started",
  "filename": "audio.mp3",
  "settings": {
    "model_size": "base",
    "language": "ru",
    "temperature": 0.1
  }
}
```

#### Логика обработки запроса

##### 🔍 1. Проверка наличия файла (с повторами)
```
1. Проверить наличие файла в shared/
2. Если файл НЕ найден:
   - Повторить проверку 5 раз с интервалом 1 секунда
   - Если после 5 попыток файл не найден → HTTP 404
3. Если файл найден → переход к следующему шагу
```

##### 📊 2. Проверка статуса обработки
```
Проверить наличие файлов:
- filename.in_progress (файл обрабатывается)
- filename.result (файл уже обработан)

Сценарии:
├── Есть .result + НЕТ .in_progress → Файл готов (возврат результата)
├── Есть .in_progress → Файл обрабатывается (ожидание завершения)  
└── НЕТ .result + НЕТ .in_progress → Новый файл (в очередь на обработку)
```

##### ⏱️ 3. Обработка по сценариям

**Сценарий A: Файл уже обработан**
```json
{
  "status": "completed",
  "message": "File already processed, returning cached result",
  "result": {
    "transcription": {...},
    "metadata": {...}
  }
}
```

**Сценарий B: Файл обрабатывается**
```json
{
  "status": "processing",
  "message": "File is currently being processed, waiting for completion",
  "wait_time_seconds": 120,
  "current_attempt": 1
}
```
*Система ожидает завершения обработки и возвращает результат*

**Сценарий C: Новый файл**
```json
{
  "status": "started", 
  "message": "File added to processing queue",
  "queue_position": 1,
  "estimated_wait_time": "2-5 minutes"
}
```

#### Коды ответов
| Код | Сценарий | Описание |
|-----|----------|----------|
| 200 | Файл готов | Возврат готового результата |
| 202 | Обработка | Файл в процессе или в очереди |
| 404 | Файл не найден | После 5 попыток файл не найден |
| 409 | Конфликт настроек | Файл обрабатывается с другими настройками |

#### Примеры детальных ответов

##### ✅ HTTP 200 - Файл уже обработан
```json
{
  "status": "completed",
  "message": "File already processed, returning cached result",
  "filename": "audio.mp3",
  "cached": true,
  "processing_completed_at": "2024-01-01T10:05:00Z",
  "result": {
    "transcription": {
      "text": "Полный текст транскрипции...",
      "segments": [
        {
          "start": 0.0,
          "end": 5.2,
          "text": "Привет, как дела?"
        }
      ]
    },
    "metadata": {
      "duration_seconds": 135.5,
      "confidence": 0.89,
      "word_count": 156
    }
  }
}
```

##### ⏳ HTTP 202 - Файл в процессе обработки (ожидание)
```json
{
  "status": "processing",
  "message": "File is currently being processed, waiting for completion",
  "filename": "audio.mp3",
  "wait_started_at": "2024-01-01T10:00:00Z",
  "current_attempt": 1,
  "estimated_completion": "2024-01-01T10:03:00Z",
  "polling_info": {
    "check_status_url": "/status/audio.mp3",
    "recommended_interval_seconds": 5
  }
}
```

##### 🚀 HTTP 202 - Новый файл в очереди
```json
{
  "status": "queued",
  "message": "File added to processing queue",
  "filename": "audio.mp3",
  "queue_position": 1,
  "estimated_wait_time": "2-5 minutes"
}
```

##### 🔄 HTTP 202 - Перезапуск с новыми настройками
```json
{
  "status": "restarted",
  "message": "Previous processing interrupted, restarted with new settings", 
  "filename": "audio.mp3",
  "previous_settings": {
    "model_size": "base",
    "language": "ru"
  },
  "new_settings": {
    "model_size": "large",
    "language": "en"
  },
  "processing_restarted_at": "2024-01-01T10:00:00Z"
}
```

##### ❌ HTTP 404 - Файл не найден
```json
{
  "status": "error",
  "error_code": "file_not_found",
  "message": "Audio file not found after 5 attempts",
  "filename": "audio.mp3",
  "attempts_made": 5,
  "total_wait_time_seconds": 5,
  "suggestion": "Please ensure the file is uploaded to the shared directory"
}
```

##### ⚠️ HTTP 409 - Конфликт настроек (если система не может прервать)
```json
{
  "status": "conflict",
  "error_code": "settings_conflict",
  "message": "File is being processed with different settings and cannot be interrupted",
  "filename": "audio.mp3",
  "current_settings": {
    "model_size": "large",
    "language": "en"
  },
  "requested_settings": {
    "model_size": "base", 
    "language": "ru"
  },
  "suggestion": "Wait for current processing to complete or delete the file first"
}
```

## 🗑️ DELETE /transcribe

### Немедленное удаление файлов и прекращение обработки

**DELETE запросы выполняются немедленно, минуя очередь**

#### Параметры запроса
```json
{
  "filename": "audio.mp3"              // Один файл
}
```
или
```json
{
  "filenames": ["audio1.mp3", "audio2.wav", "audio3.m4a"]  // Несколько файлов
}
```

#### Логика выполнения DELETE
```
1. Немедленное выполнение (высший приоритет)
2. Прерывание текущей обработки файла (если обрабатывается)
3. Удаление файла из очереди обработки
4. Удаление всех связанных файлов:
   - filename.mp3 (исходный файл)
   - filename.in_progress (статус)
   - filename.result (результат)
5. Мгновенный ответ клиенту
```

#### Примеры ответов DELETE

##### ✅ Успешное удаление
```json
{
  "status": "deleted",
  "message": "Files deleted successfully",
  "filename": "audio.mp3",
  "deleted_files": ["audio.mp3", "audio.in_progress", "audio.result"],
  "processing_interrupted": true,
  "removed_from_queue": true,
  "execution_time_ms": 15
}
```

##### ⚠️ Частичное удаление
```json
{
  "status": "partially_deleted",
  "message": "Some files were not found",
  "filename": "audio.mp3", 
  "deleted_files": ["audio.mp3"],
  "not_found_files": ["audio.in_progress", "audio.result"],
  "processing_interrupted": false,
  "removed_from_queue": true
}
```

##### ❌ Файл не найден
```json
{
  "status": "not_found",
  "message": "No files found to delete",
  "filename": "audio.mp3",
  "deleted_files": [],
  "processing_interrupted": false,
  "removed_from_queue": false
}
```

## 🔄 Система приоритетной очереди

### Приоритеты обработки

| Приоритет | Тип запроса | Описание |
|-----------|-------------|----------|
| **0** | DELETE | Немедленное выполнение, минуя очередь |
| **1** | POST/GET API | Высший приоритет в очереди |
| **2** | Auto-scan | Файлы из автосканирования shared директории |

### Примеры ответов с информацией об очереди

##### 🚀 POST запрос - высокий приоритет
```json
{
  "status": "queued",
  "message": "File added to processing queue with high priority",
  "filename": "audio.mp3",
  "queue_info": {
    "priority": 1,
    "source": "api_request",
    "position": 1,
    "estimated_wait": "2-5 minutes",
    "ahead_in_queue": 0
  }
}
```

##### 📁 Auto-scan - низкий приоритет  
```json
{
  "status": "queued",
  "message": "File discovered via directory scan, added to queue",
  "filename": "auto_discovered.mp3",
  "queue_info": {
    "priority": 2,
    "source": "shared_scan", 
    "position": 5,
    "estimated_wait": "15-25 minutes",
    "ahead_in_queue": 4
  }
}
```

## 🐛 Debug режим при ошибках

### Включение через параметр запроса
```json
{
  "filename": "audio.mp3",
  "debug": true  // Включает детальную информацию при ошибках
}
```

**По умолчанию:** `debug: false`

### Поведение при ошибках

#### Обычный режим (debug: false)
```json
{
  "status": "error",
  "error_code": "whisperx_failed", 
  "message": "WhisperX process failed",
  "filename": "audio.mp3",
  "suggestion": "Check audio file format and try again"
}
```

#### Debug режим (debug: true)
```json
{
  "status": "error",
  "filename": "audio.mp3", 
  "error": {
    "code": "WhisperXError",
    "message": "WhisperX process failed with exit code 1",
    "timestamp": "2024-01-01T10:05:00Z",
    "attempt": 2
  },
  "debug_info": {
    "in_progress_content": {
      "filename": "audio.mp3",
      "status": "processing",
      "start_time": "2024-01-01T10:00:00Z",
      "attempt": 2,
      "settings": {...},
      "error": {...}
    }
  }
}
```

⚠️ **Внимание:** Debug режим раскрывает внутреннюю информацию системы. Используйте только при диагностике проблем.

#### Примеры запросов

**Минимальный запрос:**
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{"filename": "audio.mp3"}'
```

**Полный запрос:**
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.mp3",
    "language": "en",
    "model_size": "large",
    "temperature": 0.0
  }'
```

**Запрос с debug режимом:**
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.mp3",
    "debug": true
  }'
```
