"""
Django settings for harry project.
"""
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import timedelta
from decouple import config, Csv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'harryapi.dsrt321.online,localhost,127.0.0.1').split(',')

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv('CSRF_TRUSTED_ORIGINS', 'https://harryapi.dsrt321.online,http://localhost:8000').split(',') if origin.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'drf_spectacular',
    
    # Local appsSTATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' 
    'authentication.apps.AuthenticationConfig',
    'dashboard.apps.DashboardConfig',
    'user_management.apps.UserManagementConfig',
    'administrators.apps.AdministratorsConfig',
    'chat.apps.ChatConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # Static files handling
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'harry.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'harry.wsgi.application'

# Database
# Use SQLite for development/testing, PostgreSQL for production
if config('USE_SQLITE', default=True, cast=bool):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', default='django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', default='ai_chat_db'),
            'USER': os.getenv('DB_USER', default='postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', default='postgres'),
            'HOST': os.getenv('DB_HOST', default='localhost'),
            'PORT': os.getenv('DB_PORT', default='5432'),
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # Static files handling

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'authentication.utils.custom_exception_handler',
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=3600, cast=int)),
    'REFRESH_TOKEN_LIFETIME': timedelta(minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=10080, cast=int)),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS Settings
CORS_ALLOW_HEADERS = [
    'content-type',
    'authorization',
    'accept',
    'origin',
    'x-requested-with',
]
 
CORS_ALLOW_METHODS = [
    'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'
]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',') if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

# Email Settings
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='poritoshpal98@gmail.com')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='cdjr oxby fnat wyog')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='poritoshpal98@gmail.com')

# Redis Configuration
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Celery Settings
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'AI Chat Application API',
    'DESCRIPTION': 'Backend API for AI Chat Application',
    'VERSION': '1.0.0',
}

# OTP Settings
OTP_EXPIRY_MINUTES = 10
