#!/usr/bin/python3

import os, sys, asyncio, socket
import ast

# Global constants
HELLO, DATA, ALIVE, GOODBYE = 0, 1, 2, 3
MAGIC = 0xC461
VERSION = 1
# timeout interval in seconds
TIMEOUT_INTERVAL = 20  # debug


class SessionNonThread:
    def __init__(
        self,
        sessionId,
        serverSocket,
        serverAddress,
        clientAddress,
        asyncLock,
    ):
        self.sessionId = sessionId
        self.serverAddress = serverAddress
        self.clientAddress = clientAddress
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
        if self.isSessionAlive:
            print(f"{hex(self.sessionId)} Session closed")
            self.isSessionAlive = False
        await self.sendMessage(GOODBYE, "")

    async def processData(self, message: list):
        # process data
        magic, version, command, clientSeqNum, sessionId, serverLogicalClock = message[
            :6
        ]
        self.destroyTimer()

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
            # timer restarted inside send message
            self.printDataToTerminal(message[6])
            await self.sendMessage(ALIVE, "")

    def printDataToTerminal(self, data: str):
        print(f"{hex(self.sessionId)} [{self.sessionSeqNum}] {data}")

    async def sendMessage(self, command: int, data: str):
        loop = asyncio.get_event_loop()
        async with self.asyncLock:
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
            # await self.serverSocket.sendto(sendMessage, self.clientAddress)
            await loop.sock_sendto(self.serverSocket, sendMessage, self.clientAddress)
            self.sessionSeqNum += 1

            # start timer
            self.destroyTimer()
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
        if self.timerTask is None:
            return
        async with self.asyncLock:
            if self.isSessionAlive:
                print(f"Timeout occured, stopping session {hex(self.sessionId)}")
                self.isSessionAlive = False
        self.destroyTimer()
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

        self.serverSocket.setblocking(False)

        self.isServerRunning = True
        self.loop = None
        self.asyncLock = asyncio.Lock()
        self.sessions = {}
        self.sessionTasks = {}
        self.checkSessionAliveTasks = {}
        print(f"Server listening on port number {portNum}")

    async def asyncInput(self) -> str:
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, input)
        except EOFError or KeyboardInterrupt as e:
            return "q"

    async def handleTerminal(self):
        while True:
            try:
                userInput = await self.asyncInput()
                if userInput.strip() == "q":
                    print("q or EOF occured. exiting server")
                    await self.stopServer()
                    return

                # print(userInput)

            except Exception as e:
                await self.stopServer()

    async def handleClient(self):
        loop = asyncio.get_event_loop()
        while self.isServerRunning:
            data, clientAddress = await loop.sock_recvfrom(self.serverSocket, 4096)
            message = ast.literal_eval(data.decode())
            magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                message[:6]
            )

            assert magic == MAGIC and version == VERSION

            if sessionId not in self.sessions:
                if command != HELLO:
                    continue
                session = SessionNonThread(
                    sessionId,
                    self.serverSocket,
                    self.serverAddress,
                    clientAddress,
                    self.asyncLock,
                )
                self.sessions[sessionId] = session
                # await session.startSession(message)
                sessionStart = asyncio.create_task(session.startSession(message))

            else:
                session = self.sessions[sessionId]
                sessionTask = asyncio.create_task(session.processData(message))

    async def startServer(self):
        self.loop = asyncio.get_event_loop()

        await asyncio.gather(self.handleClient(), self.handleTerminal())

    async def stopServer(self):
        for session in self.sessions.values():
            assert isinstance(session, SessionNonThread)
            if session.isSessionAlive:
                await session.stopSession()

        os._exit(0)


if __name__ == "__main__":
    argList = sys.argv
    assert len(argList) == 2, "Use as : ./server_non_thread.py <portNum>"
    portNum = int(argList[1])
    hostname = "127.0.0.1"

    server = ServerNonThread(hostname, portNum)
    asyncio.run(server.startServer(), debug=False)
