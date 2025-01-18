from time import sleep

from utils.LicensePlateFinder import LicensePlateClient

def main():
    test_plates = [
    "WE12345",  # Warszawa
    "KR9876A",  # Kraków
    "GD54321",  # Gdańsk
    "PO45678",  # Poznań
    "LU3210B",  # Lublin
    "WR5678C",  # Wrocław
    "SZ78901",  # Szczecin
    "SK43210",  # Katowice
    "BI87654",  # Białystok
    "EL65432"   # Łódź
    ]
    lpc = LicensePlateClient('127.0.0.1',  33333)
    for plate in test_plates:
        lpc.send_license_plate(plate)

    sleep(120)
    lpc.close_connection()

if __name__ == '__main__':
    main()