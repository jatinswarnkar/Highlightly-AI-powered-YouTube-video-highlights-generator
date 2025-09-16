import subprocess
import os

def make_highlights(video_path, highlight_times, clip_len=10, output_path="media/highlight.mp4"):
    os.makedirs("media", exist_ok=True)
    parts = []

    # Generate highlight clips
    for i, t in enumerate(highlight_times):
        start = max(0, t - clip_len // 2)
        duration = clip_len
        part_file = f"media/part_{i}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-ss", str(start),
            "-t", str(duration),
            "-c", "copy",  # no re-encode → super fast
            part_file
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        parts.append(part_file)

    # Create concat list file
    list_file = "media/parts.txt"
    with open(list_file, "w") as f:
        for part in parts:
            f.write(f"file '{os.path.abspath(part)}'\n")

    # Concat all parts into final highlight video
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_file,
        "-c", "copy",
        output_path
    ]
    subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Cleanup
    for part in parts:
        os.remove(part)
    os.remove(list_file)

    return output_path

