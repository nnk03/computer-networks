#!/usr/bin/python3

"""

Computer Networks CS4150
Lab - 4 : Implemeting proxy server
By:
Neeraj Krishna N (112101033)
Evans Samuel Biju (112101017)

"""


from sys import argv
import socket
import threading
from datetime import datetime

LOG_FILE = open("./output.log", "w")
LOCK = threading.Lock()

CONNECT = "CONNECT"
GET = "GET"
UNKNOWN_METHOD = "UNKNOWN_METHOD"


def currentDateTime():
    return datetime.now().strftime("%d %b %Y %H:%M:%S")


def logOutput(message: str):
    with LOCK:
        LOG_FILE.write(f"{currentDateTime()} - {message}")
        LOG_FILE.write("\n")


def logToTerminal(message: str):
    print(f"{currentDateTime()} - >>> {message}")


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
                # logToTerminal(f"DATA  {data}")
                # logToTerminal(f"hostColonPort {hostColonPort}")

                if hostColonPort:
                    if ":" in hostColonPort:
                        targetHost, targetPortNumber = hostColonPort.split(":")
                        targetPortNumber = int(targetPortNumber)
                        self.targetHost = targetHost
                        self.targetPortNumber = targetPortNumber
                    else:
                        targetHost = hostColonPort
                        self.targetHost = targetHost
                        if "https:" in self.target:
                            self.targetPortNumber = 443
                        else:
                            self.targetPortNumber = 80

            if "keep-alive" in line.lower():
                # changing 'keep-alive' to 'close' to not allow persistent connections
                line = line.replace("keep-alive", "close")

            # append the line to headerAndBody after processing
            headerAndBody += line

            # if it is end of header
            # if "\r\n\r\n" in line:
            #     headerAndBody += line + "\r\n\r\n"
            # else:
            #     headerAndBody += line + "\r\n"

        # logToTerminal(f"TARGET {self.target}")
        # logToTerminal(f"TARGETHOST TARGETPORTNUBMER {targetHost} {targetPortNumber}")

        # after processing, self.targetHost must not be empty string and
        # self.targetPortNumber must not be zero
        assert (
            self.targetHost and self.targetPortNumber
        ), f"ERROR : targetHost = {targetHost} and targetPortNumber = {targetPortNumber}"

        self.encodedHeaderAndBody = headerAndBody.encode()

    def isNotConnectRequest(self):
        # some methods in the output resulted in POST, hence checking that
        # it is not CONNECT
        return self.method.upper() != CONNECT

    def getEncodedHeaderAndBody(self):
        return self.encodedHeaderAndBody

    def getEncodedRequestLine(self) -> bytes:
        # self.version will be HTTP/1.0
        requestLine = f"{self.method} {self.target} {self.version}"
        return requestLine.encode()

    def getTotalMessageEncoded(self) -> bytes:
        return self.getEncodedRequestLine() + b"\r\n" + self.getEncodedHeaderAndBody()


class ProxyServer:
    def __init__(self, hostName: str, portNumber: int) -> None:
        self.hostName = hostName
        self.portNumber = portNumber
        self.socket = None
        self.lock = LOCK

    def forwardingThread(self, sourceConnection, destConnection):
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
        logToTerminal(f"{message.getEncodedRequestLine().decode()}")

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
        if message.isNotConnectRequest():
            proxyServerConnection.send(message.getTotalMessageEncoded())

            headerFromServer = ""
            tempData = ""

            while not headerFromServer[-4:] == "\r\n\r\n":
                tempData += proxyServerConnection.recv(1).decode()

                headerFromServer += tempData
                tempData = ""

                # tempData receives data from server byte by byte
                tempData += proxyServerConnection.recv(1).decode()

            if "keep-alive" in headerFromServer:
                headerFromServer.replace("keep-alive", "close")

            clientProxyConnection.send(headerFromServer.encode())

            # From server
            data = proxyServerConnection.recv(1024)
            while data:
                # whatever data received from the server is sent to the client
                clientProxyConnection.send(data)
                data = proxyServerConnection.recv(1024)

            proxyServerConnection.close()
            clientProxyConnection.close()

        else:
            clientProxyConnection.send(STATUS_CODES["ok"])

            clientToServerThread = threading.Thread(
                target=self.forwardingThread,
                args=(clientProxyConnection, proxyServerConnection),
            )
            clientToServerThread.daemon = True

            serverToClientThread = threading.Thread(
                target=self.forwardingThread,
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

        logToTerminal(
            f"Proxy Server listening at hostname {self.hostName} and portNumber {self.portNumber}"
        )

        try:
            while True:
                clientConnection, clientAddress = self.socket.accept()
                logOutput(f"Connection accpted from {clientAddress}")

                forwardingThread = threading.Thread(
                    target=self.proxyThread, args=(clientConnection,)
                )
                # we want to kill all threads when the main proxy server terminates
                forwardingThread.daemon = True
                forwardingThread.start()

        except KeyboardInterrupt:
            logOutput("Closing Proxy Server")

        finally:
            LOG_FILE.close()
            self.stopProxyServer()

    def stopProxyServer(self):
        logToTerminal("Closing Server")
        assert isinstance(self.socket, socket.socket)
        self.socket.close()
        exit()


if __name__ == "__main__":
    hostName = "localhost"
    portNumber = 8998

    if len(argv) == 1:
        pass

    elif len(argv) == 2:
        hostName = "localhost"

    elif len(argv) == 3:
        hostName = argv[1]
        portNumber = int(argv[2])

    else:
        raise Exception("USAGE : ./proxyServer.py [hostName] [portNumber]")

    proxyServer = ProxyServer(hostName, portNumber)
    proxyServer.startProxyServer()
