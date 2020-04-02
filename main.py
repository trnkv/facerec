# -*- coding: utf-8 -*-
# GUI URL: https://gist.github.com/Lukse/e5f9022f5944599c949ca24d1d4154a2#file-pyqt_opencv-py


from PyQt4 import QtCore, QtGui, uic
import sys
import cv2
import numpy as np
import threading
import time
import datetime
import queue
import face_recognition
import os.path
import shutil
from PyQt4.QtCore import pyqtSlot
from photomanager import save_encodings_by_photos, get_encodings


RUNNING = False
CAPTURE_THREAD = None
form_class = uic.loadUiType("design.ui")[0]
q = queue.Queue()

photos_path = 'photos/'
encodings_path = 'encodings/'

start_time_save_encodings = time.time()
save_encodings_by_photos(photos_path, encodings_path)
print(f'=======  Time to save encoding(s): {time.time()-start_time_save_encodings} seconds. =======')

KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = get_encodings(encodings_path)

FRAME_REC = None
NAME_REC = 'Unknown'
TOP_REC = RIGHT_REC = BOTTOM_REC = LEFT_REC = 0
FLAG_KNOWN_FACE = False
DETECTED_UNKNOWN = False
FRAME_NUMBER = 0
 

def grab(cam, queue, width, height, fps):
    global RUNNING
    capture = cv2.VideoCapture(cam)
    # capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    # capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
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


# def initial():
    # 'Прогреваем' камеру, чтобы снимок не был тёмным
    # for i in range(30):
    #     video_capture.read()
    # return KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES


