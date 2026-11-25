SECRET_KEY = "layout"
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "rest_framework", "api"]
ROOT_URLCONF = "proj.urls"
DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
