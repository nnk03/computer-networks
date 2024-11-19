#!/usr/bin/python3

import socket, threading, os
from sys import argv
import ast
from datetime import datetime


LOCK = threading.Lock()
TERMINAL_LOCK = threading.Lock()

TIMEOUT_INTERVAL = 10

CHUNK = 4096

ELECTION = 'ELECTION'
COORDINATOR = 'COORDINATOR'
OK = 'OK'

N = 8

process_server_address = {}
process_client_sockets = {}

BASE_PORT = 55555

def currentDateTime():
    return datetime.now().strftime("%d %b %Y %H:%M:%S")


def logToTerminal(message: str):
    with TERMINAL_LOCK:
        print(f"{currentDateTime()} - >>> {message}")


class SampleProcess():
    def __init__(self, process_id: int) -> None:
        self.clientThreadLock = threading.Lock()
        self.serverThreadLock = threading.Lock()
        self.isServerRunning = True
        self.isClientRunning = True
        self.receivedElectionMessage = False
        self.process_id = process_id
        self.createServer()
        self.createClient()
        self.timerThread = None

        pass

    def startSampleProcess(self):
        if self.process_id != 7:
            clientThread = threading.Thread(target = self.handleClient)
            clientThread.start()
            # listenThread = threading.Thread(target = self.listenForServer)
            # listenThread.start()
        if self.process_id == 4:
            waitAndSendElection = threading.Timer(TIMEOUT_INTERVAL // 2, self.sendElectionMessage)
            waitAndSendElection.start()

    def handleClient(self):
        while self.isServerRunning:
            data, clientAddress = self.serverSocket.recvfrom(CHUNK)
            message, from_process_id = self.decodeMessage(data.decode())
            self.notifyTerminal(message, from_process_id)

            if message == ELECTION:
                # send OK to the server of the process
                self.sendMessageToClient(OK, clientAddress)
                if not self.receivedElectionMessage:
                    with self.serverThreadLock:
                        self.receivedElectionMessage = True
                    self.sendElectionMessage()
                    self.startTimer()

            elif message == OK:
                # someone else will conduct the election, hence stop timer
                self.stopTimer()
            else:
                # message is COORDINATOR
                # self.sendMessageToClient(OK, clientAddress)
                self.stopTimer()
                pass

    def notifyTerminal(self, message, from_process_id):
        logToTerminal(f'{self.process_id} : Received {message} from {from_process_id}')

    def sendElectionMessage(self):
        for process_id in range(self.process_id + 1, N):
            if process_id in process_server_address:
                serverAddress = process_server_address[ process_id ]
                self.sendMessageToServer(ELECTION, serverAddress)

    def sendCoordinatorMessage(self):
        for process_id, serverAddress in process_server_address.items():
            if process_id != self.process_id:
                self.sendMessageToServer(COORDINATOR, serverAddress)
        logToTerminal(f'{self.process_id} : I\'m the COORDINATOR')

    def listenForServer(self):
        while self.isClientRunning:
            data, serverAddress = self.clientSocket.recvfrom(CHUNK)
            message, from_process_id = self.decodeMessage(data)
            if message == OK:
                self.stopTimer()
            elif message == COORDINATOR:
                self.stopTimer()


    def startTimer(self):
        if self.timerThread is not None:
            return
        self.timerThread = threading.Timer(TIMEOUT_INTERVAL, self.sendCoordinatorMessage)
        self.timerThread.start()

    def stopTimer(self):
        if self.timerThread:
            # timer already running
            self.timerThread.cancel()

        self.timerThread = None


        
    def createServer(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.serverAddress = ('', BASE_PORT + self.process_id)
        self.hostname = 'localhost'
        self.port = BASE_PORT + self.process_id
        self.serverSocket.bind(self.serverAddress)
        with LOCK:
            process_server_address[self.process_id] = ('localhost', self.port)

    def createClient(self):
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # with LOCK:
        #     process_client_sockets[self.process_id] = self.clientSocket

        
    def decodeMessage(self, message: str):
        decodedMessage = tuple(message.split())
        return decodedMessage

    def sendMessageToServer(self, message: str, serverAddress):
        with self.clientThreadLock:
            sendMessage = f'{message} {self.process_id}'
            sendMessage = sendMessage.encode()
            self.serverSocket.sendto(sendMessage, serverAddress)

    def sendMessageToClient(self, message: str, clientAddress):
        with self.serverThreadLock:
            sendMessage = f'{message} {self.process_id}'
            sendMessage = sendMessage.encode()
            self.serverSocket.sendto(sendMessage, clientAddress)

if __name__ == '__main__':
    sampleProcesses = []
    for i in range(N):
        sampleProcesses.append(SampleProcess(i))
        

    for p in sampleProcesses:
        p.startSampleProcess()


















