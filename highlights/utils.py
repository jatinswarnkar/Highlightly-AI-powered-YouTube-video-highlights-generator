# import os
# from pytube import YouTube
# import ffmpeg
# import cv2
# import numpy as np
# import subprocess
# import numpy as np
# from urllib.parse import urlparse, parse_qs
# import os
# import yt_dlp
# import azure.cognitiveservices.speech as speechsdk
# from django.conf import settings
# import json



# def transcribe_with_azure(audio_path):
#     speech_config = speechsdk.SpeechConfig(
#         subscription=settings.AZURE_SPEECH_KEY,
#         region=settings.AZURE_SPEECH_REGION
#     )

#     speech_config.request_word_level_timestamps()
#     speech_config.output_format = speechsdk.OutputFormat.Detailed

#     audio_input = speechsdk.AudioConfig(filename=audio_path)
#     recognizer = speechsdk.SpeechRecognizer(
#         speech_config=speech_config,
#         audio_config=audio_input
#     )

#     result = recognizer.recognize_once()

#     if result.reason == speechsdk.ResultReason.RecognizedSpeech:
#         return json.loads(result.json)

#     return None


# def download_youtube(url: str) -> str:
#     output_dir = "downloads"
#     os.makedirs(output_dir, exist_ok=True)

#     ydl_opts = {
#         "format": "mp4",
#         "outtmpl": os.path.join(output_dir, "%(title)s.%(ext)s"),
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         return ydl.prepare_filename(info)

# # Extract audio from video
# def extract_audio(video_path, output_audio="media/audio.wav"):
#     os.makedirs(os.path.dirname(output_audio), exist_ok=True)
#     ffmpeg.input(video_path).output(output_audio, ac=1, ar=16000).run(overwrite_output=True)
#     return output_audio

# # Simple scene detection using frame differences
# def detect_scenes(video_path, threshold=30.0):
#     scenes = []
#     cap = cv2.VideoCapture(video_path)
#     fps = cap.get(cv2.CAP_PROP_FPS)
#     prev_frame = None
#     start = 0
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
#         gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#         if prev_frame is not None:
#             diff = cv2.absdiff(gray, prev_frame)
#             score = np.mean(diff)
#             if score > threshold:
#                 time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
#                 scenes.append(time)
#         prev_frame = gray
#     cap.release()
#     return scenes

# # # Detect loud audio peaks
# # def detect_audio_peaks(audio_path, top_k=5):
# #     y, sr = librosa.load(audio_path)
# #     energy = librosa.feature.rms(y=y)[0]
# #     frames = np.argsort(energy)[-top_k:]
# #     times = librosa.frames_to_time(frames, sr=sr)
# #     return list(times)

# def detect_audio_peaks(audio_path, top_k=5):
#     """
#     Detect top K loudest audio peaks using FFmpeg (no librosa needed).
#     Returns timestamps (in seconds) of the detected peaks.
#     """

#     # FFmpeg command to extract per-frame RMS loudness
#     cmd = [
#         "ffmpeg",
#         "-i", audio_path,
#         "-af", "astats=metadata=1:reset=1",
#         "-f", "null",
#         "-"
#     ]

#     process = subprocess.Popen(
#         cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, universal_newlines=True
#     )

#     rms_values = []
#     timestamps = []

#     # Parse RMS and timestamp from FFmpeg astats logs
#     for line in process.stderr:
#         if "RMS level" in line:
#             try:
#                 rms = float(line.split("RMS level:")[1].strip())
#                 rms_values.append(rms)
#             except:
#                 pass

#         if "Parsed_astats" in line and "pts_time" in line:
#             try:
#                 ts = float(line.split("pts_time:")[1].split()[0])
#                 timestamps.append(ts)
#             except:
#                 pass

#     process.wait()

#     if not rms_values or not timestamps:
#         return []

#     rms_values = np.array(rms_values)
#     timestamps = np.array(timestamps)

#     # Get indices of top K loudest frames
#     peak_indices = np.argsort(rms_values)[-top_k:]
#     peak_times = timestamps[peak_indices]

#     return sorted(peak_times.tolist())



# # Cleanup temporary files
# def cleanup_video(video_path):
#     if os.path.exists(video_path):
#         os.remove(video_path)
#         print(f"Deleted original video: {video_path}")


