#!/usr/bin/python3

import asyncio
import socket
import time
import sys
import json
import ast
from enum import Enum, auto

"""
Message is list of the fields
[ magic #, version, command, seq #, session id, logical clock]
"""


"""
Map from session id to session
"""
SESSIONS = {}
MAGIC = 0xC461
VERSION = 1
LOGICAL_CLOCK = 0
SEQ_NUM = 0


class Command(Enum):
    HELLO = 0
    DATA = auto()
    ALIVE = auto()
    GOODBYE = auto()


class Session:
    def __init__(self, session_id, writer) -> None:
        self.session_id = session_id
        self.writer = writer
        self.timer = 0
        self.threshold = 10
        self.timer_task = None
        self.timer_task = asyncio.create_task(self.run_timer())

    async def restart_timer(self):
        self.timer_task = asyncio.create_task(self.run_timer())

    async def run_timer(self):
        while self.timer < self.threshold:
            await asyncio.sleep(1)
            self.timer += 1

        await self.timeout()

    async def timeout(self):
        print(f"Session {self.session_id} TIMEOUT")


async def handle_client(reader, writer):
    addr = writer.get_extra_info("peername")
    print(f"Client connected from {addr}")

    try:
        data = await reader.read(1024)
        if not data:
            print(f"Client {addr} disconnected")

        message = data.decode()
        message_received = ast.literal_eval(message)

        magic_number = int(message_received[0])
        version = int(message_received[1])
        command = message_received[2]
        seq_number = message_received[3]
        session_id = message_received[4]
        logical_clock = message_received[5]
        assert magic_number == MAGIC and version == VERSION

        # print(f"Received from client {addr} : {data}")
        if session_id not in SESSIONS:
            assert command == Command.HELLO.value
            SESSIONS[session_id] = Session(session_id, writer)

        # let the session handle the packet
        # session = SESSIONS[session_id]
        # session.handle()

        # response = "alive"
        writer.write(response.encode())
        await writer.drain()

    except (asyncio.CancelledError, EOFError):
        return

    except Exception as e:
        print(f"Error handling client {addr} : {e}")

    # writer.close()
    # await writer.wait_closed()


async def handle_terminal_input():
    loop = asyncio.get_running_loop()
    while True:
        try:
            input_future = loop.run_in_executor(None, sys.stdin.readline)
            input_data = await input_future
            if not input_data:
                print("EOF from terminal input.")
                return
            input_data = input_data.strip()
            if input_data == "q":
                return
            print(f"Received from terminal: {input_data}")
            # Perform some action based on terminal input
        except (asyncio.CancelledError, EOFError):
            break


async def main(portNum):

    host = "127.0.0.1"
    serverAddress = (host, portNum)

    server = await asyncio.start_server(handle_client, host, portNum)
    addr = server.sockets[0].getsockname()
    print(f"Server on {addr}")

    try:
        async with server:
            # Run both server and terminal input handling concurrently
            server_task = asyncio.create_task(server.serve_forever())
            terminal_task = asyncio.create_task(handle_terminal_input())

            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [server_task, terminal_task], return_when=asyncio.FIRST_COMPLETED
            )

            # Handle terminal input completion (EOF)
            if terminal_task in done:
                print("Terminal input ended. Shutting down the server.")
                server_task.cancel()  # Request cancellation of the server task

                try:
                    await server_task  # Ensure server task is properly awaited
                except asyncio.CancelledError:
                    pass  # Server task was cancelled

    except EOFError:
        print("Server shutting down due to EOF.")
    finally:
        server.close()
        await server.wait_closed()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("USE AS : ./server_non_thread.py <portnum>")

    else:
        portNum = int(sys.argv[1])
        asyncio.run(main(portNum))
