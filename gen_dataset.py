import cv2
import face_recognition
import pickle


cam = cv2.VideoCapture(0)
cam.set(3, 200)  # set video width
cam.set(4, 200)  # set video height

face_detector = cv2.CascadeClassifier('cascades/haarcascade_frontalface_default.xml')
encodings_path = 'encodings'

# For each person, enter one numeric face id
face_name = input('\n Enter person name in format FirstName_LastName end press <return> ==>  ')

print("\n [INFO] Initializing face capture. Look the camera and wait ...")
# Initialize individual sampling face count
count = 0

while(True):
    ret, img = cam.read()
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    faces = face_detector.detectMultiScale(rgb, 1.3, 5)

    for (x, y, w, h) in faces:

        cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
        count += 1

        # Save the captured image into the datasets folder
        cv2.imwrite("dataset/" + str(face_name) + ".jpg", rgb[y:y + h, x:x + w])
        # train the neural network to recognize this person
        encoding = face_recognition.face_encodings(rgb[y:y + h, x:x + w])
        if len(encoding) > 0:  # если закодировать лицо получилось
            with open(f'{encodings_path}/{str(face_name)}.pckl', "wb") as encoding_file:
                pickle.dump(encoding[0], encoding_file)
                print(f'\n [SUCCESS] Encoding {encodings_path}/{str(face_name)}.pckl have been saved')
        else:
            print("\n [ERROR] Ooops, I couldn't recognize this face!")
        cv2.imshow('image', img)

    k = cv2.waitKey(100) & 0xff  # Press 'ESC' for exiting video
    if k == 27:
        break
    elif count >= 1:  # Take 1 face sample and stop video
        break

# Do a bit of cleanup
print("\n [SUCCESS] OK! Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
