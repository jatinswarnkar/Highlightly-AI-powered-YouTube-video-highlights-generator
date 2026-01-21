import subprocess
import os
from .azure_upload import upload_to_azure


def make_highlights_multiple(
    video_path,
    highlight_times,
    clip_len=10,
    output_dir="media",
    center=True,
    min_gap=6   # 🔥 NEW: minimum seconds between clips
):
    """
    Generates highlight clips optimized for Reels/Shorts.
    - Prevents near-duplicate clips
    - Centers action in clip
    - Uploads to Azure
    """

    os.makedirs(output_dir, exist_ok=True)

    highlights = []
    folder_name = os.path.basename(output_dir.rstrip("/"))

    last_used_time = -999  # for deduplication

    for i, t in enumerate(sorted(highlight_times)):

        # 🔥 Skip timestamps too close to previous clip
        if abs(t - last_used_time) < min_gap:
            continue

        last_used_time = t

        # Center clip around event
        start = max(0, t - clip_len // 2) if center else t
        duration = clip_len

        local_video = os.path.join(output_dir, f"highlight_{i}.mp4")
        local_thumb = os.path.join(output_dir, f"thumb_{i}.jpg")

        blob_video = f"{folder_name}/highlight_{i}.mp4"
        blob_thumb = f"{folder_name}/thumb_{i}.jpg"

        # ✅ Accurate & fast clip cut (recommended FFmpeg order)
        subprocess.run([
            "ffmpeg", "-y",
            "-ss", str(start),
            "-i", video_path,
            "-t", str(duration),
            "-c", "copy",
            local_video
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Thumbnail (first frame)
        subprocess.run([
            "ffmpeg", "-y",
            "-i", local_video,
            "-vf", "select=eq(n\\,0)",
            "-q:v", "2",
            local_thumb
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        video_url = upload_to_azure(local_video, blob_video)
        thumb_url = upload_to_azure(local_thumb, blob_thumb)

        highlights.append({
            "video": video_url,
            "thumbnail": thumb_url
        })

        # Optional cap for Shorts
        if len(highlights) >= 10:
            break

    return highlights
