SECRET_KEY = "fixture"
DEBUG = False
ALLOWED_HOSTS = ["*"]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "shop",
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request",
                                                  "django.contrib.auth.context_processors.auth",
                                                  "django.contrib.messages.context_processors.messages"]}}]
ROOT_URLCONF = "config.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
USE_TZ = True
USE_I18N = True
LANGUAGE_CODE = "en"
LANGUAGES = [("en", "English"), ("it", "Italiano")]
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
