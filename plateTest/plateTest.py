from utils.LicensePlateFinder import find_license_plate,find_plate,show_plate, find_license_plate_test
import numpy as np
import skimage.exposure
from skimage import io
from skimage.morphology import disk
from skimage import img_as_ubyte
import cv2
import cv2.videostab

def main(plates):
    found_plates = set()
    device = "../temp/tablice_rejestracyje_3.mp4"
    cap = cv2.VideoCapture(device)
    prev_frame = None  # Poprzednia klatka (do obliczenia różnic)
    search_paused = False  # Flaga kontrolująca, czy kontynuować wyszukiwanie
    prev_motion_frame = None  # Zapis klatki, gdy wykryto ruch
    processed_diff = None
    while not cap.isOpened():
        cap = cv2.VideoCapture(device)
        cv2.waitKey(2000)
        print("Waiting for video")
    while True:
        flag, frame = cap.read()
        if flag:
            pos_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)

            # Przekształcenie do skali szarości
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None and pos_frame % 5 == 0:
                # Obliczenie różnicy między klatkami
                frame_diff = cv2.absdiff(gray_frame, prev_frame)

                # Odszumianie różnicy
                blurred_diff = cv2.GaussianBlur(frame_diff, (5, 5), 0)

                # Progowanie różnicy
                _, binary_diff = cv2.threshold(blurred_diff, 25, 255, cv2.THRESH_BINARY)

                # Operacje morfologiczne (usunięcie małych zakłóceń)
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
                processed_diff = cv2.morphologyEx(binary_diff, cv2.MORPH_OPEN, kernel)

                # Sprawdzenie, czy wykryto zmiany w klatce
                motion_detected = np.sum(processed_diff) > 10000  # Próg detekcji ruchu

                if motion_detected:
                    # Jeśli wyszukiwanie nie jest wstrzymane, wykonaj detekcję tablicy
                    if not search_paused:
                        found = find_license_plate(frame)
                        print(found.keys())

                        for i in plates:
                            items_found = find_plate(i, found)
                            if items_found is not None:
                                found_plates.add(items_found[1])
                                print(f"Plate found: {items_found[1]}")
                                search_paused = True  # Zatrzymujemy wyszukiwanie
                                prev_motion_frame = gray_frame  # Zapisujemy klatkę z ruchem
                else:
                    try:
                        motion_diff = cv2.absdiff(gray_frame,prev_motion_frame)
                        if np.sum(motion_diff) > 5000:
                            search_paused = False
                            print("New motion detected")
                    except Exception:
                        continue
            # Zapis bieżącej klatki jako poprzednia
            prev_frame = gray_frame

            # Wyświetlanie wyników
            if processed_diff is not None:
                cv2.imshow("Processed Diff", processed_diff)
            cv2.imshow("Frame", frame)
        else:
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame - 1)
            print("Frame is not ready")
            print(found_plates)
            cv2.waitKey(1)

        # Zakończenie programu przy wciśnięciu klawisza ESC
        if cv2.waitKey(1) == 27:
            print(found_plates)
            cv2.destroyAllWindows()
            break


LICENSE_PLATES = ["CWL34950","WP14831","WP5207N","CWL17991"]
main(LICENSE_PLATES)