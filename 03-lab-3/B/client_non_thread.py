#!/usr/bin/python3

import socket, asyncio, os, sys
from random import randint
import ast

# Global constants
HELLO, DATA, ALIVE, GOODBYE = 0, 1, 2, 3
MAGIC = 0xC461
VERSION = 1
# timeout interval in seconds
TIMEOUT_INTERVAL = 10


class ClientNonThread:
    def __init__(self, hostname="127.0.0.1", portNum=1234) -> None:
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverAddress = (hostname, portNum)
        self.sessionId = randint(0, 2**31 - 1)
        self.clientSeqNum = 0
        self.asyncLock = asyncio.Lock()
        self.logicalClock = 0
        self.isClientRunning = True
        self.timerTask = None

    async def waitForServerHello(self):
        loop = asyncio.get_event_loop()
        while self.isClientRunning:
            try:
                data, serverAddress = await loop.sock_recvfrom(self.clientSocket, 4096)
                message = ast.literal_eval(data.decode())
                magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                    message[:6]
                )

                assert magic == MAGIC and version == VERSION
                if command == HELLO and self.sessionId == sessionId:
                    print("Received HELLO from server")
                    self.destroyTimer()
                    return

            except EOFError or KeyboardInterrupt as e:
                await self.stopClient()

            except AssertionError as e:
                print(f"Invalid Response {e}")

    async def listenForServer(self):
        loop = asyncio.get_event_loop()
        while self.isClientRunning:
            try:
                # data, serverAddress = await loop.sock_recvfrom(self.clientSocket, 4096)
                data, serverAddress = await asyncio.to_thread(
                    self.clientSocket.recvfrom, 4096
                )
                message = ast.literal_eval(data.decode())
                magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
                    message[:6]
                )

                assert magic == MAGIC and version == VERSION

                if command == ALIVE:
                    self.destroyTimer()
                    pass
                elif command == GOODBYE:
                    print("Server has terminated the session")
                    await self.stopClient()
                    return

            except EOFError or KeyboardInterrupt as e:
                await self.stopClient()

            except AssertionError as e:
                print(f"Invalid Response {e}")

    async def asyncInput(self) -> str:
        loop = asyncio.get_event_loop()
        try:
            # return await loop.run_in_executor(None, lambda: input("Enter input : "))
            return await loop.run_in_executor(None, input)
        except EOFError or KeyboardInterrupt as e:
            return "q"

    async def handleInput(self):
        try:
            while self.isClientRunning:
                inputData = await self.asyncInput()
                if inputData.strip() == "q":
                    await self.stopClient()
                    return

                # hello would already have been received by now

                await self.sendMessage(DATA, inputData)

        except EOFError as e:
            await self.stopClient()

        finally:
            await self.stopClient()

    async def startClient(self):
        await self.sendMessage(HELLO, "")
        await self.waitForServerHello()

        await asyncio.gather(self.listenForServer(), self.handleInput())

        # handleInputTask = asyncio.create_task(self.handleInput())
        # loop = asyncio.get_event_loop()
        # while self.isClientRunning:
        #     print("LISTENING FOR SERVER")
        #     try:
        #         # data, serverAddress = await loop.sock_recvfrom(self.clientSocket, 4096)
        #         data, serverAddress = await asyncio.to_thread(
        #             self.clientSocket.recvfrom, 4096
        #         )
        #         message = ast.literal_eval(data.decode())
        #         magic, version, command, serverSeqNum, sessionId, serverLogicalClock = (
        #             message[:6]
        #         )
        #
        #         assert magic == MAGIC and version == VERSION
        #
        #         if command == ALIVE:
        #             print("ALIVE")
        #             self.destroyTimer()
        #             pass
        #         elif command == GOODBYE:
        #             print("Server has terminated the session")
        #             await self.stopClient()
        #             return
        #
        #     except EOFError or KeyboardInterrupt as e:
        #         await self.stopClient()
        #
        #     except AssertionError as e:
        #         print(f"Invalid Response {e}")
        #
        # await handleInputTask
        # await asyncio.gather(self.listenForServer(), self.handleInput())
        # _ = asyncio.create_task(self.handleInput())
        # _ = asyncio.create_task(self.listenForServer())

    async def sendMessage(self, command: int, data: str):
        loop = asyncio.get_event_loop()
        async with self.asyncLock:
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
            await loop.sock_sendto(self.clientSocket, sendMessage, self.serverAddress)

            self.clientSeqNum += 1

            # restart timer ??
            # self.destroyTimer()
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
        print(f"Timeout occured, stopping session {hex(self.sessionId)}")
        async with self.asyncLock:
            self.isClientRunning = False
        self.destroyTimer()
        await self.stopClient()

    async def stopClient(self):
        await self.sendMessage(GOODBYE, "")
        self.isClientRunning = False
        print("Terminating Client")
        os._exit(0)

    async def startTimer(self):
        # timer start
        await asyncio.sleep(TIMEOUT_INTERVAL)
        # timer finish
        await self.timeout()


if __name__ == "__main__":
    argList = sys.argv
    assert len(argList) == 3, "Use as : ./client_thread.py <hostname> <portNum>"
    hostname = argList[1]
    portNum = int(argList[2])

    client = ClientNonThread(hostname, portNum)
    asyncio.run(client.startClient())
