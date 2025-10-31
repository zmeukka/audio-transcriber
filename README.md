# Audio Transcriber

Программа автоматической транскрипции аудиофайлов с использованием WhisperX.
Поддерживает русский и английский языки с возможностью точной настройки параметров распознавания.

## 🚀 Быстрая установка

### Windows (PowerShell)
```powershell
.\setup_environment.ps1
```

### Ubuntu 24.04 / Linux
```bash
chmod +x setup_environment_ubuntu.sh
./setup_environment_ubuntu.sh
```

Подробные инструкции:
- **Windows:** Используйте PowerShell и `setup_environment.ps1`
- **Ubuntu:** См. [README_UBUNTU.md](README_UBUNTU.md) для подробной установки

## ⚡ Быстрый старт

### Windows
```powershell
# Настройка окружения (один раз)
.\setup_environment.ps1

# Тест программы
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --test

# Обработка файла
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --file input\audio.oga
```

### Ubuntu
```bash
# Настройка окружения (один раз)
./setup_environment_ubuntu.sh

# Активация окружения
source ./activate_env.sh

# Тест программы
python transcriber.py --test

# Обработка файла
python transcriber.py --file input/audio.oga
```

## 📁 Использование

### Поддерживаемые форматы
- `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.oga`

### Команды

```bash
# Тестирование на примере
python transcriber.py --test

# Обработка конкретного файла
python transcriber.py --file input/audio.oga

# Обработка всех файлов в папке input
python transcriber.py
```

### Пример результата
```
=== РАСШИФРОВКА АУДИОЗАПИСИ ===
Файл: sample.oga
Дата обработки: 2025-10-31 14:10:11
Продолжительность: 00:00:01
Расшифровка заняла: 27.1 seconds

=== ТРАНСКРИПЦИЯ ===
[00:00:00] Ты сакс
```

## 📂 Структура проекта

```
Audio_Transcriber/
├── transcriber.py                    # Основная программа
├── config.yaml                       # Настройки программы
├── prepare_env.py                    # Подготовка окружения
├── setup_environment.ps1             # Установка для Windows
├── setup_environment_ubuntu.sh       # Установка для Ubuntu
├── README.md                         # Основная документация
├── README_UBUNTU.md                  # Документация для Ubuntu
├── technical_specification.md        # Техническое задание
├── requirements.txt                  # Python зависимости
├── modules/                          # Модули программы
│   ├── audio_processor.py           # Обработка аудио через WhisperX
│   ├── config_loader.py             # Загрузка конфигурации
│   ├── file_manager.py              # Управление файлами
│   └── logger.py                    # Логирование
├── input/                           # Аудиофайлы для обработки
├── output/                          # Готовые транскрипции
├── manual/                          # Проблемные файлы
└── models/                          # Модели WhisperX (автозагрузка)
```

## ⚙️ Конфигурация

Отредактируйте `config.yaml` для настройки параметров:

```yaml
whisperx:
  model_size: "base"           # tiny, base, small, medium, large
  language: "ru"               # ru, en, auto
  temperature: 0.1             # 0.1 = высокая точность, 0.9 = креативность  
  compute_type: "int8"         # int8, float32, float16
  device: "cpu"                # cpu, cuda

processing:
  max_retry_attempts: 3        # Попытки при ошибке
```

## 🎯 Рекомендуемые настройки

- **Для русской речи:** `model_size: "base"`, `language: "ru"`, `temperature: 0.1`
- **Для английской речи:** `model_size: "base"`, `language: "en"`, `temperature: 0.1`
- **Для скорости:** `model_size: "tiny"`, `compute_type: "int8"`
- **Для качества:** `model_size: "medium"`, `compute_type: "float32"`
