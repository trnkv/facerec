from os import listdir
import os.path
import face_recognition
import pickle
# import time


class Trainer:
    """
    Класс для обучения нейросети на фотографиях.

    ...

    Атрибуты
    --------
    - photos_path : str
        папка, где лежат фотографии для обучения
    - encodings_path : str
        папка, где лежат кодировки тренировочных фотографий

    Методы
    ------
    - train_one(folder_of_photo_file, name_of_photo_file):
        Обучает нейросеть распознавать одного конкретного человека по его фотографии.

        Параметры
        ---------
        - folder_of_photo_file : str
            папка, где лежит фотография для обучения
        - name_of_photo_file : str
            имя фотографии с расширением

    - train_all()
        Обучает нейросеть распознавать всех людей, фотографии которых находятся в папке photos_path.
    """
    def __init__(self, photos_path, encodings_path):
        self.__photos_path = photos_path
        self.__encodings_path = encodings_path

    def __train(self, folder, photo_file):
        if not os.path.isfile(f"{self.__encodings_path}{photo_file[:-4]}.pckl"):  # если encoding для этого изображения не существует
            print(f"I haven't encoding for {photo_file}. Try to generate it...")
            # start_time = time.time()
            image = face_recognition.load_image_file(folder + photo_file)
            encoding = face_recognition.face_encodings(image)
            if len(encoding) > 0:
                with open(f"{self.__encodings_path}{photo_file[:-4]}.pckl", "wb") as new_encoding_file:
                    pickle.dump(encoding[0], new_encoding_file)
                    print(f"Encoding {self.__encodings_path + photo_file[:-4]}.pckl have been saved!")
                    # print(f'=== Время сохранения encoding для {photo_file}: {time.time() - start_time} секунд. ===\n\n')
            else:
                print("Ooops, I couldn't recognize the face!\n")
                return -1

    def train_one(self, folder_of_photo_file, name_of_photo_file):
        """
        Обучает нейросеть распознавать одного конкретного человека по его фотографии.

        Параметры
        ---------
        - folder_of_photo_file : str
                папка, где лежит фотография для обучения
        - name_of_photo_file : str
                имя фотографии с расширением

        Возвращаемое значение
        ---------------------
        None, если обучение прошло успешно
        -1 в обратном случае
        """
        self.__train(folder_of_photo_file, name_of_photo_file)

    def train_all(self):
        """
        Обучает нейросеть распознавать всех людей, фотографии которых находятся в папке photos_path.

        Возвращаемое значение
        ---------------------
        None, если обучение прошло успешно
        -1 в обратном случае
        """
        for photo_file in listdir(self.__photos_path):
            self.__train(self.__photos_path, photo_file)
