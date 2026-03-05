import cv2
import os

def get_haar_cascade_path():
    # OpenCV provides haarcascades out of the box
    return cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'

def detect_face_bias(video_path, clip_start, clip_len, sample_rate=1):
    """
    Analyzes several frames in a clip to determine where the speaker's face is predominately located.
    Returns: 'left' | 'center' | 'right'
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Error: Could not open video file {video_path}")
        return "center"

    cascade_path = get_haar_cascade_path()
    if not os.path.exists(cascade_path):
        print(f"❌ Error: Haar cascade not found at {cascade_path}")
        return "center"

    face_cascade = cv2.CascadeClassifier(cascade_path)
    positions = []
    
    for sec in range(int(clip_start), int(clip_start + clip_len), sample_rate):
        cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
        ret, frame = cap.read()
        if not ret:
            continue

        h, w, _ = frame.shape
        # Haar cascades work best on grayscale images
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        faces = face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5, 
            minSize=(30, 30)
        )

        if len(faces) > 0:
            # Assume the largest detection is the primary speaker
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            x, y, fw, fh = faces[0]

            # Relative X-coordinate of the center of the face (0.0 to 1.0)
            cx = (x + fw / 2) / w

            if cx < 0.35:
                positions.append("left")
            elif cx > 0.65:
                positions.append("right")
            else:
                positions.append("center")

    cap.release()

    if not positions:
        print(f"⚠️ No faces detected for clip at {clip_start}s, defaulting to center.")
        return "center"

    # Return the most frequent position found in the samples
    bias = max(set(positions), key=positions.count)
    print(f"✅ Detected '{bias}' bias for clip at {clip_start}s")
    return bias
