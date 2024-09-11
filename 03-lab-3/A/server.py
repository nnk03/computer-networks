import socket
import threading

class Server:

    def __init__(self, port_number, timeout, host_addr):
        self.port = port_number
        self.timeout = timeout
        self.host_addr = host_addr

        self.magic_number = 1245
        self.version = 1

        self.thread_mapping = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host_addr, port_number))
        self.state = 0

    def data_processing(self, encoded_data, addr):
        data = encoded_data.decode('utf-8').split(',')

        if len(data) != 6:
            print("Malformed data received.")
            return

        magic, version, command, session_no, sequence_number, logical_clock = data

        if int(magic) != self.magic_number or int(version) != self.version:
            print("Invalid magic number or version.")
            return

        session_no = int(session_no)

        if session_no not in self.thread_mapping:
            self.create_new_thread(session_no, addr)

        self.hand_over_to_threads(session_no, encoded_data, addr)

    def create_new_thread(self, session_id, addr):
        command = self.data.decode('utf-8').split(',')[2]
        if command != 'hello':
            print("Error: Command should be 'hello' for new sessions.")
            return

        session_thread = threading.Thread(target=self.handle_client, args=(session_id, addr))
        self.thread_mapping[session_id] = session_thread
        session_thread.start()

    def hand_over_to_threads(self, session_id, encoded_data, addr):
        if session_id in self.thread_mapping:
            # Here we should ideally send the data to the specific thread, but since we're handling
            # client connections in a separate thread already, this is a no-op in this simple model.
            print(f"Passing data to thread for session {session_id}")
        else:
            print(f"No thread found for session {session_id}")




    def handle_client(self, session_id, addr):
        while True:
            try:
                data, client_addr = self.socket.recvfrom(1024)
                if client_addr != addr:
                    print("Data from unexpected client. Ignoring.")
                    continue

                print(f"Received data from session {session_id}: {data.decode('utf-8')}")
                
                # Process received data as needed
                self.data_processing(data, client_addr)
                
            except Exception as e:
                print(f"Error in session {session_id}: {e}")
                break

    def start(self):
        print(f"Server listening on {self.host_addr}:{self.port}")
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                self.data_processing(data, addr)
            except Exception as e:
                print(f"Server error: {e}")

if __name__ == "__main__":
    server = Server(port_number=9999, timeout=10, host_addr='0.0.0.0')
    server.start()
