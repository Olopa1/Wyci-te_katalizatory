import cv2
import numpy as np
import torch
import socket
import mysql.connector

class LabelingClient:
    def __init__(self, ip, port):
        self.port = port
        self.ip = ip
        self.s = socket.socket()
        self.s.timeout(1)
        self.license_plate = ''
        tries = 0
        while True:
            try:
                self.s.connect((ip, port))
                self.s.send('LabelCar'.encode())
                data = self.s.recv(1024).decode()
                if data.lower() == 'welcome':
                    print("Label car client started...")
                    break
            except ConnectionRefusedError:
                print(f"Connection refused by {ip}:{port}. Retrying...")
            except socket.timeout:
                print("Connection timed out. Retrying...")
            except OSError as e:
                print(f"Socket error: {e}")
            finally:
                tries += 1
                if tries > 5:
                    raise Exception(f"Cannot connect to {ip}:{port} after 5 attempts")

    def get_license_plate(self) -> str:
        return self.license_plate

    def close_connection(self):
        try:
            self.s.close()
        except OSError as e:
            print(f"Error closing connection: {e}")

    def receive_license_plate(self) -> bool:
        try:
            print("Waiting for data...")
            data = self.s.recv(1024).decode()
            if data.lower() == 'found':
                print(f"Data found: {data}")
                self.s.send('give'.encode())
                data = self.s.recv(1024).decode()
                if data.lower() != 'wrong command given':
                    self.license_plate = data
                    return True
                else:
                    print("Wrong command received from server.")
                    return False
        except ConnectionResetError:
            print("Connection reset by server.")
        except socket.timeout:
            print("Timeout while waiting for data.")
        except OSError as e:
            print(f"Socket error while receiving data: {e}")
        return False


# Funkcja do obliczania IoU (Intersection over Union)
def compute_iou(box1, box2):
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    inter_area = max(0, x2 - x1) * max(0, y2 - y1)
    box1_area = (box1[2] - box1[0]) * (box1[3] - box1[1])
    box2_area = (box2[2] - box2[0]) * (box2[3] - box2[1])

    iou = inter_area / (box1_area + box2_area - inter_area)
    return iou


# Klasa do śledzenia obiektów z poprawką
# Klasa do śledzenia obiektów
class Tracker:
    def __init__(self, max_lost=10):
        self.next_id = 1
        self.objects = {}
        self.lost_frames = {}
        self.max_lost = max_lost
        self.stationary_time = {}

    def update(self, detections):
        updated_objects = {}
        for obj_id in self.objects.keys():
            self.lost_frames[obj_id] += 1

        for detection in detections:
            best_match = None
            best_iou = 0.0

            for obj_id, obj_bbox in self.objects.items():
                iou = compute_iou(obj_bbox, detection)
                if iou > best_iou and iou > 0.3:
                    best_match = obj_id
                    best_iou = iou

            if best_match is not None:
                updated_objects[best_match] = detection
                self.lost_frames[best_match] = 0
                prev_pos = self.objects[best_match]
                dist = np.linalg.norm(np.array(detection[:2]) - np.array(prev_pos[:2]))
                if dist < 5:
                    self.stationary_time[best_match] += 1
                else:
                    self.stationary_time[best_match] = 0
            else:
                updated_objects[self.next_id] = detection
                self.lost_frames[self.next_id] = 0
                self.stationary_time[self.next_id] = 0
                self.next_id += 1

        self.objects = {k: v for k, v in updated_objects.items() if self.lost_frames[k] <= self.max_lost}
        return self.objects


# Funkcja do wykrywania i kadrowania białej kartki
def crop_to_white_paper(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        raise ValueError("Nie znaleziono białej kartki na obrazie.")

    largest_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest_contour)
    cropped_image = image[y:y + h, x:x + w]
    return cropped_image


