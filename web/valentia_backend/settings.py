import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'change-me-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '*').split(',')

# Allow hostnames with underscores (for Cloudflare tunnels)
# Django validates hostnames according to RFC, but Cloudflare allows underscores
import django.http.request
import re

# Patch the hostname validation to allow underscores
original_validate_host = django.http.request.validate_host

def validate_host(host, allowed_hosts):
    # Allow underscores in hostnames for Cloudflare compatibility
    if '_' in host:
        # Check if host matches any allowed host pattern
        if '*' in allowed_hosts or any(host == allowed or host.endswith('.' + allowed) for allowed in allowed_hosts if allowed != '*'):
            return True
    return original_validate_host(host, allowed_hosts)

django.http.request.validate_host = validate_host

# Also patch the get_host method to bypass RFC validation for underscores
original_get_host = django.http.request.HttpRequest.get_host

def get_host(self):
    """Override get_host to allow underscores in hostnames"""
    # Get the raw host header
    host = self.META.get('HTTP_HOST', '')
    if not host:
        # Fallback to SERVER_NAME
        host = self.META.get('SERVER_NAME', '')
    
    # If hostname contains underscore, bypass Django's strict validation
    if '_' in host:
        # Remove port if present
        if ':' in host:
            host, port = host.rsplit(':', 1)
        # Return the host as-is (bypassing RFC validation)
        return host
    
    # Use original method for normal hostnames
    return original_get_host(self)

django.http.request.HttpRequest.get_host = get_host

# CSRF trusted origins
_csrf_trusted_origins_env = os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '')
if _csrf_trusted_origins_env:
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_trusted_origins_env.split(',') if origin.strip()]
else:
    # Default CSRF trusted origins for Cloudflare tunnels
    CSRF_TRUSTED_ORIGINS = [
        'https://meshcore_bridge.enviroscan.ai',
        'https://meshcore_app.enviroscan.ai',
    ]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'apps.meshcore',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'valentia_backend.urls'

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

WSGI_APPLICATION = 'valentia_backend.wsgi.application'

# Database
DATABASES = {
    'default': dj_database_url.config(
        default=f'postgresql://meshtastic:meshtastic@db:5432/meshtastic',
        conn_max_age=600
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# CORS settings
CORS_ALLOW_ALL_ORIGINS = DEBUG
_cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '').strip()
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in _cors_origins.split(',') if origin.strip()] if _cors_origins and not DEBUG else []

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Login URL
LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/meshtastic/'
