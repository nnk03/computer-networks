#!/usr/bin/python3
from sys import argv
import socket
import threading

LOG_FILE = open("./output.txt", "w")
LOCK = threading.Lock()

CONNECT = "CONNECT"
GET = "GET"
UNKNOWN_METHOD = "UNKNOWN_METHOD"


def logOutput(message):
    with LOCK:
        LOG_FILE.write(message)
        LOG_FILE.write("\n")


STATUS_CODES = {
    "bad-gateway": "HTTP/1.0 502 Bad Gateway\r\n\r\n".encode(),
    "ok": "HTTP/1.0 200 OK\r\n\r\n".encode(),
}


class Message:
    def __init__(self, request: bytes):
        self.request = request
        self.processRequest(request)

    def processRequest(self, request: bytes):
        self.requestSplit = request.split(b"\r\n")

        # annotation, that requestSplit is a varaible which is a list of bytes
        # self.requestSplit: list[bytes]
        self.requestLine = self.requestSplit[0].decode()
        # remaining body after saving the requestLine which will be displayed in the terminal
        self.body = request[len(self.requestLine) :]

        # method, target and version will be found in the requestLine (which is same as the request line)
        # for example CONNECT www.google.com:443 HTTP/1.1
        # *_ is to ignore any other fields, if any
        self.method, self.target, self.version, *_ = self.requestLine.split()

        # downgrading the HTTP version, in order to avoid persistent connectoin
        self.version = "HTTP/1.0"

        targetHost = ""
        targetPortNumber = 0
        headerAndBody = ""
        self.targetHost = targetHost
        self.targetPortNumber = targetPortNumber
        self.headerAndBody = headerAndBody

        for data in self.requestSplit[1:]:
            line = data.decode()

            """
            check for Host
            example : "Host: www.google.com:443"
            """

            if "host" in line.lower():
                # we need to take www.google.com:443, separately
                # stop at the first ':'
                hostColonPort = data.split(b":", 1)
                hostColonPort = hostColonPort[1].decode().strip()

                if hostColonPort:
                    if ":" in hostColonPort:
                        targetHost, targetPortNumber = hostColonPort.split(":")
                        targetPortNumber = int(targetPortNumber)
                        self.targetHost = targetHost
                        self.targetPortNumber = targetPortNumber
                    else:
                        targetHost = hostColonPort
                        self.targetHost = targetHost

            if "keep-alive" in line.lower():
                # changing 'keep-alive' to 'close' to not allow persistent connections
                line = line.replace("keep-alive", "close")

            headerAndBody += line + "\r\n"

        # suppose, host and port details were not extracted
        if "://" in self.targetHost:
            # example : 'https://www.google.com:443'
            httpOrHttps, hostAndPort = self.targetHost.split("//")
            if httpOrHttps == "http:":
                targetPortNumber = 80
            elif httpOrHttps == "https:":
                targetPortNumber = 443

            if ":" in hostAndPort:
                targetHost, targetPortNumber = hostAndPort.split(":")
                targetPortNumber = int(targetPortNumber)
            else:
                targetHost = hostAndPort

        self.targetHost = targetHost
        self.targetPortNumber = int(targetPortNumber)

        self.encodedHeaderAndBody = headerAndBody.encode()

    def isGetRequest(self):
        return self.method.upper() == GET

    def getEncodedHeaderAndBody(self):
        return self.encodedHeaderAndBody

    def getEncodedRequestLine(self) -> bytes:
        # self.version will be HTTP/1.0
        requestLine = f"{self.method} {self.target} {self.version}"
        return requestLine.encode()


