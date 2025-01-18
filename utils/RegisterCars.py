import cv2
import numpy as np
import torch
import sqlite3  # Użycie SQLite jako przykładowej bazy danych
from skimage.metrics import structural_similarity as ssim
import socket

from torch.sparse import addmm


class LabelingClient:
    def __init__(self,ip,port):
        self.port = port
        self.ip = ip
        self.s = socket.socket()
        self.license_plate = ''
        tries = 0
        while True:
            try:
                self.s.connect((ip,port))
                self.s.send('LabelCar'.encode())
                data = self.s.recv(1024).decode()
                if data.lower() == 'welcome':
                    print("Label car client started...")
                    break
            except:
                if tries > 5:
                    raise Exception(f"Cannot connect to {ip}:{port}")
                else:
                    tries += 1
                    continue


    def get_license_plate(self) -> str:
        return self.license_plate

    def close_connection(self):
        self.s.close()

    def receive_license_plate(self) -> bool:
        print("waiting for data...")
        data = self.s.recv(1024).decode()
        if data.lower() == 'found':
            print(f"data found: {data}")
            self.s.send('give'.encode())
            data = self.s.recv(1024).decode()
            if data.lower() != 'wrong command given':
                return True
            else:
                return False
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

# Funkcja do pobierania ostatniego numeru rejestracyjnego z bazy danych
def get_latest_plate():
    conn = sqlite3.connect('database.db')  # Podłącz do bazy danych SQLite
    cursor = conn.cursor()
    cursor.execute("SELECT plate_number FROM plates ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "Unknown"

# Funkcja do śledzenia obiektów
class Tracker:
    def __init__(self, max_lost=10):
        self.next_id = 1
        self.objects = {}
        self.lost_frames = {}
        self.max_lost = max_lost
        self.object_plates = {}  # Przypisanie obiektów do tablic rejestracyjnych

    def update(self, detections):
        updated_objects = {}
        for obj_id, obj_bbox in self.objects.items():
            self.lost_frames[obj_id] += 1

        for detection in detections:
            best_match = None
            best_iou = 0.0

            for obj_id, obj_bbox in self.objects.items():
                iou = compute_iou(obj_bbox, detection)
                if iou > best_iou and iou > 0.3:  # Próg IoU
                    best_match = obj_id
                    best_iou = iou

            if best_match is not None:
                updated_objects[best_match] = detection
                self.lost_frames[best_match] = 0
            else:
                # Nowy obiekt
                updated_objects[self.next_id] = detection
                self.lost_frames[self.next_id] = 0
                #self.object_plates[self.next_id] = get_latest_plate()  # Pobierz tablicę rejestracyjną
                self.next_id += 1

        self.objects = {k: v for k, v in updated_objects.items() if self.lost_frames[k] <= self.max_lost}
        self.object_plates = {k: v for k, v in self.object_plates.items() if k in self.objects}
        return self.objects

# Funkcja przetwarzania wideo
def process_video(video_source):
    cap = cv2.VideoCapture(video_source)  # Możesz podać URL RTSP lub HTTP zamiast ścieżki do pliku

    # Załaduj przetrenowany model YOLOv5
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='C:/Users/milos/yolov5/runs/train/exp3(best)/weights/best.pt')

    tracker = Tracker()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print("Nie udało się pobrać obrazu ze źródła wideo.")
            break

        height, width, _ = frame.shape

        # Wykrywanie obiektów za pomocą przetrenowanego modelu YOLOv5
        results = model(frame)
        detections = []

        # Przetwarzanie wyników detekcji
        for *box, conf, cls in results.xyxy[0].tolist():
            x1, y1, x2, y2 = map(int, box)
            if conf > 0.53:  # Próg pewności dla detekcji
                detections.append([x1, y1, x2, y2])

        # Aktualizacja trackerów
        tracked_objects = tracker.update(detections)

        for obj_id, bbox in tracked_objects.items():
            x1, y1, x2, y2 = bbox
            plate_number = tracker.object_plates.get(obj_id, "Unknown")
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"Car: {plate_number}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Wyświetlanie klatki
        cv2.imshow("Frame", frame)

        # Wyjście na klawisz ESC
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()

# Uruchom przetwarzanie wideo (zastąp URL poniżej właściwym URL strumienia)
#process_video("http://192.168.1.25:8080/video")