# Funkcja do podziału obrazu na siatkę z poprawnym oznaczeniem dróg
def divide_into_grid(image, rows, cols):
    height, width, _ = image.shape

    # Predefiniowane wysokości dla każdej sekcji
    row1_height = int(height // 2.75)
    row3_height = int(height // 2.75)
    row2_height = height - row1_height - row3_height

    cell_width = width // cols
    grid_cells = []

    y1 = 0
    for row in range(rows):
        if row == 0:
            y2 = y1 + row1_height
        elif row == 1:
            y2 = y1 + row2_height
        else:
            y2 = y1 + row3_height

        for col in range(cols):
            x1 = col * cell_width
            x2 = x1 + cell_width

            # Oznaczenie drogi
            if row == 1 or (row == 2 and col < 2):
                is_road = True
            else:
                is_road = False

            grid_cells.append((image[y1:y2, x1:x2], (x1, y1, x2, y2), is_road))

        y1 = y2

    return grid_cells



def is_car_parked_correctly(car_bbox, grid_cells, rows, cols):
    result = {
        'parked_correctly': True,
        'reasons': []
    }

    occupied_cells = []

    for idx, (cell, (x1, y1, x2, y2), is_road) in enumerate(grid_cells):
        if not (car_bbox[2] <= x1 or car_bbox[0] >= x2 or car_bbox[3] <= y1 or car_bbox[1] >= y2):
            overlap_x1 = max(car_bbox[0], x1)
            overlap_x2 = min(car_bbox[2], x2)
            overlap_y1 = max(car_bbox[1], y1)
            overlap_y2 = min(car_bbox[3], y2)

            overlap_area = max(0, overlap_x2 - overlap_x1) * max(0, overlap_y2 - overlap_y1)
            cell_area = (x2 - x1) * (y2 - y1)

            overlap_percentage = (overlap_area / cell_area) * 100

            if overlap_percentage > 15:
                occupied_cells.append((idx, is_road))

    rows_occupied = {}
    road_overlap = False

    for idx, is_road in occupied_cells:
        row, col = divmod(idx, cols)
        rows_occupied.setdefault(row, set()).add(col)
        if is_road:
            road_overlap = True

    for row, cols_occupied in rows_occupied.items():
        if len(cols_occupied) > 1:
            result['parked_correctly'] = False
            result['reasons'].append(f'Zajmuje więcej niż 1 kolumnę w wierszu {row + 1}')

    if road_overlap:
        result['parked_correctly'] = False
        result['reasons'].append('Stoi na drodze lub wjeździe')

    return result



def merge_road_areas(grid_cells, rows, cols, image_shape):
    """
    Łączy wszystkie obszary oznaczone jako "droga" w jeden kontur.
    """
    road_mask = np.zeros((image_shape[0], image_shape[1]), dtype=np.uint8)

    for cell, (x1, y1, x2, y2), is_road in grid_cells:
        if is_road:
            cv2.rectangle(road_mask, (x1, y1), (x2, y2), 255, thickness=-1)

    contours, _ = cv2.findContours(road_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        largest_road_contour = max(contours, key=cv2.contourArea)
        return largest_road_contour
    return None


# Funkcja do sprawdzania czasu postoju i wysyłania komunikatów o błędach parkowania
def check_parking_time(tracker, grid_cells, rows, cols):
    for obj_id, stationary_time in tracker.stationary_time.items():
        bbox = tracker.objects.get(obj_id)
        if bbox is None:
            continue

        parking_status = is_car_parked_correctly(bbox, grid_cells, rows, cols)
        if stationary_time > 20 and not parking_status['parked_correctly']:
            print(f"Błąd parkowania: Samochód ID {obj_id} zaparkowany nieprawidłowo")

# Funkcja przetwarzania wideo
def process_video(video_source):
    cap = cv2.VideoCapture(video_source)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 3)

    # Załaduj przetrenowany model YOLOv5
    model = torch.hub.load('ultralytics/yolov5', 'custom',
                           path='C:/Users/milos/yolov5/runs/train/exp3(best)/weights/best.pt')

    tracker = Tracker()

    register_car = LabelingClient("127.0.0.1",33333)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Nie udało się pobrać obrazu ze źródła wideo.")
            break

        # Obsługa białej kartki z rozszerzonymi metodami
        try:
            # Próba znalezienia białej kartki
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                cropped_frame = frame[y:y + h, x:x + w]
            else:
                cropped_frame = frame


        except Exception as e:
            print(f"Błąd podczas kadrowania białej kartki: {e}")
            cropped_frame = frame.copy()


        # Po wygenerowaniu grid_cells
        rows, cols = 3, 5
        grid_cells = divide_into_grid(cropped_frame, rows, cols)

        # Łączenie drogi w jeden kształt
        road_contour = merge_road_areas(grid_cells, rows, cols, cropped_frame.shape)


        # Narysowanie połączonej drogi na obrazie
        if road_contour is not None:
            cv2.drawContours(cropped_frame, [road_contour], -1, (0, 255, 255), 2)  # Żółty kolor dla drogi

        # Detekcja samochodów
        try:
            results = model(cropped_frame)
            detections = []
            for *xyxy, conf, cls in results.xyxy[0]:
                if int(cls) == 0 and conf > 0.5:  # Klasa "car" z progiem pewności
                    x1, y1, x2, y2 = map(int, xyxy)
                    detections.append((x1, y1, x2, y2))
        except Exception as e:
            print(f"Błąd podczas detekcji samochodów: {e}")
            detections = []

        tracked_objects = tracker.update(detections)



        # Wyświetlenie komórek siatki
        for idx, (cell, (x1, y1, x2, y2), is_road) in enumerate(grid_cells):
            row, col = divmod(idx, cols)

            # Określenie koloru i etykiety
            if row == 0:
                label = "Miejsce"
                color = (255, 0, 0)  # Niebieski
            elif row == 2:
                label = "Droga" if col < 2 else "Miejsce"  # Zmieniono z "Wjazd" na "Droga"
                color = (0, 255, 0) if col < 2 else (255, 0, 0)  # Kolor zielony dla drogi
            elif is_road:
                label = "Droga"
                color = (0, 255, 0)  # Zielony
            else:
                label = f"Cell {idx + 1}"
                color = (255, 0, 0)  # Niebieski

            # Rysowanie prostokąta i etykiety
            cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), color, 2)

            # Tło pod tekstem dla lepszej widoczności
            text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            text_x = x1 + 5
            text_y = y1 + 20
            cv2.rectangle(cropped_frame, (text_x - 2, text_y - text_size[1] - 2),
                          (text_x + text_size[0] + 2, text_y + 2), (0, 0, 0), -1)
            cv2.putText(cropped_frame, label, (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Rysowanie i status samochodów
        for obj_id, bbox in tracked_objects.items():
            parking_status = is_car_parked_correctly(bbox, grid_cells, rows, cols)
            color = (0, 255, 0) if parking_status['parked_correctly'] else (0, 0, 255)
            status = "Poprawnie" if parking_status['parked_correctly'] else "Niepoprawnie"

            # Pobranie tablicy rejestracyjnej z LabelingClient
            register_car.receive_license_plate()
            license_plate = register_car.get_license_plate() if 'register_car' in locals() else "Brak danych"

            x1, y1, x2, y2 = bbox
            cv2.rectangle(cropped_frame, (x1, y1), (x2, y2), color, 2)

            # Wyświetlanie statusu i tablicy rejestracyjnej
            cv2.putText(cropped_frame, f"ID {obj_id}: {status}", (x1, y1 - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            cv2.putText(cropped_frame, f"Tablica: {license_plate}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Sprawdzanie czasu postoju i wysyłanie komunikatów
        check_parking_time(tracker, grid_cells, rows, cols)

        # Wyświetlanie wideo
        cv2.imshow("Cropped Frame with Grid and Cars", cropped_frame)

        if cv2.waitKey(1) & 0xFF == 27:  # ESC key
            break

    cap.release()
    cv2.destroyAllWindows()


process_video("./temp/parking.mp4")