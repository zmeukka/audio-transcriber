"""
Быстрый транскрибер с использованием pre-warmed моделей
Значительно ускоряет повторные запуски за счет переиспользования загруженных моделей
"""

import time
import sys
import os
from pathlib import Path

# Добавляем modules в путь
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from prewarmer import WhisperXPrewarmer


class FastTranscriber:
    """Быстрый транскрибер с pre-warmed моделями"""

    def __init__(self, config_path="config.yaml"):
        self.prewarmer = WhisperXPrewarmer(config_path)
        self.ready = False

    def ensure_ready(self):
        """Убеждается что модели готовы к работе"""
        if self.ready:
            return

        print("⚡ Инициализация быстрого транскрибера...")
        start_time = time.time()

        # Проверяем, есть ли уже загруженные модели
        try:
            self.prewarmer.warm_up_model()
            self.ready = True

            elapsed = time.time() - start_time
            print(f"✅ Готов к работе за {elapsed:.1f} секунд")

        except Exception as e:
            print(f"❌ Ошибка инициализации: {e}")
            raise

    def transcribe_file(self, audio_path):
        """Быстрая транскрипция файла"""
        self.ensure_ready()

        audio_file = Path(audio_path)
        if not audio_file.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")

        print(f"🎵 Обработка: {audio_file.name}")
        start_time = time.time()

        try:
            import whisperx

            # Получаем модели
            model, align_model, metadata = self.prewarmer.get_models()

            # Загружаем аудио
            audio = whisperx.load_audio(str(audio_file))

            # Транскрибируем
            config = self.prewarmer.config['whisperx']
            result = model.transcribe(
                audio,
                batch_size=16,
                language=config['language']
                # Убираем temperature - не поддерживается в FasterWhisperPipeline
            )

            # Выравниваем (если доступно)
            if align_model and metadata:
                try:
                    result = whisperx.align(
                        result["segments"],
                        align_model,
                        metadata,
                        audio,
                        config['device']
                    )
                except Exception as e:
                    print(f"⚠️ Alignment не удался: {e}")

            elapsed = time.time() - start_time
            print(f"⚡ Обработано за {elapsed:.1f} секунд")

            return result

        except Exception as e:
            print(f"❌ Ошибка транскрипции: {e}")
            raise

    def transcribe_to_text(self, audio_path, output_path=None):
        """Транскрибирует файл и сохраняет результат в формате программы"""
        result = self.transcribe_file(audio_path)

        if not output_path:
            audio_file = Path(audio_path)
            output_path = Path("output") / f"{audio_file.stem}.txt"

        # Создаем текстовый файл в том же формате, что и основная программа
        self._create_text_output(Path(audio_path), result, output_path)

        return output_path

    def _create_text_output(self, audio_file, results, output_file):
        """Создает выходной файл в формате программы"""
        from datetime import datetime

        # Вычисляем продолжительность
        segments = results.get('segments', [])
        duration = 0
        if segments:
            last_segment = segments[-1]
            duration = last_segment.get('end', 0)

        duration_str = self._format_duration(duration)
        process_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Создаем содержимое
        content = f"""=== РАСШИФРОВКА АУДИОЗАПИСИ ===
Файл: {audio_file.name}
Дата обработки: {process_time}
Продолжительность: {duration_str}
Расшифровка заняла: быстрый режим

=== ТРАНСКРИПЦИЯ ===
"""

        # Добавляем сегменты транскрипции
        for segment in segments:
            start_time = self._format_timestamp(segment.get('start', 0))
            text = segment.get('text', '').strip()

            if text:  # Только непустые сегменты
                content += f"[{start_time}] {text}\n"

        # Создаем директорию если нужно
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Записываем файл
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"💾 Результат сохранен: {output_file}")

    def _format_timestamp(self, seconds):
        """Форматирует временную метку"""
        try:
            from datetime import timedelta
            td = timedelta(seconds=int(seconds))
            hours, remainder = divmod(td.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except:
            return "00:00:00"

    def _format_duration(self, seconds):
        """Форматирует продолжительность"""
        return self._format_timestamp(seconds)


def main():
    """Основная функция для тестирования быстрого транскрибера"""
    import argparse

    parser = argparse.ArgumentParser(description='Быстрый транскрибер WhisperX')
    parser.add_argument('--file', required=True, help='Путь к аудиофайлу')
    parser.add_argument('--output', help='Путь к выходному файлу')

    args = parser.parse_args()

    try:
        # Создаем быстрый транскрибер
        transcriber = FastTranscriber()

        # Обрабатываем файл
        output_path = transcriber.transcribe_to_text(args.file, args.output)

        print(f"\n🎉 Готово! Результат: {output_path}")

    except KeyboardInterrupt:
        print("\n⚠️ Обработка прервана пользователем")
        return 1
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
