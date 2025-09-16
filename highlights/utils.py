import os
from pytube import YouTube
import ffmpeg
import cv2
import numpy as np
import librosa
from urllib.parse import urlparse, parse_qs

import os
import yt_dlp

def download_youtube(url: str) -> str:
    output_dir = "downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "mp4",
        "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# Extract audio from video
def extract_audio(video_path, output_audio="media/audio.wav"):
    os.makedirs(os.path.dirname(output_audio), exist_ok=True)
    ffmpeg.input(video_path).output(output_audio, ac=1, ar=16000).run(overwrite_output=True)
    return output_audio

# Simple scene detection using frame differences
def detect_scenes(video_path, threshold=30.0):
    scenes = []
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    prev_frame = None
    start = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            score = np.mean(diff)
            if score > threshold:
                time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                scenes.append(time)
        prev_frame = gray
    cap.release()
    return scenes

# Detect loud audio peaks
def detect_audio_peaks(audio_path, top_k=5):
    y, sr = librosa.load(audio_path)
    energy = librosa.feature.rms(y=y)[0]
    frames = np.argsort(energy)[-top_k:]
    times = librosa.frames_to_time(frames, sr=sr)
    return list(times)
