from os import listdir
import os.path
import face_recognition
import pickle


def save_encodings(photo_folder, encoding_path):
    for photo_file in listdir(photo_folder):
        if not os.path.isfile(encoding_path+photo_file[:-4]+".pckl"):
            name = photo_file
            print(name)
            image = face_recognition.load_image_file(photo_folder + name)
            if len(image) > 0:
                print('Image exists!')
            if len(face_recognition.face_encodings(image)) > 0:
                print("FACE ENCODING:\n")
                print(face_recognition.face_encodings(image))
                new_encoding = face_recognition.face_encodings(image)[0]
                with open(encoding_path + name[:-4] + ".pckl", "wb") as new_encoding_file:
                    pickle.dump(new_encoding, new_encoding_file)
                    print('Encoding %s have been saved!' % (encoding_path + name[:-4] + ".pckl"))
            else:
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
