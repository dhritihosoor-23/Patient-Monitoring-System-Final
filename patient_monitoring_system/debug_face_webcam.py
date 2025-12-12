# debug_face_webcam.py
"""Capture a single frame from the webcam and run MediaPipe face detection.
The script saves two images:
  - debug_face_input.jpg : raw webcam frame
  - debug_face_output.jpg: frame with detected face bounding boxes (yellow)
"""
import cv2
from perception.face_detector import FaceDetector
from config import FACE_DETECTION_CONFIG

def capture_frame():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam (index 0)")
    # Warm‑up a few frames for exposure
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to read frame from webcam")
    cv2.imwrite("debug_face_input.jpg", frame)
    print("[DEBUG] Saved debug_face_input.jpg")
    return frame

if __name__ == "__main__":
    frame = capture_frame()
    detector = FaceDetector(FACE_DETECTION_CONFIG)
    # Run detection on the whole frame (no person bbox needed for this test)
    faces = detector.detect(frame)
    print(f"[DEBUG] Faces detected: {len(faces)}")
    for i, f in enumerate(faces):
        print(f"  Face {i}: ({f.x1:.0f}, {f.y1:.0f}) – ({f.x2:.0f}, {f.y2:.0f})  conf={f.confidence:.2f}")
    if faces:
        vis = detector.visualize(frame.copy(), faces)
        cv2.imwrite("debug_face_output.jpg", vis)
        print("[DEBUG] Saved debug_face_output.jpg with drawn boxes")
    else:
        print("[DEBUG] No faces detected – try adjusting lighting or lowering confidence threshold.")
