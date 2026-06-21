# PowerShell script for installing Google Drive Integration
# Windows-compatible version

Write-Host "🚀 Installing Google Drive Integration for CPC Web App" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Find Python - check multiple locations
$PythonCmd = $null
$PipCmd = $null

# Check for Python in venv first (Windows)
if (Test-Path "venv\Scripts\python.exe") {
    $PythonCmd = "venv\Scripts\python.exe"
    $PipCmd = "venv\Scripts\pip.exe"
    Write-Host "✅ Found Python in virtual environment" -ForegroundColor Green
}
# Check for Python in venv (Unix-style, in case of WSL)
elseif (Test-Path "venv/bin/python3") {
    $PythonCmd = "venv/bin/python3"
    $PipCmd = "venv/bin/pip3"
    Write-Host "✅ Found Python in virtual environment (Unix-style)" -ForegroundColor Green
}
elseif (Test-Path "venv/bin/python") {
    $PythonCmd = "venv/bin/python"
    $PipCmd = "venv/bin/pip"
    Write-Host "✅ Found Python in virtual environment (Unix-style)" -ForegroundColor Green
}
# Check system Python
else {
    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    $python = Get-Command python -ErrorAction SilentlyContinue
    
    if ($python3) {
        $PythonCmd = "python3"
        $PipCmd = "pip3"
        Write-Host "✅ Found system Python3" -ForegroundColor Green
    }
    elseif ($python) {
        $PythonCmd = "python"
        $PipCmd = "pip"
        Write-Host "✅ Found system Python" -ForegroundColor Green
    }
}

# Check if Python was found
if (-not $PythonCmd) {
    Write-Host "❌ Python is not installed or not found in PATH." -ForegroundColor Red
    Write-Host "💡 Tip: If you have a virtual environment, make sure it's activated or run this script from the project root." -ForegroundColor Yellow
    exit 1
}

# Verify Python works
try {
    $version = & $PythonCmd --version 2>&1
    Write-Host "✅ Found Python: $version" -ForegroundColor Green
    Write-Host "✅ Using: $PythonCmd" -ForegroundColor Green
    Write-Host ""
}
catch {
    Write-Host "❌ Python found but not working: $PythonCmd" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}

# Install Google Drive dependencies
Write-Host "📦 Installing Google Drive dependencies..." -ForegroundColor Cyan
& $PipCmd install google-api-python-client google-auth-oauthlib google-auth

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Dependencies installed successfully" -ForegroundColor Green
}
else {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create data directory if it doesn't exist
if (-not (Test-Path "data")) {
    New-Item -ItemType Directory -Path "data" | Out-Null
    Write-Host "✅ Created data directory" -ForegroundColor Green
}

# Create a simple test script
Write-Host "🧪 Creating test script..." -ForegroundColor Cyan
$testScriptTemplate = @'
#!/usr/bin/env python3
# Test Google Drive integration

try:
    from google_drive_integration import GoogleDriveGalleryManager
    print("Google Drive integration is ready!")
    print("Next steps:")
    print("1. Set up Google Cloud Console credentials")
    print("2. Download credentials.json to project root")
    print("3. Run: {0} google_drive_integration.py sync")
    print("4. Or use the admin interface at /admin/google-drive")
except ImportError as e:
    print(f"Import error: {e}")
    print("Please check your Python environment and try again.")
'@

$testScript = $testScriptTemplate -f $PythonCmd
$testScriptPath = Join-Path $PWD "test_google_drive.py"
[System.IO.File]::WriteAllText($testScriptPath, $testScript)
Write-Host "✅ Test script created: test_google_drive.py" -ForegroundColor Green

# Run the test
Write-Host "🧪 Testing Google Drive integration..." -ForegroundColor Cyan
& $PythonCmd test_google_drive.py

Write-Host ""
Write-Host "🎉 Google Drive integration setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:"
Write-Host "1. Go to https://console.cloud.google.com/"
Write-Host "2. Create a project and enable Google Drive API"
Write-Host "3. Create OAuth 2.0 credentials (Desktop application)"
Write-Host "4. Download credentials.json to your project root"
Write-Host "5. Run: $PythonCmd google_drive_integration.py sync"
Write-Host "6. Or access the admin interface at /admin/google-drive"
Write-Host ""
$helpCmd = $PythonCmd + ' setup_google_drive.py'
Write-Host 'For help, run:' $helpCmd
Write-Host ''

