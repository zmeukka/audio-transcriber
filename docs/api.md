# 📡 API документация Audio Transcriber

## 🌐 Базовая информация

**Base URL:** `http://localhost:8000`  
**Content-Type:** `application/json`  
**API версия:** 1.0.0  

## 📋 Endpoints

### 🔍 GET /health
Проверка состояния сервиса и системных ресурсов

#### Запрос
```bash
curl -X GET http://localhost:8000/health
```

#### Ответ
```json
{
  "status": "healthy",
  "service": "Audio Transcriber API", 
  "version": "1.0.0",
  "uptime": 3600.5,
  "whisperx_available": true,
  "models_loaded": ["tiny", "base", "small"],
  "system_info": {
    "cpu_percent": 25.4,
    "memory_percent": 68.2,
    "memory_available_gb": 8.5
  },
  "disk_space": {
    "total_gb": 500.0,
    "used_gb": 250.0,
    "free_gb": 250.0,
    "free_percent": 50.0
  }
}
```

### 🎵 POST /transcribe
Запуск транскрипции аудиофайла

#### Минимальный запрос
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.mp3"
  }'
```

#### Полный запрос с параметрами
```bash
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.mp3",
    "language": "en",
    "model": "small",
    "compute_type": "float32",
    "output_format": "json",
    "debug": true,
    "temperature": 0.0,
    "beam_size": 5,
    "best_of": 5,
    "patience": 1.0,
    "word_timestamps": true
  }'
```

#### Параметры запроса
| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|-------------|--------------|----------|
| `filename` | string | ✅ | - | Имя аудиофайла в shared директории |
| `language` | string\|null | ❌ | null | Код языка (en, ru, etc.) или null для автоопределения |
| `model` | enum | ❌ | "small" | Модель Whisper: tiny, base, small, medium, large |
| `compute_type` | enum | ❌ | "float32" | Тип вычислений: float16, float32, int8 |
| `output_format` | enum | ❌ | "json" | Формат вывода: json, txt, srt, vtt, tsv |
| `debug` | boolean | ❌ | false | Включение отладочной информации |
| `temperature` | float | ❌ | 0.0 | Температура семплирования (0.0-1.0) |
| `beam_size` | integer | ❌ | 5 | Размер луча для декодирования (≥1) |
| `best_of` | integer | ❌ | 5 | Количество кандидатов (≥1) |
| `patience` | float | ❌ | 1.0 | Терпение для beam search (≥0.0) |
| `word_timestamps` | boolean | ❌ | true | Включение временных меток слов |

#### Возможные ответы

**✅ Файл добавлен в очередь (новый файл)**
```json
{
  "status": "pending",
  "filename": "audio.mp3",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Task added to processing queue",
  "queue_position": 2,
  "estimated_wait_time": 120.5,
  "debug_info": {
    "file_exists": true,
    "file_size": 2048576,
    "queue_length": 3
  }
}
```

**🔄 Файл уже обрабатывается**
```json
{
  "status": "processing", 
  "filename": "audio.mp3",
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "File is currently being processed",
  "queue_position": null
}
```

**✅ Файл уже обработан**
```json
{
  "status": "completed",
  "filename": "audio.mp3",
  "task_id": null,
  "message": "File already processed. Use /result endpoint to get results."
}
```

**❌ Файл не найден**
```json
{
  "status": "file_not_found",
  "filename": "audio.mp3", 
  "task_id": null,
  "message": "File 'audio.mp3' not found after 3 attempts"
}
```

### 🗑️ DELETE /transcribe
Удаление файла и прекращение обработки

#### Запрос
```bash
curl -X DELETE http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "audio.mp3",
    "force": true
  }'
