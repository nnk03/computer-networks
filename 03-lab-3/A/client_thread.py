#!/usr/bin/python3

import socket, threading, os, sys
from random import randint
import ast

# Global constants
HELLO, DATA, ALIVE, GOODBYE = 0, 1, 2, 3
MAGIC = 0xC461
VERSION = 1
# timeout interval in seconds
TIMEOUT_INTERVAL = 10


class ClientThread:
    def __init__(self, hostname="127.0.0.1", portNum=1234) -> None:
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverAddress = (hostname, portNum)
        self.sessionId = randint(0, 2**31 - 1)
        self.clientSeqNum = 0
        self.threadLock = threading.Lock()
        # what is logical clock doing ?
        self.logicalClock = 0
        self.isClientRunning = True
        self.timer = None

    def startClient(self):
        # Send HELLO and wait for response
        self.sendMessage(HELLO, "")
        # timer is automatically started if there are no existing timers
        waitForServerHelloThread = threading.Thread(target=self.waitForServerHello)
        waitForServerHelloThread.start()

        listenForServerThread = threading.Thread(target=self.listenForServer)
        listenForServerThread.start()

        helloReceived = False

        try:
            while self.isClientRunning:
                inputData = input("Enter Input : ")
                if inputData == "q":
                    self.stopClient()
                    return

                # wait for server hello and then only send
                if not helloReceived:
                    waitForServerHelloThread.join()
                    helloReceived = True
                # print(inputData)  # debug
                # send the data to server
                self.sendMessage(DATA, inputData)

        except EOFError as e:
            self.stopClient()

        finally:
            self.stopClient()
            # listenForServerThread.join()

    def stopClient(self):
        # Send goodbye before terminating client
        self.sendMessage(GOODBYE, "")
        self.isClientRunning = False
        print("Terminating Client")
        os._exit(0)

    def listenForServer(self):
        while self.isClientRunning:
            try:
                data, serverAddress = self.clientSocket.recvfrom(4096)
                message = ast.literal_eval(data.decode())
                magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                    message[:6]
                )

                assert magic == MAGIC and version == VERSION

                if command == ALIVE:
                    # print("ALIVE")
                    self.stopTimer()
                    pass
                elif command == GOODBYE:
                    print("SERVER has terminated the session")
                    self.stopClient()
                    return

            except:
                pass

    def waitForServerHello(self):
        while self.isClientRunning:
            try:
                data, serverAddress = self.clientSocket.recvfrom(4096)
                message = ast.literal_eval(data.decode())

                magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                    message[:6]
                )
                assert magic == MAGIC and version == VERSION

                if command == HELLO and self.sessionId == sessionId:
                    print("Received Hello from Server")
                    self.stopTimer()
                    # self.startTimer()
                    return

            except EOFError or KeyboardInterrupt as e:
                self.stopClient()

            except AssertionError as e:
                print(f"Invalid Response {e}")

    def sendMessage(self, command: int, data: str):
        with self.threadLock:
            messageList = [
                MAGIC,
                VERSION,
                command,
                self.clientSeqNum,
                self.sessionId,
                self.logicalClock,
                data,
            ]

            sendMessage = str(messageList).encode()
            self.clientSocket.sendto(sendMessage, self.serverAddress)

            self.clientSeqNum += 1
            # restart timer
            # self.stopTimer()
            self.startTimer()

    def startTimer(self):
        if self.timer:
            # already timer running
            return
        self.timer = threading.Timer(TIMEOUT_INTERVAL, self.timeout)
        self.timer.start()

    def stopTimer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = None

    def timeout(self):
        print("TIMEOUT occured. Terminating client....")
        self.stopClient()


if __name__ == "__main__":
    argList = sys.argv
    assert len(argList) == 3, "Use as : ./client_thread.py <hostname> <portNum>"
    hostname = argList[1]
    portNum = int(argList[2])

    client = ClientThread(hostname, portNum)
    client.startClient()
