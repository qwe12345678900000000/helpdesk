@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python manage.py test apps -v 2
echo.
echo  If you see "OK" above - all tests passed. Take a screenshot (Win+Shift+S).
pause
