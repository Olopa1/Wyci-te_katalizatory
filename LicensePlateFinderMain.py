import mysql.connector
import cv2
import numpy as np
from utils.LicensePlateFinder import find_license_plate, find_plate, LicensePlateClient


class FindPlate:
    def __init__(self, host, user, password, db_name, video_source):
        self.video_source = video_source
        self.db_info = [host, user, password, db_name]

        try:
            # Połączenie z bazą danych
            self.db_conn = mysql.connector.connect(
                host=self.db_info[0],
                user=self.db_info[1],
                password=self.db_info[2],
                database=self.db_info[3]
            )
            print("Połączono z bazą danych.")
        except mysql.connector.Error as e:
            print(f"Błąd połączenia z bazą danych: {e}")
            self.db_conn = None

        try:
            # Klient tablic rejestracyjnych
            self.lpc = LicensePlateClient("127.0.0.1", 33333)
        except Exception as e:
            print(f"Nie można połączyć z serwerem tablic rejestracyjnych: {e}")
            self.lpc = None

        self.found_plates = set()
        self.plates_to_find = self.get_plates_to_find("0")
        self.plates_in_parking = self.get_plates_to_find("1")

    def check_connection(self):
        if self.db_conn and not self.db_conn.is_connected():
            try:
                self.db_conn.reconnect()
                print("Połączenie z bazą danych zostało przywrócone.")
            except mysql.connector.Error as e:
                print(f"Błąd podczas ponownego łączenia z bazą danych: {e}")

    def make_query(self, query, params=None):
        try:
            self.check_connection()
            cursor = self.db_conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            print(f"Wykonano zapytanie: {query} | Parametry: {params}")
            return results
        except mysql.connector.Error as e:
            print(f"Błąd podczas wykonywania zapytania: {e}")
            return []

    def get_plates_to_find(self, plate_type) -> list:
        query = "SELECT register_plate FROM cars WHERE is_on_parking = %s"
        results = self.make_query(query, (plate_type,))
        plates = [row[0] for row in results]
        print(f"Pobrano tablice rejestracyjne ({plate_type}): {plates}")
        return plates

    def update_plates(self, plate):
        query = "UPDATE cars SET is_on_parking = %s WHERE register_plate = %s"
        params = (1, plate)
        try:
            self.insert_data(query, params)
            self.db_conn.commit()
            print(f"Zaktualizowano tablicę rejestracyjną: {plate}")
        except mysql.connector.Error as e:
            print(f"Błąd podczas aktualizacji tablicy rejestracyjnej {plate}: {e}")

    def insert_data(self, query, params):
        try:
            self.check_connection()
            cursor = self.db_conn.cursor()
            cursor.execute(query, params)
            print(f"Wstawiono dane: {query} | Parametry: {params}")
        except mysql.connector.Error as e:
            print(f"Błąd podczas wstawiania danych: {e}")

    def look_for_plates(self):
        cap = cv2.VideoCapture(self.video_source)
        prev_frame = None
        search_paused = False
        prev_motion_frame = None
        processed_diff = None

        while not cap.isOpened():
            cap = cv2.VideoCapture(self.video_source)
            cv2.waitKey(2000)
            print("Czekam na wideo...")

        while True:
            flag, frame = cap.read()
            if flag:
                pos_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if prev_frame is not None and pos_frame % 5 == 0 and len(self.plates_to_find) != 0:
                    frame_diff = cv2.absdiff(gray_frame, prev_frame)
                    blurred_diff = cv2.GaussianBlur(frame_diff, (5, 5), 0)
                    _, binary_diff = cv2.threshold(blurred_diff, 25, 255, cv2.THRESH_BINARY)
                    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 10))
                    processed_diff = cv2.morphologyEx(binary_diff, cv2.MORPH_OPEN, kernel)
                    motion_detected = np.sum(processed_diff) > 10000

                    if motion_detected:
                        if not search_paused:
                            found = find_license_plate(frame)
                            for plate in self.plates_to_find:
                                items_found = find_plate(plate, found)
                                if items_found:
                                    print(f"Znaleziono tablicę: {items_found[1]}")
                                    self.update_plates(items_found[1])
                                    self.plates_to_find = self.get_plates_to_find("0")
                                    self.plates_in_parking = self.get_plates_to_find("1")
                                    if self.lpc:
                                        self.lpc.send_license_plate(items_found[1])
                                    search_paused = True
                                    prev_motion_frame = gray_frame
                    else:
                        if prev_motion_frame is not None:
                            motion_diff = cv2.absdiff(gray_frame, prev_motion_frame)
                            if np.sum(motion_diff) > 5000:
                                search_paused = False
                                print("Wykryto nowy ruch.")

                prev_frame = gray_frame

                if processed_diff is not None:
                    cv2.imshow("Processed Diff", processed_diff)
                cv2.imshow("Frame", frame)
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pos_frame - 1)
                print("Klatka nie jest gotowa")
                cv2.waitKey(1)

            if cv2.waitKey(1) == 27:  # ESC kończy program
                cv2.destroyAllWindows()
                break


# Inicjalizacja klasy i uruchomienie
licenseFinder = FindPlate(
    host='localhost',
    user='root',
    password='',
    db_name='wyciete_katalizatory',
    video_source='./temp/tablice_rejestracyje_2.mp4'
)
licenseFinder.look_for_plates()