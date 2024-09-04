import socket
import sys
import select


def main():
    serverPort = 12000

    sessionList = []

    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(("localhost", serverPort))
    serverSocket.listen()


if __name__ == "__main__":
    main()
