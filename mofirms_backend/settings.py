import os
from pathlib import Path
from urllib.parse import unquote, urlparse

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() in {"1", "true", "yes"}
DEMO_MODE = os.environ.get("DEMO_MODE", "False").lower() in {"1", "true", "yes"}
NEWSLETTER_SIGNUPS_ENABLED = (
    os.environ.get("NEWSLETTER_SIGNUPS_ENABLED", "False").lower() in {"1", "true", "yes"}
)
DJANGO_ENVIRONMENT = os.environ.get("DJANGO_ENVIRONMENT", "development").strip().lower()
if DJANGO_ENVIRONMENT not in {"development", "staging", "production"}:
    raise ImproperlyConfigured(
        "DJANGO_ENVIRONMENT must be 'development', 'staging', or 'production'."
    )
if DJANGO_ENVIRONMENT in {"staging", "production"} and (DEBUG or DEMO_MODE):
    raise ImproperlyConfigured(
        "Staging and production require DJANGO_DEBUG=False and DEMO_MODE=False."
    )
if NEWSLETTER_SIGNUPS_ENABLED and (
    DJANGO_ENVIRONMENT != "production" or DEMO_MODE
):
    raise ImproperlyConfigured(
        "Newsletter signups can be enabled only on the non-demo production service."
    )
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured outside development.")
    SECRET_KEY = "local-development-only-change-before-deployment"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",")
    if origin.strip()
]
render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
    CSRF_TRUSTED_ORIGINS.append(f"https://{render_hostname}")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "farmers.apps.FarmersConfig",
    "smart_hasibu.apps.SmartHasibuConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "mofirms_backend.middleware.DemoReadOnlyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "mofirms_backend.urls"
SITE_ROOT = BASE_DIR
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [SITE_ROOT],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "farmers.context_processors.portal_settings",
            ],
        },
    },
]
WSGI_APPLICATION = "mofirms_backend.wsgi.application"
ASGI_APPLICATION = "mofirms_backend.asgi.application"

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
if not DEBUG and not DEMO_MODE and not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL must point to the staging or production PostgreSQL database."
    )
if DATABASE_URL:
    parsed_database = urlparse(DATABASE_URL)
    if parsed_database.scheme in {"postgres", "postgresql"}:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": unquote(parsed_database.path.lstrip("/")),
                "USER": unquote(parsed_database.username or ""),
                "PASSWORD": unquote(parsed_database.password or ""),
                "HOST": parsed_database.hostname or "",
                "PORT": parsed_database.port or "",
                "CONN_MAX_AGE": 60,
                "OPTIONS": {"sslmode": os.environ.get("DB_SSLMODE", "require")},
            }
        }
    elif parsed_database.scheme == "sqlite":
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": unquote(parsed_database.path),
            }
        }
    else:
        raise ImproperlyConfigured("DATABASE_URL must use PostgreSQL or SQLite.")
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
TIME_ZONE = "Africa/Nairobi"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [
    ("css", BASE_DIR / "css"),
    ("js", BASE_DIR / "js"),
    ("images", BASE_DIR / "images"),
]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}
PRIVATE_UPLOAD_ROOT = BASE_DIR / "private_uploads"
private_upload_setting = os.environ.get("PRIVATE_UPLOAD_ROOT", "").strip()
if private_upload_setting:
    PRIVATE_UPLOAD_ROOT = Path(private_upload_setting).resolve()
MEDIA_ROOT = PRIVATE_UPLOAD_ROOT
MEDIA_URL = "/private-media/"
FILE_UPLOAD_PERMISSIONS = 0o600
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o700
DATA_UPLOAD_MAX_MEMORY_SIZE = 110 * 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 20
FILE_UPLOAD_MAX_MEMORY_SIZE = 2_500_000

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "webmaster@localhost")
MOFIRMS_CONTACT_EMAIL = os.environ.get(
    "MOFIRMS_CONTACT_EMAIL", "mconceptslimited@gmail.com"
)
MPESA_ENABLED = os.environ.get("MPESA_ENABLED", "True").lower() in {"1", "true", "yes"}
MPESA_ENVIRONMENT = os.environ.get("MPESA_ENVIRONMENT", "sandbox").strip().lower()
if MPESA_ENVIRONMENT not in {"sandbox", "production"}:
    raise ImproperlyConfigured("MPESA_ENVIRONMENT must be 'sandbox' or 'production'.")
