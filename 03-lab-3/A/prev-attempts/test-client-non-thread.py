#!/usr/bin/python3
import asyncio
import sys
from enum import Enum, auto
import random


class Command(Enum):
    HELLO = 0
    DATA = auto()
    ALIVE = auto()
    GOODBYE = auto()


"""
Message is list of the fields
[ magic #, version, command, seq #, session id, logical clock]
"""

MAGIC = 0xC461
VERSION = 1
LOGICAL_CLOCK = 0
SEQ_NUM = 0


async def test_client(host, port, session_id):
    global LOGICAL_CLOCK, SEQ_NUM
    reader, writer = await asyncio.open_connection(host, port)

    while True:
        try:
            # Send a message to the server
            message = input("Enter message ")
            message = [
                MAGIC,
                VERSION,
                Command.DATA.value,
                SEQ_NUM,
                LOGICAL_CLOCK,
                message,
            ]
            message_send = str(message)
            SEQ_NUM += 1
            LOGICAL_CLOCK += 1

            print(f"Sending message: {message}")
            writer.write(message_send.encode())
            await writer.drain()
        except:
            break

    print("Message sent. Closing connection.")

    # Close the connection
    writer.close()
    await writer.wait_closed()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_client.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    session_id = random.randint(0, 2**32 - 1)

    asyncio.run(test_client(host, port, session_id))
