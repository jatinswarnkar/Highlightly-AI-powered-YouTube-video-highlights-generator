from django.apps import AppConfig


class HighlightsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'highlights'
    
    def ready(self):
        # Force model load at startup
        from .ml_models import EMOTION_MODEL
