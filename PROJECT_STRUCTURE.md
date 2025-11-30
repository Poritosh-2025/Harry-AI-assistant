# Django REST Framework - Auth & User Management System

## Simple Project Structure

```
auth_project/
├── config/                 # Project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
│
├── apps/
│   ├── __init__.py
│   │
│   ├── accounts/           # User model & authentication
│   │   ├── __init__.py
│   │   ├── models.py       # Custom User model
│   │   ├── serializers.py  # Auth serializers
│   │   ├── views.py        # Auth views (register, login, etc.)
│   │   ├── urls.py
│   │   ├── permissions.py  # Custom permissions
│   │   └── utils.py        # OTP helpers
│   │
│   ├── profiles/           # User profiles
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── admin_panel/        # Admin management
│   │   ├── __init__.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   └── api_keys/           # API key management
│       ├── __init__.py
│       ├── models.py
│       ├── serializers.py
│       ├── views.py
│       └── urls.py
│
├── manage.py
└── requirements.txt
```

## Apps Overview

| App | Purpose |
|-----|---------|
| `accounts` | User model, registration, login, OTP, password reset |
| `profiles` | View/update user profile |
| `admin_panel` | Staff admin creation, user management, dashboard |
| `api_keys` | API key CRUD operations |

## Quick Start

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure database in config/settings.py

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Start server
python manage.py runserver

# 6. Start Celery (for OTP emails)
celery -A config worker -l info
```
