# highlights/views.py
import os
import uuid
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from .utils import download_youtube, extract_audio, detect_scenes, detect_audio_peaks
from .highlight_generator import make_highlights

progress = {"status": "idle", "percent": 0}

def home(request):
    return render(request, "highlights/home.html")

def start_highlights(request):
    global progress
    url = request.GET.get("url")
    if not url:
        return JsonResponse({"error": "Please provide ?url="})
    
    # Unique filename
    uid = str(uuid.uuid4())[:8]
    output_filename = f"highlight_{uid}.mp4"
    output_path = os.path.join(settings.MEDIA_ROOT, output_filename)

    progress = {"status": "downloading", "percent": 10}
    video_path = download_youtube(url)

    progress = {"status": "extracting audio", "percent": 30}
    audio_path = extract_audio(video_path)

    progress = {"status": "detecting scenes & peaks", "percent": 60}
    scenes = detect_scenes(video_path)[:5]
    peaks = detect_audio_peaks(audio_path, top_k=5)
    highlight_times = sorted(set(int(t) for t in scenes + peaks))

    progress = {"status": "generating highlights", "percent": 90}
    final_path = make_highlights(video_path, highlight_times, clip_len=10, output_path=output_path)

    progress = {"status": "done", "percent": 100, "file": output_filename}
    return JsonResponse({"download_url": f"{final_path}"})

def check_progress(request):
    return JsonResponse(progress)
