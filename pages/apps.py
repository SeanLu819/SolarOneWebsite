from django.apps import AppConfig


class PagesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pages'

    def ready(self):
        # Register production system checks (e.g. contact-form persistence guard).
        from . import checks  # noqa: F401
