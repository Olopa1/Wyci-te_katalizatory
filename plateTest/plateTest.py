from utils.LicensePlateFinder import find_license_plate,find_plate,show_plate
import numpy as np
import skimage.exposure
from skimage import io
from skimage.morphology import disk
from skimage import img_as_ubyte
import cv2

def main(plates):
    found_plates = set()
    device = "../temp/tablice_rejestracyje_1.mp4"
    size = (1280,720)
    cap = cv2.VideoCapture(device)

    while not cap.isOpened():
        cap = cv2.VideoCapture(device)
        cv2.waitKey(2000)
        print("Waiting for video")
    while True:
        flag,frame = cap.read()
        if flag:
            pos_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if pos_frame % 5 == 0:
                found = find_license_plate(frame)
                print(found.keys())
                items_found = None
                for i in plates:
                    items_found = find_plate(i,found)
                    if items_found is None:
                        continue
                    else:
                        found_plates.add(items_found[1])
                    if items_found is not None:
                        print(items_found[1])
            print(found_plates)
            cv2.imshow("Frame",frame)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame-1)
            print("Frame is not ready")
            print(found_plates)
            cv2.waitKey(1)
        if cv2.waitKey(1) == 27:
            print(found_plates)
            cv2.destroyAllWindows()
            break

LICENSE_PLATES = ["CWL34950","WP14831","WP5207N","CWL17991"]
main(LICENSE_PLATES)



