"""
Django settings for sla_backend project.
Modified for Production Deployment.
"""

import os
from pathlib import Path

import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =========================================================
# SECURITY CONFIGURATION
# =========================================================

# Ambil SECRET_KEY dari Environment Variable (Railway/Render), jika tidak ada pakai default (untuk lokal)
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-default-key-for-dev-only')

# Matikan DEBUG di production. Set Environment Variable 'DEBUG' = 'False' di Railway.
# Jika tidak ada variable, defaultnya True (aman untuk lokal, bahaya untuk prod).
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

# Izinkan semua host di production (Railway/Render sering ganti domain/IP)
ALLOWED_HOSTS = ['*']


# =========================================================
# APPLICATION DEFINITION
# =========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 3rd Party Apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',            # Wajib untuk React
    'django.contrib.sites',   # Wajib untuk allauth
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'dj_rest_auth',
    'dj_rest_auth.registration',

    # Local Apps
    'tickets',
]

SITE_ID = 1

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",    # PENTING: Untuk CSS di Production
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",         # PENTING: Paling atas untuk React
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # PENTING: Allauth
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'sla_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sla_backend.wsgi.application'


# =========================================================
# DATABASE (Fixed)
# =========================================================

DATABASES = {
    'default': dj_database_url.config(
        # Saat lokal pakai sqlite, saat deploy otomatis baca DATABASE_URL dari Railway/Render
        default='sqlite:///db.sqlite3',
        conn_max_age=600
    )
}


# =========================================================
# AUTHENTICATION & PASSWORD
# =========================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Allauth & DRF Config
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' 

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}


# =========================================================
# INTERNATIONALIZATION & STATIC FILES
# =========================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# =========================================================
# CORS SETTINGS (React Connection)
# =========================================================

# Opsi 1: Izinkan semua (Gunakan ini dulu saat awal deploy agar tidak pusing)
CORS_ALLOW_ALL_ORIGINS = True 

# Opsi 2: Jika sudah production, ganti Opsi 1 dengan ini agar lebih aman:
# CORS_ALLOWED_ORIGINS = [
#     "https://nama-project-react-kamu.vercel.app",
#     "http://localhost:5173", # Jika pakai Vite local
# ]