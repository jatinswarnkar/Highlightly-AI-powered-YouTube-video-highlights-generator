# import cv2
# import mediapipe as mp

# # Correct for your installed mediapipe
# mp_face_detection = mp.solutions.face_detection
# mp_face = mp_face_detection.FaceDetection(
#     model_selection=0,
#     min_detection_confidence=0.6
# )

# def detect_face_bias(video_path, clip_start, clip_len, sample_rate=1):
#     """
#     Returns: 'left' | 'center' | 'right'
#     """
#     cap = cv2.VideoCapture(video_path)
#     positions = []

#     for sec in range(int(clip_start), int(clip_start + clip_len), sample_rate):
#         cap.set(cv2.CAP_PROP_POS_MSEC, sec * 1000)
#         ret, frame = cap.read()
#         if not ret:
#             continue

#         h, w, _ = frame.shape
#         rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#         result = mp_face.process(rgb)
#         if not result.detections:
#             continue

#         face = max(
#             result.detections,
#             key=lambda d: d.location_data.relative_bounding_box.width
#         )

#         cx = (
#             face.location_data.relative_bounding_box.xmin
#             + face.location_data.relative_bounding_box.width / 2
#         )

#         if cx < 0.33:
#             positions.append("left")
#         elif cx > 0.66:
#             positions.append("right")
#         else:
#             positions.append("center")

#     cap.release()

#     if not positions:
#         return "center"

#     return max(set(positions), key=positions.count)