class MyWindowClass(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.startButton.clicked.connect(self.start_clicked)
        
        self.window_width = self.ImgWidget.frameSize().width()
        self.window_height = self.ImgWidget.frameSize().height()
        self.ImgWidget = OwnImageWidget(self.ImgWidget)

        # global QT_lineEdit_name
        # QT_lineEdit_name= self.lineEdit_name
        # global QT_bt_add
        # QT_bt_add = self.bt_add
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
        # global FRAME_REC
        # global NAME_REC
        # global TOP_REC, RIGHT_REC, BOTTOM_REC, LEFT_REC
        # global FLAG_KNOWN_FACE
        # global DETECTED_UNKNOWN
        # global FRAME_NUMBER

        if not q.empty():
            start_time_update = time.time()
            self.startButton.setText('Camera is live')
            frame = q.get()
            img = frame["img"]

            # global FLAG_KNOWN_FACE   

            start_time_get_encodings = time.time()
            KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = get_encodings(encodings_path)
            print(f'=======  Time to get encoding(s): {time.time()-start_time_get_encodings} seconds. =======')         

            # FRAME_REC, NAME_REC, TOP_REC, RIGHT_REC, BOTTOM_REC, LEFT_REC, FLAG_KNOWN_FACE, DETECTED_UNKNOWN, KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = initial()

            img_height, img_width, img_colors = img.shape
            scale_w = float(self.window_width) / float(img_width)
            scale_h = float(self.window_height) / float(img_height)
            scale = min([scale_w, scale_h])

            if scale == 0:
                scale = 1

            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation = cv2.INTER_CUBIC)
            # small_frame = cv2.resize(img, (0, 0), fx=0.2, fy=0.2)
            # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
            # img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            # img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            # rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            height, width, bpc = img.shape
            bpl = bpc * width
            image = QtGui.QImage(img.data, width, height, bpl, QtGui.QImage.Format_RGB888)

            # if FLAG_KNOWN_FACE:
            #     draw_label(img, NAME_REC, TOP_REC, RIGHT_REC, BOTTOM_REC, LEFT_REC, (0, 255, 0))
            #     if NAME_REC.find('Unknown') != -1:
            #         if os.path.isfile('unknown/' + NAME_REC + 'png'):
            #         # Move a file from the directory d1 to d2
            #         # os.remove('unknown/' + NAME_REC + 'png')
            #             shutil.move('unknown/' + NAME_REC + 'png', 'known_photos_unnamed/' + NAME_REC + 'png')
            
            # FRAME_NUMBER += 1
            # if FRAME_NUMBER % 30 == 0:

            start_time = time.time()
            # Find all the faces and face enqcodings in the frame of video
            face_locations = face_recognition.face_locations(img)
            face_encodings = face_recognition.face_encodings(img, face_locations)
            # face_locations = face_recognition.face_locations(rgb_small_frame)
            # face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            print(f'======= Время поиска лица на изображении: {time.time()-start_time} seconds. =======')


            # Loop through each face in this frame of video
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Scale back up face locations since the frame we detected in was scaled to 1/10 size
                # top *= 20
                # right *= 20
                # bottom *= 20
                # left *= 20

                # See if the face is a match for the known face(s)
                draw_rectangle(img, top, right, bottom, left, (0, 0, 255))
                # cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

                matches = face_recognition.compare_faces(KNOWN_FACE_ENCODINGS, face_encoding)
                name = 'Unknown'

                # # If a match was found in KNOWN_FACE_ENCODINGS, just use the first one.
                if True in matches:
                    first_match_index = matches.index(True)
                    name = KNOWN_FACE_NAMES[first_match_index]
                    print('DETECTED ', name)
                    log = ''
                    if "Unknown" in name:
                        DETECTED_UNKNOWN = True
                        log = f"{datetime.datetime.now().strftime('%H:%M')} UNKNOWN: {name}"                    
                        QT_textBrowser.append(log)
                    else:
                        log = f"{datetime.datetime.now().strftime('%H:%M')} Detected: {name}"
                        QT_textBrowser.append(log)
                    # создаем лог-файл для текущей сессии
                    file_log = open(f"logs/log_{datetime.datetime.now().strftime('%d-%m-%y')}", 'a+')
                    file_log.write(log+'\n')
                    file_log.close()
                    # FRAME_REC = img
                    # NAME_REC = name
                    # TOP_REC = top
                    # RIGHT_REC = right
                    # BOTTOM_REC = bottom
                    # LEFT_REC = left
                    # FLAG_KNOWN_FACE = True
                    # draw_label(FRAME_REC, NAME_REC, TOP_REC, RIGHT_REC, BOTTOM_REC, LEFT_REC, (0, 255, 0))
                    draw_label(img, name, top, right, bottom, left, (0, 255, 0))
                    cv2.imwrite('detected/' + name + 'png', img)


                else:
                    path = '.'
                    num_files = len([f for f in os.listdir('unknown/') if os.path.isfile(os.path.join('unknown/', f))])
                    # cv2.imwrite('unknown/' + datetime.datetime.now().strftime('%d-%m-%Y__%H:%M') + '.png', frame)
                    cv2.imwrite('unknown/Unknown_' + str(num_files) + '.png', img)
                    if save_encodings_by_photos('unknown/', encodings_path) != -1:
                        print('DETECTED UNKNOWN PERSON ', 'Unknown_' + str(num_files))
                        # FLAG_KNOWN_FACE = False

            self.ImgWidget.setImage(image)
            
            
            # if DETECTED_UNKNOWN:
            #     QT_lineEdit_name.setEnabled(True)
            #     QT_bt_add.setEnabled(True)
            #     if QT_lineEdit_name.text() != "":
            #         @pyqtSlot()
            #         def bt_add_clicked():
            #             # удаляем из папки Unknown
            #             try:
            #                 os.remove('unknown/' + NAME_REC + 'png')
            #             except Exception as e:
            #                 pass                            
            #             shutil.move('detected/' + NAME_REC + 'png', 'detected/' + QT_lineEdit_name.text() + '.png')
            #             shutil.move('encodings/' + NAME_REC + 'pckl', 'encodings/' + QT_lineEdit_name.text() + '.pckl')
            #             # shutil.copy('detected/' + QT_lineEdit_name.text() + '.png', 'photos/' + QT_lineEdit_name.text() + '.png')
            #             # удалено из-за того, чтобы в photos не сохранялась фотография с лейблом!
            #             print("Person have been added to System!")
            #             QT_lineEdit_name.setText("")
            #         QT_bt_add.clicked.connect(bt_add_clicked)
            # else:
            #     QT_lineEdit_name.setText("")
            #     QT_lineEdit_name.setEnabled(False)
            #     QT_bt_add.setEnabled(False)
            
            print(f'======= Время обработки кадра: {time.time()-start_time_update} seconds. =======')

    def closeEvent(self, event):
        global RUNNING
        RUNNING = False



# CAPTURE_THREAD = threading.Thread(target=grab, args = (0, q, 1920, 1080, 2))
CAPTURE_THREAD = threading.Thread(target=grab, args = (0, q, 1920, 1080, 30))

application = QtGui.QApplication(sys.argv)
w = MyWindowClass(None)
w.setWindowTitle('facerec')
w.show()
application.exec_()
