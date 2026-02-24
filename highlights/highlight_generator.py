import subprocess
import os
from .azure_upload import upload_to_azure


# def make_highlights_multiple(
#     video_path,
#     highlight_times,
#     clip_len=10,
#     output_dir="media",
#     center=True
# ):
#     """
#     Generates highlight clips optimized for Reels/Shorts.
#     - Prevents near-duplicate clips
#     - Centers action in clip
#     - Uploads to Azure
#     """

#     os.makedirs(output_dir, exist_ok=True)

#     highlights = []
#     folder_name = os.path.basename(output_dir.rstrip("/"))

#     for i, t in enumerate(highlight_times):
#         # 🔥 Skip if too close to previous highlight

#         # Center clip around event
#         start = max(0, t - clip_len // 2) if center else t
#         duration = clip_len

#         local_video = os.path.join(output_dir, f"highlight_{i}.mp4")
#         local_thumb = os.path.join(output_dir, f"thumb_{i}.jpg")

#         blob_video = f"{folder_name}/highlight_{i}.mp4"
#         blob_thumb = f"{folder_name}/thumb_{i}.jpg"

#         # ✅ Accurate & fast clip cut (recommended FFmpeg order)
#         subprocess.run([
#             "ffmpeg", "-y",
#             "-ss", str(start),
#             "-i", video_path,
#             "-t", str(duration),
#             "-c", "copy",
#             local_video
#         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#         # Thumbnail (first frame)
#         subprocess.run([
#             "ffmpeg", "-y",
#             "-i", local_video,
#             "-vf", "select=eq(n\\,0)",
#             "-q:v", "2",
#             local_thumb
#         ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#         video_url = upload_to_azure(local_video, blob_video)
#         thumb_url = upload_to_azure(local_thumb, blob_thumb)

#         highlights.append({
#             "video": video_url,
#             "thumbnail": thumb_url
#         })

#         # Optional cap for Shorts
#         if len(highlights) >= 10:
#             break

#     return highlights

import os
import subprocess
from .azure_upload import upload_to_azure
from highlights.utils import escape_text, extract_words_for_clip


FONT_PATH = "assets/fonts/Inter-Bold.ttf"


def clamp(t, max_t):
    return round(max(0, min(t, max_t)), 2)

def build_dynamic_crop_expression(bias="center"):
    if bias == "left":
        base = "0.15"
    elif bias == "right":
        base = "0.75"
    else:
        base = "0.5"

    return (
        "crop=ih*9/16:ih:"
        f"x='(iw-ih*9/16)*{base} + (iw-ih*9/16)*0.12*sin(0.8*t)':"
        "y=0:"
        "eval=frame,"
        "setsar=1"
    )

def make_highlights_multiple(
    video_path,
    highlight_times,
    transcript_json,
    clip_len=7,
    output_dir="media",
    center=True,
    min_gap=6,
    auto_zoom=None,
    speaker_bias_map=None,
):
    os.makedirs(output_dir, exist_ok=True)
    folder_name = os.path.basename(output_dir.rstrip("/"))

    highlights = []
    last_used_time = -999

    for i, t in enumerate(sorted(highlight_times)):

        if abs(t - last_used_time) < min_gap:
            continue
        last_used_time = t

        clip_start = max(0, t - clip_len // 2) if center else t
        clip_end = clip_start + clip_len

        local_video = os.path.join(output_dir, f"highlight_{i}.mp4")
        local_thumb = os.path.join(output_dir, f"thumb_{i}.jpg")

        blob_video = f"{folder_name}/highlight_{i}.mp4"
        blob_thumb = f"{folder_name}/thumb_{i}.jpg"

        words = extract_words_for_clip(
            transcript_json,
            clip_start,
            clip_end
        )

        drawtext_filters = []

        for w in words:
            text = escape_text(w["text"])

            start = clamp(w["start"], clip_len)
            end = clamp(w["end"], clip_len)

            if end <= start:
                continue

            # 🔥 ESCAPE COMMAS FOR FFMPEG EXPRESSIONS
            enable_expr = f"between(t\\,{start}\\,{end})"

            drawtext_filters.append(
                f"drawtext=fontfile={FONT_PATH}:"
                f"text='{text}':"
                f"fontsize=46:"
                f"fontcolor=white:"
                f"borderw=4:"
                f"x=(w-text_w)/2:"
                f"y=h*0.78:"
                f"enable='{enable_expr}'"
            )

        # 🔥 SMART 9:16 CROP
        vf_filters = []

        # bias = "center"
        # if speaker_bias_map:
        #     bias = speaker_bias_map.get(t, "center")

        # vf_filters.append(build_dynamic_crop_expression(bias))

        # 🎯 Face-tracked illusion
        vf_filters.append("setsar=1")

        # 🔍 Ken Burns auto-zoom
        if auto_zoom:
            vf_filters.append(
                "scale=iw*(1+0.12*min(t\\,7)/7):ih*(1+0.12*min(t\\,7)/7)"
            )

        # 📝 Captions
        vf_filters.extend(drawtext_filters)

        vf = ",".join(vf_filters) if vf_filters else None


        cmd = [
            "ffmpeg", "-y",
            "-ss", str(clip_start),
            "-i", video_path,
            "-t", str(clip_len),
        ]

        if vf:
            print("FFMPEG FILTER:")
            print(vf)
            cmd += ["-vf", vf]
        else:
            print("FFMPEG FILTER: (no captions)")

        cmd += [
            "-preset", "veryfast",
            "-movflags", "+faststart",
            local_video
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print("❌ FFMPEG FAILED")
            print(result.stderr)
            continue

        if not os.path.exists(local_video):
            print("❌ Output video missing, skipping")
            continue

        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", local_video,
                "-frames:v", "1",
                "-q:v", "2",
                local_thumb
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        video_url = upload_to_azure(local_video, blob_video)
        thumb_url = upload_to_azure(local_thumb, blob_thumb)

        highlights.append({
            "video": video_url,
            "thumbnail": thumb_url
        })

        if len(highlights) >= 6:
            break

    return highlights
