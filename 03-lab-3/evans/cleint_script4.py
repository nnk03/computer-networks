import socket
import threading
import time

class UDPClient:
    def __init__(self, host='127.0.0.1', port=9999):
        self.server_host = host
        self.server_port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.stop_event = threading.Event()

    def send_message(self, message):
        try:
            self.sock.sendto(message.encode('utf-8'), (self.server_host, self.server_port))
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_messages(self):
        while not self.stop_event.is_set():
            try:
                data, addr = self.sock.recvfrom(1024)
                print(f"Received message from {addr}: {data.decode('utf-8')}")
            except Exception as e:
                print(f"Error receiving message: {e}")

    def start_receiving(self):
        self.receive_thread = threading.Thread(target=self.receive_messages)
        self.receive_thread.daemon = True  # Ensure the thread exits when the main program exits
        self.receive_thread.start()

    def stop_receiving(self):
        self.stop_event.set()
        self.receive_thread.join()

    def close(self):
        self.sock.close()

if __name__ == "__main__":
    client = UDPClient()
    client.start_receiving()

    try:
        while True:
            message = input("Enter message to send (or 'exit' to quit): ")
            if message.lower() == 'exit':
                break
            client.send_message(message)
            time.sleep(1)  # Sleep to avoid flooding the server
    except KeyboardInterrupt:
        print("\nClient interrupted")

    client.stop_receiving()
    client.close()
    print("Client closed")
