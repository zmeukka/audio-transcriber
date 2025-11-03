# 📊 Статусные файлы

## 🔄 Файл состояния обработки (.in_progress)

### 📁 Назначение
Файл `filename.in_progress` создается при начале обработки аудиофайла и содержит информацию о текущем состоянии, попытках обработки и настройках.

### 📝 Структура JSON
```json
{
  "filename": "audio.mp3",
  "status": "processing",
  "start_time": "2024-01-01T10:00:00Z",
  "attempt": 1,
  "settings": {
    "model_size": "base",
    "language": "ru",
    "temperature": 0.1,
    "compute_type": "int8",
    "device": "cpu",
    "debug": false
  },
  "error": null
}
```

### 🔧 Поля описания

#### 📋 Основная информация
| Поле | Тип | Описание |
|------|-----|----------|
| `filename` | string | Имя обрабатываемого файла |
| `creation_time` | ISO8601 | Время создания файла статуса |
| `current_attempt` | integer | Номер текущей попытки обработки |
| `should_continue` | boolean | Флаг продолжения обработки |
| `priority` | string | Приоритет: "api_request" или "auto_scan" |

#### 👥 Клиенты API
| Поле | Тип | Описание |
|------|-----|----------|
| `api_clients` | array | UUID клиентов, ожидающих результат |

#### 🔄 Попытки обработки
Каждая попытка содержит:
| Поле | Тип | Описание |
|------|-----|----------|
| `attempt_number` | integer | Номер попытки (1, 2, 3...) |
| `start_time` | ISO8601 | Время начала попытки |
| `end_time` | ISO8601 | Время окончания (null если в процессе) |
| `status` | string | "processing", "completed", "failed" |
| `continue_processing` | boolean | Флаг продолжения этой попытки |
| `error` | object | Информация об ошибке (если есть) |

#### ⚙️ Настройки обработки
| Поле | Тип | Описание |
|------|-----|----------|
| `model_size` | string | Размер модели: tiny/base/small/medium/large |
| `language` | string | Код языка: ru/en/es/etc |
| `temperature` | float | Температура модели (0.0-1.0) |
| `compute_type` | string | Тип вычислений: float32/float16/int8 |
| `device` | string | Устройство: cpu/cuda |
| `debug` | boolean | Debug режим для данного запроса |

#### 📈 Прогресс обработки
| Поле | Тип | Описание |
|------|-----|----------|
| `stage` | string | Этап: "loading_model", "processing_audio", "generating_text" |
| `percentage` | integer | Процент выполнения (0-100) |

### 🚨 Обработка ошибок
```json
{
  "error": {
    "code": "whisperx_failed",
    "message": "WhisperX process exited with code 1",
    "details": "Audio file format not supported",
    "timestamp": "2024-01-01T10:05:00Z",
    "retry_after": 30
  }
}
```

## ✅ Файл результата (.result)

### 📁 Назначение
Файл `filename.result` создается после успешной обработки и содержит результаты транскрипции с метаданными.

### 📝 Структура JSON
```json
{
  "filename": "audio.mp3",
  "processing_start": "2024-01-01T10:00:00Z",
  "processing_end": "2024-01-01T10:02:30Z",
  "duration_seconds": 135.5,
  "processing_time_seconds": 150.3,
  "settings": {
    "model_size": "base",
    "language": "ru",
    "temperature": 0.1,
    "compute_type": "int8",
    "device": "cpu"
  },
  "transcription": {
    "text": "Полный текст транскрипции аудиозаписи...",
    "segments": [
      {
        "id": 0,
        "start": 0.0,
        "end": 5.2,
        "text": "Привет, как дела?",
        "confidence": 0.95
      },
      {
        "id": 1,
        "start": 5.2,
        "end": 10.1,
        "text": "Хорошо, спасибо. А у тебя?",
        "confidence": 0.92
      }
    ]
  },
  "metadata": {
    "confidence": 0.89,
    "language_detected": "ru",
    "word_count": 156,
    "segment_count": 45,
    "whisperx_version": "3.1.1",
    "model_info": {
      "name": "faster-whisper-base",
      "size_mb": 74,
      "load_time_seconds": 2.3
    }
  },
  "processing_stats": {
    "total_attempts": 1,
    "memory_peak_mb": 512,
    "cpu_time_seconds": 145.2
  }
}
```

