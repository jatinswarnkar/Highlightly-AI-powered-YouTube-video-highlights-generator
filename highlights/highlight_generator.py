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
        "y=0,"
        "setsar=1"
    )

def snap_to_speech_pause(transcript_json, raw_start, raw_end, max_extend=3):
    """
    Adjust clip boundaries to align with natural speech pauses.
    Looks for gaps between words near clip edges to avoid cutting mid-sentence.
    Returns (adjusted_start, adjusted_end).
    """
    if not transcript_json:
        return raw_start, raw_end

    nbest = transcript_json.get("NBest", [])
    if not nbest:
        return raw_start, raw_end

    words = nbest[0].get("Words", [])
    if not words:
        return raw_start, raw_end

    # Get word timings in seconds
    word_times = []
    for w in words:
        ws = w["Offset"] / 10_000_000
        we = (w["Offset"] + w["Duration"]) / 10_000_000
        word_times.append((ws, we))

    # Find best start: look for a gap between words near raw_start
    best_start = raw_start
    for j in range(len(word_times) - 1):
        gap_start = word_times[j][1]  # end of word j
        gap_end = word_times[j + 1][0]  # start of word j+1
        gap_size = gap_end - gap_start

        # Only consider gaps that are actual pauses (≥ 0.3s)
        if gap_size >= 0.3 and abs(gap_start - raw_start) <= max_extend:
            best_start = gap_start
            break

    # Find best end: look for a gap near raw_end (search backwards)
    best_end = raw_end
    for j in range(len(word_times) - 2, -1, -1):
        gap_start = word_times[j][1]
        gap_end = word_times[j + 1][0] if j + 1 < len(word_times) else gap_start
        gap_size = gap_end - gap_start

        if gap_size >= 0.3 and abs(gap_start - raw_end) <= max_extend:
            best_end = gap_end
            break

    # Ensure minimum clip duration of 6 seconds
    if best_end - best_start < 6:
        best_start = raw_start
        best_end = raw_end

    return max(0, best_start), best_end


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

        # --- Sentence-aware clip boundaries ---
        # Start with a centered clip
        raw_start = max(0, t - clip_len // 2)
        raw_end = raw_start + clip_len

        # Try to snap boundaries to speech pauses in transcript
        clip_start, clip_end = snap_to_speech_pause(
            transcript_json, raw_start, raw_end, max_extend=3
        )

        local_video = os.path.join(output_dir, f"highlight_{i}.mp4")
        local_thumb = os.path.join(output_dir, f"thumb_{i}.jpg")

        blob_video = f"{folder_name}/highlight_{i}.mp4"
        blob_thumb = f"{folder_name}/thumb_{i}.jpg"

        words = extract_words_for_clip(
            transcript_json,
            clip_start,
            clip_end
        )

        # 🔥 FAST AI COPYWRITING (GEMINI)
        actual_duration = clip_end - clip_start
        clip_transcript = " ".join([w["text"] for w in words])
        from highlights.utils import generate_viral_hook
        ai_caption, ai_hashtags = generate_viral_hook(clip_transcript)

        drawtext_filters = []

        for w in words:
            text = escape_text(w["text"])

            start = clamp(w["start"], actual_duration)
            end = clamp(w["end"], actual_duration)

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

        bias = "center"
        if speaker_bias_map:
            bias = speaker_bias_map.get(t, "center")

        vf_filters.append(build_dynamic_crop_expression(bias))

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
            "-t", str(actual_duration),
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
            "thumbnail": thumb_url,
            "ai_caption": ai_caption,
            "ai_hashtags": ai_hashtags
        })

        if len(highlights) >= 6:
            break

    return highlights
