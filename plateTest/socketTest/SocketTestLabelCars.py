from time import sleep
from utils.message import LabelingClient
import mysql.connector
class DbActions:
    def __init__(self,db_conf):
        self.db_info = db_conf
        self.db_conn = mysql.connector.connect(
            host=self.db_info[0],
            user=self.db_info[1],
            password=self.db_info[2],
            database=self.db_info[3]
        )

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

def main():
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
                #print(f"Found {len(recived)} out of {len(expected_plates)}")
                tries += 1
        except:
            break
    sleep(120)
    lc.close_connection()
    print(f"Program ended with {tries} tries")


main()