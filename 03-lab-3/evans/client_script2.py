import socket

def send_test_message(port, host='127.0.0.1'):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = "1245,1,hello,2,1,0"  # Example message
    sock.sendto(message.encode('utf-8'), (host, port))
    print("Message sent:", message)
    sock.close()

if __name__ == "__main__":
    send_test_message(9999)
