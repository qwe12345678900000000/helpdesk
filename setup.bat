@echo off
cd /d "%~dp0"
echo.
echo ===== 1/6  Creating virtual environment (.venv) =====
if not exist .venv python -m venv .venv
if not exist .venv\Scripts\activate.bat goto err
call .venv\Scripts\activate.bat
echo.
echo ===== 2/6  Installing packages (needs Internet, 1-5 min) =====
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 goto err
echo.
echo ===== 3/6  Creating .env file =====
if not exist .env python -c "import secrets,pathlib; t=pathlib.Path('.env.example').read_text(encoding='utf-8'); pathlib.Path('.env').write_text(t.replace('dev-secret-change-me', secrets.token_urlsafe(50)), encoding='utf-8')"
if not exist .env goto err
echo .env is ready
echo.
echo ===== 4/6  Creating tables in database (migrations) =====
python manage.py makemigrations accounts catalog applicants tickets
if errorlevel 1 goto err
python manage.py migrate
if errorlevel 1 goto err
echo.
echo ===== 5/6  Demo data =====
python manage.py seed_demo
if errorlevel 1 goto err
echo.
echo ===== 6/6  Create main administrator =====
echo Username: admin   Email: just press Enter   Password: type it (it is invisible!)
python manage.py createsuperuser
echo.
echo ===================================================
echo  DONE! Now double-click start_server.bat
echo ===================================================
pause
exit /b 0
:err
echo.
echo !!!!! ERROR !!!!! Read the red/last lines above and find them in the instruction (section "Oshibki").
pause
exit /b 1
