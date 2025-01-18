from client.server import LicenseScanning

def main():
    lss = LicenseScanning('127.0.0.1',33333)
    lss.run_server()

if __name__ == '__main__':
    main()