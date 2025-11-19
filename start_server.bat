@echo off
echo Starting the store management server components...

REM --- 1. Start Nginx (The proxy on port 80) ---
REM The 'start ""' command runs the process without blocking the terminal.
echo.
echo Starting Nginx...
start "" "E:\@ My Clients\Deployment\Nginx\nginx-1.28.0\nginx.exe"

REM --- 2. Start Waitress (The Python server on port 8080) ---
REM We use 'cmd /k' and a title to keep the console window open.
REM This allows you to monitor the Waitress warnings/logs.
echo.
echo Starting Waitress server (A new console window will open)...
cd /d "E:\@ My Clients\Tareek Marash\store_management_app"
start "Waitress Server" cmd /k python run_server.py

echo.
echo Server launch complete.
echo Navigate to http://localhost to view the application.
pause