#!/usr/bin/env python3
"""
Model initialization script for WhisperX Audio Transcriber
Downloads required models if they don't exist locally
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def check_huggingface_hub():
    """Check if huggingface_hub is available"""
    try:
        import huggingface_hub
        return True
    except ImportError:
        print("❌ huggingface_hub не установлен")
        return False

def download_model(model_name, local_dir):
    """Download model using huggingface_hub"""
    print(f"📦 Скачиваю модель {model_name} в {local_dir}...")

    try:
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=f"Systran/{model_name}",
            local_dir=local_dir,
            local_dir_use_symlinks=False
        )
        print(f"✅ Модель {model_name} успешно скачана")
        return True
    except Exception as e:
        print(f"❌ Ошибка при скачивании модели {model_name}: {e}")
        return False

def check_model_exists(model_dir):
    """Check if model files exist"""
    model_path = Path(model_dir)
    if not model_path.exists():
        return False

    required_files = ['config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt']
    for file in required_files:
        if not (model_path / file).exists():
            return False

    return True

def main():
    """Main initialization function"""
    print("🚀 Инициализация моделей WhisperX")

    # Check dependencies
    if not check_huggingface_hub():
        print("💡 Установите huggingface_hub: pip install huggingface_hub")
        return False

    models_dir = Path(__file__).parent
    models_to_download = [
        ("faster-whisper-tiny", "faster-whisper-tiny"),
        ("faster-whisper-base", "faster-whisper-base"),
        ("faster-whisper-small", "faster-whisper-small")
    ]

    success_count = 0

    for model_name, local_dirname in models_to_download:
        local_dir = models_dir / local_dirname

        if check_model_exists(local_dir):
            print(f"✅ Модель {model_name} уже существует в {local_dir}")
            success_count += 1
        else:
            # Create directory if it doesn't exist
            local_dir.mkdir(exist_ok=True)

            if download_model(model_name, str(local_dir)):
                success_count += 1

    print(f"\n🎯 Результат: {success_count}/{len(models_to_download)} моделей готовы к использованию")

    if success_count == len(models_to_download):
        print("✅ Все модели успешно инициализированы!")
        return True
    else:
        print("⚠️  Некоторые модели не удалось загрузить")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
