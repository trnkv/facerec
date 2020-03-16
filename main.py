import cv2
import numpy as np
import face_recognition
import datetime
import os.path
from photomanager import save_encodings, get_encodings


def draw_rectangle(frame, name, top, right, bottom, left, color):
    # Draw a box around the face
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

    # Draw a label with a name below the face
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)
    cv2.imwrite("photos/Detected_" + name + '.png', frame)
    

def app(video_capture):
    photos_path = "photos/"
    encodings_path = "encodings/"
    
    frame_rec = None
    name_rec = 'Unknown'
    top_rec = right_rec = bottom_rec = left_rec = 0
    
    flag = False

    save_encodings(photos_path, encodings_path)
    known_face_encodings, known_face_names = get_encodings(encodings_path)

    # "Прогреваем" камеру, чтобы снимок не был тёмным
    # for i in range(30):
    #     video_capture.read()

    frame_number = 0
    
    while True:
        if flag:
            draw_rectangle(frame_rec, name_rec, top_rec, right_rec, bottom_rec, left_rec, (0, 255, 0))
            
        
        # Grab a single frame of video
        ret, frame = video_capture.read()
        
        frame_number += 1
        if frame_number % 50 != 0:
            cv2.imshow('Video', frame)
            # Hit 'q' on the keyboard to quit!
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue
        flag = False
        # ================= Resize frame of video to 1/10 size for faster face recognition processing ===========================
        # frame = cv2.resize(frame, (0, 0), fx=0.3, fy=0.3)

        # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
        rgb_frame = frame[:, :, ::-1]

        # Find all the faces and face enqcodings in the frame of video
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Loop through each face in this frame of video
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            
            # Scale back up face locations since the frame we detected in was scaled to 1/10 size
            # top *= 30
            # right *= 30
            # bottom *= 30
            # left *= 30            

            # See if the face is a match for the known face(s)
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            # If a match was found in known_face_encodings, just use the first one.
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]
                print('DETECTED ', name)
                frame_rec = frame
                name_rec = name
                top_rec = top
                right_rec = right
                bottom_rec = bottom
                left_rec = left
                flag = True

            # Or instead, use the known face with the smallest distance to the new face
            # face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            # best_match_index = np.argmin(face_distances)
            # if matches[best_match_index]:
            #     name = known_face_names[best_match_index]
            else:
                path = '.'
                num_files = len([f for f in os.listdir('unknown/') if os.path.isfile(os.path.join('unknown/', f))]) 
                # cv2.imwrite("unknown/" + datetime.datetime.now().strftime("%d-%m-%Y__%H:%M") + '.png', frame)
                cv2.imwrite("unknown/Unknown_" + str(num_files) + '.png', frame)
                if save_encodings("unknown/", encodings_path) != -1:                
                    print('DETECTED UNKNOWN PERSON ', "Unknown_" + str(num_files))
                    #flag = False
                    break

            

        # Display the resulting image
        cv2.imshow('Video', frame)

        # Hit 'q' on the keyboard to quit!
        #if cv2.waitKey(1) & 0xFF == ord('q'):
            #break
        
        if not flag:
            app(video_capture)

    # Release handle to the webcam
    

if __name__ == '__main__':
    video_capture = cv2.VideoCapture(0)
    # path = 'sudo modprobe bcm2835-v412 max_video_width=300 max_video_height=300'
    # os.system(path)
    # video_capture.set(3, 300)
    # video_capture.set(4, 300)

    # video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 300)
    # video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 300)
    # video_capture.set(cv2.CAP_PROP_FPS, 2)
    app(video_capture)
    video_capture.release()
    cv2.destroyAllWindows()
