# 🚀 Развертывание Audio Transcriber

## 📋 Системные требования

### Минимальные требования
- **OS:** Linux/Windows/macOS с поддержкой Docker
- **RAM:** 4 GB (рекомендуемо 8 GB)
- **Процессор:** 2 CPU cores (рекомендуемо 4+)
- **Диск:** 10 GB свободного места
- **Docker:** 20.0+ и Docker Compose 2.0+

### Рекомендуемые требования для продакшна
- **RAM:** 16 GB (для больших моделей)
- **Процессор:** 8+ CPU cores
- **GPU:** NVIDIA с поддержкой CUDA (опционально)
- **Диск:** SSD с 50+ GB для моделей и кэша

## 🐳 Развертывание через Docker Compose

### Быстрый запуск
```bash
# Клонирование репозитория
git clone <repository-url>
cd audio-transcriber

# Создание необходимых директорий
mkdir -p shared whisper_cache

# Запуск сервиса
docker-compose up -d

# Проверка состояния
curl http://localhost:8000/health
```

### Конфигурация docker-compose.yml
```yaml
version: '3.8'

services:
  audio-transcriber:
    build: .
    container_name: audio-transcriber
    ports:
      - "8000:8000"
    volumes:
      - ./shared:/app/shared
      - ./whisper_cache:/app/whisper_cache
      - ./config.yaml:/app/config.yaml
    environment:
      - LOG_LEVEL=INFO
      - WHISPERX_DEVICE=cpu
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## ⚙️ Переменные окружения

### Основные переменные
```bash
# Пути
SHARED_DIRECTORY=/app/shared
WHISPER_CACHE_DIR=/app/whisper_cache

# API настройки
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=false

# WhisperX настройки
WHISPERX_MODEL=small
WHISPERX_DEVICE=cpu
WHISPERX_COMPUTE_TYPE=float32

# Обработка
PROCESSING_TIMEOUT=180
MAX_RETRIES=3
LOG_LEVEL=INFO
```

### Пример для GPU
```yaml
environment:
  - WHISPERX_DEVICE=cuda
  - WHISPERX_COMPUTE_TYPE=float16
  - WHISPERX_MODEL=large
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

## 🔧 Конфигурация для разных сред

### Development
```yaml
# docker-compose.dev.yml
services:
  audio-transcriber:
    build:
      context: .
      target: development
    environment:
      - LOG_LEVEL=DEBUG
      - API_DEBUG=true
      - WHISPERX_MODEL=tiny
    volumes:
      - .:/app
      - ./shared:/app/shared
```

### Production
```yaml
# docker-compose.prod.yml
services:
  audio-transcriber:
    image: audio-transcriber:latest
    environment:
      - LOG_LEVEL=INFO
      - API_DEBUG=false
      - WHISPERX_MODEL=small
      - WHISPERX_DEVICE=cuda
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 8G
          cpus: '4'
```

## 🌐 Развертывание в облаке

### AWS ECS
```json
{
  "family": "audio-transcriber",
  "taskDefinition": {
    "containerDefinitions": [
      {
        "name": "audio-transcriber",
        "image": "your-registry/audio-transcriber:latest",
        "memory": 8192,
        "cpu": 4096,
        "portMappings": [
          {
            "containerPort": 8000,
            "protocol": "tcp"
          }
        ],
        "environment": [
          {"name": "WHISPERX_DEVICE", "value": "cpu"},
          {"name": "LOG_LEVEL", "value": "INFO"}
        ]
      }
    ]
  }
}
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: audio-transcriber
spec:
  replicas: 1
  selector:
    matchLabels:
      app: audio-transcriber
  template:
    metadata:
      labels:
        app: audio-transcriber
    spec:
      containers:
      - name: audio-transcriber
        image: audio-transcriber:latest
        ports:
        - containerPort: 8000
        env:
        - name: WHISPERX_DEVICE
          value: "cpu"
        - name: LOG_LEVEL
          value: "INFO"
        volumeMounts:
        - name: shared-storage
          mountPath: /app/shared
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi" 
            cpu: "4"
      volumes:
      - name: shared-storage
        persistentVolumeClaim:
          claimName: audio-transcriber-pvc
```

## 🔒 Безопасность

### HTTPS/TLS
```yaml
# С обратным прокси NGINX
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
  
  audio-transcriber:
    build: .
    expose:
      - "8000"
```

### Ограничения доступа
```python
# Обновление CORS в продакшне
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)
```

## 📊 Мониторинг

### Health checks
```bash
# Проверка состояния API
curl -f http://localhost:8000/health || exit 1

# Проверка очереди
curl -s http://localhost:8000/queue | jq '.queue_length'

# Проверка контейнера
docker ps | grep audio-transcriber
docker logs audio-transcriber --tail 50
```

### Prometheus метрики (будущая версия)
```yaml
# Добавить в docker-compose.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
```

## 🔄 Обновление и откат

### Обновление сервиса
```bash
# Остановка текущей версии
docker-compose down

# Обновление образа
docker-compose pull

# Запуск новой версии
docker-compose up -d

# Проверка
curl http://localhost:8000/health
```

### Откат к предыдущей версии
```bash
# Остановка
docker-compose down

# Запуск предыдущего образа
docker-compose -f docker-compose.yml up -d

# Проверка
docker ps
```

## 🛠️ Устранение неполадок

### Частые проблемы

**Контейнер не запускается:**
```bash
# Проверка логов
docker-compose logs audio-transcriber

# Проверка ресурсов
docker stats
```

**API недоступен:**
```bash
# Проверка портов
netstat -tulpn | grep 8000

# Проверка firewall
sudo ufw status
```

**Ошибки обработки:**
```bash
# Проверка shared директории
ls -la ./shared

# Проверка прав доступа
chmod 755 ./shared
```

**Нехватка памяти:**
```bash
# Уменьшение модели
export WHISPERX_MODEL=tiny

# Мониторинг памяти
docker stats audio-transcriber
```

### Диагностические команды
```bash
# Информация о системе
docker system info
docker system df

# Анализ образа
docker inspect audio-transcriber:latest

# Подключение к контейнеру
docker exec -it audio-transcriber bash

# Проверка версий
curl http://localhost:8000/health | jq '.version'
```

## 📋 Чек-лист развертывания

### Перед развертыванием
- [ ] Docker и Docker Compose установлены
- [ ] Созданы директории `shared` и `whisper_cache`
- [ ] Настроен `config.yaml`
- [ ] Проверены системные ресурсы
- [ ] Настроен firewall/сетевой доступ

### После развертывания
- [ ] Сервис запущен без ошибок
- [ ] Health check возвращает "healthy"
- [ ] API endpoints доступны
- [ ] Тестовая транскрипция работает
- [ ] Логи показывают нормальную работу
- [ ] Мониторинг настроен

---

**Дата обновления:** 3 ноября 2025  
**Версия:** 1.0
