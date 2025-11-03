# 🐳 Развертывание и установка

## 🚀 Быстрый старт

### Требования
- Docker Engine 20.0+
- Docker Compose 2.0+
- 2GB свободного места (для моделей)
- 2GB RAM

### Установка
```bash
# 1. Клонирование репозитория
git clone https://github.com/your-repo/audio-transcriber.git
cd audio-transcriber

# 2. Создание директорий
mkdir -p shared whisper_cache

# 3. Запуск сервиса
docker-compose up -d

# 4. Проверка состояния
curl http://localhost:8000/health
```

## 📁 Структура директорий

### Создание необходимых директорий
```bash
mkdir -p shared whisper_cache
```

### Структура проекта после развертывания
```
audio-transcriber/
├── docker-compose.yml       # Docker Compose конфигурация
├── Dockerfile               # Docker образ
├── config.yaml             # Конфигурация
├── shared/                 # Общие файлы (монтируется)
│   ├── audio.mp3          # Исходные аудиофайлы
│   ├── audio.in_progress  # Статус обработки
│   └── audio.result       # Результаты
└── whisper_cache/          # Кэш моделей (монтируется)
    ├── base.pt            # Модель base
    └── tiny.pt            # Модель tiny
```

## 🐳 Docker Compose

### Основная конфигурация
```yaml
version: '3.8'

services:
  audio-transcriber:
    build: .
    container_name: audio_transcriber
    ports:
      - "8000:8000"
    volumes:
      - ./shared:/app/shared
      - ./whisper_cache:/root/.cache/whisper
    environment:
      - LOG_LEVEL=INFO
      - WHISPERX_DEVICE=cpu
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Команды управления
```bash
# Запуск сервиса
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка сервиса
docker-compose down

# Перезапуск
docker-compose restart

# Обновление (пересборка)
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Dockerfile

### Основная структура
```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY . .

# Создание директорий
RUN mkdir -p /app/shared

# Экспорт порта
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Запуск приложения
CMD ["python", "app.py"]
```

## ⚙️ Конфигурация для разных сред

### 🧪 Разработка (development)
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  audio-transcriber:
    build: 
      context: .
      dockerfile: Dockerfile.dev
    volumes:
      - ./shared:/app/shared
      - ./whisper_cache:/root/.cache/whisper
      - .:/app  # Монтирование кода для hot reload
    environment:
      - LOG_LEVEL=DEBUG
      - WHISPERX_DEVICE=cpu
    ports:
      - "8000:8000"
```

### 🚀 Продакшн (production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  audio-transcriber:
    image: audio-transcriber:latest
    restart: always
    volumes:
      - /data/shared:/app/shared
      - /data/whisper_cache:/root/.cache/whisper
    environment:
      - LOG_LEVEL=INFO
      - WHISPERX_DEVICE=cuda  # Если есть GPU
    ports:
      - "8000:8000"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
```

### 🏗️ С GPU поддержкой
```yaml
version: '3.8'

services:
  audio-transcriber:
    build: .
    runtime: nvidia
    environment:
      - WHISPERX_DEVICE=cuda
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./shared:/app/shared
      - ./whisper_cache:/root/.cache/whisper
    ports:
      - "8000:8000"
```

## 🔒 Безопасность

### 🔑 Переменные окружения
```bash
# .env файл (не коммитить в git)
LOG_LEVEL=INFO
WHISPERX_DEVICE=cpu
API_KEY=your_secret_api_key  # Если нужна аутентификация
MAX_FILE_SIZE_MB=100
```

### 🚧 Ограничения ресурсов
```yaml
deploy:
  resources:
    limits:
      memory: 4G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '0.5'
```

## 📊 Мониторинг

### 🏥 Health checks
```bash
# Простая проверка
curl http://localhost:8000/health

# Детальная проверка
curl -s http://localhost:8000/health | jq .
```

### 📈 Логи
```bash
# Просмотр логов
docker-compose logs -f audio-transcriber

# Логи с временными метками
docker-compose logs -f -t audio-transcriber

# Только последние 100 строк
docker-compose logs --tail=100 audio-transcriber
```

### 🔍 Отладка
```bash
# Подключение к контейнеру
docker-compose exec audio-transcriber bash

# Проверка процессов
docker-compose exec audio-transcriber ps aux

# Проверка использования памяти
docker-compose exec audio-transcriber free -h
```

## 🚨 Устранение неполадок

### ❌ Проблемы с запуском

**Проблема:** Контейнер не запускается
```bash
# Проверка логов
docker-compose logs audio-transcriber

# Проверка состояния
docker-compose ps
```

**Проблема:** Порт уже занят
```bash
# Изменить порт в docker-compose.yml
ports:
  - "8001:8000"  # Вместо 8000:8000
```

### 💾 Проблемы с хранилищем

**Проблема:** Нет места для моделей
```bash
# Проверка места
docker-compose exec audio-transcriber df -h

# Очистка старых данных
docker system prune -a
```

**Проблема:** Нет доступа к файлам
```bash
# Проверка прав доступа
ls -la shared/
chmod -R 755 shared/
```

### 🤖 Проблемы с WhisperX

**Проблема:** Модели не загружаются
```bash
# Проверка кэша
ls -la whisper_cache/

# Принудительная загрузка
curl -X POST http://localhost:8000/transcribe \
  -d '{"filename": "test.mp3", "model_size": "tiny"}'
```

## 📋 Чеклист развертывания

- [ ] Docker и Docker Compose установлены
- [ ] Создана директория `shared/`
- [ ] Создана директория `whisper_cache/`
- [ ] Настроен `docker-compose.yml`
- [ ] Настроен `config.yaml`
- [ ] Сервис запущен (`docker-compose up -d`)
- [ ] Health check работает (`curl http://localhost:8000/health`)
- [ ] Тестовый файл обрабатывается
- [ ] Логи настроены и доступны
- [ ] Бэкапы настроены (для продакшн)
