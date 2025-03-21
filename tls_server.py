import socket
import ssl
import threading
import json
import RPi.GPIO as GPIO

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

def handle_client(sslsock, client_address):
    """Handles communication with a single client."""
    try:
        while True:
            data = sslsock.recv(4096)
            if data:
                try:
                    # Try to parse the JSON data
                    json_data = json.loads(data.decode())

                    # Check the format of the JSON data
                    if "mode" not in json_data or "data" not in json_data:
                        raise ValueError("Missing required fields")

                    mode = json_data["mode"]
                    if mode == "read":
                        if "gpio" in json_data["data"]:
                            gpio_pin = json_data["data"]["gpio"]
                            # Respond with the current state of the GPIO pin (for simplicity we assume it's a digital read)
                            if GPIO.input(gpio_pin) is not None:
                                response = json.dumps({
                                    "mode": "read",
                                    "data": {"gpio": gpio_pin, "value": GPIO.input(gpio_pin)}
                                })
                            else:
                                raise ValueError("Invalid GPIO pin")
                        else:
                            raise ValueError("Missing 'gpio' field in 'read' mode")

                    elif mode == "write":
                        if "gpio" in json_data["data"] and "value" in json_data["data"]:
                            gpio_pin = json_data["data"]["gpio"]
                            value = json_data["data"]["value"]
                            
                            # Check if the GPIO pin is valid
                            if gpio_pin < 0 or gpio_pin > 27:  # Assuming BCM pins 0-27
                                raise ValueError("Invalid GPIO pin number")

                            # Check if the value is valid (only 0 or 1 is allowed)
                            if value not in [0, 1]:
                                raise ValueError("Invalid value for GPIO. Only 0 or 1 is allowed")

                            # Set the GPIO pin mode
                            GPIO.setup(gpio_pin, GPIO.OUT)
                            GPIO.output(gpio_pin, value)

                            response = json.dumps({
                                "mode": "write",
                                "data": {"gpio": gpio_pin, "value": value}
                            })
                        else:
                            raise ValueError("Missing required fields for 'write' mode")

                    else:
                        raise ValueError("Invalid mode")

                except (json.JSONDecodeError, ValueError) as e:
                    # Handle invalid JSON or missing fields
                    response = json.dumps({"error": f"invalid json format: {str(e)}"})
                    print(f"Error from {client_address}: {e}")

                sslsock.sendall(response.encode())

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
    server_address = "192.168.165.168"  # Modify this with the Raspberry Pi's IP address
    server_port = 12345
    certfile = "cert.pem"  # Replace with your actual certificate file
    keyfile = "key.pem"    # Replace with your actual key file

    tls_server(server_address, server_port, certfile, keyfile)