import os
import uuid
import shutil
from django.conf import settings

from .jobs import update_job
from .utils import (
    download_youtube,
    extract_audio,
    detect_scenes,
    detect_audio_peaks,
    transcribe_with_azure,
    cleanup_video,
)
from .highlight_generator import make_highlights_multiple
from highlights.ml_models import EMOTION_MODEL
#from highlights.face_crop import detect_face_bias


REEL_CONFIG = {
    "clip_len": 10,
    "min_gap": 15,
    "max_clips": 6,
}


# =========================
# HIGHLIGHT SELECTION
# =========================
def select_reel_highlights(scored_times):
    selected = []
    candidates = sorted(scored_times.items(), key=lambda x: x[1], reverse=True)

    for t, score in candidates:
        if all(abs(t - s) >= REEL_CONFIG["min_gap"] for s in selected):
            selected.append(t)
        if len(selected) >= REEL_CONFIG["max_clips"]:
            break

    return sorted(selected)


# =========================
# MAIN WORKER
# =========================
def run_highlight_job(job_id, video_path=None, url=None):
    audio_path = None

    try:
        update_job(job_id, "downloading", 10)

        emotion_classifier = EMOTION_MODEL

        # --------------------------------------------------
        # STEP 1: COPY INPUT VIDEO (DECOUPLE REQUEST)
        # --------------------------------------------------
        if url:
            video_path = download_youtube(url)
        else:
            video_path = video_path

        if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
            raise RuntimeError("Video download failed")

        # --------------------------------------------------
        # STEP 2: EXTRACT AUDIO
        # --------------------------------------------------
        update_job(job_id, "extracting audio", 30)
        audio_path = extract_audio(video_path)

        if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
            raise RuntimeError("Audio extraction failed")

        # --------------------------------------------------
        # STEP 3: SIGNAL SCORING
        # --------------------------------------------------
        update_job(job_id, "detecting highlights", 50)

        scenes = detect_scenes(video_path)[:20]
        peaks = detect_audio_peaks(audio_path, top_k=20)

        transcript_json = transcribe_with_azure(audio_path)
        ai_scores = {}

        if transcript_json:
            detailed = transcript_json.get("NBest", [])
            detailed = detailed[0] if detailed else None

            if detailed and "Words" in detailed:
                buffer_words = []
                buffer_start = None

                for w in detailed["Words"]:
                    if buffer_start is None:
                        buffer_start = w["Offset"]

                    buffer_words.append(w["Word"])

                    if len(buffer_words) >= 6:
                        phrase = " ".join(buffer_words)
                        label = emotion_classifier(phrase)[0]["label"].lower()

                        if label in ("joy", "surprise", "excitement"):
                            t = int(buffer_start / 10_000_000)
                            ai_scores[t] = ai_scores.get(t, 0) + 4

                        buffer_words = []
                        buffer_start = None

        # --------------------------------------------------
        # STEP 4: COMBINE SCORES
        # --------------------------------------------------
        combined = {}

        for t in scenes:
            combined[int(t)] = combined.get(int(t), 0) + 1

        for t in peaks:
            combined[int(t)] = combined.get(int(t), 0) + 3

        for t, s in ai_scores.items():
            combined[t] = combined.get(t, 0) + s

        highlight_times = select_reel_highlights(combined)
        highlight_times = [max(2, t) for t in highlight_times]

        # --------------------------------------------------
        # STEP 4.1: face bias detection (left/center/right)
        # --------------------------------------------------

        # speaker_bias_map = {}

        # for t in highlight_times:
        #     speaker_bias_map[t] = detect_face_bias(
        #         video_path=video_path,
        #         clip_start=t,
        #         clip_len=REEL_CONFIG["clip_len"]
        #     )


        # --------------------------------------------------
        # STEP 5: GENERATE CLIPS
        # --------------------------------------------------
        update_job(job_id, "generating highlights", 85)

        output_dir = os.path.join(settings.MEDIA_ROOT, f"highlights_{job_id}")
        os.makedirs(output_dir, exist_ok=True)

        speaker_bias_map = {} # Fixed missing variable

        highlights = make_highlights_multiple(
            video_path=video_path,
            highlight_times=highlight_times,
            transcript_json=transcript_json,
            clip_len=REEL_CONFIG["clip_len"],
            output_dir=output_dir,
            center=True,
            speaker_bias_map=speaker_bias_map,
        )

        update_job(job_id, "done", 100, result=highlights)

    except Exception as e:
        update_job(job_id, "error", error=str(e))

    finally:
        # --------------------------------------------------
        # CLEANUP (SAFE)
        # --------------------------------------------------
        try:
            if video_path and os.path.exists(video_path):
                os.remove(video_path)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
        except Exception:
            pass
