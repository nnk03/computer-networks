#!/usr/bin/python3

import sys
import threading
import socket
import ast, os

# Global constants
HELLO, DATA, ALIVE, GOODBYE = 0, 1, 2, 3
MAGIC = 0xC461
VERSION = 1
# timeout interval in seconds
TIMEOUT_INTERVAL = 20  # debug


class SessionThread:
    def __init__(
        self, sessionId, serverSocket, serverAddress, clientAddress, threadLock
    ):
        self.sessionId = sessionId
        self.serverAddress = serverAddress
        self.clientAddress = clientAddress
        self.serverSocket = serverSocket
        self.threadLock = threadLock
        self.sessionSeqNum = 0
        self.logicalClock = 0
        self.timerThread = None
        self.isSessionAlive = True
        self.lastReceived = -1

    def startSession(self, message: list):
        magic, version, command, clientSeqNum, sessionId, serverLogicalClock = message[
            :6
        ]
        self.stopTimer()

        assert magic == MAGIC and version == VERSION and clientSeqNum == 0
        if command != HELLO:
            print(f"HELLO NOT RECEIVED from session {hex(self.sessionId)}")
            self.stopSession()

        self.lastReceived = clientSeqNum
        self.printDataToTerminal("Session Created")
        self.sendMessage(HELLO, "")

    def processData(self, message: list):
        # process data
        magic, version, command, clientSeqNum, sessionId, serverLogicalClock = message[
            :6
        ]
        self.stopTimer()

        assert magic == MAGIC and version == VERSION

        if clientSeqNum != self.lastReceived + 1:
            if clientSeqNum > self.lastReceived + 1:
                for pktNumber in range(self.lastReceived + 1, clientSeqNum):
                    print(f"{hex(self.sessionId)} Lost Packet {pktNumber}")
            elif clientSeqNum == self.lastReceived:
                print(f"{hex(self.sessionId)} Duplicate Packet")
            else:
                # consider protocol error and stop the session
                self.stopSession()
                return

        self.lastReceived = clientSeqNum
        if command == GOODBYE:
            # self.sendMessage(GOODBYE, "")
            self.stopSession()

        elif command == DATA:
            self.printDataToTerminal(message[6])
            self.sendMessage(ALIVE, "")

    def stopSession(self):
        # make session alive to be false so that the main server will delete this from its dictionary
        if self.isSessionAlive:
            self.isSessionAlive = False
            print(f"{hex(self.sessionId)} Session closed")
            self.sendMessage(GOODBYE, "")

    def printDataToTerminal(self, data: str):
        print(f"{hex(self.sessionId)} [{self.sessionSeqNum}] {data}")

    def sendMessage(self, command: int, data: str):
        with self.threadLock:
            messageList = [
                MAGIC,
                VERSION,
                command,
                self.sessionSeqNum,
                self.sessionId,
                self.logicalClock,
                data,
            ]

            sendMessage = str(messageList).encode()
            assert isinstance(self.serverSocket, socket.socket)
            self.serverSocket.sendto(sendMessage, self.clientAddress)
            self.sessionSeqNum += 1

            self.stopTimer()
            self.startTimer()

    def startTimer(self):
        if self.timerThread:
            return

        self.timerThread = threading.Timer(TIMEOUT_INTERVAL, self.timeout)
        self.timerThread.start()

    def stopTimer(self):
        if self.timerThread is None:
            return

        assert isinstance(self.timerThread, threading.Timer)
        self.timerThread.cancel()
        self.timerThread = None

    def timeout(self):
        if self.timerThread is None:
            return

        with self.threadLock:
            if self.isSessionAlive:
                print(f"Timeout occured, stopping session {hex(self.sessionId)}")
                # if self.timerThread:
                #     self.timerThread.cancel()
                if self.timerThread:
                    self.timerThread.cancel()
                self.timerThread = None
        self.stopSession()


class ServerThread:
    def __init__(self, hostname="127.0.0.1", portNum=1234):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverAddress = (hostname, portNum)
        self.serverSocket.bind(self.serverAddress)

        # self.serverSocket.setblocking(False)

        self.isServerRunning = True
        self.loop = None
        self.threadLock = threading.Lock()
        self.sessions = {}
        self.sessionTasks = {}
        self.checkSessionAliveTasks = {}
        print(f"Server listening on port number {portNum}")

    def handleTerminal(self):
        while True:
            try:
                userInput = input()
                if userInput.strip() == "q":
                    print("q or EOF occurred. Exiting server")
                    self.stopServer()

            except Exception as e:
                self.stopServer()

    def handleClient(self):
        while self.isServerRunning:
            data, clientAddress = self.serverSocket.recvfrom(4096)
            message = ast.literal_eval(data.decode())
            magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                message[:6]
            )

            assert magic == MAGIC and version == VERSION

            if sessionId not in self.sessions:
                if command != HELLO:
                    continue
                session = SessionThread(
                    sessionId,
                    self.serverSocket,
                    self.serverAddress,
                    clientAddress,
                    self.threadLock,
                )
                self.sessions[sessionId] = session
                sessionThread = threading.Thread(
                    target=session.startSession, args=(message,)
                )
                sessionThread.start()

            else:
                session = self.sessions[sessionId]
                sessionThread = threading.Thread(
                    target=session.processData, args=(message,)
                )
                sessionThread.start()

    def startServer(self):
        terminalThread = threading.Thread(target=self.handleTerminal)
        serverThread = threading.Thread(target=self.handleClient)

        terminalThread.start()
        serverThread.start()

    def stopServer(self):
        for session in self.sessions.values():
            assert isinstance(session, SessionThread)
            if session.isSessionAlive:
                session.stopSession()

        os._exit(0)


if __name__ == "__main__":
    argList = sys.argv
    assert len(argList) == 2, "Use as : ./server_non_thread.py <portNum>"
    portNum = int(argList[1])
    hostname = "127.0.0.1"

    server = ServerThread(hostname, portNum)
    server.startServer()
