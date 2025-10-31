# 🎵 Audio Transcriber v2.0

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![WhisperX](https://img.shields.io/badge/WhisperX-3.7+-green.svg)](https://github.com/m-bain/whisperX)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Ubuntu-lightgrey.svg)](#installation)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Автоматическая транскрипция аудиофайлов с использованием WhisperX. Оптимизирована для русского языка с поддержкой быстрого режима для **10-20x ускорения** повторных запусков.

## ✨ Основные возможности

- 🎯 **Высокое качество:** Оптимизированные параметры для русской речи
- ⚡ **Быстрый режим:** Pre-warming система для ускорения обработки
- 🌍 **Кроссплатформенность:** Windows PowerShell + Ubuntu/Linux
- 🔧 **Простая установка:** Автоматические скрипты настройки
- 📝 **Полная документация:** Подробные руководства и примеры
- 🛠️ **Производственная готовность:** Обработка ошибок и логирование

## 🚀 Быстрый старт

### Windows PowerShell
```powershell
git clone https://github.com/[username]/audio-transcriber.git
cd audio-transcriber
.\setup_environment.ps1
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --test
```

### Ubuntu 24.04 / Linux
```bash
git clone https://github.com/[username]/audio-transcriber.git
cd audio-transcriber
chmod +x setup_environment_ubuntu.sh
./setup_environment_ubuntu.sh
source ./activate_env.sh
python transcriber.py --test
```

## ⚡ Быстрый режим (рекомендуется)

Для **10-20x ускорения** повторных запусков:

```bash
# 1. Pre-warming (один раз, ~20-30 сек)
python prewarmer.py

# 2. Быстрая обработка (повторно, ~2-5 сек)
python transcriber.py --fast --test
python transcriber.py --fast --file input/audio.oga
```

## 📁 Использование

### Поддерживаемые форматы
`.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.oga`

### Основные команды
```bash
# Тестирование
python transcriber.py --test

# Обработка одного файла
python transcriber.py --file input/audio.oga

# Обработка всех файлов в input/
python transcriber.py

# Быстрый режим
python transcriber.py --fast --file input/audio.oga
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

## ⚙️ Конфигурация

Отредактируйте `config.yaml`:

```yaml
whisperx:
  model_size: "base"           # tiny, base, small, medium, large
  language: "ru"               # ru, en, auto
  temperature: 0.1             # 0.1 = высокая точность
  compute_type: "int8"         # int8, float32, float16
  device: "cpu"                # cpu, cuda

processing:
  max_retry_attempts: 3        # Попытки при ошибке
```

## 📊 Производительность

| Режим | Первый запуск | Повторные запуски | Память |
|-------|---------------|-------------------|--------|
| **Обычный** | 45-60 сек | 45-60 сек | ~500MB |
| **Быстрый** | 20-30 сек | **2-5 сек** | ~2-3GB |

## 📚 Документация

- 📖 [README_UBUNTU.md](README_UBUNTU.md) - Установка на Ubuntu
- ⚡ [FAST_MODE.md](FAST_MODE.md) - Подробно о быстром режиме
- 🚀 [QUICK_START.md](QUICK_START.md) - Мгновенный старт
- 📋 [technical_specification.md](technical_specification.md) - Полное ТЗ
- 📝 [SUMMARY.md](SUMMARY.md) - Сводка изменений

## 🎯 Оптимальные настройки

Найдены экспериментально для лучшего качества:

| Параметр | Значение | Причина |
|----------|----------|---------|
| model_size | "base" | Лучший баланс качества/скорости |
| language | "ru" | Принудительно русский язык |
| temperature | 0.1 | Высокая точность для коротких фраз |
| compute_type | "int8" | Производительность без потери качества |

## 🔧 Решение проблем

### Ошибка кодировки (Windows)
```powershell
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONUTF8="1"
```

### Ошибка FFmpeg
```bash
# Ubuntu
sudo apt install ffmpeg

# Windows
# Скачайте с https://ffmpeg.org/ и добавьте в PATH
```

### Очистка и переустановка
```bash
rm -rf .venv cache/
./setup_environment_ubuntu.sh  # или setup_environment.ps1
```

## 📂 Структура проекта

```
Audio_Transcriber/
├── transcriber.py              # Основная программа
├── prewarmer.py               # Pre-warming система
├── fast_transcriber.py        # Быстрый транскрибер
├── config.yaml                # Конфигурация
├── modules/                   # Модули программы
├── input/                     # Входные аудиофайлы
├── output/                    # Готовые транскрипции
├── manual/                    # Проблемные файлы для ручной обработки
└── docs/                      # Документация
```

## 🤝 Участие в разработке

1. Fork репозитория
2. Создайте feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- [WhisperX](https://github.com/m-bain/whisperX) - Основной движок транскрипции
- [OpenAI Whisper](https://github.com/openai/whisper) - Базовая модель
- Сообщество разработчиков за тестирование и обратную связь

---

**⭐ Если проект полезен, поставьте звезду!**
