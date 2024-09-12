#!/usr/bin/python3
import socket
import sys
import threading
import random
from enum import Enum, auto


class Command(Enum):
    HELLO = 0
    DATA = auto()
    ALIVE = auto()
    GOODBYE = auto()


MAGIC = 0xC461
VERSION = 1
LOGICAL_CLOCK = 0
SEQ_NUM = 0


def handle_sending(sock):
    global LOGICAL_CLOCK, SEQ_NUM
    while True:
        try:
            # Read user input and send to the server
            message = input("Enter message: ")
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
            sock.sendall(message_send.encode())
        except KeyboardInterrupt:
            print("Interrupted, closing connection.")
            # sock.close()
            break
        except Exception as e:
            print(f"Error in reading: {e}")
            # sock.close()
            break


def handle_receiving(sock):
    while True:
        try:
            # Receive and print messages from the server
            data = sock.recv(1024)
            # if not data:
            #     print("Connection closed by the server.")
            #     break
            print(f"Received: {data.decode()}")
        except Exception as e:
            print(f"Error in writing: {e}")
            break
    # sock.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python test_client.py <host> <port>")
        sys.exit(1)

    host = sys.argv[1]
    port = int(sys.argv[2])
    session_id = random.randint(0, 2**32 - 1)

    # Create a socket connection
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    # Start the reading and writing threads
    send_thread = threading.Thread(target=handle_sending, args=(sock,))
    receive_thread = threading.Thread(target=handle_receiving, args=(sock,))

    while True:
        try:
            send_thread.start()
            receive_thread.start()

        except:
            break

    # Wait for threads to complete
    send_thread.join()
    receive_thread.join()
