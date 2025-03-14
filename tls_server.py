import socket
import ssl
import threading

def handle_client(sslsock, client_address):
    """Handles communication with a single client."""
    try:
        while True:
            data = sslsock.recv(4096)
            if data:
                print(f"Received from {client_address}: {data.decode()}")
                sslsock.sendall(data)
            else:
                print(f"Client {client_address} disconnected.")
                break
    except ssl.SSLError as e:
        print(f"SSL error from {client_address}: {e}")
    except socket.error as e:
        print(f"Socket error from {client_address}: {e}")
    except Exception as e:
        print(f"An unexpected error occurred with {client_address}: {e}")
    finally:
        sslsock.close()

def tls_server(server_address, server_port, certfile, keyfile):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((server_address, server_port))
        sock.listen(5)

        print(f"TLS server listening on {server_address}:{server_port}")

        while True:
            client_sock, client_addr = sock.accept()
            sslsock = context.wrap_socket(client_sock, server_side=True)

            client_thread = threading.Thread(target=handle_client, args=(sslsock, client_addr))
            client_thread.start()

    except ssl.SSLError as e:
        print(f"SSL error: {e}")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if 'sock' in locals():
            sock.close()

if __name__ == "__main__":
    server_address = "127.0.0.1"
    server_port = 12345
    certfile = "cert.pem"
    keyfile = "key.pem"

    tls_server(server_address, server_port, certfile, keyfile)