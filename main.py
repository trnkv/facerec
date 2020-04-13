# -*- coding: utf-8 -*-
# GUI CODE URL: https://gist.github.com/Lukse/e5f9022f5944599c949ca24d1d4154a2#file-pyqt_opencv-py

import sys
import threading
import time
import datetime
import queue
import os.path

from PyQt4 import QtCore, QtGui, uic
import cv2
import face_recognition

from photomanager import save_encodings_by_photos, get_encodings


RUNNING = False
CAPTURE_THREAD = None
FORM_CLASS = uic.loadUiType("design.ui")[0]
QUEUE = queue.Queue()

PHOTOS_PATH = 'photos/'
ENCODINGS_PATH = 'encodings/'

START_TIME_SAVE_ENCODINGS = time.time()
save_encodings_by_photos(PHOTOS_PATH, ENCODINGS_PATH)
print(f'=======  Time to save encoding(s): {time.time()-START_TIME_SAVE_ENCODINGS} seconds. =======')

KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = get_encodings(ENCODINGS_PATH)


def grab(cam, queue, width, height):
    global RUNNING
    capture = cv2.VideoCapture(cam)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    # capture.set(cv2.CAP_PROP_FPS, fps)

    while(RUNNING):
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
    cv2.putText(frame, name, (left + 2, bottom - 6), font, 0.5, (0, 0, 0), 1)


class MyWindowClass(QtGui.QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.startButton.clicked.connect(self.start_clicked)
        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        global QT_textBrowser
        QT_textBrowser = self.textBrowser

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(1)


    def start_clicked(self):
        global RUNNING
        RUNNING = True
        # ==============================

        CAPTURE_THREAD.start()
        self.startButton.setEnabled(False)
        self.startButton.setText('Starting...')


    def update_frame(self):
        if not QUEUE.empty():
            start_time_update = time.time()
            self.startButton.setText('Camera is live')
            frame = QUEUE.get()
            img = frame["img"]

            start_time_get_encodings = time.time()
            known_face_encodings, known_face_names = get_encodings(ENCODINGS_PATH)
            print(f'=======  Время получения начальных encodings: {time.time()-start_time_get_encodings} seconds. =======')

            img_height, img_width, img_colors = img.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
            # small_frame = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)

            start_time = time.time()
            # Find all the faces and face enqcodings in the frame of video
            face_locations = face_recognition.face_locations(img)
            print(f'======= Время поиска лица на изображении: {time.time()-start_time} seconds. =======')

            start_time = time.time()
            face_encodings = face_recognition.face_encodings(img, face_locations)
            # face_locations = face_recognition.face_locations(rgb_small_frame)
            # face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            print(f'======= Время составления encoding для лица: {time.time()-start_time} seconds. =======')

            # Loop through each face in this frame of video
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale back up face locations since the frame we detected in was scaled to 1/10 size
                # top *= 20
                # right *= 20
                # bottom *= 20
                # left *= 20

                # See if the face is a match for the known face(s)
                draw_rectangle(img, top, right, bottom, left, (0, 0, 255))

                start_time = time.time()
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                print(f'======= Время compare_faces: {time.time()-start_time} seconds. =======')
                name = 'Unknown'

                # # If a match was found in known_face_encodings, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    print('DETECTED ', name)
                    log = ''
                    if "Unknown" in name:
                        log = f"{datetime.datetime.now().strftime('%H:%M')} UNKNOWN: {name}"                    
                        QT_textBrowser.append(log)
                    else:
                        log = f"{datetime.datetime.now().strftime('%H:%M')} Detected: {name}"
                        QT_textBrowser.append(log)
                    # создаем лог-файл для текущей сессии
                    file_log = open(f"logs/log_{datetime.datetime.now().strftime('%d-%m-%y')}", 'a+')
                    file_log.write(log+'\n')
                    file_log.close()
                    draw_label(img, name, top, right, bottom, left, (0, 255, 0))
                    cv2.imwrite('detected/' + name + 'png', img)
                else:
                    num_files = len([f for f in os.listdir('unknown/') if os.path.isfile(os.path.join('unknown/', f))])
                    cv2.imwrite('unknown/Unknown_' + str(num_files) + '.png', img)
                    if save_encodings_by_photos('unknown/', ENCODINGS_PATH) != -1:
                        print('DETECTED UNKNOWN PERSON ', 'Unknown_' + str(num_files))
            self.ImgWidget.setImage(image)
            print(f'======= Время обработки кадра: {time.time()-start_time_update} seconds. =======')

    def closeEvent(self, event):
        global RUNNING
        RUNNING = False


CAPTURE_THREAD = threading.Thread(target=grab, args=(0, QUEUE, 100, 100))

APPLICATION = QtGui.QApplication(sys.argv)
WINDOW = MyWindowClass(None)
WINDOW.setWindowTitle('facerec')
WINDOW.show()
APPLICATION.exec_()