# import os
# import json
# import subprocess
# import ffmpeg
# import cv2
# import numpy as np
# import yt_dlp
# import azure.cognitiveservices.speech as speechsdk
# from django.conf import settings


# # ==========================
# # Azure Speech-to-Text
# # ==========================
# # def transcribe_with_azure(audio_path):
# #     speech_config = speechsdk.SpeechConfig(
# #         subscription=settings.AZURE_SPEECH_KEY,
# #         region=settings.AZURE_SPEECH_REGION
# #     )

# #     speech_config.speech_recognition_language = "en-US"
# #     speech_config.request_word_level_timestamps()
# #     speech_config.output_format = speechsdk.OutputFormat.Detailed

# #     audio_input = speechsdk.AudioConfig(filename=audio_path)
# #     recognizer = speechsdk.SpeechRecognizer(
# #         speech_config=speech_config,
# #         audio_config=audio_input
# #     )

# #     result = recognizer.recognize_once()

# #     if result.reason == speechsdk.ResultReason.RecognizedSpeech:
# #         return json.loads(result.json)

# #     return None

# import time
# import json
# import azure.cognitiveservices.speech as speechsdk
# from django.conf import settings


# def transcribe_with_azure(audio_path):
#     speech_config = speechsdk.SpeechConfig(
#         subscription=settings.AZURE_SPEECH_KEY,
#         region=settings.AZURE_SPEECH_REGION
#     )

#     speech_config.speech_recognition_language = "en-US"
#     speech_config.request_word_level_timestamps()
#     speech_config.output_format = speechsdk.OutputFormat.Detailed

#     audio_input = speechsdk.AudioConfig(filename=audio_path)
#     recognizer = speechsdk.SpeechRecognizer(
#         speech_config=speech_config,
#         audio_config=audio_input
#     )

#     collected_words = []
#     done = False

#     def recognized_handler(evt):
#         if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
#             try:
#                 data = json.loads(evt.result.json)
#                 nbest = data.get("NBest", [])
#                 if nbest and "Words" in nbest[0]:
#                     collected_words.extend(nbest[0]["Words"])
#             except Exception:
#                 pass

#     def stop_handler(evt):
#         nonlocal done
#         done = True

#     recognizer.recognized.connect(recognized_handler)
#     recognizer.session_stopped.connect(stop_handler)
#     recognizer.canceled.connect(stop_handler)

#     recognizer.start_continuous_recognition()

#     # ✅ BLOCK UNTIL FINISHED (SAFE)
#     while not done:
#         time.sleep(0.2)

#     recognizer.stop_continuous_recognition()

#     if not collected_words:
#         return None

#     # Normalize output to match your pipeline
#     return {
#         "NBest": [
#             {
#                 "Words": collected_words
#             }
#         ]
#     }



# ==========================
# YouTube Download (Azure Safe)
# ==========================
# def download_youtube(url: str) -> str:
#     output_dir = "downloads"
#     os.makedirs(output_dir, exist_ok=True)

#     ydl_opts = {
#         "format": "bv*+ba/best",
#         "merge_output_format": "mp4",
#         "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
#         "quiet": True,
#         "no_warnings": True,
#         "retries": 3,
#     }

#     with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#         info = ydl.extract_info(url, download=True)
#         return ydl.prepare_filename(info)

import os
import json
import uuid
import time
import subprocess
import cv2
import numpy as np
import yt_dlp
import azure.cognitiveservices.speech as speechsdk
from django.conf import settings


# =====================================================
# AZURE TRANSCRIPTION (BLOCKING + SAFE)
# =====================================================
def transcribe_with_azure(audio_path: str):
    speech_config = speechsdk.SpeechConfig(
        subscription=settings.AZURE_SPEECH_KEY,
        region=settings.AZURE_SPEECH_REGION,
    )

    speech_config.speech_recognition_language = "en-US"
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    audio_input = speechsdk.AudioConfig(filename=audio_path)
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_input,
    )

    # ✅ SAFE: single blocking call
    result = recognizer.recognize_once()

    if result.reason != speechsdk.ResultReason.RecognizedSpeech:
        return None

    try:
        data = json.loads(result.json)
        nbest = data.get("NBest", [])
        if not nbest:
            return None

        return {
            "NBest": [
                {
                    "Words": nbest[0].get("Words", [])
                }
            ]
        }
    except Exception:
        return None


