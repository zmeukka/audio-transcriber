он# 🚀 Быстрое развертывание Audio Transcriber

## Windows PowerShell
```powershell
git clone <repository_url>
cd Audio_Transcriber
.\setup_environment.ps1
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --test
```

## Ubuntu 24.04
```bash
git clone <repository_url>
cd Audio_Transcriber
chmod +x setup_environment_ubuntu.sh
./setup_environment_ubuntu.sh
source ./activate_env.sh
python transcriber.py --test
```

## Мгновенная проверка работоспособности

### 1. Положите тестовый аудиофайл в папку `input/`
### 2. Запустите:

**Windows:**
```powershell
$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py
```

**Ubuntu:**
```bash
python transcriber.py
```

### 3. Проверьте результат в папке `output/`

## 🎯 Что должно работать из коробки:
- ✅ Распознавание русской речи
- ✅ Модель `base` (оптимальное качество/скорость)
- ✅ Автоматическая очистка временных файлов
- ✅ Отображение времени обработки
- ✅ UTF-8 кодировка для корректной работы с кириллицей
- ✅ Обработка форматов: .mp3, .wav, .m4a, .ogg, .flac, .oga

## 🔧 Если что-то не работает:
1. Проверьте версию Python: `python --version` (нужен 3.8+)
2. Проверьте ffmpeg: `ffmpeg -version`
3. Ubuntu: `sudo apt install python3-dev build-essential`
4. Windows: Запустите PowerShell от имени администратора
