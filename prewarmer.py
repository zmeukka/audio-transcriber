"""
WhisperX Pre-warmer для ускорения загрузки
Загружает модели в память заранее для быстрых последующих запусков
"""

import time
import logging
import pickle
import os
import sys
import threading
from pathlib import Path
import yaml

class WhisperXPrewarmer:
    """Класс для предварительной загрузки WhisperX моделей"""

    def __init__(self, config_path="config.yaml"):
        self.config = self._load_config(config_path)
        self.model = None
        self.align_model = None
        self.metadata = None
        self.cache_path = Path("cache")
        self.cache_path.mkdir(exist_ok=True)
        self.ready = False

    def _load_config(self, config_path):
        """Загружает конфигурацию из YAML"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"❌ Ошибка загрузки конфигурации: {e}")
            # Возвращаем базовую конфигурацию
            return {
                'whisperx': {
                    'model_size': 'base',
                    'language': 'ru',
                    'temperature': 0.1,
                    'compute_type': 'int8',
                    'device': 'cpu'
                }
            }

    def warm_up_model(self):
        """Pre-warming модели WhisperX"""
        print("🔥 Запуск pre-warming модели WhisperX...")
        start_time = time.time()

        try:
            import whisperx
            import torch
            import numpy as np

            whisperx_config = self.config['whisperx']

            print(f"📦 Загружаем модель {whisperx_config['model_size']}...")

            # Загружаем основную модель
            self.model = whisperx.load_model(
                whisperx_config['model_size'],
                whisperx_config['device'],
                compute_type=whisperx_config['compute_type'],
                language=whisperx_config['language']
            )

            print(f"🎯 Загружаем align модель для языка {whisperx_config['language']}...")

            # Загружаем align модель
            try:
                self.align_model, self.metadata = whisperx.load_align_model(
                    language_code=whisperx_config['language'],
                    device=whisperx_config['device']
                )
            except Exception as e:
                print(f"⚠️ Не удалось загрузить align модель: {e}")
                self.align_model = None
                self.metadata = None

            # Тестовая обработка для полной инициализации
            print("🧪 Выполняем тестовую обработку...")
            self._test_processing()

            self.ready = True
            elapsed = time.time() - start_time
            print(f"✅ Pre-warming завершен за {elapsed:.1f} секунд")

        except Exception as e:
            print(f"❌ Ошибка pre-warming: {e}")
            raise

    def _test_processing(self):
        """Тестовая обработка для полной инициализации"""
        try:
            import numpy as np

            # Создаем короткий тестовый аудио (1 секунда тишины)
            test_audio = np.zeros(16000, dtype=np.float32)  # 1 сек @ 16kHz

            # Обрабатываем тестовый аудио
            result = self.model.transcribe(test_audio)

            if self.align_model and self.metadata:
                # Пытаемся выровнять результат
                import whisperx
                result = whisperx.align(
                    result["segments"],
                    self.align_model,
                    self.metadata,
                    test_audio,
                    self.config['whisperx']['device']
                )

            print("✅ Тестовая обработка успешна")

        except Exception as e:
            print(f"⚠️ Тестовая обработка не удалась: {e}")

    def save_warmed_state(self):
        """Сохраняет состояние для быстрой загрузки"""
        cache_file = self.cache_path / "warmed_state.pkl"

        # Для безопасности сохраняем только флаг готовности
        # Сами модели слишком большие для pickle
        state = {
            'ready': self.ready,
            'timestamp': time.time(),
            'config': self.config
        }

        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(state, f)
            print(f"💾 Состояние сохранено в {cache_file}")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить состояние: {e}")

    def load_warmed_state(self, max_age_hours=24):
        """Проверяет, есть ли свежий кэш"""
        cache_file = self.cache_path / "warmed_state.pkl"

        if not cache_file.exists():
            return False

        try:
            with open(cache_file, 'rb') as f:
                state = pickle.load(f)

            # Проверяем возраст кэша
            age_hours = (time.time() - state['timestamp']) / 3600
            if age_hours > max_age_hours:
                print(f"⚠️ Кэш устарел ({age_hours:.1f}ч), нужен новый pre-warming")
                return False

            print(f"✅ Найден свежий кэш (возраст: {age_hours:.1f}ч)")
            return True

        except Exception as e:
            print(f"❌ Ошибка проверки кэша: {e}")
            return False

    def get_models(self):
        """Возвращает загруженные модели"""
        if not self.ready:
            raise RuntimeError("Модели не готовы! Выполните warm_up_model() сначала.")

        return self.model, self.align_model, self.metadata


def main():
    """Основная функция для запуска pre-warming"""
    print("🚀 WhisperX Pre-warmer")
    print("=" * 50)

    prewarmer = WhisperXPrewarmer()

    # Проверяем кэш
    if prewarmer.load_warmed_state():
        print("💡 Кэш найден, но выполним полный pre-warming для уверенности...")

    # Выполняем pre-warming
    try:
        prewarmer.warm_up_model()
        prewarmer.save_warmed_state()

        print("\n🎉 Pre-warming завершен успешно!")
        print("💡 Теперь можно запускать transcriber.py --fast для быстрой обработки")

    except KeyboardInterrupt:
        print("\n⚠️ Pre-warming прерван пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка pre-warming: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
