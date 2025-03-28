import socket
import ssl
import threading
import json
import RPi.GPIO as GPIO
import smbus
import time

# Setze den GPIO-Modus
GPIO.setmode(GPIO.BCM)

# Verwende den I²C-Bus 1 (wie in deinen Terminalbefehlen)
bus = smbus.SMBus(1)

# I²C-Adressen
MAGNETOMETER_ADDR = 0x1c
GYRO_ACCEL_ADDR = 0x6a

# Registeradressen für die Konfiguration (Kontinuierlicher Messmodus)
CTRL_REG1_G = 0x10
CTRL_REG6_XL = 0x20

# Für die Winkelmessung: Registeradressen (jeweils: low byte und high byte)
ANGLE_REGS = {
    "x_angle": 0x18,  # low byte x-Achse; high byte unter 0x19
    "y_angle": 0x1A,  # low byte y-Achse; high byte unter 0x1B
    "z_angle": 0x1C   # low byte z-Achse; high byte unter 0x1D
}

def configure_sensors():
    """Konfiguriert Gyro und Beschleunigungssensor für kontinuierliche Messungen.
       Es werden in die Register 0x10 und 0x20 der Wert 0xa0 geschrieben."""
    try:
        bus.write_byte_data(GYRO_ACCEL_ADDR, CTRL_REG1_G, 0xa0)
        bus.write_byte_data(GYRO_ACCEL_ADDR, CTRL_REG6_XL, 0xa0)
        time.sleep(0.05)  # kurze Pause, damit der Sensor starten kann
        print("Sensoren konfiguriert (kontinuierlicher Messmodus).")
    except Exception as e:
        print(f"Fehler bei der Sensor-Konfiguration: {e}")

def read_acceleration(axis):
    """Liest die Beschleunigung für die angegebene Achse.
       (Die Registeradressen für die Beschleunigung bleiben unverändert.)"""
    try:
        if axis == "x_acc":
            return bus.read_word_data(GYRO_ACCEL_ADDR, 0x28)
        elif axis == "y_acc":
            return bus.read_word_data(GYRO_ACCEL_ADDR, 0x2A)
        elif axis == "z_acc":
            return bus.read_word_data(GYRO_ACCEL_ADDR, 0x2C)
        else:
            raise ValueError(f"Ungültige Achse: {axis}")
    except Exception as e:
        print(f"Fehler beim Lesen der Beschleunigung für {axis}: {e}")
        return None

def read_angle(axis):
    """Liest den Winkel (in Grad) für die angegebene Achse.
       Dabei werden Low- und High-Byte aus den Registern (siehe ANGLE_REGS) eingelesen und kombiniert."""
    try:
        if axis not in ANGLE_REGS:
            raise ValueError(f"Ungültige Achse: {axis}")
        base_reg = ANGLE_REGS[axis]
        low_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, base_reg)
        high_byte = bus.read_byte_data(GYRO_ACCEL_ADDR, base_reg + 1)
        raw_data = (high_byte << 8) | low_byte
        if raw_data > 32767:
            raw_data -= 65536  # 2er-Komplement-Korrektur für negative Werte
        # Umrechnung: Hier wird wie zuvor durch 131.0 geteilt.
        angle = raw_data / 131.0
        return angle
    except Exception as e:
        print(f"Fehler beim Lesen des Winkels für {axis}: {e}")
        return None

def write_gpio(pin, value):
    """Schreibt einen Wert in den angegebenen GPIO-Pin."""
    try:
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, value)
        print(f"GPIO {pin} gesetzt auf {value}")
    except Exception as e:
        print(f"Fehler beim Schreiben in GPIO {pin}: {e}")
        return None

def handle_client(sslsock, client_address):
    """Behandelt die Kommunikation mit einem Client."""
    try:
        while True:
            data = sslsock.recv(4096)
            if data:
                try:
                    json_data = json.loads(data.decode())
                    if "mode" not in json_data or "data" not in json_data:
                        raise ValueError("Erforderliche Felder fehlen")
                    mode = json_data["mode"]
                    if mode == "read":
                        if "value" in json_data["data"]:
                            value = json_data["data"]["value"]
                            if value in ["x_acc", "y_acc", "z_acc"]:
                                acceleration = read_acceleration(value)
                                if acceleration is not None:
                                    response = json.dumps({
                                        "mode": "read",
                                        "data": {value: {"value": acceleration, "unit": "m/s^2"}}
                                    })
                                else:
                                    response = json.dumps({"error": "Fehler beim Lesen der Beschleunigungsdaten"})
                            elif value in ["x_angle", "y_angle", "z_angle"]:
                                angle = read_angle(value)
                                if angle is not None:
                                    response = json.dumps({
                                        "mode": "read",
                                        "data": {value: {"value": angle, "unit": "degrees"}}
                                    })
                                else:
                                    response = json.dumps({"error": "Fehler beim Lesen der Winkel-Daten"})
                            else:
                                response = json.dumps({"error": "Ungültiger Wert. Erwartet: 'x_acc', 'y_acc', 'z_acc', 'x_angle', 'y_angle' oder 'z_angle'"})
                        else:
                            response = json.dumps({"error": "Fehlendes 'value'-Feld im Read-Modus"})
                    elif mode == "write":
                        if "gpio" in json_data["data"] and "value" in json_data["data"]:
                            gpio_pin = json_data["data"]["gpio"]
                            value = json_data["data"]["value"]
                            if write_gpio(gpio_pin, value) is None:
                                response = json.dumps({"error": f"Fehler beim Schreiben in GPIO {gpio_pin}"})
                            else:
                                response = json.dumps({
                                    "mode": "write",
                                    "data": {"gpio": gpio_pin, "value": value}
                                })
                        else:
                            response = json.dumps({"error": "Erforderliche Felder für 'write'-Modus fehlen"})
                    else:
                        response = json.dumps({"error": "Ungültiger Modus"})
                except (json.JSONDecodeError, ValueError) as e:
                    response = json.dumps({"error": f"Ungültiges JSON-Format: {str(e)}"})
                    print(f"Fehler von {client_address}: {e}")
                sslsock.sendall(response.encode())
            else:
                print(f"Client {client_address} hat die Verbindung beendet.")
                break
    except ssl.SSLError as e:
        print(f"SSL-Fehler von {client_address}: {e}")
    except socket.error as e:
        print(f"Socket-Fehler von {client_address}: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler trat bei {client_address} auf: {e}")
    finally:
        sslsock.close()

def tls_server(server_address, server_port, certfile, keyfile):
    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((server_address, server_port))
        sock.listen(5)
        print(f"TLS-Server lauscht auf {server_address}:{server_port}")
        while True:
            client_sock, client_addr = sock.accept()
            sslsock = context.wrap_socket(client_sock, server_side=True)
            client_thread = threading.Thread(target=handle_client, args=(sslsock, client_addr))
            client_thread.start()
    except ssl.SSLError as e:
        print(f"SSL-Fehler: {e}")
    except socket.error as e:
        print(f"Socket-Fehler: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler trat auf: {e}")
    finally:
        if 'sock' in locals():
            sock.close()

if __name__ == "__main__":
    server_address = "192.168.10.168"  # Passe diese IP-Adresse bei Bedarf an
    server_port = 12347
    certfile = "cert.pem"  # Pfad zum Zertifikat
    keyfile = "key.pem"    # Pfad zum privaten Schlüssel

    # Konfiguriere die Sensoren exakt wie im Terminal:
    # Schreibe in Register 0x10 und 0x20 jeweils den Wert 0xa0
    configure_sensors()

    tls_server(server_address, server_port, certfile, keyfile)