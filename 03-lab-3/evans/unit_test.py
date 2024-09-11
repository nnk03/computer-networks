import unittest
import socket
import threading
import time

from server import Server  # Adjust the import based on your file structure

class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up the server for testing."""
        cls.server_port = 9999
        cls.server_host = '127.0.0.1'
        cls.server = Server(port_number=cls.server_port, timeout=10, host_addr=cls.server_host)
        
        # Start the server in a separate thread
        cls.server_thread = threading.Thread(target=cls.server.start, daemon=True)
        cls.server_thread.start()
        
        # Give the server a moment to start
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests."""
        cls.server.socket.close()
        cls.server_thread.join(timeout=1)  # Ensure server thread is closed

    def send_udp_message(self, message, port, host):
        """Helper function to send a UDP message."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(message.encode('utf-8'), (host, port))

    def test_server_processes_valid_data(self):
        print("entered here")
        """Test that the server processes valid data correctly."""
        test_message = "1245,1,hello,1,1,1"
        self.send_udp_message(test_message, self.server_port, self.server_host)

        time.sleep(2)  # Give the server some time to process the message
        print("here?")
        # Check server output (using print statements in the server isn't ideal)
        # You would typically check server logs or other outputs here
        # This example assumes output is visible or use mock to verify internal behavior

    def test_server_rejects_invalid_data(self):
        """Test that the server rejects malformed or invalid data."""
        invalid_message = "0000,0,wrong_command,1,1,1"
        self.send_udp_message(invalid_message, self.server_port, self.server_host)

        time.sleep(1)  # Give the server some time to process the message

        # Validate that the server printed an error or rejected the invalid data
        # Depending on the implementation, this could involve checking logs or output

    def test_server_creates_new_thread_for_new_session(self):
        """Test that the server creates a new thread for a new session."""
        test_message = "1245,1,hello,2,1,1"
        self.send_udp_message(test_message, self.server_port, self.server_host)

        time.sleep(1)  # Give the server some time to process

        self.assertIn(2, self.server.thread_mapping)  # Verify that the new thread is created

    def test_server_does_not_create_thread_for_existing_session(self):
        """Test that the server does not create a new thread for an existing session."""
        test_message = "1245,1,hello,3,1,1"
        self.send_udp_message(test_message, self.server_port, self.server_host)
        
        time.sleep(1)  # Give the server some time to process

        self.assertIn(3, self.server.thread_mapping)  # First, ensure the thread is created
        initial_thread_count = len(self.server.thread_mapping)

        # Send the same session data again
        self.send_udp_message(test_message, self.server_port, self.server_host)

        time.sleep(1)  # Give the server some time to process

        self.assertEqual(initial_thread_count, len(self.server.thread_mapping))  # Thread count should not change

if __name__ == "__main__":
    unittest.main()
