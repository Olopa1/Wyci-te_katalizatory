import mysql.connector
import cv2
import numpy as np
from utils.LicensePlateFinder import find_license_plate,find_plate,LicensePlateClient

#db_conn = mysql.connector.connect(
#    host='localhost',
#    user='root',
#    password='',
#    database='wyciete_katalizatory'
#)


class FindPlate:
    def __init__(self,host,user,password,db_name,video_souorce):
        self.vide_source = video_souorce
        self.db_info = [host,user,password,db_name]
        self.db_conn = mysql.connector.connect(
                host=self.db_info[0],
                user=self.db_info[1],
                password=self.db_info[2],
                database=self.db_info[3]
        )
        try:
            self.lpc = LicensePlateClient("127.0.0.1",33333)
        except Exception:
            print("Cannot connect")
        self.found_plates = set()
        self.plates_to_find = self.get_plates_to_find("0")
        self.plates_in_parking = self.get_plates_to_find("1")
    def check_connection(self):
        if self.db_conn.is_connected() is False:
            self.db_conn.reconnect()

    def make_querry(self,querry) ->list:
        self.check_connection()
        coursor = self.db_conn.cursor()
        coursor.execute(querry)
        results = coursor.fetchall()
        return results

    def get_plates_to_find(self,type) -> list:
        result = self.make_querry("SELECT register_plate FROM cars WHERE is_on_parking =" + type)
        plates = []
        for i in result:
            plates.append(i[0])
        return plates

    def update_plates(self,plate):
        params = [1,plate]
        self.insert_data("UPDATE cars SET is_on_parking = %s WHERE register_plate = %s",params)
        self.db_conn.commit()

    def insert_data(self,querry,params):
        self.check_connection()
        coursor = self.db_conn.cursor()
        coursor.execute(querry,params)

    def look_for_plates(self):
        device = self.vide_source
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

                if (prev_frame is not None and pos_frame % 5 == 0) and len(self.plates_to_find) != 0 :
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
                            #print(found.keys())

                            for i in self.plates_to_find:
                                items_found = find_plate(i, found)
                                if items_found is not None:
                                    print(f"Plate found: {items_found[1]}")
                                    self.update_plates(items_found[1])
                                    self.plates_to_find = self.get_plates_to_find("0")
                                    self.plates_in_parking = self.get_plates_to_find("1")
                                    self.lpc.send_license_plate(items_found[1])
                                    search_paused = True  # Zatrzymujemy wyszukiwanie
                                    prev_motion_frame = gray_frame  # Zapisujemy klatkę z ruchem
                    else:
                        try:
                            motion_diff = cv2.absdiff(gray_frame, prev_motion_frame)
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
                cv2.waitKey(1)

            # Zakończenie programu przy wciśnięciu klawisza ESC
            if cv2.waitKey(1) == 27:
                cv2.destroyAllWindows()
                break

licenseFinder = FindPlate(host='localhost',user='root',password='',db_name='wyciete_katalizatory',video_souorce='./temp/tablice_rejestracyje_2.mp4')
licenseFinder.look_for_plates()