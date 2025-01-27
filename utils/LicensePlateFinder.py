import re

import cv2
import skimage
import pytesseract as pt
import numpy as np
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import socket
import time


from skimage.filters import farid


class LicensePlateClient:
    def __init__(self, ip, port):
        self.port = port
        self.ip = ip
        self.s = socket.socket()
        tries = 0
        while True:
            try:
                self.s.connect((ip, port))
                self.s.send("FindPlate".encode())
                data = self.s.recv(1024).decode()
                if data.lower() == 'welcome':
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

    def close_connection(self):
        try:
            self.s.close()
        except OSError as e:
            print(f"Error closing connection: {e}")

    def send_license_plate(self, plate) -> bool:
        try:
            self.s.send("found".encode())
            data = self.s.recv(1024).decode()
            if data.lower() == 'ok':
                self.s.send(plate.encode())
                return True
            else:
                print("Server responded with an error.")
                return False
        except ConnectionResetError:
            print("Connection reset by server while sending license plate.")
        except socket.timeout:
            print("Timeout while sending license plate.")
        except OSError as e:
            print(f"Socket error while sending license plate: {e}")
        return False


def open_gate():
    print("Open gate")
    time.time(5)
    print("Close gate")

def find_license_plate(img) -> dict:
    gray_image = rgb2gray(img)
    if gray_image.dtype != np.uint8:
        gray_image = (gray_image * 255).astype(np.uint8)

    blurred = cv2.GaussianBlur(gray_image,(5,5),0)
    edges = cv2.Canny(blurred,50,150)
    contours,_ = cv2.findContours(edges,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    potential_plates = {}
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)


        if 2 < aspect_ratio < 6 and 150 < w * h:
            license_plate = gray_image[y:y + h, x:x + w]

            license_plate = cv2.resize(license_plate, (400, 100))

            pt.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text_reg = pt.image_to_string(license_plate, config='--psm 8')
            text_reg = re.sub(r'[^a-zA-Z0-9]','',text_reg)
            potential_plates[text_reg.upper()] = license_plate
    return potential_plates

def find_license_plate_test(img)->dict:
    gray_image = rgb2gray(img)
    if gray_image.dtype != np.uint8:
        gray_image = (gray_image * 255).astype(np.uint8)

    _, binary_image = cv2.threshold(gray_image, 120, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(binary_image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    potential_plates = {}
    pt.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)


        if 2 < aspect_ratio < 6 and 150 < w * h:
            license_plate = gray_image[y:y + h, x:x + w]


            license_plate = cv2.resize(license_plate, (400, 100))

            text_reg = pt.image_to_string(license_plate, config='--psm 8')
            text_reg = re.sub(r'[^a-zA-Z0-9]', '', text_reg)
            if text_reg:
                potential_plates[text_reg.upper()] = license_plate

    return potential_plates



def find_plate(plate_name,found_plates):
    # print(plate_name)
    # print(found_plates.keys())
    if plate_name in found_plates.keys():
        return found_plates[plate_name],plate_name

def show_plate(original,plate,text):
    if plate is None:
        return
    fig, axs = plt.subplots(1, 2, figsize=(15, 20))
    axs[0].imshow(original, cmap='gray')
    axs[0].set_title("Oryginalny obraz")
    axs[1].imshow(plate, cmap='gray')
    axs[1].set_title(f"Rejstracja: {text}")
    plt.show()

#image1 = cv2.imread("D:\\dominik\\programy\\psio_projekt\\temp\\test1.jpg")
#image2 = cv2.imread("D:\\dominik\\programy\\psio_projekt\\temp\\test2.jpg")
#image3 = cv2.imread("D:\\dominik\\programy\\psio_projekt\\temp\\test4.png")
#testing = {"WE2U656":image1,"DW2DK01":image2,"CWL17991":image3}
#potential_plates = find_license_plate(image1)

#start = time.time_ns()
#potenial_plates1 = find_license_plate_test(image2)
#end = time.time_ns()

#find1time = (end - start)/1000000000

#start = time.time_ns()
#potenial_plates2 = find_license_plate(image2)
#end = time.time_ns()

#find2time = (end - start)/1000000000

#print(f"First run time: {find1time} Second run time: {find2time}")

#potenial_plates3 = find_license_plate_test(image3)

#paltes_key = ["WE2U656","DW2DK01","CWL17991"]

#found_plate1 = find_plate(paltes_key[1],potenial_plates1)
#found_plate2 = find_plate(paltes_key[1],potenial_plates2)
#found_plate3 = find_plate(paltes_key[2],potenial_plates3)

#show_plate(image1,found_plate1[0],paltes_key[0])
#show_plate(image2,found_plate2[0],paltes_key[1])
#show_plate(image3,found_plate3[0],paltes_key[2])