```

#### Параметры
| Параметр | Тип | Обязательный | Описание |
|----------|-----|-------------|----------|
| `filename` | string | ✅ | Имя файла для удаления |
| `force` | boolean | ❌ | Принудительное удаление даже при обработке |

#### Ответ
```json
{
  "status": "success",
  "filename": "audio.mp3",
  "message": "Successfully deleted 4 files",
  "files_deleted": [
    "/app/shared/audio.mp3",
    "/app/shared/audio.in_progress", 
    "/app/shared/audio.result",
    "/app/shared/audio.txt"
  ]
}
```

### 📊 GET /status/{filename}
Проверка статуса обработки файла

#### Запрос
```bash
curl http://localhost:8000/status/audio.mp3?debug=true
```

#### Параметры query
| Параметр | Тип | Описание |
|----------|-----|----------|
| `debug` | boolean | Включение отладочной информации |

#### Возможные ответы

**⏳ Ожидает обработки**
```json
{
  "status": "pending",
  "filename": "audio.mp3",
  "progress": null,
  "message": "File status: pending",
  "queue_position": 1,
  "priority": "API",
  "estimated_completion": "2025-11-03T10:35:00",
  "processing_time": null,
  "debug_info": {
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "created_at": "2025-11-03T10:30:00",
    "queue_length": 3
  }
}
```

**🔄 В процессе обработки**
```json
{
  "status": "processing",
  "filename": "audio.mp3", 
  "progress": 65.5,
  "message": "File status: processing",
  "queue_position": null,
  "priority": "API",
  "estimated_completion": null,
  "processing_time": 45.2,
  "debug_info": {
    "started_at": "2025-11-03T10:32:00",
    "model_used": "small",
    "current_stage": "transcription"
  }
}
```

**✅ Обработка завершена**
```json
{
  "status": "completed",
  "filename": "audio.mp3",
  "progress": 100.0,
  "message": "File status: completed", 
  "queue_position": null,
  "priority": null,
  "estimated_completion": null,
  "processing_time": 78.4
}
```

### 📄 GET /result/{filename}
Получение результата транскрипции

#### Запрос
```bash
curl http://localhost:8000/result/audio.mp3
```

#### Ответ при успешной обработке
```json
{
  "status": "success",
  "filename": "audio.mp3",
  "result": {
    "filename": "audio.mp3",
    "language": "en",
    "duration": 120.5,
    "text": "This is the complete transcribed text from the audio file.",
    "segments": [
      {
        "start": 0.0,
        "end": 3.5,
        "text": "This is the complete",
        "confidence": 0.95,
        "words": [
          {"start": 0.0, "end": 0.4, "text": "This", "confidence": 0.98},
          {"start": 0.5, "end": 0.7, "text": "is", "confidence": 0.92}
        ]
      }
    ],
    "word_count": 12,
    "confidence_avg": 0.92,
    "model_used": "small",
    "processing_time": 78.4,
    "timestamp": "2025-11-03T10:33:18"
  },
  "message": "Result retrieved successfully"
}
```

#### Ответ при отсутствии результата
```json
{
  "status": "not_found",
  "filename": "audio.mp3",
  "result": null,
  "message": "No result found for this file"
}
```

### 📋 GET /queue
Получение информации о текущей очереди

#### Запрос
```bash
curl http://localhost:8000/queue
```

#### Ответ
```json
{
  "status": "success",
  "queue_length": 3,
  "processing_count": 1,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "filename": "audio1.mp3",
      "priority": "API",
      "status": "processing",
      "created_at": "2025-11-03T10:30:00",
      "started_at": "2025-11-03T10:32:00"
    },
    {
      "task_id": "660f9511-f3ac-52e5-b827-557766551111",
      "filename": "audio2.wav",
      "priority": "API", 
      "status": "pending",
      "created_at": "2025-11-03T10:31:00",
      "started_at": null
    },
    {
      "task_id": "770a0622-04bd-63f6-c938-668877662222", 
      "filename": "audio3.flac",
      "priority": "AUTO_SCAN",
      "status": "pending",
      "created_at": "2025-11-03T10:32:00",
      "started_at": null
    }
  ]
}
```

### 🤖 GET /models
Получение списка доступных моделей

#### Запрос
```bash
curl http://localhost:8000/models
```

#### Ответ
```json
{
  "status": "success",
  "models": [
    {
      "name": "tiny",
      "size_mb": 39,
      "loaded": true,
      "path": "/app/models/faster-whisper-tiny"
    },
    {
      "name": "base", 
      "size_mb": 74,
      "loaded": true,
      "path": "/app/models/faster-whisper-base"
    },
    {
      "name": "small",
      "size_mb": 244,
      "loaded": true,
      "path": "/app/models/faster-whisper-small"
    }
  ]
}
```

## 🚨 Коды ошибок

### HTTP статус коды
- **200** - Успешный запрос
- **400** - Неверные параметры запроса  
- **404** - Endpoint не найден
- **422** - Ошибка валидации данных
- **500** - Внутренняя ошибка сервера
- **503** - Сервис недоступен

### Стандартный формат ошибки
```json
{
  "status": "error",
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid filename format",
  "details": {
    "field": "filename",
    "constraint": "cannot_be_empty"
  },
  "timestamp": "2025-11-03T10:30:00"
}
```

### Типичные ошибки

**Неверное имя файла**
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "filename"],
      "msg": "Filename contains invalid characters: ['<', '>', ':']",
      "input": "audio<test>.mp3"
    }
  ]
}
```

