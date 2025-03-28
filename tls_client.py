import json
import socket
import ssl

class TLSClient:
    def __init__(self, server_address, server_port, cert_file="cert.pem"):
        self.server_address = server_address
        self.server_port = server_port
        self.cert_file = cert_file
        self.sslsock = None

    def create_context(self):
        """Creates and returns an SSL context."""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_verify_locations(self.cert_file)
            return context
        except Exception as e:
            print(f"Error creating SSL context: {e}")
            return None

    def connect(self):
        """Creates a socket, wraps it in SSL, and connects to the server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            context = self.create_context()
            if context is None:
                return False

            self.sslsock = context.wrap_socket(sock, server_hostname=self.server_address)
            self.sslsock.connect((self.server_address, self.server_port))
            print(f"Connected to {self.server_address}:{self.server_port}")
            return True
        except ssl.SSLError as e:
            print(f"SSL error: {e}")
        except socket.error as e:
            print(f"Socket error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        return False

    def send_read_request(self, sensor_value):
        """Sends a read request for a specified sensor value and returns the value from the server."""
        valid_values = ['x_acc', 'y_acc', 'z_acc', 'x_angle', 'y_angle', 'z_angle']
        if sensor_value not in valid_values:
            print("Invalid sensor value. Please enter one of:", ", ".join(valid_values))
            return None

        payload = {
            "mode": "read",
            "data": {"value": sensor_value}
        }
        try:
            self.sslsock.sendall(json.dumps(payload).encode())
            response = self.sslsock.recv(4096)
            if not response:
                print("Server closed the connection.")
                return None
            
            response_data = json.loads(response.decode())
            if "error" in response_data:
                print(f"Error from server: {response_data['error']}")
                return None
            
            sensor_data = response_data['data'].get(sensor_value, None)
            if sensor_data:
                print(f"Received sensor data: {sensor_data}")
                return sensor_data  # Return the sensor data dictionary, e.g., {'value': ..., 'unit': ...}
            else:
                print("No data received for the requested value.")
                return None
        except (ssl.SSLError, socket.error) as e:
            print(f"Connection error: {e}")
            return None

    def send_write_request(self, pin, value):
        """Sends a write request with a pin and value."""
        try:
            payload = {
                "mode": "write",
                "data": {
                    "gpio": int(pin),
                    "value": int(value)
                }
            }
        except ValueError:
            print("Invalid input. Pin and value should be integers.")
            return True  # Continue execution

        try:
            self.sslsock.sendall(json.dumps(payload).encode())
            response = self.sslsock.recv(4096)
            if not response:
                print("Server closed the connection.")
                return False
            
            print(f"Server response: {response.decode()}")
        except (ssl.SSLError, socket.error) as e:
            print(f"Connection error: {e}")
            return False
        return True

    def run(self):
        """Runs the interactive loop for read/write requests."""
        if not self.connect():
            return

        while True:
            mode = input("Enter read or write (or 'quit' to exit): ").lower()
            if mode in ['read', 'r']:
                sensor_value = input("Enter the sensor value to read (e.g., x_acc, y_acc, z_acc, x_angle, y_angle, z_angle): ")
                if not self.send_read_request(sensor_value):
                    break
            elif mode in ['write', 'w']:
                pin = input("Enter pin: ")
                value = input("Enter value: ")
                if not self.send_write_request(pin, value):
                    break
            elif mode == 'quit':
                break
            else:
                print("Invalid input, try again.")
                continue

        self.close()

    def close(self):
        """Closes the SSL connection."""
        if self.sslsock:
            self.sslsock.close()
            print("Connection closed.")


if __name__ == "__main__":
    server_address = "192.168.10.168"  # Replace with your server IP
    server_port = 12347  # Replace with your server port

    client = TLSClient(server_address, server_port)
    client.run()