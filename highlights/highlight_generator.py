import subprocess
import os
from django.conf import settings
from .azure_upload import upload_to_azure

def make_highlights_multiple(video_path, highlight_times, clip_len=10, output_dir="media"):
    # Ensure folder exists locally (temporary only)
    os.makedirs(output_dir, exist_ok=True)

    highlights = []
    folder_name = os.path.basename(output_dir.rstrip("/"))

    for i, t in enumerate(highlight_times):
        start = max(0, t - clip_len // 2)
        duration = clip_len

        # Local temporary files
        local_video = os.path.join(output_dir, f"highlight_{i}.mp4")
        local_thumb = os.path.join(output_dir, f"thumb_{i}.jpg")

        # Azure blob names (inside container folder)
        blob_video = f"{folder_name}/highlight_{i}.mp4"
        blob_thumb = f"{folder_name}/thumb_{i}.jpg"

        # Generate highlight clip (no re-encode)
        subprocess.run([
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            local_video
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Generate thumbnail
        subprocess.run([
            "ffmpeg", "-y",
            "-i", local_video,
            "-vf", r"select=eq(n\,0)",
            "-q:v", "2",
            local_thumb
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Upload both files to Azure
        video_url = upload_to_azure(local_video, blob_video)
        thumb_url = upload_to_azure(local_thumb, blob_thumb)

        # Append result
        highlights.append({
            "video": video_url,
            "thumbnail": thumb_url
        })

    return highlights
