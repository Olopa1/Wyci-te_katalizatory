import socket
import mysql.connector

class LicenseScanning:

    def __init__(self, ip, port,db_info):
        self.db_info = db_info
        self.ip = ip
        self.port = port
        self.lastLicensePlateFound = ''
        self.connectedDevices = {'FindPlate': None, 'LabelCar': None}
        self.s = socket.socket()
        self.db_conn = mysql.connector.connect(
            host=self.db_info[0],
            user=self.db_info[1],
            password=self.db_info[2],
            database=self.db_info[3]
        )
        self.on_parking = self.get_plates_to_find("1")
        self.off_parking = self.get_plates_to_find("0")
        try:
            self.s.bind((self.ip, self.port))
            print("Socket bound successfully")
        except OSError as e:
            print(f"Error binding socket: {e}")
            raise

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

    def get_current_license_plate(self) -> str:
        return self.lastLicensePlateFound

    def wait_for_connections(self):
        self.s.listen(5)
        print("Socket is listening\n")
        while None in self.connectedDevices.values():
            try:
                print("Waiting for clients...\n")
                c, addr = self.s.accept()
                print(f"Got connection from: {addr}")
                data = c.recv(1024).decode()
                print(f"{addr} introduced as: {data}")
                if data in self.connectedDevices.keys() and self.connectedDevices[data] is None:
                    self.connectedDevices[data] = (c, addr)
                    self.connectedDevices[data][0].send("welcome".encode())
                    print(f"Connection accepted, welcome {data}")
                else:
                    c.send("Connection refused".encode())
                    c.close()
            except OSError as e:
                print(f"Socket error while waiting for connections: {e}")

    def close_connections(self):
        for key, conn in self.connectedDevices.items():
            if conn is not None:
                try:
                    conn[0].close()
                except OSError as e:
                    print(f"Error closing connection for {key}: {e}")

    def waiting_for_plate(self) -> bool:
        try:
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
        except ConnectionResetError:
            print("Connection reset by FindPlate client.")
        except socket.timeout:
            print("Timeout while waiting for plate.")
        except OSError as e:
            print(f"Socket error while waiting for plate: {e}")
        return False

    def send_license_plate(self) -> bool:
        try:
            if None in self.connectedDevices.values():
                raise Exception("Some clients are disconnected")
            if self.lastLicensePlateFound == '':
                raise Exception("There is no license plate to send")

            self.connectedDevices['LabelCar'][0].send("found".encode())
            data = self.connectedDevices['LabelCar'][0].recv(1024).decode()
            if data.lower() == 'give':
                self.connectedDevices['LabelCar'][0].send(self.lastLicensePlateFound.encode())
                self.lastLicensePlateFound = ''
                return True
            else:
                self.connectedDevices['LabelCar'][0].send("wrong command given".encode())
                return False
        except ConnectionResetError:
            print("Connection reset by LabelCar client.")
        except socket.timeout:
            print("Timeout while sending license plate.")
        except OSError as e:
            print(f"Socket error while sending license plate: {e}")
        return False

    def run_server(self):
        self.wait_for_connections()
        while True:
            try:
                if self.waiting_for_plate() is True:
                    current_plate = self.get_current_license_plate()
                    print(f"Car with plate: {current_plate} entering the parking")
                    print(f"Cars on parking: {self.on_parking}")
                    self.send_license_plate()
                else:
                    print("Something went wrong. Server continues...")
            except Exception as e:
                print(f"Unexpected error in server: {e}")
                break
        self.close_connections()