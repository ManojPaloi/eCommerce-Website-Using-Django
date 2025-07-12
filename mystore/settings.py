import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent

# Security
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-default-key")
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "t")
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    'ecommerce-website-using-django-wu5o.onrender.com'
]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Custom apps
    "category",
    "store",
    "carts",
    "accounts",
    "orders",

    # Third-party
    "widget_tweaks",
    "crispy_forms",
    "crispy_bootstrap5",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
    "allauth.socialaccount.providers.twitter",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "mystore.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.template.context_processors.csrf",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "category.context_processors.menu_links",
                "mystore.context_processors.cart_quantity",
                "store.context_processors.cart_item_count",
                "store.context_processors.wishlist_count",
            ],
        },
    },
]

WSGI_APPLICATION = "mystore.wsgi.application"

AUTH_USER_MODEL = "accounts.Account"

# Allauth updated settings for Django 5.2+
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_SIGNUP_REDIRECT_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/accounts/login/'
SITE_ID = 1
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# # Social providers
# SOCIALACCOUNT_PROVIDERS = {
#     'google': {
#         'APP': {
#             'client_id': os.getenv('GOOGLE_CLIENT_ID', ''),
#             'secret': os.getenv('GOOGLE_CLIENT_SECRET', ''),
#             'key': os.getenv('GOOGLE_API_KEY', ''),
#         },
#         'SCOPE': ['profile', 'email'],
#         'AUTH_PARAMS': {'access_type': 'online'},
#     },
#     'facebook': {
#         'APP': {
#             'client_id': os.getenv('FACEBOOK_APP_ID', ''),
#             'secret': os.getenv('FACEBOOK_APP_SECRET', ''),
#             'key': ''
#         },
#         'METHOD': 'oauth2',
#         'SCOPE': ['email', 'public_profile'],
#         'VERSION': 'v12.0',
#     },
#     'twitter': {
#         'APP': {
#             'client_id': os.getenv('TWITTER_API_KEY', ''),
#             'secret': os.getenv('TWITTER_API_SECRET', ''),
#             'key': ''
#         },
#     }
# }

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Localization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# Static and Media files
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"


# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "paloimanoj@gmail.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "wpseoomhfebzwusn")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Session and CSRF settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_SECURE = False  # Set to True in production
CSRF_COOKIE_HTTPONLY = False

# Razorpay credentials
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_NqgKbEIscBSeuB")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "IDKoHuiNOxIi72uukBJdlwj5")

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",  # Changed to DEBUG to capture more logs
            "class": "logging.FileHandler",
            "filename": BASE_DIR / "debug.log",
        },
        "console": {  # Added console handler for debugging
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file", "console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}