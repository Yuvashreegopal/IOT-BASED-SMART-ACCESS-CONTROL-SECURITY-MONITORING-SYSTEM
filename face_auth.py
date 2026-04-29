import cv2
import os
import numpy as np

DATASET_PATH = "face_dataset"

faces = []
labels = []
label_map = {}
current_label = 0

print("🔄 Loading dataset...")

for person_name in os.listdir(DATASET_PATH):
    person_path = os.path.join(DATASET_PATH, person_name)

    if not os.path.isdir(person_path):
        continue

    label_map[current_label] = person_name

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)

        img = cv2.imread(img_path)

        # ✅ FIX: skip invalid images
        if img is None:
            print(f"⚠️ Skipping invalid image: {img_path}")
            continue

        try:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        except:
            print(f"⚠️ Error processing image: {img_path}")
            continue

        faces.append(gray)
        labels.append(current_label)

    current_label += 1

print("✅ Dataset loaded")

# ------------------------------
# Train Model
# ------------------------------
model = cv2.face.LBPHFaceRecognizer_create()

if len(faces) > 0:
    model.train(faces, np.array(labels))
    print("✅ Model trained")
else:
    print("❌ No valid faces found!")

# ------------------------------
# Face Detector
# ------------------------------
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# ------------------------------
# Recognize from frame
# ------------------------------
def recognize_face(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces_rect = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces_rect:
        face = gray[y:y+h, x:x+w]

        try:
            label, confidence = model.predict(face)
        except:
            return None

        if confidence < 70:
            return label_map[label]

    return None

# ------------------------------
# CAMERA FUNCTION
# ------------------------------
def recognize_face_from_camera(timeout=5):

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("❌ Camera not working")
        return None

    print("📸 Face verification started...")

    start = cv2.getTickCount()

    while True:
        ret, frame = cap.read()

        if not ret:
            continue

        name = recognize_face(frame)

        cv2.imshow("Face Verification", frame)

        if name:
            print("✅ Face matched:", name)
            cap.release()
            cv2.destroyAllWindows()
            return name

        elapsed = (cv2.getTickCount() - start) / cv2.getTickFrequency()

        if elapsed > timeout:
            print("❌ Face not recognized")
            break

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    return None