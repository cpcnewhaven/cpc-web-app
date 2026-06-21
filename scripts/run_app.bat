@echo off
echo ========================================
echo Starting CPC Web App
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please create it first by running: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if activation was successful
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo Virtual environment activated successfully!
echo.
echo Starting Flask application...
echo.

REM Run the Flask app
python app.py

REM If app exits, keep window open
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)

