# Setup Virtual Environment for Audio Transcriber
# Creates .venv and installs required packages

param(
    [switch]$Force  # Force recreate if exists
)

Set-Location $PSScriptRoot\..

# Check if .venv exists
if (Test-Path ".venv") {
    if ($Force) {
        Write-Host "Removing existing .venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force .venv
    } else {
        Write-Host ".venv already exists. Use -Force to recreate" -ForegroundColor Green
        Write-Host "To activate: .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
        exit 0
    }
}

# Find Python executable
$pythonExes = @("python", "python3", "py")
$foundPython = $null

foreach ($exe in $pythonExes) {
    try {
        $version = & $exe --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $foundPython = $exe
            Write-Host "Found Python: $version" -ForegroundColor Green
            break
        }
    }
    catch {
        # Continue to next executable
    }
}

if (-not $foundPython) {
    Write-Host "Python not found. Please install Python 3.6+ and add it to PATH" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
& $foundPython -m venv .venv

if (-not $?) {
    Write-Host "Failed to create virtual environment" -ForegroundColor Red
    exit 1
}

Write-Host "Virtual environment created successfully!" -ForegroundColor Green

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .venv\Scripts\Activate.ps1

# Install requirements if they exist
if (Test-Path "requirements.txt") {
    Write-Host "Installing requirements..." -ForegroundColor Cyan
    & .venv\Scripts\python.exe -m pip install --upgrade pip
    & .venv\Scripts\python.exe -m pip install -r requirements.txt

    if ($?) {
        Write-Host "Requirements installed successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to install some requirements" -ForegroundColor Yellow
    }
} else {
    Write-Host "No requirements.txt found, skipping package installation" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup completed!" -ForegroundColor Green
Write-Host "To activate the environment: .venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host "To deactivate: deactivate" -ForegroundColor Cyan
Write-Host ""
Write-Host "Now you can run: cd models; .\init.ps1" -ForegroundColor Cyan
