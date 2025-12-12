# debug_face_cropped.py
"""Capture a webcam frame, run person detection, then run face detection on the PERSON BBOX crop.
It prints whether a face is found inside the person region.
"""
import cv2
from perception.person_detector import PersonDetector
from perception.face_detector import FaceDetector
from config import PERSON_DETECTION_CONFIG, FACE_DETECTION_CONFIG

def capture_frame():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Could not open webcam")
    for _ in range(5):
        cap.read()
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Failed to read frame")
    cv2.imwrite("debug_cropped_input.jpg", frame)
    print("[DEBUG] Saved debug_cropped_input.jpg")
    return frame

if __name__ == "__main__":
    frame = capture_frame()
    person_det = PersonDetector(PERSON_DETECTION_CONFIG)
    person_boxes = person_det.detect(frame)
    print(f"[DEBUG] Person boxes: {len(person_boxes)}")
    if not person_boxes:
        print("No person detected – cannot test face inside crop")
        exit()
    # Use the first person bbox
    person_bbox = person_boxes[0]
    # Visualize person bbox
    person_vis = person_det.visualize(frame.copy(), [person_bbox])
    cv2.imwrite("debug_person_bbox.jpg", person_vis)
    print("[DEBUG] Saved debug_person_bbox.jpg with person box")
    # Run face detection on the cropped person region
    face_det = FaceDetector(FACE_DETECTION_CONFIG)
    faces = face_det.detect(frame, person_bbox)
    print(f"[DEBUG] Faces inside person bbox: {len(faces)}")
    for i, f in enumerate(faces):
        print(f"  Face {i}: ({f.x1:.0f}, {f.y1:.0f}) – ({f.x2:.0f}, {f.y2:.0f})  conf={f.confidence:.2f}")
    if faces:
        vis = face_det.visualize(frame.copy(), faces)
        cv2.imwrite("debug_face_cropped.jpg", vis)
        print("[DEBUG] Saved debug_face_cropped.jpg with face boxes")
    else:
        print("[DEBUG] No faces detected inside the person crop – may need to adjust cropping or thresholds.")
