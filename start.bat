@echo off
REM Simple startup script for LLM Analysis Quiz System (Windows)

echo Starting LLM Analysis Quiz System...

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install Playwright browsers
echo Installing Playwright browsers...
playwright install chromium

REM Check if .env exists
if not exist ".env" (
    echo Warning: .env file not found. Copying from .env.example...
    copy .env.example .env
    echo Please edit .env with your credentials before running again.
    exit /b 1
)

REM Start the application
echo Starting application...
python -m src.main
