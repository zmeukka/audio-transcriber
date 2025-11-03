# 📁 Структура проекта

## 🏗️ Общая архитектура

```
audio-transcriber/
├── specs/                           # Спецификации и техническое задание
│   ├── README.md                    # Краткая спецификация с ссылками
│   ├── technical_specification.md   # Полное техническое задание
│   └── ai_agent_task_specification.txt # Исходное задание
├── docs/                           # Детальная документация
│   ├── api.md                      # API спецификация
│   ├── configuration.md            # Конфигурация системы
│   ├── deployment.md               # Развертывание и установка
│   ├── project_structure.md        # Этот файл
│   └── status_files.md             # Формат статусных файлов
├── api/                            # API модули [К РЕАЛИЗАЦИИ]
│   ├── __init__.py
│   ├── routes.py                   # REST API endpoints
│   ├── models.py                   # Pydantic модели
│   └── middleware.py               # API middleware
├── core/                           # Основная логика [К РЕАЛИЗАЦИИ]
│   ├── __init__.py
│   ├── config_loader.py            # ✅ Загрузка конфигурации
│   ├── logger.py                   # ✅ Система логирования
│   ├── transcriber.py              # Интеграция с WhisperX
│   ├── task_manager.py             # Управление задачами
│   └── file_manager.py             # Работа с файлами
├── shared/                         # ✅ Общие файлы (монтируется в Docker)
│   ├── input/                      # ✅ Документация входных файлов
│   │   └── README.md              # ✅ Спецификация shared директории
│   └── output/                     # ✅ Документация выходных файлов
│       └── README.md              # ✅ Формат результатов
├── models/                         # ✅ Кэш моделей Whisper
│   ├── README.txt                  # ✅ Описание моделей
│   ├── faster-whisper-base/        # Модель base
│   ├── faster-whisper-small/       # Модель small
│   └── faster-whisper-tiny/        # Модель tiny
├── tests/                          # Тесты [К РЕАЛИЗАЦИИ]
│   ├── test_api.py                # Тесты API
│   ├── test_transcriber.py        # Тесты транскрипции
│   └── test_integration.py        # Интеграционные тесты
├── whisper_cache/                  # Кэш моделей WhisperX (монтируется)
├── config.yaml                     # ✅ Основная конфигурация
├── requirements.txt                # ✅ Python зависимости
├── Dockerfile                      # Docker образ [К РЕАЛИЗАЦИИ]
├── docker-compose.yml             # Docker Compose [К РЕАЛИЗАЦИИ]
├── app.py                          # Главный файл приложения [К РЕАЛИЗАЦИИ]
├── README.md                       # ✅ Главная документация
└── LICENSE                         # Лицензия
```

## 📦 Модули системы

### 🎯 API слой (`api/`)
**Назначение:** REST API интерфейс для взаимодействия с системой

| Файл | Описание | Статус |
|------|----------|--------|
| `routes.py` | FastAPI endpoints (POST/GET/DELETE) | 🚧 К реализации |
| `models.py` | Pydantic модели для валидации | 🚧 К реализации |
| `middleware.py` | Логирование, CORS, обработка ошибок | 🚧 К реализации |

### 🔧 Основная логика (`core/`)
**Назначение:** Бизнес-логика и координация компонентов

| Файл | Описание | Статус |
|------|----------|--------|
| `config_loader.py` | Загрузка YAML конфигурации | ✅ Спецификация готова |
| `logger.py` | Настройка логирования | ✅ Спецификация готова |
| `transcriber.py` | Интеграция с WhisperX | 🚧 К реализации |
| `task_manager.py` | Асинхронная обработка задач | 🚧 К реализации |
| `file_manager.py` | Управление статусными файлами | 🚧 К реализации |

### 📁 Файловая система (`shared/`)
**Назначение:** Общие файлы между контейнером и хостом

| Элемент | Описание | Статус |
|---------|----------|--------|
| Аудиофайлы | `audio.mp3`, `recording.wav` | ✅ Спецификация готова |
| Статус файлы | `audio.in_progress` (JSON) | ✅ Спецификация готова |
| Результаты | `audio.result` (JSON) | ✅ Спецификация готова |

### 🤖 Модели (`models/` & `whisper_cache/`)
**Назначение:** Кэширование и управление моделями Whisper

