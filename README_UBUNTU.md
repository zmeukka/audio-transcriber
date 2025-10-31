# Audio Transcriber - Установка в Ubuntu 24.04

## 🚀 Быстрая установка

### Вариант 1: Автоматическая установка (рекомендуется)

```bash
# Скачайте или склонируйте проект
cd /path/to/Audio_Transcriber

# Сделайте скрипт исполняемым
chmod +x setup_environment_ubuntu.sh

# Запустите установку
./setup_environment_ubuntu.sh
```

### Вариант 2: Быстрая установка

```bash
# Для опытных пользователей
chmod +x quick_setup_ubuntu.sh
./quick_setup_ubuntu.sh
```

## 📋 Системные требования

- **ОС:** Ubuntu 20.04+ (тестировалось на 24.04)
- **Python:** 3.8+ (обычно предустановлен)
- **Свободное место:** ~3GB (для моделей WhisperX)
- **Интернет:** для загрузки пакетов и моделей

## 🔧 Ручная установка

Если автоматические скрипты не работают:

### 1. Установка системных зависимостей

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev ffmpeg git curl build-essential
```

### 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Установка Python пакетов

```bash
pip install --upgrade pip
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install whisperx pyyaml psutil
```

### 4. Создание директорий

```bash
mkdir -p input output manual models
```

### 5. Настройка переменных среды

```bash
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

## 🎵 Использование

### Активация окружения

После установки для каждой новой сессии терминала:

```bash
cd /path/to/Audio_Transcriber
source .venv/bin/activate
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
```

Или используйте удобный скрипт (если использовали автоматическую установку):

```bash
source ./activate_env.sh
```

### Запуск программы

```bash
# Тестирование на примере
python transcriber.py --test

# Обработка одного файла
python transcriber.py --file input/audio.oga

# Обработка всех файлов в папке input
python transcriber.py
```

## 📁 Структура файлов

```
Audio_Transcriber/
├── input/              # Поместите сюда аудиофайлы для обработки
├── output/             # Здесь появятся готовые транскрипции
├── manual/             # Проблемные файлы для ручной обработки
├── models/             # Модели WhisperX (загружаются автоматически)
├── .venv/              # Виртуальное окружение Python
├── transcriber.py      # Основная программа
├── config.yaml         # Настройки программы
└── modules/            # Модули программы
```

## 🎛️ Настройка

Отредактируйте `config.yaml` для изменения параметров:

```yaml
# Настройки WhisperX
whisperx:
  model_size: "base"        # tiny, base, small, medium, large
  language: "ru"            # Язык распознавания
  temperature: 0.1          # Точность (0.1 = высокая точность)
  compute_type: "int8"      # Тип вычислений
  device: "cpu"             # Устройство обработки

# Настройки обработки
processing:
  max_retry_attempts: 3     # Максимум попыток при ошибке
```

## 🔧 Решение проблем

### Ошибка "ffmpeg not found"

```bash
sudo apt update
sudo apt install -y ffmpeg
```

### Ошибка с кодировкой UTF-8

```bash
sudo apt install -y locales
sudo locale-gen en_US.UTF-8
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Проблемы с PyTorch

```bash
pip uninstall torch torchaudio
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
```

### Очистка и переустановка

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
# Повторите установку пакетов
```

## 🚀 Оптимизация производительности

### Для лучшей производительности на серверах:

1. **Используйте GPU** (если доступен):
   ```yaml
   whisperx:
     device: "cuda"
     compute_type: "float16"
   ```

2. **Увеличьте размер модели** для лучшего качества:
   ```yaml
   whisperx:
     model_size: "medium"  # или "large"
   ```

3. **Мониторинг ресурсов**:
   ```bash
   htop  # Установка: sudo apt install htop
   ```

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи: сообщения об ошибках в терминале
2. Убедитесь, что все зависимости установлены
3. Проверьте, что файлы имеют поддерживаемый формат (.mp3, .wav, .m4a, .ogg, .flac, .oga)
4. Убедитесь, что достаточно места на диске (минимум 3GB)

## 🎯 Быстрый старт

1. `chmod +x setup_environment_ubuntu.sh && ./setup_environment_ubuntu.sh`
2. `source ./activate_env.sh`
3. `python transcriber.py --test`
4. Поместите свои аудиофайлы в папку `input/`
5. `python transcriber.py`
6. Результаты в папке `output/`

Готово! 🎉
