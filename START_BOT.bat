@echo off
echo ============================================================
echo   STARTING WHATSAPP BOT
echo ============================================================
echo.

cd /d "%~dp0AI-CHATBOT"

echo [1] Checking dependencies...
pip show twilio >nul 2>&1
if errorlevel 1 (
    echo     Installing dependencies...
    pip install -r requirements.txt
)

echo [2] Starting bot on port 5000...
echo.
echo Bot will start in 3 seconds...
echo Press Ctrl+C to stop
echo.
timeout /t 3 >nul

python run.py

pause
