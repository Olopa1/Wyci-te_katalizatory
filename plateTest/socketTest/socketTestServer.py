from client.server import LicenseScanning

def main():
    lss = LicenseScanning(ip = '127.0.0.1',port = 33333,db_info = ['localhost','root','','wyciete_katalizatory'])
    lss.run_server()

if __name__ == '__main__':
    main()