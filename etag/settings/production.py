import os
from etag.settings.base import *
import logging

logger = logging.getLogger(__name__)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Временно включим DEBUG для просмотра ошибок

# Добавляем отладочную информацию
print(f"BASE_DIR: {BASE_DIR}")
print(f"STATIC_ROOT: {os.path.join(BASE_DIR, 'staticfiles')}")
print(f"STATICFILES_DIRS: {[os.path.join(BASE_DIR, 'profiles', 'static')]}")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'profiles', 'static'),
]

# Включаем сжатие статики обратно
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Добавим отладочную информацию
print("Checking static directories:")
for static_dir in STATICFILES_DIRS:
    print(f"Directory {static_dir} exists: {os.path.exists(static_dir)}")
print(f"STATIC_ROOT directory exists: {os.path.exists(STATIC_ROOT)}")

logger.info(f"STATIC_ROOT: {STATIC_ROOT}")
logger.info(f"STATICFILES_DIRS: {STATICFILES_DIRS}")
logger.info(f"BASE_DIR: {BASE_DIR}")

# Whitenoise settings
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

# Whitenoise specific settings
WHITENOISE_USE_FINDERS = True
WHITENOISE_ROOT = None
WHITENOISE_MAX_AGE = 31536000
WHITENOISE_MANIFEST_STRICT = False
WHITENOISE_ALLOW_ALL_ORIGINS = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Security settings
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
} 