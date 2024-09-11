import socket

def send_test_message(sock, port, host='127.0.0.1'):
    message = "1245,1,hello,3,1,0"  # Example message
    sock.sendto(message.encode('utf-8'), (host, port))
    print("Message sent:", message)

if __name__ == "__main__":
    port = 9999
    host = '127.0.0.1'
    
    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    # Send a test message
    send_test_message(sock, port, host)
    
    # Receive responses
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            print(f"Received message from {addr}: {data.decode('utf-8')}")
    except KeyboardInterrupt:
        print("\nClient interrupted")
    finally:
        sock.close()
        print("Socket closed")
