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
    transcribe_with_azure,   # <-- NEW
    cleanup_video
)
from .highlight_generator import make_highlights_multiple

# Emotion classifier stays exactly the same
from transformers import pipeline
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

    # 3A: Detect scenes
    scenes = detect_scenes(video_path)[:20]
    scene_scores = {int(t): 1 for t in scenes}

    # 3B: Detect audio peaks (FFmpeg based)
    peaks = detect_audio_peaks(audio_path, top_k=20)
    peak_scores = {int(t): 2 for t in peaks}

    # 3C: Azure Speech-to-Text transcription (REPLACES WHISPER)
    transcript_json = transcribe_with_azure(audio_path)

    ai_scores = {}

    if transcript_json:
        # Azure returns a JSON with word-level timing + full text
        detailed = transcript_json.get("NBest", [])[0] if "NBest" in transcript_json else None

        if detailed and "Words" in detailed:
            # Words includes start/end timestamps + text
            for word_data in detailed["Words"]:
                start_time = int(word_data["Offset"] / 10_000_000)   # convert 100ns → seconds
                text = word_data["Word"]

                # Emotion classification on each word OR buffer words (choose one)
                emotion = emotion_classifier(text)[0]
                label = emotion["label"].lower()

                if label in ["joy", "surprise", "excitement"]:
                    ai_scores[start_time] = 3

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

    # Step 5: Generate highlight videos + thumbnails uploaded to Azure
    progress = {"status": "generating highlights", "percent": 90}

    highlights = make_highlights_multiple(
        video_path,
        highlight_times,
        clip_len=10,
        output_dir=output_dir
    )

    # Prepare output list
    result = []
    for h in highlights:
        result.append({
            "video": h["video"],        # Azure URL
            "thumbnail": h["thumbnail"] # Azure URL
        })

    # Cleanup
    cleanup_video(video_path)

    progress = {"status": "done", "percent": 100}
    return JsonResponse({"highlights": result})


def check_progress(request):
    return JsonResponse(progress)
