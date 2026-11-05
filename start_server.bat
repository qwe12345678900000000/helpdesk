@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo .venv not found. Run setup.bat first!
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
echo.
echo  Server is starting. Open in browser:  http://127.0.0.1:8000/admin/
echo  DO NOT CLOSE THIS WINDOW while you work. To stop: Ctrl+C or close window.
echo.
python manage.py runserver
pause
