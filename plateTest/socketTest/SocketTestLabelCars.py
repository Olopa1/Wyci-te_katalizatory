from time import sleep

from utils.RegisterCars import LabelingClient

def main():
    expected_plates = [
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
    recived = set()
    tries = 0
    lc = LabelingClient('127.0.0.1', 33333)
    #print("ok")
    while True:
        try:
            if lc.receive_license_plate():
                plate = lc.get_license_plate()
                recived.add(plate)
                print(plate)
                print(f"Found {len(recived)} out of {len(expected_plates)}")
                tries += 1
        except:
            break
    sleep(120)
    lc.close_connection()
    print(f"Program ended with {tries} tries")


main()