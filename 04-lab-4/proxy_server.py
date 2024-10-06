#!/usr/bin/python3

import socket
import threading

# Define the server's address and port
HOST = "127.0.0.1"
PORT = 8888
NEWLINE = "\n"

# Buffer size for receiving data
BUFFER_SIZE = 4096

CONNECT = "CONNECT"
GET = "GET"

file = open("output.txt", "w")


class Message(dict):
    def __getitem__(self, key):
        if key not in self:
            return None
        return self[key]

    def filterWhiteSpaces(self):
        for key in self.items():
            val = self[key]
            if isinstance(val, str):
                self[key] = val.strip()

    def __str__(self) -> str:
        ans = ""
        for key, value in self.items():
            ans += key + " " + value + NEWLINE

        return ans

    def connectRequest(self) -> str:
        """
        returns the string format of the proxy CONNECT request
        """
        ans = ""
        ans += f"CONNECT {self['target']} {self['httpVersion']}"

    def getRequest(self) -> str:
        """
        returns the string format of the proxy GET request
        """


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

    def parseRequest(self, request):
        pass


def parseConnectRequest(decodedDataList: list[str], message: Message):
    userAgent = decodedDataList[1]
    proxyConnection, proxyKeepAlive, *_ = decodedDataList[2].split(":")
    connection, keepAlive, *_ = decodedDataList[3].split(":")

    message["userAgent"] = userAgent
    message["proxyConnection"] = f"{proxyConnection}: close"
    message["connection"] = f"{connection}: close"
    message["hostDetails"] = decodedDataList[4]


def parseGetRequest(decodedDataList: list[str], message: Message):

    connection = "Connection"
    for data in decodedDataList:
        if connection in data:
            connectionType, _, *_ = data.split(":")
            message["connection"] = f"{connection}: close"
            break


def parseRequest(request: bytes):
    """

    CONNECT www.google.com:443 HTTP/1.1
    User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0
    Proxy-Connection: keep-alive
    Connection: keep-alive
    Host: www.google.com:443


    GET http://google.com/ HTTP/1.1
    Host: google.com
    User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0
    Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8
    Accept-Language: en-US,en;q=0.5
    Accept-Encoding: gzip, deflate
    Connection: keep-alive
    Upgrade-Insecure-Requests: 1
    Priority: u=0, i


    """
    message = Message()
    if b"\r" in request:
        data = request.split(b"\r\n")
    else:
        data = request.split(b"\n")

    decodedDataList = [dataElement.decode() for dataElement in data]

    for word in decodedDataList:
        file.write(word + NEWLINE)

    # http method
    methodLine = decodedDataList[0]

    # *_ is to ignore any remaining fields
    method, target, httpVersion, *_ = methodLine.split()

    message["method"] = method
    message["target"] = target

    if ":" in target:
        hostname, portNumber = target.split(":")
    else:
        # if port number is not mentioned, take it as 80
        hostname = target
        portNumber = 80

    message["targetHostname"] = hostname
    message["targetPortNumber"] = portNumber

    # ignoring HTTP/1.1 version and setting it to HTTP/1.0
    message["httpVersion"] = "HTTP/1.0"

    if method.upper() == CONNECT:
        parseConnectRequest(decodedDataList, message)
    elif method.upper() == GET:
        parseGetRequest(decodedDataList, message)

    message.filterWhiteSpaces()
    return message


def handle_client(client_socket):
    # Receive the client's request
    request = client_socket.recv(BUFFER_SIZE)

    message = parseRequest(request)

    file.write(str(message))

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
