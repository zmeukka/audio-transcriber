#!/usr/bin/env python3
"""
Скрипт подготовки окружения: создание директорий и скачивание моделей Whisper, если их нет.
"""
from pathlib import Path
import sys
import subprocess

# --- Проверка и установка huggingface_hub ---
try:
    import huggingface_hub
except ImportError:
    print("huggingface_hub не найден, устанавливаю...")
    subprocess.run([sys.executable, "-m", "pip", "install", "huggingface_hub"], check=True)
    import huggingface_hub

from huggingface_hub import snapshot_download

# --- 1. Создание директорий ---
directories = ['input', 'output', 'manual', 'models']
for dir_name in directories:
    Path(dir_name).mkdir(exist_ok=True)
    print(f"Создана директория: {dir_name}")

# --- 2. Скачивание моделей Whisper, если их нет ---
MODELS = {
    "tiny": "Systran/faster-whisper-tiny",
    "base": "Systran/faster-whisper-base",
    "small": "Systran/faster-whisper-small"  # дефолтная модель
}
for name, repo in MODELS.items():
    model_dir = Path('models') / f"faster-whisper-{name}"
    if not any(model_dir.iterdir()):
        model_dir.mkdir(exist_ok=True)
        print(f"Скачиваю модель {name} в {model_dir}...")
        try:
            snapshot_download(
                repo_id=repo,
                local_dir=str(model_dir),
                local_dir_use_symlinks=False
            )
            print(f"Модель {name} успешно скачана!")
        except Exception as e:
            print(f"Ошибка при скачивании модели {name}: {e}")
print("\nОкружение готово!")
