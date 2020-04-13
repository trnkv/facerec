from os import listdir
import os.path
import face_recognition
import pickle
import time


def save_encodings_by_photos(photos_folder, encodings_folder):
    for photo_file in listdir(photos_folder):
        if not os.path.isfile(encodings_folder+photo_file[:-4]+".pckl"): # если encoding для этого изображения не существует
            print(f"I haven't encoding for {photo_file}. Try to generate it...")
            start_time = time.time()
            image = face_recognition.load_image_file(photos_folder + photo_file)
            encoding = face_recognition.face_encodings(image)
            if len(encoding) > 0:
                with open(encodings_folder + photo_file[:-4] + ".pckl", "wb") as new_encoding_file:
                    pickle.dump(encoding[0], new_encoding_file)
                    print(f'Encoding {encodings_folder + photo_file[:-4]}.pckl have been saved!' )
                    print(f'=== Время сохранения encoding для {photo_file}: {time.time() - start_time} секунд. ===\n\n')
            else:
                print("Ooops, I couldn't recognize the face!\n")
                return -1


def save_one_encoding_by_photo(photo_folder, photo_file, encodings_folder):
    if not os.path.isfile(encodings_folder+photo_file[:-4]+".pckl"): # если encoding для этого изображения не существует
        print(f"I haven't encoding for {photo_file}. Try to generate it...")
        start_time = time.time()
        image = face_recognition.load_image_file(photo_folder + photo_file)
        encoding = face_recognition.face_encodings(image)
        if len(encoding) > 0:
            with open(encodings_folder + photo_file[:-4] + ".pckl", "wb") as new_encoding_file:
                pickle.dump(encoding[0], new_encoding_file)
                print(f'Encoding {encodings_folder + photo_file[:-4]}.pckl have been saved!' )
                print(f'=== Время сохранения encoding для {photo_file}: {time.time() - start_time} секунд. ===\n\n')
        else:
            print("Ooops, I couldn't recognize the face!\n")
            return -1


def get_encodings(encoding_path):
    known_face_encodings = []
    known_face_names = []
    
    for file in listdir(encoding_path):
        with open(encoding_path + file, "rb") as fp:   # Unpickling
            encoding = pickle.load(fp)
            known_face_encodings.append(encoding)
            known_face_names.append(file[:-4])
    
    return known_face_encodings, known_face_names
