import os
import time
import socket
import sys
import threading
os.system("echo '" + "220" + ";" + "' | pdsend 3001")
os.system("echo '" + "Arp" + ";" + "' | pdsend 3002")
# s = socket.socket()
# host = socket.gethostname()
# port = 3000

# s.connect((host, port))


def serverWatcher():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('localhost', 3003)
    print(f'starting up on {server_address[0]} port {server_address[1]}')

    sock.bind(server_address)
    sock.listen(1)
  
    while True:
        print('waiting for a connection')
        connection, client_address = sock.accept()
        try:
                print('client connected:', client_address)
                while True:
                    data = connection.recv(16)
                    data = data.decode("utf-8")
                    data = data.replace('\n', '').replace(
                        '\t', '').replace('\r', '').replace(';', '')
                    print(f'received {data}')
                    if not data:
                        break
        finally:
            connection.close()
watcherThread = threading.Thread(target=serverWatcher)
watcherThread.start()
while True:
    foundObjs = ""
    # foundObjs += str(1) + " " + str(0.0631249) + " "
    # foundObjs += str(0) + " " + str(0.03) + " "
    # foundObjs += str(2) + " " + str(0.09) + " "
    # foundObjs += str(9) + " " + str(0.9) + " "
    # foundObjs += str(3) + " " + str(0.4) + " "
    # foundObjs += str(3) + " " + str(0.5) + " "
    #foundObjs += str(3) + " " + str(0.0631249) + " "
    #foundObjs += str(2) + " " + str(0.03) + " "
    foundObjs += str(0) + " " + str(0.5) + " "
    foundObjs += str(1) + " " + str(0.2) + " "
    foundObjs += str(2) + " " + str(0.1) + " "
    foundObjs += str(5) + " " + str(0.6) + " "
    foundObjs += str(0) + " " + str(0.7) + " "
    #foundObjs += str(2) + " " + str(0.9) + " "
   # foundObjs += str(3) + " " + str(0.4) + " "
    # foundObjs += str(4) + " " + str(0.5) + " "
    #foundObjs += str(5) + " " + str(0.5) + " "
    # foundObjs += str(6) + " " + str(0.5) + " "
    #foundObjs += str(0) + " " + str(0) + " "
    os.system("echo '" + str(foundObjs) + ";" + "' | pdsend 3000")
    time.sleep(1)
    # foundObjs = ""
    # foundObjs += str(9) + " " + str(0.031249) + " "
    # foundObjs += str(0) + " " + str(0.03) + " "
    # foundObjs += str(1) + " " + str(0.09) + " "
    # foundObjs += str(2) + " " + str(0.9) + " "
    # foundObjs += str(3) + " " + str(0.4) + " "
    # foundObjs += str(4) + " " + str(0.5) + " "
    # foundObjs += str(5) + " " + str(0.5) + " "
    # foundObjs += str(6) + " " + str(0.5) + " "
    # os.system("echo '" + str(foundObjs) + ";" + "' | pdsend 3000")

#os.system("echo '" + str(1)  + " " + str(0.222) + ";" + "' | pdsend 3000")
