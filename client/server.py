import socket
import numpy as np
import skimage.exposure
from skimage import io
from skimage.morphology import disk
from skimage import img_as_ubyte
import cv2

class LicenseScanning:

    def __init__(self,ip,port):
        self.ip = ip
        self.port = port
        self.lastLicensePlateFound = ''
        self.connectedDevices = {'FindPlate' : None, 'LabelCar' : None}
        self.s = socket.socket()
        self.s.bind((self.ip, self.port))
        print("SOCKET BINDED")

    def get_current_license_plate(self) -> str:
        return self.lastLicensePlateFound

    def wait_for_connections(self):
        self.s.listen(5)
        print("Socket is listening\n")
        while None in self.connectedDevices.values():
            print("Waiting for clients...\n")
            c,addr = self.s.accept()
            print(f"Got connection from: {addr}")
            data = c.recv(1024).decode()
            print(f"{addr} introduced as : {data}")
            if data in self.connectedDevices.keys() and self.connectedDevices[data] is None:
                self.connectedDevices[data] = (c,addr)
                self.connectedDevices[data][0].send("welcome".encode())
                print(f"Connection accepted, welcome {data}")
            else:
                c.send("Connection refused".encode())
                c.close()

    def close_connections(self):
        if None in self.connectedDevices.values():
            raise Exception("Some clients are disconnected")
        if self.connectedDevices['FindPlate'] is not None:
            self.connectedDevices['FindPlate'][0].close()
        if self.connectedDevices['LabelCar'] is not None:
            self.connectedDevices['LabelCar'][0].close()

    def waiting_for_plate(self) -> bool:
        if None in self.connectedDevices.values():
            raise Exception("Some clients are disconnected")
        data = self.connectedDevices['FindPlate'][0].recv(1024).decode()
        if data.lower() == 'found':
            self.connectedDevices['FindPlate'][0].send("ok".encode())
            data = self.connectedDevices['FindPlate'][0].recv(1024).decode()
            self.lastLicensePlateFound = data
            return True
        else:
            self.connectedDevices['FindPlate'][0].send("wrong command given".encode())
            self.lastLicensePlateFound = ''
            return False

    def send_license_plate(self) -> bool:
        if None in self.connectedDevices.values():
            raise Exception("Some clients are disconnected")
        if self.lastLicensePlateFound == '':
            raise Exception("There is no license plate to send")

        self.connectedDevices['LabelCar'][0].send("found".encode())
        data = self.connectedDevices['LabelCar'][0].recv(1024).decode()
        print(data)
        if data.lower() == 'give':
            self.connectedDevices['LabelCar'][0].send(self.lastLicensePlateFound.encode())
            self.lastLicensePlateFound = ''
            return True
        else:
            self.connectedDevices['LabelCar'][0].send("wrong command given".encode())
            return False

    def run_server(self):
        self.wait_for_connections()
        while True:
            try:
                if self.waiting_for_plate() is True:
                    current_plate = self.get_current_license_plate()
                    print(f"Found plate{current_plate}")
                    self.send_license_plate()
                else:
                    print("Something went wrong server continues it's work...")
            except:
                print("Something went wrong")
                self.close_connections()