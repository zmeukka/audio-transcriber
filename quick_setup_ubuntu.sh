#!/bin/bash
# Быстрая установка Audio Transcriber для Ubuntu 24.04

echo "🚀 Быстрая установка Audio Transcriber..."

# Установка системных зависимостей
sudo apt update && sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Создание и активация виртуального окружения
python3 -m venv .venv
source .venv/bin/activate

# Установка Python пакетов
pip install --upgrade pip
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu
pip install whisperx pyyaml psutil

# Создание директорий
mkdir -p input output manual models

# Настройка переменных среды
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

echo "✅ Установка завершена!"
echo "Для активации окружения: source .venv/bin/activate"
echo "Для тестирования: python transcriber.py --test"
