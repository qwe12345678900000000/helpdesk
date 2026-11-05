# HelpDesk — Система регистрации обращений пользователей

Django 5.1 + Django REST Framework + PostgreSQL + Redis (Memurai) + JWT.

## Быстрый старт (Windows, PowerShell)

```powershell
cd C:\Study\helpdesk
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env          # затем вписать свой SECRET_KEY
```

База данных (в отдельном окне, от имени postgres):

```sql
CREATE USER helpdesk WITH PASSWORD 'helpdesk' CREATEDB;
CREATE DATABASE helpdesk OWNER helpdesk;
```

```powershell
python manage.py makemigrations accounts catalog applicants tickets
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo       # демо-данные, пароль сотрудников Demo12345!
python manage.py runserver
```

| Адрес | Что там |
|---|---|
| http://127.0.0.1:8000/admin/ | панель управления |
| http://127.0.0.1:8000/dashboard/ | дашборд KPI |
| http://127.0.0.1:8000/api/ | список эндпоинтов (DRF) |
| http://127.0.0.1:8000/api/docs/ | Swagger |

Тесты: `python manage.py test apps`
