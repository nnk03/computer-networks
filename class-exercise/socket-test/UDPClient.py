from socket import *

serverName = "localhost"  # exact ip address of the server
serverPort = 12000
clientSocket = socket(AF_INET, SOCK_DGRAM)

message = input("Input Lowercase sentence")

clientSocket.sendto(message.encode(), (serverName, serverPort))

receivedMessage, serverAddress = clientSocket.recvfrom(2048)

print(receivedMessage.decode())

clientSocket.close()
