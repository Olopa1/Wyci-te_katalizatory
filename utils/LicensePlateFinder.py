import re

import cv2
import skimage
import pytesseract as pt
import numpy as np
from skimage.color import rgb2gray
import matplotlib.pyplot as plt
import matplotlib.image as mpimg



def find_license_plate(img) -> dict:
    gray_image = rgb2gray(img)
    if gray_image.dtype != np.uint8:
        gray_image = (gray_image * 255).astype(np.uint8)

    blurred = cv2.GaussianBlur(gray_image,(5,5),0)
    edges = cv2.Canny(blurred,50,150)
    contours,_ = cv2.findContours(edges,cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    potential_plates = {}
    for contour in contours:
        # Obliczenie prostokąta ograniczającego dla każdego konturu
        x, y, w, h = cv2.boundingRect(contour)
        aspect_ratio = w / float(h)

        # Warunki wstępne dla tablic rejestracyjnych (np. proporcja szerokości do wysokości)
        if 2 < aspect_ratio < 6 and 150 < w * h:  # Możesz dostosować warunki
            # Wycięcie potencjalnego obszaru tablicy
            license_plate = gray_image[y:y + h, x:x + w]

            # Opcjonalna korekcja perspektywy lub zmiana rozmiaru
            license_plate = cv2.resize(license_plate, (400, 100))

            # 4. OCR na wyciętej tablicy
            pt.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text_reg = pt.image_to_string(license_plate, config='--psm 8')  # Tryb dla pojedynczej linii
            text_reg = re.sub(r'[^a-zA-Z0-9]','',text_reg)
            potential_plates[text_reg.upper()] = license_plate
    return potential_plates

def find_plate(plate_name,found_plates):
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

#potenial_plates1 = find_license_plate(image1)
#potenial_plates2 = find_license_plate(image2)
#potenial_plates3 = find_license_plate(image3)

#paltes_key = ["WE2U656","DW2DK01","CWL17991"]

#found_plate1 = find_plate(paltes_key[0],potenial_plates1)
#found_plate2 = find_plate(paltes_key[1],potenial_plates2)
#found_plate3 = find_plate(paltes_key[2],potenial_plates3)

#show_plate(image1,found_plate1,paltes_key[0])
#show_plate(image2,found_plate2,paltes_key[1])
#show_plate(image3,found_plate3,paltes_key[2])