# import cv2
import os

def get_haar_cascade_path():
    # OpenCV provides haarcascades out of the box
    return cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

def detect_face_bias(video_path, clip_start, clip_len, sample_rate=1):
    """
    Analyzes several frames in a clip to determine where the speaker's face is predominately located.
    Returns: 'left' | 'center' | 'right'
    """
    # Temporarily disabled OpenCV to fix Azure App Service deployment crash.
    return "center"
