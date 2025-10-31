#!/bin/bash
# Скрипт для запуска WhisperX Pre-warmer в Linux/Ubuntu

echo "🔥 Запуск WhisperX Pre-warmer..."

# Проверяем виртуальное окружение
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️ Виртуальное окружение не активировано"
    echo "Активируем .venv..."

    if [[ -f ".venv/bin/activate" ]]; then
        source .venv/bin/activate
    else
        echo "❌ Виртуальное окружение .venv не найдено"
        echo "Запустите: python3 -m venv .venv && source .venv/bin/activate"
        exit 1
    fi
fi

# Устанавливаем UTF-8
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

echo "📦 Запускаем pre-warming..."
python prewarmer.py

echo "✅ Pre-warmer завершен!"
echo ""
echo "💡 Теперь можно использовать быстрый режим:"
echo "  python transcriber.py --fast --file input/audio.oga"
echo "  python transcriber.py --fast --test"
