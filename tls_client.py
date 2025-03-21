import json
import socket
import ssl

def tls_client(server_address, server_port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations("cert.pem")

        sslsock = context.wrap_socket(sock, server_hostname=server_address)

        sslsock.connect((server_address, server_port))
        print(f"Connected to {server_address}:{server_port}")

        while True:
            # Enter info
            mode = input("Enter read or write (or 'quit' to exit): ")

            if mode.lower() in ['read', 'r']:
                value = input("Enter the sensor value to read (e.g., x_acc, y_acc, z_acc): ")

                if value not in ['x_acc', 'y_acc', 'z_acc']:
                    print("Invalid value. Please enter one of 'x_acc', 'y_acc', or 'z_acc'.")
                    continue

                payload = {
                    "mode": "read",
                    "data": {
                        "value": value
                    }
                }

                try:
                    sslsock.sendall(json.dumps(payload).encode())
                    response = sslsock.recv(4096)

                    if not response:
                        print("Server closed the connection.")
                        break
                    
                    print(f"Server response: {response.decode()}")
                except (ssl.SSLError, socket.error) as e:
                    print(f"Connection error: {e}")
                    break

            elif mode.lower() in ['write', 'w']:
                pin = input("Enter pin: ")
                value = input("Enter value: ")

                payload = {
                    "mode": "write",
                    "data": {
                        "gpio": int(pin),
                        "value": int(value)
                    }
                }

                try:
                    sslsock.sendall(json.dumps(payload).encode())
                    response = sslsock.recv(4096)

                    if not response:
                        print("Server closed the connection.")
                        break
                    
                    print(f"Server response: {response.decode()}")
                except (ssl.SSLError, socket.error) as e:
                    print(f"Connection error: {e}")
                    break

            elif mode.lower() == 'quit':
                break

            else:
                print('Invalid input, try again.')
                continue

        sslsock.close()
        print("Connection closed.")

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    server_address = "192.168.165.168"  # Replace with your server IP
    server_port = 12346  # Replace with your server port

    tls_client(server_address, server_port)