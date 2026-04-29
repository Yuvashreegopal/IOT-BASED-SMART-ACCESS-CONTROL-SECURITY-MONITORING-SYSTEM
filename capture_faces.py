import cv2
import os

name = input("Enter user name: ")

path = f"face_dataset/{name}"

if not os.path.exists(path):
    os.makedirs(path)

cam = cv2.VideoCapture(0)

count = 0

while True:
    ret, frame = cam.read()

    cv2.imshow("Capture Face", frame)

    key = cv2.waitKey(1)

    if key == ord('s'):
        img_path = f"{path}/{count}.jpg"
        cv2.imwrite(img_path, frame)
        print("Saved:", img_path)
        count += 1

    if key == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()