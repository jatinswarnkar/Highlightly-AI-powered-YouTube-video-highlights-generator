from transformers import pipeline
import os

# Prevent HF from trying telemetry / online checks
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

_EMOTION_MODEL = None


def get_emotion_model():
    """Lazy-load the emotion model on first use instead of at import time."""
    global _EMOTION_MODEL
    if _EMOTION_MODEL is None:
        print("🔁 Loading emotion model (one-time)...")
        _EMOTION_MODEL = pipeline(
            "text-classification",
            model="bhadresh-savani/distilbert-base-uncased-emotion",
        )
        print("✅ Emotion model loaded successfully")
    return _EMOTION_MODEL


# Keep backward-compatible attribute for existing imports
# This is a lazy proxy — the model won't load until actually called
class _LazyModel:
    def __call__(self, *args, **kwargs):
        return get_emotion_model()(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(get_emotion_model(), name)


EMOTION_MODEL = _LazyModel()