| Компонент | Описание | Статус |
|-----------|----------|--------|
| Предзагруженные модели | `models/faster-whisper-*` | ✅ Структура готова |
| Кэш времени выполнения | `whisper_cache/` | ✅ Спецификация готова |

## 🔄 Потоки данных

### 📤 Поток запроса транскрипции
```
1. API запрос (POST /transcribe) 
   ↓
2. Валидация в routes.py
   ↓
3. Создание задачи в task_manager.py
   ↓
4. Создание .in_progress файла
   ↓
5. Обработка в transcriber.py
   ↓
6. Создание .result файла
   ↓
7. Ответ клиенту
```

### 🗑️ Поток удаления файла
```
1. API запрос (DELETE /transcribe)
   ↓
2. Остановка обработки в task_manager.py
   ↓
3. Удаление всех файлов `filename.*`
   ↓
4. Очистка очереди задач
   ↓
5. Ответ клиенту
```

### 🔄 Поток автоматического сканирования
```
1. Состояние ожидания в task_manager.py
   ↓
2. Сканирование shared/ директории
   ↓
3. Поиск файлов без .in_progress/.result
   ↓
4. Создание задач с настройками по умолчанию
   ↓
5. Обработка по одному файлу
```

## 🧩 Взаимодействие компонентов

### 🎯 API → Core
- `routes.py` → `task_manager.py` для создания задач
- `routes.py` → `file_manager.py` для проверки статусов
- `routes.py` → `config_loader.py` для получения настроек по умолчанию

### 🔧 Core → Core
- `task_manager.py` → `transcriber.py` для выполнения обработки
- `task_manager.py` → `file_manager.py` для работы со статусными файлами
- `transcriber.py` → `config_loader.py` для получения конфигурации

### 📁 Core → Files
- `file_manager.py` → `shared/` для чтения/записи файлов
- `transcriber.py` → `whisper_cache/` для кэширования моделей

## 🧪 Тестирование

### 📊 Структура тестов
```
tests/
├── test_api.py                    # Unit тесты API endpoints
│   ├── test_transcribe_endpoint()
│   ├── test_delete_endpoint()
│   ├── test_status_endpoint()
│   └── test_result_endpoint()
├── test_transcriber.py           # Unit тесты транскрипции
│   ├── test_whisperx_integration()
│   ├── test_model_loading()
│   └── test_error_handling()
├── test_task_manager.py          # Unit тесты управления задачами
│   ├── test_queue_management()
│   ├── test_priority_handling()
│   └── test_interruption_logic()
├── test_file_manager.py          # Unit тесты файловых операций
│   ├── test_status_file_creation()
│   ├── test_result_file_parsing()
│   └── test_file_cleanup()
└── test_integration.py           # Интеграционные тесты
    ├── test_full_transcription_flow()
    ├── test_concurrent_requests()
    └── test_docker_deployment()
```

### 🎯 Покрытие тестами
- **API endpoints** - 100% покрытие всех маршрутов
- **Бизнес-логика** - 90%+ покрытие критичных функций
- **Интеграция** - Основные сценарии использования
- **Docker** - Тесты развертывания и health checks

## 📋 Чеклист реализации

### ✅ Завершенные компоненты
- [x] Спецификации и документация
- [x] Структура конфигурации
- [x] Формат статусных файлов
- [x] API спецификация
- [x] Структура проекта

### 🚧 К реализации (Приоритет 1)
- [ ] `app.py` - главный файл приложения
- [ ] `api/routes.py` - REST API endpoints
- [ ] `core/task_manager.py` - управление задачами
- [ ] `core/transcriber.py` - интеграция с WhisperX
- [ ] `core/file_manager.py` - работа с файлами

### 🚧 К реализации (Приоритет 2)
- [ ] `Dockerfile` и `docker-compose.yml`
- [ ] `api/models.py` - Pydantic модели
- [ ] `core/config_loader.py` - загрузчик конфигурации
- [ ] `core/logger.py` - система логирования
- [ ] Тесты основной функциональности

### 🚧 К реализации (Приоритет 3)
- [ ] `api/middleware.py` - middleware
- [ ] Полный набор тестов
- [ ] Обработка ошибок и resilience
- [ ] Оптимизация производительности
