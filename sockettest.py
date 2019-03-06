import socket
from secrets import TSHES13_IPADDR

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TSHES13_IPADDR,9750))

while True:
    data = s.recv(1024)

    if data:
        print('Received',repr(data))
    else:
        break

s.close()
