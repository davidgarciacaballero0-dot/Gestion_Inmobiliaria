"""
Django settings for Autogestión Inmobiliaria.
"""
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key')

DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# ─── Aplicaciones ────────────────────────────────────────────────
INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'cloudinary_storage',
    'cloudinary',
    'django_filters',
    'channels',
    'django.contrib.postgres',
    # Local apps
    'usuarios',
    'inmuebles',
    'pagos',
]

# ─── Middleware ───────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

redis_url = os.getenv('REDIS_URL')
if redis_url:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [redis_url],
            },
        },
    }
else:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ─── Base de Datos ───────────────────────────────────────────────
db_url = os.getenv('DATABASE_URL')
if db_url and (db_url.startswith('postgres://') or db_url.startswith('postgresql://')):
    from urllib.parse import urlparse
    url = urlparse(db_url)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': url.path[1:],
            'USER': url.username,
            'PASSWORD': url.password,
            'HOST': url.hostname,
            'PORT': url.port or '5432',
        }
    }
else:
    db_host = os.getenv('DB_HOST', 'localhost')
    db_options = {}
    if not db_host.startswith('/cloudsql') and (os.getenv('DB_ENGINE') or '').endswith('postgresql'):
        sslmode = os.getenv('DB_SSLMODE')
        if sslmode:
            db_options['sslmode'] = sslmode

    DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.getenv('DB_NAME', 'inmobiliaria_db'),
            'USER': os.getenv('DB_USER', 'postgres'),
            'PASSWORD': os.getenv('DB_PASSWORD', ''),
            'HOST': db_host,
            'PORT': os.getenv('DB_PORT', '5432'),
            'OPTIONS': db_options,
        }
    }

# ─── Contraseñas ─────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── Internacionalización ───────────────────────────────────────
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True

# ─── Archivos estáticos y media ─────────────────────────────────
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ─── Modelo de usuario personalizado ────────────────────────────
AUTH_USER_MODEL = 'usuarios.Usuario'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Django REST Framework ──────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─── Simple JWT ─────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ─── CORS ────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ─── Cloudinary (almacenamiento de imágenes) ───────────────────
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv('CLOUDINARY_CLOUD_NAME', ''),
    'API_KEY': os.getenv('CLOUDINARY_API_KEY', ''),
    'API_SECRET': os.getenv('CLOUDINARY_API_SECRET', ''),
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# ─── Stripe (Pasarela de pagos) ─────────────────────────────
STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# ─── Frontend URL ───────────────────────────────────────────
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')

# ─── Groq (IA Generativa) ───────────────────────────────────
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '').strip()

# ─── IA Local (LM Studio) ───────────────────────────────────
LOCAL_AI_URL = os.getenv('LOCAL_AI_URL', 'http://192.168.56.1:1234/v1/chat/completions')
LOCAL_AI_MODEL = os.getenv('LOCAL_AI_MODEL', 'meta-llama-3.1-8b-instruct')

# ─── Blockchain Gateway ──────────────────────────────────────
BLOCKCHAIN_GATEWAY_URL = os.getenv('BLOCKCHAIN_GATEWAY_URL', 'http://localhost:4000')
if BLOCKCHAIN_GATEWAY_URL and not BLOCKCHAIN_GATEWAY_URL.endswith('/api/blockchain'):
    BLOCKCHAIN_GATEWAY_URL = BLOCKCHAIN_GATEWAY_URL.rstrip('/') + '/api/blockchain'

# ─── Google Gemini AI Studio (Virtual Staging & Diseñador de Interiores con IA) ───
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '').strip()



