import subprocess
import os

def make_highlights_multiple(video_path, highlight_times, clip_len=10, output_dir="media"):
    os.makedirs(output_dir, exist_ok=True)
    highlights = []

    for i, t in enumerate(highlight_times):
        start = max(0, t - clip_len // 2)
        duration = clip_len
        video_file = os.path.join(output_dir, f"highlight_{i}.mp4")
        thumb_file = os.path.join(output_dir, f"thumb_{i}.jpg")

        # Generate highlight clip
        cmd_video = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",
            video_file
        ]
        subprocess.run(cmd_video, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Generate thumbnail (first frame)
        cmd_thumb = [
            "ffmpeg", "-y",
            "-i", video_file,
            "-vf", r"select=eq(n\,0)",
            "-q:v", "2",
            thumb_file
        ]
        subprocess.run(cmd_thumb, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        highlights.append({"video": video_file, "thumbnail": thumb_file})

    return highlights
