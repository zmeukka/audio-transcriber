# Audio Transcriber Environment Setup
Write-Host "Configuring Audio Transcriber environment..." -ForegroundColor Green

# Add ffmpeg to user PATH permanently
$ffmpegPath = "C:\Users\C5363083\IdeaProjects\ffmpeg-8.0-essentials_build\bin"
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($currentPath -notlike "*$ffmpegPath*") {
    [Environment]::SetEnvironmentVariable("Path", $currentPath + ";$ffmpegPath", "User")
    Write-Host "ffmpeg added to user PATH permanently." -ForegroundColor Yellow
} else {
    Write-Host "ffmpeg already in user PATH." -ForegroundColor Cyan
}

# Update PATH in current session
$env:Path += ";$ffmpegPath"

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\.venv\Scripts\Activate.ps1"

# Set UTF-8 encoding for better Unicode support
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
Write-Host "UTF-8 encoding configured for Python." -ForegroundColor Green

# Test ffmpeg
Write-Host "Testing ffmpeg..." -ForegroundColor Green
try {
    $result = ffmpeg -version 2>$null
    Write-Host "ffmpeg works correctly!" -ForegroundColor Green
} catch {
    Write-Host "WARNING: ffmpeg not working. Restart PowerShell." -ForegroundColor Red
}

# Test Python
Write-Host "Testing Python..." -ForegroundColor Green
try {
    $pythonVersion = & .\.venv\Scripts\python.exe --version
    Write-Host "Python works: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not working in .venv" -ForegroundColor Red
}

# Test whisperx
Write-Host "Testing WhisperX..." -ForegroundColor Green
try {
    & .\.venv\Scripts\python.exe -c "import whisperx; print('WhisperX imported successfully')"
    Write-Host "WhisperX works correctly!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: WhisperX not working" -ForegroundColor Red
}

Write-Host ""
Write-Host "Environment configured. You can now run:" -ForegroundColor Green
Write-Host '$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --test' -ForegroundColor Cyan
Write-Host "Or for single file:" -ForegroundColor Green
Write-Host '$env:PYTHONIOENCODING="utf-8"; $env:PYTHONUTF8="1"; python transcriber.py --file input\filename.oga' -ForegroundColor Cyan
