@echo off
REM Скрипт для настройки окружения Audio Transcriber

echo Настройка переменных среды...

REM Добавление ffmpeg в PATH пользователя
powershell -Command "[Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';C:\Users\C5363083\IdeaProjects\ffmpeg-8.0-essentials_build\bin', 'User')"

echo ffmpeg добавлен в PATH пользователя.

REM Активация виртуального окружения
echo Активация виртуального окружения...
call .venv\Scripts\activate.bat

REM Проверка ffmpeg
echo Проверка ffmpeg...
ffmpeg -version 2>nul
if %errorlevel% equ 0 (
    echo ffmpeg работает корректно!
) else (
    echo ОШИБКА: ffmpeg не найден. Перезапустите PowerShell.
)

echo.
echo Окружение настроено. Для активации в новой сессии выполните:
echo .venv\Scripts\Activate.ps1

pause
