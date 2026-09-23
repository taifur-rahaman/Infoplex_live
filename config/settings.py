"""
Django settings for InfoPlex.
SQLite by default; set DATABASE_URL for PostgreSQL (Render).
"""
import os
from pathlib import Path

import dj_database_url


BASE_DIR = Path(__file__).resolve().parent.parent

# Prefer SECRET_KEY (Render); fall back to DJANGO_SECRET_KEY for local/.env.example
SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-infoplex-dev-only-change-in-production",
)

# Default False for production safety; set DJANGO_DEBUG=True (or DEBUG=true) locally
_debug_raw = os.environ.get("DEBUG", os.environ.get("DJANGO_DEBUG", "False"))
DEBUG = str(_debug_raw).lower() in ("1", "true", "yes")

_allowed = os.environ.get(
    "ALLOWED_HOSTS",
    os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver"),
)
ALLOWED_HOSTS = [h.strip() for h in _allowed.split(",") if h.strip()]

# Render injects the public hostname; also accept any *.onrender.com subdomain
_render_host = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _render_host and _render_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_render_host)
if ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")

if DEBUG and "*" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append("*")

_csrf = os.environ.get("CSRF_TRUSTED_ORIGINS", "").strip()
CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf.split(",") if o.strip()]
if _render_host:
    _origin = f"https://{_render_host}"
    if _origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(_origin)
# Trust Render subdomains when not explicitly listed
if not any(o.endswith(".onrender.com") or "onrender.com" in o for o in CSRF_TRUSTED_ORIGINS):
    CSRF_TRUSTED_ORIGINS.append("https://*.onrender.com")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
    "lms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lms.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if DATABASE_URL:
    # Render sets RENDER=true and requires SSL to managed Postgres
    _ssl = bool(os.environ.get("RENDER")) or os.environ.get(
        "DATABASE_SSL_REQUIRE", ""
    ).lower() in ("1", "true", "yes")
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL, conn_max_age=600, ssl_require=_ssl
        ),
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "lms:dashboard"
LOGOUT_REDIRECT_URL = "lms:home"

# Render / reverse-proxy TLS termination
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
if not DEBUG:
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in (
        "1",
        "true",
        "yes",
    )
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Brevo email (mock/fallback when no API key)
BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "").strip()
BREVO_SENDER_EMAIL = os.environ.get(
    "BREVO_SENDER_EMAIL", "noreply@infoplex.local"
)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = BREVO_SENDER_EMAIL

# Brand / site display name (single source of truth for UI titles & chrome)
# Brand is fixed — do not override via env (avoids stale SITE_NAME=InfoPlex)
SITE_NAME = "InfoPlex"
BRAND_MARK = "I"

# Manual bKash payment
BKASH_ACCOUNT_NUMBER = os.environ.get("BKASH_ACCOUNT_NUMBER", "01700000000")
BKASH_ACCOUNT_NAME = os.environ.get("BKASH_ACCOUNT_NAME", SITE_NAME)

# Pagination
COURSES_PER_PAGE = 8
