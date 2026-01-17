# AI Chat Application - Backend API

A Django REST Framework backend for AI Chat Application with JWT authentication, role-based access control, and admin management.

## Project Structure

```
harry/
├── manage.py
├── requirements.txt
├── .env
├── harry/                    # Project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── celery.py
│   ├── wsgi.py
│   └── asgi.py
├── authentication/           # User authentication
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── tasks.py
│   ├── permissions.py
│   ├── utils.py
│   └── admin.py
├── dashboard/                # Dashboard statistics
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── user_management/          # User management
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
├── administrators/           # Admin management
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── permissions.py
├── templates/
│   └── emails/
├── media/
│   └── profile_pictures/
```

## Quick Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Edit `.env` file with your settings:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=ai_chat_db
DB_USER=postgres
DB_PASSWORD=your-password
```

### 4. Create Database

```bash
# PostgreSQL
createdb ai_chat_db
```

### 5. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Start Redis (for Celery)

```bash
redis-server
```

### 7. Start Celery Worker

```bash
celery -A harry worker -l info
```

### 8. Start Celery Beat (Optional - for scheduled tasks)

```bash
celery -A harry beat -l info
```

### 9. Run Server

```bash
python manage.py runserver
```

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/register-superadmin/` | Register Super Admin |
| POST | `/api/register/` | Register User |
| POST | `/api/resend-otp/` | Resend OTP |
| POST | `/api/verify-otp/` | Verify OTP |
| POST | `/api/login/` | Login |
| POST | `/api/logout/` | Logout |
| POST | `/api/password-reset-request/` | Request Password Reset |
| POST | `/api/verify-reset-otp/` | Verify Reset OTP |
| POST | `/api/password-reset/` | Reset Password |
| POST | `/api/change-password/` | Change Password |
| POST | `/api/token-refresh/` | Refresh Token |
| GET/PATCH | `/api/profile/` | View/Update Profile |

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats/` | Dashboard Statistics |
| GET | `/api/dashboard/chat-growth/monthly/` | Monthly Growth |
| GET | `/api/dashboard/chat-growth/yearly/` | Yearly Growth |

### User Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/user-management/users/` | List Users |
| POST | `/api/user-management/users/{id}/disable/` | Disable User |
| POST | `/api/user-management/users/{id}/enable/` | Enable User |
| DELETE | `/api/user-management/users/{id}/` | Delete User (Request) |
| POST | `/api/user-management/users/{id}/confirm-delete/` | Confirm Delete |
| POST | `/api/user-management/users/{id}/cancel-delete/` | Cancel Delete |

### Administrators

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/administrators/admins/` | List Admins |
| POST | `/api/administrators/admins/create/` | Create Staff Admin |
| PATCH | `/api/administrators/admins/{id}/` | Update Admin |
| POST | `/api/administrators/admins/{id}/disable/` | Disable Admin |
| POST | `/api/administrators/admins/{id}/enable/` | Enable Admin |
| DELETE | `/api/administrators/admins/{id}/delete/` | Delete Admin |

## API Documentation

Visit `/api/docs/` for Swagger UI documentation.

## User Roles

- **USER**: Regular application user
- **STAFF_ADMIN**: Staff administrator
- **SUPER_ADMIN**: Super administrator with full access

## Response Format

### Success Response

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": {}
}
```

### Error Response

```json
{
  "success": false,
  "message": "Error description",
  "errors": {
    "field_name": ["Error message"]
  }
}
```

## Testing with cURL

### Register User

```bash
curl -X POST http://localhost:8000/api/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "TestPass@123",
    "re_type_password": "TestPass@123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass@123"
  }'
```

### Get Profile (with token)

```bash
curl -X GET http://localhost:8000/api/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```
