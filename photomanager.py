from os import listdir
import os.path
import face_recognition
import pickle


def save_encodings_by_photos(photos_folder, encodings_folder):
    for photo_file in listdir(photos_folder):
        if not os.path.isfile(encodings_folder+photo_file[:-4]+".pckl"):
            name = photo_file
            print(f"I haven't encoding for {name}. Try to generate it...")
            image = face_recognition.load_image_file(photos_folder + name)
            if len(image) > 0:
                print('Image exists!')
            encoding = face_recognition.face_encodings(image)
            if len(encoding) > 0:
                print(f"FACE ENCODING:\n{str(encoding)}")
                new_encoding = face_recognition.face_encodings(image)[0]
                with open(encodings_folder + name[:-4] + ".pckl", "wb") as new_encoding_file:
                    pickle.dump(new_encoding, new_encoding_file)
                    print('Encoding %s have been saved!' % (encodings_folder + name[:-4] + ".pckl"))
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
