from transformers import pipeline
import os

# Prevent HF from trying telemetry / online checks
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

print("🔁 Loading emotion model (one-time)...")

EMOTION_MODEL = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion",
)

print("✅ Emotion model loaded successfully")
