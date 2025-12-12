
import cv2

def list_cameras(max_cameras=10):
    available_cameras = []
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                available_cameras.append(i)
            cap.release()
    return available_cameras

if __name__ == "__main__":
    print("Checking available cameras...")
    cameras = list_cameras()
    if cameras:
        print(f"Available cameras: {cameras}")
    else:
        print("No cameras found.")
