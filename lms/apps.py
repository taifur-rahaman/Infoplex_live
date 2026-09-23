from django.apps import AppConfig


class LmsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lms"
    # Keep in sync with settings.SITE_NAME (AppConfig loads before env is always safe)
    verbose_name = "InfoPlex LMS"
