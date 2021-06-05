"""
Module with first steps about the RCSS connection.
"""

# imports
import socket

# variables
msgFromClient = "(init YellowTeam (version 15))"
bytesToSend = str.encode(msgFromClient)
port = 6000
serverAddressPort = ("192.168.2.116", port)
# TODO: change size to a normal value
bufferSize = 102400


# Create a UDP socket at client side
UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Send to server using created UDP socket
UDPClientSocket.sendto(bytesToSend, serverAddressPort)
print(bytesToSend)

i = 0

while True:
    msgFromServer = UDPClientSocket.recvfrom(bufferSize)
    print(msgFromServer)
    print ('\n-----------------------\n')


    msg = input('Befehl: ')
    bytesToSend = str.encode(msg)

    if port == 6000:
        port = int(input('PORT: '))
        serverAddressPort = ("192.168.2.116", port)
    UDPClientSocket.sendto(bytesToSend, serverAddressPort)
    print(serverAddressPort)
    print(bytesToSend)