**Превышение лимитов**
```json
{
  "detail": "Temperature must be between 0.0 and 1.0"
}
```

## 🔧 Режим отладки

### Включение debug режима
Debug режим включается параметром `debug: true` в запросе и предоставляет дополнительную информацию:

#### В POST /transcribe
```json
{
  "debug_info": {
    "file_exists": true,
    "file_size": 2048576,
    "file_modified": "2025-11-03T10:29:00",
    "queue_length": 3,
    "system_load": 0.65,
    "available_memory_gb": 8.5
  }
}
```

#### В GET /status
```json
{
  "debug_info": {
    "in_progress_file_content": {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "started_at": "2025-11-03T10:32:00",
      "progress": 45.5,
      "current_stage": "transcription"
    },
    "task_timeline": [
      {"time": "2025-11-03T10:30:00", "event": "task_created"},
      {"time": "2025-11-03T10:32:00", "event": "processing_started"},
      {"time": "2025-11-03T10:32:30", "event": "transcription_progress_50"}
    ]
  }
}
```

## 📝 Примеры использования

### Полный workflow обработки файла
```bash
# 1. Проверка здоровья сервиса
curl http://localhost:8000/health

# 2. Запуск транскрипции
curl -X POST http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{"filename": "interview.mp3", "language": "en", "debug": true}'

# 3. Проверка статуса (повторять пока status != "completed")
curl http://localhost:8000/status/interview.mp3

# 4. Получение результата
curl http://localhost:8000/result/interview.mp3

# 5. Удаление файлов (опционально)
curl -X DELETE http://localhost:8000/transcribe \
  -H "Content-Type: application/json" \
  -d '{"filename": "interview.mp3"}'
```

### Batch обработка множественных файлов
```bash
# Запуск нескольких файлов
for file in audio1.mp3 audio2.wav audio3.flac; do
  curl -X POST http://localhost:8000/transcribe \
    -H "Content-Type: application/json" \
    -d "{\"filename\": \"$file\"}"
done

# Проверка очереди
curl http://localhost:8000/queue

# Проверка статуса всех файлов
for file in audio1.mp3 audio2.wav audio3.flac; do
  echo "Status for $file:"
  curl http://localhost:8000/status/$file
done
```

## 🔒 Рекомендации по безопасности

### Валидация имен файлов
- Запрещены символы: `< > : " | ? *`
- Максимальная длина: 255 символов
- Только UTF-8 кодировка

### Ограничения размера файлов
- Рекомендуемый максимум: 100 MB
- Timeout обработки: 180 секунд

### CORS настройки
В продакшн среде настройте CORS для ограничения доступа:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)
```

---

**Дата обновления:** 3 ноября 2025  
**Версия API:** 1.0.0
