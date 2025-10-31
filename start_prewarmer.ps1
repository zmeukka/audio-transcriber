# Скрипт для запуска WhisperX Pre-warmer в Windows PowerShell

Write-Host "🔥 Запуск WhisperX Pre-warmer..." -ForegroundColor Yellow

# Проверяем виртуальное окружение
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠️ Виртуальное окружение не активировано" -ForegroundColor Yellow
    Write-Host "Активируем .venv..." -ForegroundColor Cyan

    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & ".venv\Scripts\Activate.ps1"
    } else {
        Write-Host "❌ Виртуальное окружение .venv не найдено" -ForegroundColor Red
        Write-Host "Запустите: python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
}

# Устанавливаем UTF-8
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

Write-Host "📦 Запускаем pre-warming..." -ForegroundColor Green
python prewarmer.py

Write-Host "✅ Pre-warmer завершен!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Теперь можно использовать быстрый режим:" -ForegroundColor Cyan
Write-Host '  $env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --fast --file input\audio.oga' -ForegroundColor White
Write-Host '  $env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --fast --test' -ForegroundColor White
