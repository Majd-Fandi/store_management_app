@echo off
echo Starting the store management server components...

REM --- 1. Start Nginx (The proxy on port 80) ---
REM The 'start ""' command runs the process without blocking the terminal.
echo.
echo Starting Nginx...

start "" "C:\majd\nginx-1.28.0\nginx.exe"

REM --- 2. Start Waitress (The Python server on port 8080) ---
REM We use 'cmd /k' and a title to keep the console window open.
REM This allows you to monitor the Waitress warnings/logs.
echo.
echo Starting Waitress server (A new console window will open)...
cd /d "C:\majd\tarek\store_management_app"

start "Waitress Server" cmd /k "call venv\Scripts\activate.bat && python run_server.py"

echo.
echo Server launch complete.
echo Navigate to http://localhost to view the application.

timeout /t 3 >nul
start "" "http://localhost:8080"
pause
