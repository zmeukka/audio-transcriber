# PowerShell wrapper script for Windows systems
# Finds Python and runs the initialization script with virtual environment support

Set-Location $PSScriptRoot

# Check if virtual environment exists and is activated
$venvPath = "..\\.venv"
$isVenvActivated = $env:VIRTUAL_ENV -ne $null

if (Test-Path $venvPath) {
    if (-not $isVenvActivated) {
        Write-Host "Virtual environment found but not activated" -ForegroundColor Yellow
        Write-Host "Activating virtual environment..." -ForegroundColor Cyan
        try {
            & "$venvPath\\Scripts\\Activate.ps1"
            $pythonExe = "$venvPath\\Scripts\\python.exe"
        }
        catch {
            Write-Host "Failed to activate virtual environment, falling back to system Python" -ForegroundColor Yellow
            $pythonExe = $null
        }
    } else {
        Write-Host "Virtual environment is active" -ForegroundColor Green
        $pythonExe = "$venvPath\\Scripts\\python.exe"
    }
} else {
    Write-Host "No virtual environment found at $venvPath" -ForegroundColor Yellow
    Write-Host "Run setup_venv.ps1 from project root to create one" -ForegroundColor Cyan
    $pythonExe = $null
}

# If no venv python, try to find system Python
if (-not $pythonExe) {
    $pythonExes = @("python", "python3", "py")

    foreach ($exe in $pythonExes) {
        try {
            $null = & $exe --version 2>$null
            if ($LASTEXITCODE -eq 0) {
                $pythonExe = $exe
                break
            }
        }
        catch {
            # Continue to next executable
        }
    }
}

if ($pythonExe) {
    Write-Host "Using Python: $pythonExe" -ForegroundColor Green
    & $pythonExe init_models.py $args
} else {
    Write-Host "Python not found. Please install Python 3.6+ and add it to PATH" -ForegroundColor Red
    Write-Host "Or run setup_venv.ps1 from project root to create virtual environment" -ForegroundColor Yellow
    exit 1
}

