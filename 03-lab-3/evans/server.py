import socket
import threading

class Session:

    def __init__(self,data):
        
        self.magic=int(data[0])
        self.version=int(data[1])
        self.command=data[2]
        self.session_id=int(data[3])
        self.sequence_no=0
        self.state=0
        self.timer=10






class Server:

    def __init__(self, port_number, timeout, host_addr):
        self.port = port_number
        self.timeout = timeout
        self.host_addr = host_addr

        self.magic_number = 1245
        self.version = 1

        self.session_thread_mapping = {}
        self.session_threadclass_mapping={}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((host_addr, port_number))
        self.state = 0

    def data_processing(self, encoded_data, addr):
        #print(type(encoded_data))
        self.data = encoded_data.decode('utf-8').split(',')

        if len(self.data) != 6:
            print("Malformed data received.")
            return

        
        self.create_new_session(int(self.data[3]),addr)

    def create_new_session(self, session_id, addr):
    #check if there is a need to create a new thread
        print(self.session_threadclass_mapping)
        if session_id  in self.session_threadclass_mapping:
            print("already there")
            self.handle_client(session_id,addr)
            return
        command = self.data[2]
        #print(self.data)
        #print(command)
        if command != 'hello':
            print("Error: Command should be 'hello' for new sessions.")
            return

        #session_thread = threading.Thread(target=self.handle_client, args=(session_id,addr,))
        #self.session_thread_mapping[session_id] = session_thread
        self.session_threadclass_mapping[session_id]=Session(self.data)
        print('going to start')
        self.handle_client(session_id,addr)
        #session_thread.start()

    def hand_over_to_threads(self, session_id, encoded_data, addr):
        if session_id in self.session_threadclass_mapping:
            # Here we should ideally send the data to the specific thread, but since we're handling
            # client connections in a separate thread already, this is a no-op in this simple model.
            print(f"Passing data to thread for session {session_id}")
            print(encoded_data)
        else:
            print(f"No thread found for session {session_id}")




    def handle_client(self,Session_ID,addr):
       # print(addr,"thread addr")
            try:
                print(Session_ID)
                Session=self.session_threadclass_mapping[Session_ID]
                print(Session.state,"session state")
                print(Session.command,"session_command")
                if Session.command=='hello' and Session.state==1:
                    #recieved hello while in recieve state ,something is wrong
                    #close
                    Session.state=2
                    self.send_back("GOODBYE",addr)
                    self.close_session(Session_ID)
                    return
                    #close the session
                
                #check error conditions
                if Session.sequence_no==int(self.data[4]):
                    #packet is repeated
                    print("packet repeated")


                if Session.sequence_no+1<int(self.data[4]):
                    while(Session.sequence_no!=int(self.data[4])):
                        print("packet lost")
                        Session.sequence_no+=1

                if Session.sequence_no>int(self.data[4]):
                    #caused by a protocol error
                    self.send_back("GOODBYE",addr)
                    Session.state=2;
                    self.close_session

                if Session.command=="hello":
                    self.send_message("HELLO",addr)
                    Session.state=1
                else:
                    self.send_message("ALIVE",addr)
                self.console_print(self.data)

                
                #to a hello message reply back with hello,and for others reply back with alive and for goodbye reply back with goodbye
            except Exception as e:
                print(f"Error in session {Session_ID}: {e}")
    def send_message(self, message, addr):
        self.socket.sendto(message.encode(), addr)

    def send_back(self, message, addr):
        self.send_message(message, addr)

    def close_session(self, session_id):
        if session_id in self.session_threadclass_mapping:
            thread = self.session_threadclass_mapping.pop(session_id)
            #thread.join()
            print(f"Session {session_id} closed.")

    def console_print(self, data):
        print(f"Received data: {data}")        

    def start(self):
        print(f"Server listening on {self.host_addr}:{self.port}")
        while True:
            try:
                data, addr = self.socket.recvfrom(1024)
                print("server still runs ","\n")
                thread=threading.Thread(target=self.data_processing,args=(data,addr))
                #self.data_processing(data, addr)
                #self.create_new_thread(int(self.data[3]),addr)
                thread.start()
                print("do we reach here")
            except Exception as e:
                print(f"Server error: {e}")

if __name__ == "__main__":
    server = Server(port_number=9999, timeout=10, host_addr='0.0.0.0')
    server.start()
