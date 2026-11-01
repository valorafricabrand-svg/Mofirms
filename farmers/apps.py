from django.apps import AppConfig


class FarmersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "farmers"

    def ready(self):
        from . import signals
