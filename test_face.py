import cv2
from face_auth import recognize_face

cam = cv2.VideoCapture(0)

print("📸 Press Q to exit")

while True:
    ret, frame = cam.read()

    name = recognize_face(frame)

    if name:
        cv2.putText(frame, f"User: {name}", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    else:
        cv2.putText(frame, "Unknown", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)

    cv2.imshow("Face Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()