import mysql.connector

db_conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='wyciete_katalizatory'
)

coursor = db_conn.cursor()

coursor.execute("SELECT * FROM Cars")

myresult = coursor.fetchall()

print(myresult)