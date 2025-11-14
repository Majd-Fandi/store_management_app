@echo off
echo Setting up database...
python manage.py migrate
echo Starting server...
start "" "python" manage.py runserver
timeout /t 3 >nul
start "" "http://localhost:8000"
pause