### 🔧 Поля результата

#### 📋 Основная информация
| Поле | Тип | Описание |
|------|-----|----------|
| `filename` | string | Имя обработанного файла |
| `processing_start` | ISO8601 | Время начала обработки |
| `processing_end` | ISO8601 | Время завершения обработки |
| `duration_seconds` | float | Длительность аудио в секундах |
| `processing_time_seconds` | float | Время обработки в секундах |

#### 📝 Результат транскрипции
| Поле | Тип | Описание |
|------|-----|----------|
| `text` | string | Полный текст транскрипции |
| `segments` | array | Массив сегментов с временными метками |

#### 🎯 Сегменты транскрипции
Каждый сегмент содержит:
| Поле | Тип | Описание |
|------|-----|----------|
| `id` | integer | Порядковый номер сегмента |
| `start` | float | Время начала в секундах |
| `end` | float | Время окончания в секундах |
| `text` | string | Текст сегмента |
| `confidence` | float | Уверенность модели (0.0-1.0) |

#### 📊 Метаданные
| Поле | Тип | Описание |
|------|-----|----------|
| `confidence` | float | Общая уверенность транскрипции |
| `language_detected` | string | Определенный язык |
| `word_count` | integer | Количество слов в результате |
| `segment_count` | integer | Количество сегментов |

#### 🤖 Информация о модели
| Поле | Тип | Описание |
|------|-----|----------|
| `name` | string | Название модели |
| `size_mb` | integer | Размер модели в МБ |
| `load_time_seconds` | float | Время загрузки модели |

## 🔄 Жизненный цикл файлов

### 1. Создание .in_progress
```
Аудиофайл обнаружен
         ↓
   Создается filename.in_progress
         ↓
   Статус: {"status": "processing", "current_attempt": 1}
```

### 2. Обновление прогресса
```
Загрузка модели
         ↓
   Обновление: {"stage": "loading_model", "percentage": 25}
         ↓
Обработка аудио
         ↓
   Обновление: {"stage": "processing_audio", "percentage": 75}
```

### 3. Завершение обработки
```
Обработка завершена успешно
         ↓
   Создается filename.result
         ↓
   Удаляется filename.in_progress
```

### 4. Обработка ошибок
```
Произошла ошибка
         ↓
   Обновление .in_progress с error
         ↓
   Retry попытка или перемещение в manual/
```

## 🛠️ Операции с файлами

### 📖 Чтение статуса
```python
import json

def read_status(filename):
    try:
        with open(f"{filename}.in_progress", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
```

### ✏️ Обновление прогресса
```python
def update_progress(filename, stage, percentage):
    status = read_status(filename)
    if status:
        current_attempt = status["attempts"][-1]
        current_attempt["progress_info"] = {
            "stage": stage,
            "percentage": percentage
        }
        write_status(filename, status)
```

### 💾 Сохранение результата
```python
def save_result(filename, transcription_data, metadata):
    result = {
        "filename": filename,
        "processing_end": datetime.now().isoformat(),
        "transcription": transcription_data,
        "metadata": metadata
    }
    
    with open(f"{filename}.result", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Удаляем .in_progress после успешного сохранения
    os.remove(f"{filename}.in_progress")
```

## 📋 Примеры использования

### 🔍 Проверка статуса файла
```python
def get_file_status(filename):
    if os.path.exists(f"{filename}.result"):
        return "completed"
    elif os.path.exists(f"{filename}.in_progress"):
        return "processing"
    elif os.path.exists(filename):
        return "pending"
    else:
        return "not_found"
```

### ⏰ Проверка времени обработки
```python
def check_processing_timeout(filename, timeout_minutes=60):
    status = read_status(filename)
    if status:
        start_time = datetime.fromisoformat(status["creation_time"])
        if (datetime.now() - start_time).seconds > timeout_minutes * 60:
            return True  # Таймаут превышен
    return False
```

