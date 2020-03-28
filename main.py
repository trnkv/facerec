# -*- coding: utf-8 -*-
# GUI URL: https://gist.github.com/Lukse/e5f9022f5944599c949ca24d1d4154a2#file-pyqt_opencv-py


from PyQt4 import QtCore, QtGui, uic
import sys
import cv2
import numpy as np
import threading
import time
import queue
import face_recognition
import os.path
import shutil
from PyQt4.QtCore import pyqtSlot
from photomanager import save_encodings, get_encodings


running = False
capture_thread = None
form_class = uic.loadUiType("design.ui")[0]
q = queue.Queue()

photos_path = 'photos/'
encodings_path = 'encodings/'
known_face_encodings = None
known_face_names = None

#global frame_rec
frame_rec = None
#global name_rec
name_rec = 'Unknown'
#global top_rec, right_rec, bottom_rec, left_rec
top_rec = right_rec = bottom_rec = left_rec = 0
#global flag_known_face
flag_known_face = False
#global detected_unknown
detected_unknown = False
frame_number = 0
 

def grab(cam, queue, width, height):
    global running
    capture = cv2.VideoCapture(cam)
    # capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    # capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # capture.set(cv2.CAP_PROP_FPS, fps)

    while(running):
        frame = {}
        capture.grab()
        retval, img = capture.retrieve(0)
        frame["img"] = img

        if queue.qsize() < 10:
            queue.put(frame)
        else:
            print(queue.qsize())

class OwnImageWidget(QtGui.QWidget):
    def __init__(self, parent=None):
        super(OwnImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        sz = image.size()
        self.setMinimumSize(sz)
        self.update()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QtCore.QPoint(0, 0), self.image)
        qp.end()


def draw_rectangle(frame, top, right, bottom, left, color):
    # Draw a box around the face
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)


def draw_label(frame, name, top, right, bottom, left, color):
    # Draw a box around the face
    draw_rectangle(frame, top, right, bottom, left, color)
    # Draw a label with a name below the face
    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, name, (left + 6, bottom - 6), font, 1.0, (0, 0, 0), 1)


# def initial():
    # 'Прогреваем' камеру, чтобы снимок не был тёмным
    # for i in range(30):
    #     video_capture.read()
    # return known_face_encodings, known_face_names


class MyWindowClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.startButton.clicked.connect(self.start_clicked)
        
        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        global qt_lineEdit_name
        qt_lineEdit_name= self.lineEdit_name
        global qt_bt_add
        qt_bt_add = self.bt_add

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)


    def start_clicked(self):
        global running
        running = True
        # ==============================

        capture_thread.start()
        self.startButton.setEnabled(False)
        self.startButton.setText('Starting...')


    def update_frame(self):
        global frame_rec
        global name_rec
        global top_rec, right_rec, bottom_rec, left_rec
        global flag_known_face
        global detected_unknown
        global frame_number

        if not q.empty():
            start_time_update = time.time()
            self.startButton.setText('Camera is live')
            frame = q.get()
            img = frame["img"]

            global flag_known_face
            
            start_time_save_encodings = time.time()
            save_encodings(photos_path, encodings_path)
            print(f'=======  Time to save encoding(s): {time.time()-start_time_save_encodings} seconds. =======')
            
            start_time_get_encodings = time.time()
            known_face_encodings, known_face_names = get_encodings(encodings_path)
            print(f'=======  Time to get encoding(s): {time.time()-start_time_get_encodings} seconds. =======')

            # frame_rec, name_rec, top_rec, right_rec, bottom_rec, left_rec, flag_known_face, detected_unknown, known_face_encodings, known_face_names = initial()

            img_height, img_width, img_colors = img.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)

            if flag_known_face:
                draw_label(img, name_rec, top_rec, right_rec, bottom_rec, left_rec, (0, 255, 0))
                if name_rec.find('Unknown') != -1:
                    if os.path.isfile('unknown/' + name_rec + 'png'):
                    # Move a file from the directory d1 to d2
                    # os.remove('unknown/' + name_rec + 'png')
                        shutil.move('unknown/' + name_rec + 'png', 'known_photos_unnamed/' + name_rec + 'png')
            
            frame_number += 1
            if frame_number % 30 == 0:
                start_time = time.time()
                # Find all the faces and face enqcodings in the frame of video
                face_locations = face_recognition.face_locations(img)
                face_encodings = face_recognition.face_encodings(img, face_locations)
                print(f'======= Время поиска лица на изображении: {time.time()-start_time} seconds. =======')

                # Loop through each face in this frame of video
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    # Scale back up face locations since the frame we detected in was scaled to 1/10 size
                    # top *= 30
                    # right *= 30
                    # bottom *= 30
                    # left *= 30

                    # See if the face is a match for the known face(s)
                    draw_rectangle(img, top, right, bottom, left, (0, 0, 255))
                    # cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = 'Unknown'

                    # If a match was found in known_face_encodings, just use the first one.
                    if True in matches:
                        first_match_index = matches.index(True)
                        name = known_face_names[first_match_index]
                        print('DETECTED ', name)
                        frame_rec = img
                        name_rec = name
                        top_rec = top
                        right_rec = right
                        bottom_rec = bottom
                        left_rec = left
                        flag_known_face = True
                        draw_label(frame_rec, name_rec, top_rec, right_rec, bottom_rec, left_rec, (0, 255, 0))
                        cv2.imwrite('detected/' + name_rec + 'png', frame_rec)
                        if "Unknown" in name:
                            detected_unknown = True


                        # Or instead, use the known face with the smallest distance to the new face
                        # face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        # best_match_index = np.argmin(face_distances)
                        # if matches[best_match_index]:
                        #     name = known_face_names[best_match_index]

                    else:
                        path = '.'
                        num_files = len([f for f in os.listdir('unknown/') if os.path.isfile(os.path.join('unknown/', f))])
                        # cv2.imwrite('unknown/' + datetime.datetime.now().strftime('%d-%m-%Y__%H:%M') + '.png', frame)
                        cv2.imwrite('unknown/Unknown_' + str(num_files) + '.png', img)
                        if save_encodings('unknown/', encodings_path) != -1:
                            print('DETECTED UNKNOWN PERSON ', 'Unknown_' + str(num_files))
                            flag_known_face = False
                            break
                
                if detected_unknown:
                    qt_lineEdit_name.setEnabled(True)
                    qt_bt_add.setEnabled(True)
                    if qt_lineEdit_name.text() != "":
                        @pyqtSlot()
                        def bt_add_clicked():
                            # удаляем из папки Unknown
                            try:
                                os.remove('unknown/' + name_rec + 'png')
                            except Exception as e:
                                pass                            
                            shutil.move('detected/' + name_rec + 'png', 'detected/' + qt_lineEdit_name.text() + '.png')
                            shutil.move('encodings/' + name_rec + 'pckl', 'encodings/' + qt_lineEdit_name.text() + '.pckl')
                            # shutil.copy('detected/' + qt_lineEdit_name.text() + '.png', 'photos/')
                            print("Person have been added to System!")
                            qt_lineEdit_name.setText("")
                        qt_bt_add.clicked.connect(bt_add_clicked)
                else:
                    qt_lineEdit_name.setText("")
                    qt_lineEdit_name.setEnabled(False)
                    qt_bt_add.setEnabled(False)
            self.ImgWidget.setImage(image)
            print(f'======= Время обработки кадра: {time.time()-start_time_update} seconds. =======')

    def closeEvent(self, event):
        global running
        running = False



# capture_thread = threading.Thread(target=grab, args = (0, q, 1920, 1080, 2))
capture_thread = threading.Thread(target=grab, args = (0, q, 1920, 1080))

application = QtGui.QApplication(sys.argv)
w = MyWindowClass(None)
w.setWindowTitle('facerec')
w.show()
application.exec_()
