from django.apps import AppConfig


class HighlightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'highlights'

    def ready(self):
        # Model loads lazily on first request via _LazyModel proxy
        pass
