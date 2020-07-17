# -*- coding: utf-8 -*-
# GUI CODE URL: https://gist.github.com/Lukse/e5f9022f5944599c949ca24d1d4154a2#file-pyqt_opencv-py

import sys
import threading
import time
# import timeit
import datetime
import queue
import os.path
from os import listdir
# import pathlib

from PyQt4 import QtCore, QtGui, uic
# from espeakng import ESpeakNG
import pyttsx3

import cv2
# import numpy as np
import face_recognition
import pickle
# import pyscreenshot as ImageGrab
# from PIL import Image
import trainer


def create_folders():
    if not os.path.exists('detected/'):
        os.makedirs('detected/')
    if not os.path.exists('detected/unknown/'):
        os.makedirs('detected/unknown/')
    if not os.path.exists('logs/'):
        os.makedirs('logs/')
    if not os.path.exists('photos/'):
        os.makedirs('photos/')
    if not os.path.exists('unknown/'):
        os.makedirs('unknown/')


def get_encodings(encoding_path):
    known_face_encodings = []
    known_face_names = []
    for file in listdir(encoding_path):
        with open(encoding_path + file, "rb") as fp:   # Unpickling
            encoding = pickle.load(fp)
            known_face_encodings.append(encoding)
            known_face_names.append(file[:-4])
    return known_face_encodings, known_face_names


def draw_rectangle(frame, top, right, bottom, left, color):
    # Draw a box around the face
    cv2.rectangle(frame, (left, top), (right, bottom), color, 2)


def draw_label(frame, name, top, right, bottom, left, color):
    # Draw a box around the face
    draw_rectangle(frame, top, right, bottom, left, color)
    # Draw a label with a name below the face
    cv2.rectangle(frame, (left, bottom - 20), (right, bottom), color, cv2.FILLED)
    font = cv2.FONT_HERSHEY_DUPLEX
    cv2.putText(frame, name, (left + 2, bottom - 6), font, 0.3, (0, 0, 0), 1)


RUNNING = False
CAPTURE_THREAD = None
FORM_CLASS = uic.loadUiType("design.ui")[0]
QUEUE = queue.Queue()

create_folders()
PHOTOS_PATH = 'photos/'
ENCODINGS_PATH = 'encodings/'

TRAINER = trainer.Trainer(PHOTOS_PATH, ENCODINGS_PATH)
START_TIME_SAVE_ENCODINGS = time.time()
TRAINER.train_all()
print(f'=======  Time to save encoding(s): {time.time()-START_TIME_SAVE_ENCODINGS} seconds. =======')

KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = get_encodings(ENCODINGS_PATH)

# инициализируем синтезатор речи
ENGINE = pyttsx3.init()
# устанавливаем скорость произношения
ENGINE.setProperty('rate', 125)


def grab(cam, queue, width, height, fps):
    global RUNNING
    capture = cv2.VideoCapture(cam)
    # capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    # capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    capture.set(cv2.CAP_PROP_FPS, fps)
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    while(RUNNING):
        frame = {}
        capture.grab()
        retval, img = capture.read(0)
        img = cv2.resize(img, (200, 200))
        # cv2.imwrite('image.png', img)
        # print(f'###### [SHAPE] {img.shape}')
        # frame["img"] = cv2.imread('image.png')
        frame["img"] = img

        if queue.qsize() < 1:
            queue.put(frame)
#             time.sleep(1)
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
            self.startButton.setText('Camera is live')
            known_face_encodings, known_face_names = get_encodings(ENCODINGS_PATH)
            frame = QUEUE.get()
            img = frame["img"]
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # Find all the faces and face encodings in the current frame of video
            face_locations = face_recognition.face_locations(img)
            face_encodings = face_recognition.face_encodings(img, face_locations)

            match_founded = False
            face_names = []
            for face_encoding in face_encodings:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                # # Use the known face with the smallest distance to the new face
                # start_time = time.time()                                              ######################## очень долго (6-8 мс на ноуте)! ###############################
                # face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                # best_match_index = np.argmin(face_distances)
                # if matches[best_match_index]:
                #     name = known_face_names[best_match_index]
                #     face_names.append(name)
                #     print(f'[TIME] Нахожу похожее лицо: {time.time() - start_time}')  ######################## очень долго (6-8 мс на ноуте)! ###############################

                # If a match was found in known_face_encodings, just use the first one.
                # start_time = time.time()                                              ########### 1-2 мс на ноуте ###########
                if True in matches:  # если совпадение нашли
                    first_match_index = matches.index(True)
                    name = known_face_names[first_match_index]
                    face_names.append(name)
                    # print(f"[TIME] Нахожу похожее лицо: {time.time() - start_time}")  ########### 1-2 мс на ноуте ###########
                    match_founded = True

                    # Display the results
                    # for (top, right, bottom, left) in face_locations:
                    #     draw_label(img, name, top, right, bottom, left, (0, 255, 0))

                    print(f"DETECTED {name}")
                else:  # если совпадение не нашли
                    match_founded = False

            # рисуем лейбл(ы)
            for (top, right, bottom, left), name in zip(face_locations, face_names):
                draw_label(img, name, top, right, bottom, left, (0, 255, 0))
            
            if match_founded:
                # создаем или открываем лог-файл для текущей сессии
                with open(f"logs/log_{datetime.datetime.now().strftime('%d-%m-%y')}.txt", "a+") as file_log:
                    # file_log.seek(0)  # ставим курсор на начало файла, т. к. в режиме a+ он по умолчанию в конце
                    text_in_textBrowser = QT_textBrowser.toPlainText()
                    name_in_last_line = text_in_textBrowser[text_in_textBrowser.rfind(' ') + 1:]
                    if name != name_in_last_line:
                        log = f"{datetime.datetime.now().strftime('%H:%M')} Detected: {name}"
                        QT_textBrowser.append(log)
                        file_log.write(log + '\n')
                        ENGINE.say(f"Hello, {name}!")
                        ENGINE.runAndWait()
                if "Unknown" in name:
                    cv2.imwrite(f"detected/unknown/{name}png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                else:
                    cv2.imwrite(f"detected/unknown/{name}png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            else:
                num_files = len([f for f in os.listdir('unknown/') if os.path.isfile(os.path.join('unknown/', f))])
                unknown_name_file = f"Unknown_{num_files}.png"
                cv2.imwrite(f"unknown/{unknown_name_file}", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
                if TRAINER.train_one('unknown/', unknown_name_file) != -1:  # если обучение прошло успешно
                    log = f"=== {datetime.datetime.now().strftime('%H:%M')} DETECTED NEW UNKNOWN: {unknown_name_file[:-4]} ==="
                    QT_textBrowser.append(log)
                    with open(f"logs/log_{datetime.datetime.now().strftime('%d-%m-%y')}.txt", "a+") as file_log:
                        file_log.write(log + '\n')
                    ENGINE.say(f"Hello, {unknown_name_file[:-4]}! I remember you.")
                    ENGINE.runAndWait()
                    print(f"DETECTED UNKNOWN PERSON: {unknown_name_file[:-4]}")

            # подгоняем изображение под размер окошка
            img_height, img_width, img_colors = img.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])
            if scale == 0:
                scale = 1
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)
            self.ImgWidget.setImage(image)

    def closeEvent(self, event):
        global RUNNING
        RUNNING = False


CAPTURE_THREAD = threading.Thread(target=grab, args=(0, QUEUE, 200, 200, 30))

APPLICATION = QtGui.QApplication(sys.argv)
WINDOW = MyWindowClass(None)
WINDOW.setWindowTitle('facerec')
WINDOW.show()
APPLICATION.exec_()
