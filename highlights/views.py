# # highlights/views.py
# import os
# import uuid
# from django.conf import settings
# from django.shortcuts import render
# from django.http import JsonResponse
# from .utils import download_youtube, extract_audio, detect_scenes, detect_audio_peaks,cleanup_video
# from .highlight_generator import make_highlights_multiple

# # AI imports
# import whisper
# from transformers import pipeline

# # Load AI models once at startup
# whisper_model = whisper.load_model("base")
# emotion_classifier = pipeline("text-classification", model="bhadresh-savani/distilbert-base-uncased-emotion")

# # Global progress dictionary
# progress = {"status": "idle", "percent": 0}


# def home(request):
#     return render(request, "highlights/home.html")


# def start_highlights(request):
#     global progress
#     url = request.GET.get("url")
#     if not url:
#         return JsonResponse({"error": "Please provide ?url="})

#     # Create unique folder for this request
#     uid = str(uuid.uuid4())[:8]
#     output_dir = os.path.join(settings.MEDIA_ROOT, f"highlights_{uid}")
#     os.makedirs(output_dir, exist_ok=True)

#     # Step 1: Download video
#     progress = {"status": "downloading", "percent": 10}
#     video_path = download_youtube(url)

#     # Step 2: Extract audio
#     progress = {"status": "extracting audio", "percent": 30}
#     audio_path = extract_audio(video_path)

#     # Step 3: Detect scenes, audio peaks, and AI highlights
#     progress = {"status": "detecting highlights", "percent": 50}

#     # Scene changes (weight = 1)
#     scenes = detect_scenes(video_path)[:20]  # get more for scoring
#     scene_scores = {int(t): 1 for t in scenes}

#     # Audio peaks (weight = 2)
#     peaks = detect_audio_peaks(audio_path, top_k=20)
#     peak_scores = {int(t): 2 for t in peaks}

#     # AI highlights (weight = 3)
#     transcription = whisper_model.transcribe(audio_path, word_timestamps=False)
#     ai_scores = {}
#     for seg in transcription.get("segments", []):
#         text = seg["text"]
#         emotion = emotion_classifier(text)[0]
#         if emotion["label"].lower() in ["joy", "surprise", "excitement"]:
#             ai_scores[int(seg["start"])] = 3

#     # Combine all scores
#     combined = {}
#     for t, score in scene_scores.items():
#         combined[t] = combined.get(t, 0) + score
#     for t, score in peak_scores.items():
#         combined[t] = combined.get(t, 0) + score
#     for t, score in ai_scores.items():
#         combined[t] = combined.get(t, 0) + score

#     # Take top 5–10 by score
#     highlight_times = sorted(combined, key=lambda x: combined[x], reverse=True)[:10]
#     highlight_times = sorted(highlight_times)  # sort by time for video generation


#     # Step 5: Generate multiple highlight videos + thumbnails
#     progress = {"status": "generating highlights", "percent": 90}
#     highlights = make_highlights_multiple(video_path, highlight_times, clip_len=10, output_dir=output_dir)

#     # Step 6: Return list of highlights with thumbnails
#     result = []
#     for h in highlights:
#         video_rel = os.path.relpath(h["video"], settings.MEDIA_ROOT)
#         thumb_rel = os.path.relpath(h["thumbnail"], settings.MEDIA_ROOT)

#         video_file = f"{settings.MEDIA_URL}{video_rel}"
#         thumb_file = f"{settings.MEDIA_URL}{thumb_rel}"

#         result.append({"video": video_file, "thumbnail": thumb_file})

    
#     # Cleanup original video
#     cleanup_video(video_path)

#     progress = {"status": "done", "percent": 100}
#     return JsonResponse({"highlights": result})


# def check_progress(request):
#     return JsonResponse(progress)



# highlights/views.py
import os
import uuid
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .utils import (
    download_youtube,
    extract_audio,
    detect_scenes,
    detect_audio_peaks,
    cleanup_video
)
from .highlight_generator import make_highlights_multiple

# AI imports
import whisper
from transformers import pipeline

# Load AI models once at startup
whisper_model = whisper.load_model("base")
emotion_classifier = pipeline(
    "text-classification",
    model="bhadresh-savani/distilbert-base-uncased-emotion"
)

# Global progress dictionary
progress = {"status": "idle", "percent": 0}


def home(request):
    return render(request, "highlights/home.html")


def start_highlights(request):
    global progress
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "Please provide ?url="})

    # Unique folder for this job (for Azure prefix)
    uid = str(uuid.uuid4())[:8]
    output_dir = os.path.join(settings.MEDIA_ROOT, f"highlights_{uid}")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Download video
    progress = {"status": "downloading", "percent": 10}
    video_path = download_youtube(url)

    # Step 2: Extract audio
    progress = {"status": "extracting audio", "percent": 30}
    audio_path = extract_audio(video_path)

    # Step 3: AI-based highlight scoring
    progress = {"status": "detecting highlights", "percent": 50}

    # Scene changes (1 point)
    scenes = detect_scenes(video_path)[:20]
    scene_scores = {int(t): 1 for t in scenes}

    # Audio peaks (2 points)
    peaks = detect_audio_peaks(audio_path, top_k=20)
    peak_scores = {int(t): 2 for t in peaks}

    # Emotion-based AI highlights (3 points)
    transcription = whisper_model.transcribe(audio_path, word_timestamps=False)
    ai_scores = {}
    for seg in transcription.get("segments", []):
        emotion = emotion_classifier(seg["text"])[0]
        if emotion["label"].lower() in ["joy", "surprise", "excitement"]:
            ai_scores[int(seg["start"])] = 3

    # Combine scores
    combined = {}
    for t, score in scene_scores.items():
        combined[t] = combined.get(t, 0) + score
    for t, score in peak_scores.items():
        combined[t] = combined.get(t, 0) + score
    for t, score in ai_scores.items():
        combined[t] = combined.get(t, 0) + score

    # Choose top 10 highlight timestamps
    highlight_times = sorted(combined, key=lambda x: combined[x], reverse=True)[:10]
    highlight_times = sorted(highlight_times)

    # Step 5: Generate highlight videos + thumbnails in Azure
    progress = {"status": "generating highlights", "percent": 90}
    highlights = make_highlights_multiple(video_path, highlight_times, clip_len=10, output_dir=output_dir)

    # Step 6: Return Azure URLs directly (NO MEDIA_ROOT logic)
    result = []
    for h in highlights:
        result.append({
            "video": h["video"],        # already Azure URL
            "thumbnail": h["thumbnail"] # already Azure URL
        })

    # Cleanup
    cleanup_video(video_path)

    progress = {"status": "done", "percent": 100}
    return JsonResponse({"highlights": result})


def check_progress(request):
    return JsonResponse(progress)
