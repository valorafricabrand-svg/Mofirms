from django.apps import AppConfig


class FarmersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "farmers"

    def ready(self):
        from . import notifications, signals  # noqa: F401 (registers signal handlers)
