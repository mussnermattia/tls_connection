
from tls_client import TLSClient

server_address = "192.168.10.168"
server_port = 12347
client = TLSClient(server_address, server_port)


def main():
    client.connect()
    while True:
        x = client.send_read_request("x_angle").get('value')
        y = client.send_read_request("y_angle").get('value')
        z = client.send_read_request("z_angle").get('value')

        print(f"x: {x}, y: {y}, z: {z}")


if __name__ == "__main__":
    main()