### 🧹 Очистка старых файлов
```python
def cleanup_old_files(max_age_hours=24):
    for file in glob.glob("*.in_progress"):
        if file_age_hours(file) > max_age_hours:
            # Переместить в папку для ручной обработки
            move_to_manual_processing(file)
```
# 📊 Статусные файлы

## 🔄 Файл состояния обработки (.in_progress)

### 📁 Назначение
Файл `filename.in_progress` создается при начале обработки аудиофайла и содержит информацию о текущем состоянии обработки.

### 📝 Упрощенная структура JSON
```json
{
  "filename": "audio.mp3",
  "status": "processing",
  "start_time": "2024-01-01T10:00:00Z",
  "attempt": 1,
  "settings": {
    "model_size": "base",
    "language": "ru",
    "temperature": 0.1,
    "compute_type": "int8",
    "device": "cpu"
  },
  "error": null
}
```

### 🔧 Описание полей

| Поле | Тип | Описание |
|------|-----|----------|
| `filename` | string | Имя обрабатываемого файла |
| `status` | string | Статус: "processing", "completed", "error" |
| `start_time` | ISO8601 | Время начала обработки |
| `attempt` | integer | Номер текущей попытки (1-3) |
| `settings` | object | Настройки обработки |
| `error` | object/null | Информация об ошибке (если есть) |

## ✅ Файл результата (.result)

### 📁 Назначение
Файл `filename.result` создается после успешной обработки и содержит результаты транскрипции.

### 📝 Упрощенная структура JSON
```json
{
  "filename": "audio.mp3",
  "processing_time_seconds": 27.1,
  "transcription": {
    "text": "Полный текст транскрипции аудиозаписи...",
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
```

### 🔧 Описание полей результата

| Поле | Тип | Описание |
|------|-----|----------|
| `filename` | string | Имя обработанного файла |
| `processing_time_seconds` | float | Время обработки в секундах |
| `transcription.text` | string | Полный текст транскрипции |
| `transcription.segments` | array | Сегменты с временными метками |
| `metadata.duration_seconds` | float | Длительность аудио |
| `metadata.confidence` | float | Уверенность модели (0.0-1.0) |
| `metadata.word_count` | integer | Количество слов |

## 🔄 Жизненный цикл файлов

### Процесс обработки
```
1. Аудиофайл обнаружен → создается filename.in_progress
2. Обработка WhisperX → обновляется статус в .in_progress
3. Обработка завершена → создается filename.result
4. Успех → удаляется filename.in_progress
5. Ошибка → обновляется error в .in_progress
```

### Определение статуса файла
- **pending**: есть только `audio.mp3`
- **processing**: есть `audio.mp3` + `audio.in_progress`
- **completed**: есть `audio.mp3` + `audio.result`
- **error**: есть `audio.mp3` + `audio.in_progress` с полем error

## 🛠️ Примеры использования

### Чтение статуса
```python
import json
import os

def get_file_status(filename):
    if os.path.exists(f"shared/{filename}.result"):
        return "completed"
    elif os.path.exists(f"shared/{filename}.in_progress"):
        return "processing"
    elif os.path.exists(f"shared/{filename}"):
        return "pending"
    else:
        return "not_found"
```

### Создание .in_progress
```python
def create_in_progress(filename, settings):
    data = {
        "filename": filename,
        "status": "processing", 
        "start_time": datetime.now().isoformat(),
        "attempt": 1,
        "settings": settings,
        "error": None
    }
    with open(f"shared/{filename}.in_progress", "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

### Сохранение результата
```python
def save_result(filename, transcription_data, metadata):
    result = {
        "filename": filename,
        "processing_time_seconds": 27.1,
        "transcription": transcription_data,
        "metadata": metadata
    }
    
    with open(f"shared/{filename}.result", "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    # Удаляем .in_progress после успешного сохранения
    os.remove(f"shared/{filename}.in_progress")
```