MPESA_BASE_URL = (
    "https://api.safaricom.co.ke"
    if MPESA_ENVIRONMENT == "production"
    else "https://sandbox.safaricom.co.ke"
)
MPESA_CONSUMER_KEY = os.environ.get("MPESA_CONSUMER_KEY", "").strip()
MPESA_CONSUMER_SECRET = os.environ.get("MPESA_CONSUMER_SECRET", "").strip()
MPESA_SHORTCODE = os.environ.get("MPESA_SHORTCODE", "").strip()
MPESA_PASSKEY = os.environ.get("MPESA_PASSKEY", "").strip()
MPESA_CALLBACK_URL = os.environ.get("MPESA_CALLBACK_URL", "").strip()
RETENTION_WEBHOOK_SECRET = os.environ.get("RETENTION_WEBHOOK_SECRET", "").strip()
RETENTION_WEBHOOK_URL = os.environ.get("RETENTION_WEBHOOK_URL", "").strip()
MPESA_TRANSACTION_TYPE = os.environ.get(
    "MPESA_TRANSACTION_TYPE", "CustomerPayBillOnline"
).strip()
if MPESA_TRANSACTION_TYPE not in {
    "CustomerPayBillOnline",
    "CustomerBuyGoodsOnline",
}:
    raise ImproperlyConfigured(
        "MPESA_TRANSACTION_TYPE must be CustomerPayBillOnline or CustomerBuyGoodsOnline."
    )
if not DEBUG and not DEMO_MODE:
    if DJANGO_ENVIRONMENT not in {"staging", "production"}:
        raise ImproperlyConfigured(
            "Set DJANGO_ENVIRONMENT to 'staging' or 'production' for a hosted service."
        )
    expected_mpesa_environment = (
        "sandbox" if DJANGO_ENVIRONMENT == "staging" else "production"
    )
    if MPESA_ENVIRONMENT != expected_mpesa_environment:
        raise ImproperlyConfigured(
            f"MPESA_ENVIRONMENT must be '{expected_mpesa_environment}' for "
            f"{DJANGO_ENVIRONMENT}."
        )
    missing_mpesa_settings = [] if not MPESA_ENABLED else [
        name
        for name, value in {
            "MPESA_CONSUMER_KEY": MPESA_CONSUMER_KEY,
            "MPESA_CONSUMER_SECRET": MPESA_CONSUMER_SECRET,
            "MPESA_SHORTCODE": MPESA_SHORTCODE,
            "MPESA_PASSKEY": MPESA_PASSKEY,
            "MPESA_CALLBACK_URL": MPESA_CALLBACK_URL,
        }.items()
        if not value
    ]
    if missing_mpesa_settings:
        raise ImproperlyConfigured(
            "Hosted M-PESA configuration is incomplete: "
            + ", ".join(missing_mpesa_settings)
            + "."
        )
    callback_url = urlparse(MPESA_CALLBACK_URL)
    if callback_url.scheme != "https" or not callback_url.netloc:
        raise ImproperlyConfigured(
            "MPESA_CALLBACK_URL must be an absolute HTTPS URL for hosted deployments."
        )
    if len(RETENTION_WEBHOOK_SECRET) < 32:
        raise ImproperlyConfigured(
            "RETENTION_WEBHOOK_SECRET must be a generated secret of at least 32 characters."
        )
    retention_url = urlparse(RETENTION_WEBHOOK_URL)
    if retention_url.scheme != "https" or not retention_url.netloc:
        raise ImproperlyConfigured(
            "RETENTION_WEBHOOK_URL must be an absolute HTTPS URL for hosted deployments."
        )

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.environ.get("DJANGO_HSTS_SECONDS", "0"))
    if SECURE_HSTS_SECONDS:
        SECURE_HSTS_INCLUDE_SUBDOMAINS = (
            os.environ.get("DJANGO_HSTS_INCLUDE_SUBDOMAINS", "False").lower()
            in {"1", "true", "yes"}
        )
    if os.environ.get("DJANGO_TRUST_PROXY_SSL_HEADER", "False").lower() in {
        "1", "true", "yes"
    }:
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

PORTAL_RATE_LIMIT = 5
PORTAL_RATE_PERIOD = 60 * 60

ANTIVIRUS_ENABLED = os.environ.get(
    "ANTIVIRUS_ENABLED", str(not DEBUG and not DEMO_MODE)
).lower() in {"1", "true", "yes"}
ANTIVIRUS_COMMAND = os.environ.get("CLAMSCAN_COMMAND", "clamscan")
if not DEBUG and not DEMO_MODE and not ANTIVIRUS_ENABLED:
    raise ImproperlyConfigured("ANTIVIRUS_ENABLED must be true before accepting production uploads.")

REDIS_URL = os.environ.get("REDIS_URL", "").strip()
REDIS_HOST = os.environ.get("REDIS_HOST", "").strip()
REDIS_PORT = os.environ.get("REDIS_PORT", "").strip()
if not DEBUG and not DEMO_MODE and not REDIS_URL:
    if not REDIS_HOST or not REDIS_PORT:
        raise ImproperlyConfigured(
            "REDIS_URL or both REDIS_HOST and REDIS_PORT are required for production rate limiting."
        )
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
elif REDIS_HOST and REDIS_PORT:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "mofirms-development-rate-limit",
        }
    }

if not DEBUG and not DEMO_MODE and (
    PRIVATE_UPLOAD_ROOT == BASE_DIR
    or BASE_DIR in PRIVATE_UPLOAD_ROOT.parents
):
    raise ImproperlyConfigured(
        "PRIVATE_UPLOAD_ROOT must be an encrypted directory outside the application code."
    )
