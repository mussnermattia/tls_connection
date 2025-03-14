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
            message = input("Enter your message (type 'quit' to exit): ")
            if message.lower() == 'quit':
                break

            try:
                sslsock.sendall(message.encode())
                response = sslsock.recv(4096)

                if not response:
                    print("Server closed the connection.")
                    break
                
                print(f"Server response: {response.decode()}")
            except (ssl.SSLError, socket.error) as e:
                print(f"Connection error: {e}")
                break

        sslsock.close()
        print("Connection closed.")

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    server_address = "localhost"
    server_port = 12345

    tls_client(server_address, server_port)