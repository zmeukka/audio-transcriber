#!/usr/bin/env python3
"""
Audio Transcriber - Main application file
Automatically transcribes audio files using WhisperX
"""

import argparse
import sys
import os
from pathlib import Path

# Add modules directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from config_loader import ConfigLoader
from logger import Logger
from file_manager import FileManager
from audio_processor import AudioProcessor


def main():
    """Main application entry point"""
    # Set UTF-8 encoding for stdout to handle Russian text
    if sys.platform == "win32":
        import codecs
        sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
        sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Audio Transcriber using WhisperX')
    parser.add_argument('--file', help='Process specific file instead of all files')
    parser.add_argument('--config', default='config.yaml', help='Path to configuration file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    parser.add_argument('--test', action='store_true', help='Enable test mode (process sample.oga)')
    parser.add_argument('--fast', action='store_true', help='Use fast mode with pre-warmed models')

    args = parser.parse_args()

    # Быстрый режим с pre-warmed моделями
    if args.fast:
        print("🚀 Запуск в быстром режиме...")
        from fast_transcriber import FastTranscriber

        try:
            transcriber = FastTranscriber(args.config)

            if args.test:
                # Тестовый режим
                test_file = Path("input/sample.oga")
                if test_file.exists():
                    transcriber.transcribe_to_text(str(test_file))
                else:
                    print("❌ Тестовый файл input/sample.oga не найден")
                    return 1

            elif args.file:
                # Обработка одного файла
                transcriber.transcribe_to_text(args.file)

            else:
                # Пакетная обработка не поддерживается в быстром режиме
                print("⚠️ Быстрый режим поддерживает только обработку одного файла")
                print("Используйте: python transcriber.py --fast --file path/to/audio.oga")
                return 1

            print("✅ Быстрая обработка завершена!")
            return 0

        except Exception as e:
            print(f"❌ Ошибка быстрого режима: {e}")
            return 1

    # Обычный режим (существующий код)
    try:
        # Load configuration
        config = ConfigLoader.load(args.config)

        # Initialize logger
        debug_flag = config.get('whisperx', {}).get('debug', False)
        logger = Logger(config.get('output_directory', 'output'), verbose=args.verbose, debug=debug_flag)
        logger.info("Starting Audio Transcriber")

        # Initialize components
        file_manager = FileManager(config, logger, test_mode=args.test)
        audio_processor = AudioProcessor(config, logger)

        # Process files
        if args.file:
            # Process single file
            logger.info(f"Processing single file: {args.file}")
            file_manager.process_file(args.file, audio_processor)
        else:
            # Process all files in input directory
            if args.test:
                logger.info("Test mode: Processing sample.oga file")
            else:
                logger.info("Processing all files in input directory (excluding sample.oga)")
            file_manager.process_all_files(audio_processor)

        logger.info("Audio Transcriber completed successfully")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
