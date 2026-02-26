@echo off
echo ========================================
echo AI Chatbot ML - Windows Setup
echo ========================================

echo Step 1: Checking Python...
python --version
if errorlevel 1 (
    echo Python not found! Please install Python 3.8+
    pause
    exit /b
)

echo Step 2: Upgrading pip...
python -m pip install --upgrade pip setuptools wheel

echo Step 3: Installing requirements...
python -m pip install -r requirements-simple.txt

echo Step 4: Running setup helper...
python setup_helper.py

echo.
echo Setup complete! Press any key to exit.
pause