# =====================================================
# YOUTUBE DOWNLOAD (BOT-SAFE)
# =====================================================
def download_youtube(url: str) -> str:
    output_dir = "/tmp/downloads"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["android"]
            }
        },
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)


# =====================================================
# AUDIO EXTRACTION (NO ffmpeg-python)
# =====================================================
def extract_audio(video_path: str) -> str:
    audio_path = f"/tmp/{uuid.uuid4().hex}.wav"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-ac", "1",
        "-ar", "16000",
        audio_path,
    ]

    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )

    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        raise RuntimeError("Audio extraction failed")

    return audio_path


# =====================================================
# SCENE DETECTION
# =====================================================
def detect_scenes(video_path, threshold=30.0):
    scenes = []
    cap = cv2.VideoCapture(video_path)
    prev_frame = None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if prev_frame is not None:
            diff = cv2.absdiff(gray, prev_frame)
            score = np.mean(diff)
            if score > threshold:
                scenes.append(cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0)

        prev_frame = gray

    cap.release()
    return scenes


# =====================================================
# AUDIO PEAKS (RAW FFmpeg)
# =====================================================
def detect_audio_peaks(audio_path, top_k=5):
    cmd = [
        "ffmpeg",
        "-i", audio_path,
        "-af", "astats=metadata=1:reset=1",
        "-f", "null",
        "-"
    ]

    proc = subprocess.Popen(
        cmd,
        stderr=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        text=True
    )

    peaks = []

    for line in proc.stderr:
        if "RMS level" in line and "pts_time" in line:
            try:
                rms = float(line.split("RMS level:")[1].split()[0])
                ts = float(line.split("pts_time:")[1].split()[0])
                peaks.append((rms, ts))
            except:
                pass

    proc.wait()

    if not peaks:
        return []

    peaks.sort(key=lambda x: x[0])
    return [int(t) for _, t in peaks[-top_k:]]


# =====================================================
# CLEANUP
# =====================================================
def cleanup_video(video_path):
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
    except:
        pass



def escape_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
            .replace(":", "\\:")
            .replace("'", "\\'")
            .replace("%", "\\%")
            .replace(",", "\\,")
    )


def extract_words_for_clip(transcript_json, clip_start, clip_end):
    """
    Returns word-level captions normalized to clip time.
    """
    if not transcript_json:
        return []

    nbest = transcript_json.get("NBest", [])
    if not nbest:
        return []

    words = nbest[0].get("Words", [])
    result = []

    for w in words:
        start = w["Offset"] / 10_000_000
        end = (w["Offset"] + w["Duration"]) / 10_000_000

        if end < clip_start or start > clip_end:
            continue

        result.append({
            "text": w["Word"],
            "start": max(0, start - clip_start),
            "end": min(clip_end - clip_start, end - clip_start),
        })

    return result

def clamp_time(t, max_t):
    return max(0, min(round(t, 2), round(max_t, 2)))

from google import genai

def generate_viral_hook(transcript_text):
    if not transcript_text or not transcript_text.strip():
        return "No speech detected.", ""
        
    import os
    from django.conf import settings
    
    api_key = getattr(settings, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Please set GEMINI_API_KEY in .env", ""
    
    try:
        client = genai.Client(api_key=api_key)
        # Using gemini-2.5-flash for the latest API support
        model_id = "gemini-2.5-flash"
        prompt = (
            f"Act as a TikTok and Instagram Reels growth expert. "
            f"Write a 2-sentence engaging viral hook/caption and provide 3 relevant viral hashtags "
            f"for this short video transcript:\n\n{transcript_text}\n\n"
            f"Format your response exactly like this:\n"
            f"Caption: [your 2-sentence captivating hook here]\n"
            f"Hashtags: [your 3 hashtags here]"
        )
        
        response = client.models.generate_content(
            model=model_id,
            contents=prompt
        )
        text = response.text
        
        caption = ""
        hashtags = ""
        for line in text.split('\n'):
            if line.strip().lower().startswith('caption:'):
                caption = line.split(':', 1)[1].strip()
            elif line.strip().lower().startswith('hashtags:'):
                hashtags = line.split(':', 1)[1].strip()
        
        if not caption and not hashtags:
            caption = text.strip()
            
        return caption, hashtags
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "Failed to generate AI caption.", ""
