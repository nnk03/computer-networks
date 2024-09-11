#!/usr/bin/python3

import os, sys, asyncio, socket
from random import randint
import ast

# Global constants
HELLO, DATA, ALIVE, GOODBYE = 0, 1, 2, 3
MAGIC = 0xC461
VERSION = 1
# timeout interval in seconds
TIMEOUT_INTERVAL = 20


class Session:
    def __init__(self, sessionId, serverSocket, serverAddress, asyncLock):
        self.sessionId = sessionId
        self.serverAddress = serverAddress
        self.serverSocket = serverSocket
        self.asyncLock = asyncLock
        self.sessionSeqNum = 0
        self.logicalClock = 0
        self.timerTask = None
        self.isSessionAlive = True
        self.lastReceived = -1

    async def startSession(self, message: list):
        magic, version, command, clientSeqNum, sessionId, serverLogicalClock = message[
            :6
        ]

        assert magic == MAGIC and version == VERSION and clientSeqNum == 0
        if command != HELLO:
            print(f"HELLO NOT RECEIVED from session {hex(self.sessionId)}")
            await self.stopSession()

        self.lastReceived = clientSeqNum
        self.printDataToTerminal("Session Created")
        await self.sendMessage(HELLO, "")

    async def stopSession(self):
        # make session alive to be false so that the main server will delete this from its dictionary
        self.isSessionAlive = False
        print(f"{hex(self.sessionId)} Session closed")
        await self.sendMessage(GOODBYE, "")

    async def processData(self, message: list):
        # process data
        magic, version, command, clientSeqNum, sessionId, serverLogicalClock = message[
            :6
        ]

        assert magic == MAGIC and version == VERSION

        if clientSeqNum != self.lastReceived + 1:
            if clientSeqNum > self.lastReceived + 1:
                for pktNumber in range(self.lastReceived + 1, clientSeqNum):
                    print(f"{hex(self.sessionId)} Lost Packet {pktNumber}")
            elif clientSeqNum == self.lastReceived:
                print(f"{hex(self.sessionId)} Duplicate Packet")
            else:
                # consider protocol error and stop the session
                await self.stopSession()

        self.lastReceived = clientSeqNum
        if command == GOODBYE:
            await self.sendMessage(GOODBYE, "")
            await self.stopSession()

        elif command == DATA:
            self.printDataToTerminal(message[6])
            await self.sendMessage(ALIVE, "")

    def printDataToTerminal(self, data: str):
        print(f"{hex(self.sessionId)} [{self.sessionSeqNum}] {data}")

    async def sendMessage(self, command: int, data: str):
        with self.asyncLock:
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
            self.serverSocket.sendto(sendMessage, self.serverAddress)
            self.sessionSeqNum += 1

            # start timer
            self.createTimer()

    def createTimer(self):
        if self.timerTask:
            return

        self.timerTask = asyncio.create_task(self.startTimer())

    def destroyTimer(self):
        if not self.timerTask:
            return

        self.timerTask.cancel()
        self.timerTask = None

    async def timeout(self):
        print(f"Timeout occured, stopping session {hex(self.sessionId)}")
        await self.stopSession()

    async def startTimer(self):
        # timer start
        await asyncio.sleep(TIMEOUT_INTERVAL)
        # timer finish
        await self.timeout()


class ServerNonThread:
    def __init__(self, hostname="127.0.0.1", portNum=1234):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverAddress = (hostname, portNum)
        self.serverSocket.bind(self.serverAddress)
        # self.serverSocket.setblocking(False)
        self.isServerRunning = True
        self.asyncLock = asyncio.Lock()
        self.sessions = {}
        self.sessionTasks = {}
        self.checkSessionAliveTasks = {}
        print(f"Server listening on port number {portNum}")

    async def handleTerminal(self):
        loop = asyncio.get_event_loop()
        while True:
            try:
                inputTerminal = await loop.run_in_executor(None, sys.stdin.readline)
                print(inputTerminal)
                if inputTerminal.strip() == "q":
                    # stop the server
                    await self.stopServer()
                    return

            except EOFError or KeyboardInterrupt as e:
                print(e)
                break

    async def handleClient(self):
        while self.isServerRunning:
            data, clientAddress = self.serverSocket.recvfrom(4096)
            message = ast.literal_eval(data.decode())
            magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                message[:6]
            )

            assert magic == MAGIC and version == VERSION

            sessionTask = None

            if sessionId not in self.sessions:
                self.sessions[sessionId] = Session(
                    sessionId, self.serverSocket, self.serverAddress, self.asyncLock
                )
                session = self.sessions[sessionId]
                sessionTask = asyncio.create_task(session.startSession(message))
                self.sessionTasks[sessionId] = sessionTask
                checkSessionTask = asyncio.create_task(
                    self.checkSessionAlive(sessionId)
                )
                self.checkSessionAliveTasks[sessionId] = checkSessionTask
            else:
                session = self.sessions[sessionId]
                sessionTask = asyncio.create_task(session.processData(message))

    async def checkSessionAlive(self, sessionId):
        while True:
            if sessionId not in self.sessions:
                break
            session = self.sessions[sessionId]
            assert isinstance(session, Session)
            if not session.isSessionAlive:
                del self.sessions[sessionId]

    async def startServer(self):
        clientTask = asyncio.create_task(self.handleClient())
        terminalTask = asyncio.create_task(self.handleTerminal())

        # while True:
        done, pending = await asyncio.wait(
            [clientTask, terminalTask], return_when=asyncio.FIRST_COMPLETED
        )
        if done == terminalTask:
            await self.stopServer()
            return

    async def stopServer(self):
        for session in self.sessions.values():
            await session.stopSession()

        os._exit(0)


if __name__ == "__main__":
    argList = sys.argv
    assert len(argList) == 2, "Use as : ./server_non_thread.py <portNum>"
    portNum = int(argList[1])
    hostname = "127.0.0.1"

    server = ServerNonThread(hostname, portNum)
    asyncio.run(server.startServer())
