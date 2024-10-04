#!/usr/bin/python3

import socket
import threading

# Define the server's address and port
HOST = "127.0.0.1"
PORT = 8888

# Buffer size for receiving data
BUFFER_SIZE = 4096

file = open("output.txt", "w")


class ProxyServer:
    def __init__(self, portNumber, host="127.0.0.1") -> None:
        self.host = host
        self.portNumber = portNumber
        self.proxyAddress = (host, portNumber)

    def start(self):
        pass

    def stop(self):
        pass

    def handleClient(self):
        pass

    def handleServer(self):
        pass

    def sendMessage(self, message):
        pass


def handle_client(client_socket):
    # Receive the client's request
    request = client_socket.recv(BUFFER_SIZE)

    data = request.split(b"\r\n")

    for i in range(len(data)):
        data[i] = data[i].decode()

    for word in data:
        file.write(word)
        file.write("\n")
    file.write("\n")

    # # Extract the requested destination from the request
    # request_line = request.split(b"\n")[0]
    # url = request_line.split(b" ")[1]
    #
    # # Check if the URL is absolute or relative
    # http_position = url.find(b"://")
    # if http_position == -1:
    #     host_start = 0
    # else:
    #     host_start = http_position + 3
    #
    # # Get the host and port
    # host_end = url.find(b"/", host_start)
    # if host_end == -1:
    #     host_end = len(url)
    #
    # host = url[host_start:host_end]
    #
    # # Try connecting to the destination server
    # try:
    #     # Create a new socket for the destination server
    #     proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     proxy_socket.connect((host.decode(), 80))
    #
    #     # Forward the client's request to the destination server
    #     proxy_socket.send(request)
    #
    #     # Receive the response from the destination server
    #     while True:
    #         response = proxy_socket.recv(BUFFER_SIZE)
    #         if len(response) > 0:
    #             # Forward the response back to the client
    #             client_socket.send(response)
    #         else:
    #             break
    # except Exception as e:
    #     print(f"Error: {e}")
    # finally:
    #     # Close the sockets
    #     proxy_socket.close()
    #     client_socket.close()


def start_proxy_server():
    # Create a server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"[*] Proxy server listening on {HOST}:{PORT}")

    # Accept incoming connections
    while True:
        client_socket, addr = server_socket.accept()
        print(f"[*] Received connection from {addr}")

        # Handle the client's request in a new thread
        client_handler = threading.Thread(target=handle_client, args=(client_socket,))
        client_handler.start()


if __name__ == "__main__":
    try:
        start_proxy_server()
    except:
        file.close()
    # proxyServer = ProxyServer(portNumber=PORT, host=HOST)