class ProxyServer:
    def __init__(self, hostName: str, portNumber: int) -> None:
        self.hostName = hostName
        self.portNumber = portNumber
        self.socket = None
        self.lock = LOCK

    def logToTerminal(self, message: str):
        print(f">>> {message}")

    def connectionThread(self, sourceConnection, destConnection):
        assert isinstance(sourceConnection, socket.socket) and isinstance(
            destConnection, socket.socket
        )

        try:
            while True:
                data = sourceConnection.recv(1024)
                if not data:
                    break
                destConnection.send(data)
        except Exception as e:
            logOutput(
                f"ERROR : Exception {e} in connection between {sourceConnection} and {destConnection}"
            )
            return

    def proxyThread(self, clientProxyConnection: socket.socket):
        # intercept message from the browser
        data = b""

        while not data[-4:] == b"\r\n\r\n":
            # 2 CRLF represents end of header
            data += clientProxyConnection.recv(1)

        # encapsulate it as a message object which does the processing of the request
        message = Message(data)
        self.logToTerminal(f"{message.getEncodedRequestLine().decode()}")

        # proxy acting as a client
        proxyServerConnection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverAddress = (message.targetHost, message.targetPortNumber)
        try:
            proxyServerConnection.connect(serverAddress)
        except Exception as e:
            proxyServerConnection.send(STATUS_CODES["bad-gateway"])
            logOutput(
                f"ERROR : when trying to connect to {serverAddress}, exception {e} occurred"
            )
            clientProxyConnection.close()
            # exit from proxyThread
            return

        # if message is GET request
        if message.isGetRequest():
            proxyServerConnection.send(
                message.getEncodedRequestLine()
                + b"\r\n"
                + message.getEncodedHeaderAndBody()
            )
            headerAndBody = ""
            line = ""

            while True:
                if headerAndBody[-4:] == "\r\n":
                    break

                line += proxyServerConnection.recv(1).decode()

                if line[-1] == "\n":
                    if "keep-alive" in line.lower():
                        line = line.replace("keep-alive", "close")
                    headerAndBody += line
                    line = ""

            clientProxyConnection.send(headerAndBody.encode())

            # From server
            data = proxyServerConnection.recv(1024)
            while data:
                clientProxyConnection.send(data)
                data = proxyServerConnection.recv(1024)

            proxyServerConnection.close()
            clientProxyConnection.close()

        else:
            clientProxyConnection.send(STATUS_CODES["ok"])

            clientToServerThread = threading.Thread(
                target=self.connectionThread,
                args=(clientProxyConnection, proxyServerConnection),
            )
            clientToServerThread.daemon = True

            serverToClientThread = threading.Thread(
                target=self.connectionThread,
                args=(proxyServerConnection, clientProxyConnection),
            )
            serverToClientThread.daemon = True

            clientToServerThread.start()
            serverToClientThread.start()

    def startProxyServer(self):
        """
        creates TCP socket and starts the proxy server
        """

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.hostName, self.portNumber))

        self.socket.listen()

        print(
            f"Proxy Server listening at hostname {self.hostName} and portNumber {self.portNumber}"
        )

        try:
            while True:
                clientConnection, clientAddress = self.socket.accept()
                logOutput(f"Connection accpted from {clientAddress}")

                connectionThread = threading.Thread(
                    target=self.proxyThread, args=(clientConnection,)
                )
                # we want to kill all threads when the main proxy server terminates
                connectionThread.daemon = True
                connectionThread.start()

        except KeyboardInterrupt:
            logOutput("Closing Proxy Server")

        finally:
            LOG_FILE.close()
            self.stopProxyServer()

    def stopProxyServer(self):
        print(f"Closing Server")
        assert isinstance(self.socket, socket.socket)
        self.socket.close()
        exit()


if __name__ == "__main__":
    hostName = "localhost"
    portNumber = 8888

    if len(argv) == 1:
        pass

    elif len(argv) == 2:
        hostName = "localhost"
        portNumber = int(argv[1])

    elif len(argv) == 3:
        hostName = argv[0]
        portNumber = int(argv[1])

    else:
        print("USAGE : ./proxyServer.py [hostName] [portNumber]")

    proxyServer = ProxyServer(hostName, portNumber)
    proxyServer.startProxyServer()
