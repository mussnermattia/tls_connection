import socket
import ssl
import threading
import json
import RPi.GPIO as GPIO
import smbus
import time

# Set up GPIO mode
GPIO.setmode(GPIO.BCM)

# Set up I2C bus (I2C bus 1 for Raspberry Pi)
bus = smbus.SMBus(1)

# I2C Addresses
MAGNETOMETER_ADDR = 0x1c
GYRO_ACCEL_ADDR = 0x6a

# Sensor Register Addresses for acceleration (assuming these are correct)
CTRL_REG1_G = 0x10
CTRL_REG6_XL = 0x20

# Sensor Register Addresses for angles (assuming these are correct)
OUT_X_G = 0x22  # Register address for x-axis gyro
OUT_Y_G = 0x24  # Register address for y-axis gyro
OUT_Z_G = 0x26  # Register address for z-axis gyro

# Configure Gyroscope and Accelerometer (write 0xa0 to control registers)
def configure_sensors():
    try:
        bus.write_byte_data(GYRO_ACCEL_ADDR, CTRL_REG1_G, 0xa0)  # Gyro configuration
        bus.write_byte_data(GYRO_ACCEL_ADDR, CTRL_REG6_XL, 0xa0)  # Accelerometer configuration
        print("Sensors configured.")
    except Exception as e:
        print(f"Error configuring sensors: {e}")

def read_acceleration(axis):
    """Read the acceleration in the specified axis."""
    try:
        if axis == "x_acc":
            x_acc = bus.read_word_data(GYRO_ACCEL_ADDR, 0x28)  # Read x-axis acceleration
            return x_acc
        elif axis == "y_acc":
            y_acc = bus.read_word_data(GYRO_ACCEL_ADDR, 0x2A)  # Read y-axis acceleration
            return y_acc
        elif axis == "z_acc":
            z_acc = bus.read_word_data(GYRO_ACCEL_ADDR, 0x2C)  # Read z-axis acceleration
            return z_acc
        else:
            raise ValueError(f"Invalid acceleration axis: {axis}")
    except Exception as e:
        print(f"Error reading acceleration for {axis}: {e}")
        return None

def read_gyro(axis):
    """Read the gyro data (angular velocity) for the specified axis (combine low and high bytes)."""
    try:
        if axis == "x_angle":
            low_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_X_G)  # Read x-axis gyro low byte
            high_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_X_G + 1)  # Read x-axis gyro high byte
            raw_data = (high_byte << 8) | low_byte  # Combine high and low byte into 16-bit data
            if raw_data > 32767:
                raw_data -= 65536  # 2's complement correction for negative values
            x_angle = raw_data / 131.0  # Scale based on ±250°/s for this sensor
            return x_angle
        elif axis == "y_angle":
            low_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_Y_G)  # Read y-axis gyro low byte
            high_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_Y_G + 1)  # Read y-axis gyro high byte
            raw_data = (high_byte << 8) | low_byte  # Combine high and low byte into 16-bit data
            if raw_data > 32767:
                raw_data -= 65536  # 2's complement correction for negative values
            y_angle = raw_data / 131.0  # Scale based on ±250°/s for this sensor
            return y_angle
        elif axis == "z_angle":
            low_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_Z_G)  # Read z-axis gyro low byte
            high_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, OUT_Z_G + 1)  # Read z-axis gyro high byte
            raw_data = (high_byte << 8) | low_byte  # Combine high and low byte into 16-bit data
            if raw_data > 32767:
                raw_data -= 65536  # 2's complement correction for negative values
            z_angle = raw_data / 131.0  # Scale based on ±250°/s for this sensor
            return z_angle
        else:
            raise ValueError(f"Invalid angle axis: {axis}")
    except Exception as e:
        print(f"Error reading angle for {axis}: {e}")
        return None

def write_gpio(pin, value):
    """Write a value to a specified GPIO pin."""
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, value)
        print(f"GPIO {pin} set to {value}")
    except Exception as e:
        print(f"Error writing to GPIO {pin}: {e}")
        return None

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
                        if "value" in json_data["data"]:
                            value = json_data["data"]["value"]

                            # Handle reading acceleration or angles
                            if value in ["x_acc", "y_acc", "z_acc"]:
                                # Read the acceleration value for the requested axis
                                acceleration = read_acceleration(value)

                                if acceleration is not None:
                                    response = json.dumps({
                                        "mode": "read",
                                        "data": {value: {"value": acceleration, "unit": "m/s^2"}}
                                    })
                                else:
                                    response = json.dumps({"error": "Failed to read acceleration data"})
                            elif value in ["x_angle", "y_angle", "z_angle"]:
                                # Read the angle (gyro) value for the requested axis
                                angle = read_gyro(value)

                                if angle is not None:
                                    response = json.dumps({
                                        "mode": "read",
                                        "data": {value: {"value": angle, "unit": "degrees"}}
                                    })
                                else:
                                    response = json.dumps({"error": "Failed to read angle data"})
                            else:
                                response = json.dumps({"error": "Invalid value for read. Expected 'x_acc', 'y_acc', 'z_acc', 'x_angle', 'y_angle', or 'z_angle'"})
                        else:
                            response = json.dumps({"error": "Missing 'value' field in read mode"})

                    elif mode == "write":
                        if "gpio" in json_data["data"] and "value" in json_data["data"]:
                            gpio_pin = json_data["data"]["gpio"]
                            value = json_data["data"]["value"]

                            # Write to the GPIO pin
                            if write_gpio(gpio_pin, value) is None:
                                response = json.dumps({"error": f"Failed to write to GPIO {gpio_pin}"})
                            else:
                                response = json.dumps({
                                    "mode": "write",
                                    "data": {"gpio": gpio_pin, "value": value}
                                })
                        else:
                            response = json.dumps({"error": "Missing required fields for 'write' mode"})

                    else:
                        response = json.dumps({"error": "Invalid mode"})

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
    server_address = "192.168.10.168"  # Modify this with the Raspberry Pi's IP address
    server_port = 12346
    certfile = "cert.pem"  # Replace with your actual certificate file
    keyfile = "key.pem"    # Replace with your actual key file

    # Configure the sensors
    configure_sensors()

    tls_server(server_address, server_port, certfile, keyfile)