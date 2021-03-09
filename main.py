# -*- coding: utf-8 -*-
# GUI CODE URL: https://gist.github.com/Lukse/e5f9022f5944599c949ca24d1d4154a2#file-pyqt_opencv-py

import sys
import threading
import time
import datetime
import queue
import os.path

from PyQt5 import QtCore, QtGui, QtWidgets, uic
import cv2
import face_recognition

#import pyttsx3  # синтезатор голоса
from espeakng import ESpeakNG  # синтезатор голоса
import speech_recognition as sr  # распознавание речи

from photomanager import save_encodings_by_photos, get_encodings


RUNNING = False
CAPTURE_THREAD = None
FORM_CLASS = uic.loadUiType("design.ui")[0]
QUEUE = queue.Queue()

PHOTOS_PATH = 'photos/'
ENCODINGS_PATH = 'encodings/'
LOG_FILENAME = f"logs/log_{datetime.datetime.now().strftime('%d-%m-%y')}"
VISITORS_FILENAME = f"logs/events/visitors_{datetime.datetime.now().strftime('%d-%m-%y')}"
SEARCH_FILENAME = f"logs/events/search_{datetime.datetime.now().strftime('%d-%m-%y')}"

START_TIME_SAVE_ENCODINGS = time.time()
save_encodings_by_photos(PHOTOS_PATH, ENCODINGS_PATH)
print(f'=======  Time to save encoding(s): {time.time()-START_TIME_SAVE_ENCODINGS} seconds. =======')

KNOWN_FACE_ENCODINGS, KNOWN_FACE_NAMES = get_encodings(ENCODINGS_PATH)


def say_was(search_name):
        """
        проходим по файлу VISITORS_FILENAME, ищем имя
        читаем вслух последнюю строку, когда был человек
        """
        visitors_file = open(VISITORS_FILENAME, r)
        all_lines = visitors_file.readlines()
        last_string = ""

        for i in range(len(all_lines)):  # line = "Иван Иванов был сегодня в 15 часов 10 минут"
            if search_name in all_lines[i]:
                last_string = all_lines[i]
        
        if last_string != "":
            TTS.say(last_string)
        else:
            TTS.say(f"Я сегодня не видела {search_name}.")


def say_find(name_ask):
    """
    последняя строка из файла событий:
    {name_lookfor}, вас искал {name_ask} в *время*
    """
    search_file = open(SEARCH_FILENAME, r)
    all_lines = search_file.readlines()
    for line in all_lines:  # line = "Иван Иванов 15:10"
        name_searcher = line.split(" ", -1)[0]  # разбиваем по последнему пробелу, получаем имя искомого чел-ка
        time_search = line.split(" ", -1)[1]  # разбиваем по последнему пробелу, получаем время
        if name_ask in line:
            TTS.say(f"{name_ask}, Вас искал {name_searcher} в {time_search}.")


def listen_forever:
    """
    recognize_bing(): Microsoft Bing Speech
    recognize_google(): Google Web Speech API
    recognize_google_cloud(): Google Cloud Speech - требует установки пакета google-cloud-speech package
    recognize_houndify(): Houndify by SoundHound
    recognize_ibm(): IBM Speech to Text
    recognize_sphinx(): CMU Sphinx - требует установки PocketSphinx
    recognize_wit(): Wit.ai

    Из семи только recognize_sphinx() работает в автономном режиме с движком CMU Sphinx. Остальные шесть требуют подключения к интернету.
    """
    r = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        while True:
            r.adjust_for_ambient_noise(source)  # распознает речь в шуме
            audio = r.listen(source)  # записывает ввод от источника до тех пор, пока не будет обнаружена тишина
            heard = r.recognize_google(audio)
            if "Гитовна" in heard:
                if "меня кто-то искал" in heard:
                    say_find(...)  # передать сюда имя, полученное с распознанной фото
                if "где" in heard:
                    say_was(heard[4:])  # имя, полученное после слова "где"


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


class OwnImageWidget(QtWidgets.QWidget):
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


def write_visitor(name):
    global VISITORS_FILENAME
    file_log = open(VISITORS_FILENAME, 'a+')
    file_log.write(
        f"{name} был сегодня в " +
        datetime.datetime.now().strftime('%H часов %M минут') +
        '\n')
    file_log.close()



class MyWindowClass(QtWidgets.QMainWindow, FORM_CLASS):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
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

            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
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
                        write_visitor(name) # записать в журнал посещений
                        # TODO: спросить имя, записать, узнать, что хотел, записать в журнал событий
                    else:
                        log = f"{datetime.datetime.now().strftime('%H:%M')} Detected: {name}"
                        QT_textBrowser.append(log)
                        write_visitor(name) # записать в журнал посещений
                        current_hour = int(datetime.datetime.now().strftime('%H'))
                        if current_hour >= 0 and current_hour < 12:
                            TTS.say(f"Доброе утро, {name}!")
                        elif current_hour >=12 and current_hour < 17:
                            TTS.say(f"Добрый день, {name}!")
                        elif current_hour >=17 and current_hour < 0:
                            TTS.say(f"Добрый вечер, {name}!")
                        # TODO: проверить, не искал ли его кто-то; если да - сказать
                        say_find(name)
                    # создаем лог-файл для текущей сессии
                    global LOG_FILENAME
                    file_log = open(LOG_FILENAME, 'a+')
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


CAPTURE_THREAD = threading.Thread(target=grab, args=(0, QUEUE, 200, 200))

# TTS = pyttsx3.init()
TTS = ESpeakNG()
TTS.speed(150)
TTS.voice = 'russian'

APPLICATION = QtWidgets.QApplication(sys.argv)
WINDOW = MyWindowClass(None)
WINDOW.setWindowTitle('facerec')
WINDOW.show()
APPLICATION.exec_()
