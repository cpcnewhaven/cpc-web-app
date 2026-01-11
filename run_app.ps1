# PowerShell script to start the CPC Web App with virtual environment
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting CPC Web App" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Please create it first by running: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
try {
    & .\venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated successfully!" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Failed to activate virtual environment!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if app.py exists
if (-not (Test-Path "app.py")) {
    Write-Host "ERROR: app.py not found!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting Flask application..." -ForegroundColor Yellow
Write-Host ""

# Run the Flask app
try {
    python app.py
} catch {
    Write-Host ""
    Write-Host "Application exited with an error." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Read-Host "Press Enter to exit"
}

