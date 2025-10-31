#!/bin/bash
# Скрипт для настройки окружения Audio Transcriber в Ubuntu 24.04

set -e  # Остановить выполнение при ошибке

echo "🚀 Начинаем настройку окружения Audio Transcriber для Ubuntu 24.04..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Проверка версии Ubuntu
print_step "Проверка версии операционной системы..."
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    echo "Операционная система: $NAME $VERSION"
    if [[ "$VERSION_ID" != "24.04" && "$VERSION_ID" != "22.04" && "$VERSION_ID" != "20.04" ]]; then
        print_warning "Скрипт оптимизирован для Ubuntu 20.04+, но может работать и на вашей версии."
    fi
else
    print_warning "Не удалось определить версию ОС. Продолжаем..."
fi

# Обновление пакетов
print_step "Обновление списка пакетов..."
sudo apt update

# Установка системных зависимостей
print_step "Установка системных зависимостей..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    git \
    curl \
    build-essential \
    pkg-config \
    libasound2-dev \
    portaudio19-dev \
    libsndfile1-dev

# Проверка версии Python
print_step "Проверка версии Python..."
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "Версия Python: $PYTHON_VERSION"

# Проверка, что Python версии 3.8+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [[ $PYTHON_MAJOR -lt 3 ]] || [[ $PYTHON_MAJOR -eq 3 && $PYTHON_MINOR -lt 8 ]]; then
    print_error "Требуется Python 3.8 или выше. Найдена версия: $PYTHON_VERSION"
    exit 1
fi

print_status "Python версии $PYTHON_VERSION подходит!"

# Проверка ffmpeg
print_step "Проверка установки ffmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VERSION=$(ffmpeg -version | head -n1 | cut -d' ' -f3)
    print_status "ffmpeg установлен: версия $FFMPEG_VERSION"
else
    print_error "ffmpeg не найден после установки!"
    exit 1
fi

# Создание виртуального окружения
print_step "Создание виртуального окружения..."
if [[ -d ".venv" ]]; then
    print_warning "Виртуальное окружение .venv уже существует. Удаляем старое..."
    rm -rf .venv
fi

python3 -m venv .venv
print_status "Виртуальное окружение .venv создано!"

# Активация виртуального окружения
print_step "Активация виртуального окружения..."
source .venv/bin/activate

# Обновление pip
print_step "Обновление pip..."
pip install --upgrade pip

# Установка PyTorch (совместимые версии)
print_step "Установка PyTorch..."
pip install torch==2.8.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cpu

# Установка WhisperX
print_step "Установка WhisperX..."
pip install whisperx

# Установка дополнительных зависимостей
print_step "Установка дополнительных Python пакетов..."
pip install pyyaml psutil

# Проверка установки WhisperX
print_step "Проверка установки WhisperX..."
if python -c "import whisperx; print('WhisperX успешно импортирован')" 2>/dev/null; then
    print_status "WhisperX установлен корректно!"
else
    print_error "Проблема с установкой WhisperX!"
    exit 1
fi

# Создание необходимых директорий
print_step "Создание директорий проекта..."
mkdir -p input output manual models

print_status "Директории созданы: input/, output/, manual/, models/"

# Установка переменных среды для UTF-8
print_step "Настройка переменных среды для UTF-8..."
cat >> ~/.bashrc << 'EOF'

# Audio Transcriber environment variables
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
EOF

# Создание скрипта активации
print_step "Создание скрипта активации..."
cat > activate_env.sh << 'EOF'
#!/bin/bash
# Скрипт для активации окружения Audio Transcriber

echo "🎵 Активация окружения Audio Transcriber..."

# Активация виртуального окружения
source .venv/bin/activate

# Установка переменных среды
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

echo "✅ Окружение активировано!"
echo ""
echo "Доступные команды:"
echo "  python transcriber.py --test                    # Тест на sample.oga"
echo "  python transcriber.py --file input/file.oga     # Обработка одного файла"
echo "  python transcriber.py                           # Обработка всех файлов"
echo ""
echo "Для выхода из окружения: deactivate"
EOF

chmod +x activate_env.sh
print_status "Создан скрипт активации: ./activate_env.sh"

# Проверка финальной настройки
print_step "Финальная проверка настройки..."

# Проверка Python в виртуальном окружении
VENV_PYTHON_VERSION=$(python --version 2>&1)
print_status "Python в виртуальном окружении: $VENV_PYTHON_VERSION"

# Проверка установленных пакетов
echo "Установленные ключевые пакеты:"
pip list | grep -E "(torch|whisperx|pyyaml|psutil)" || true

print_step "Настройка завершена! 🎉"
echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}🎵 Audio Transcriber успешно настроен! 🎵${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo "Для начала работы:"
echo "1. Активируйте окружение:"
echo -e "   ${BLUE}source ./activate_env.sh${NC}"
echo ""
echo "2. Запустите тест:"
echo -e "   ${BLUE}python transcriber.py --test${NC}"
echo ""
echo "3. Для обработки своих файлов поместите их в папку input/ и запустите:"
echo -e "   ${BLUE}python transcriber.py${NC}"
echo ""
echo "📝 Примечания:"
echo "- Файлы для обработки помещайте в папку input/"
echo "- Результаты будут в папке output/"
echo "- Проблемные файлы попадут в папку manual/"
echo "- Поддерживаемые форматы: .mp3, .wav, .m4a, .ogg, .flac, .oga"
echo ""
echo "Для перезапуска в новой сессии терминала:"
echo -e "   ${BLUE}cd $(pwd) && source ./activate_env.sh${NC}"
echo ""
