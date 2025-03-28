import tkinter as tk
from tkinter import ttk, messagebox
import json

from tls_client import TLSClient

server_address = "192.168.10.168"  # Ersetze durch die Server-IP
server_port = 12347                # Ersetze durch den Server-Port

# TLSClient-Instanz erstellen und verbinden
client = TLSClient(server_address, server_port)
if not client.connect():
    # Verbindung konnte nicht hergestellt werden – Fehlermeldung anzeigen und Programm beenden
    messagebox.showerror("Verbindungsfehler", f"Verbindung zu {server_address}:{server_port} fehlgeschlagen!")
    exit()

# Funktion zum Senden der Werte
def send_values():
    data = {
        "gpio": selected_gpio.get(),
        "value": value.get()
    }
    # Sende Schreibanfrage über den TLSClient
    client.send_write_request(data["gpio"], data["value"])

# Funktion zum Umschalten des Toggle-Werts (0 oder 1)
def toggle_value(event=None):
    if value.get() == 0:
        value.set(1)
        canvas.coords(toggle_slider, 50, 5, 95, 45)  # Slider-Position auf ON setzen
    else:
        value.set(0)
        canvas.coords(toggle_slider, 5, 5, 50, 45)   # Slider-Position auf OFF setzen

# Funktion zum Lesen und Anzeigen der Sensorwerte
def display_value():
    # Ermitteln des gewünschten Sensorwerts (z.B. "x_acc" oder "z_angle")
    value_type = f"{selected_axis.get()}_{selected_type.get().lower()}"
    
    # Anfordern der Sensorwerte über den TLSClient
    sensor_value = client.send_read_request(value_type)
    if sensor_value is None:
        value_label.config(text="Sensor Value: Fehler")
        return

    # Payload zum Debuggen/Protokollieren (hier nur zur Ausgabe in der Konsole)
    payload = {
        "mode": "read",
        "data": {
            "value": value_type,
            "sensor_value": sensor_value
        }
    }
    json_data = json.dumps(payload, indent=4)
    print(json_data)
    
    try:
        # Falls sensor_value ein numerischer Wert ist:
        value_label.config(text=f"Sensor Value: {float(sensor_value):.2f}")
    except (ValueError, TypeError):
        # Falls sensor_value kein reiner Zahlenwert ist, gib ihn direkt aus
        value_label.config(text=f"Sensor Value: {sensor_value}")

# Hauptfenster
root = tk.Tk()
root.title("GPIO Steuerung")
root.geometry("800x600")
root.resizable(False, False)

# Stil definieren
style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=("Arial", 12))
style.configure("TCheckbutton", font=("Arial", 12))
style.configure("TLabel", font=("Arial", 12))
style.configure("TRadiobutton", font=("Arial", 12))

# Variablen
selected_gpio = tk.IntVar(value=-1)  # Kein GPIO ausgewählt
value = tk.IntVar(value=0)            # Toggle-Startwert 0

# Header
header_label = ttk.Label(root, text="GPIO Steuerung", font=("Arial", 16))
header_label.grid(row=0, column=0, columnspan=2, pady=20)

# Linke GPIO-Auswahl-Buttons
gpio_buttons_left = [4, 17, 27, 22, 5, 6, 13, 19, 26]
for i, gpio in enumerate(gpio_buttons_left):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

# Rechte GPIO-Auswahl-Buttons
gpio_buttons_right = [18, 23, 24, 25, 12, 16, 20, 21]
for i, gpio in enumerate(gpio_buttons_right):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")

# Toggle Switch für GPIO-Wert
toggle_label = ttk.Label(root, text="Toggle Value (0/1)", font=("Arial", 12))
toggle_label.grid(row=19, column=0, columnspan=2, pady=10)

canvas = tk.Canvas(root, width=100, height=50, bg="#ccc", bd=0, highlightthickness=0)
canvas.grid(row=20, column=0, columnspan=2)
toggle_slider = canvas.create_rectangle(5, 5, 50, 45, fill="white", outline="white")
canvas.bind("<Button-1>", toggle_value)

# Senden-Button
send_btn = ttk.Button(root, text="Senden", command=send_values)
send_btn.grid(row=21, column=0, columnspan=2, pady=20)

# Fußzeile
footer_label = tk.Label(root, text="By Kaserer, Gredna, Kouflor, Imraaain")
footer_label.grid(row=22, column=0)

# Dropdowns und Sensorlesen
selected_type = tk.StringVar(value="acc")
selected_axis = tk.StringVar(value="x")

type_label = ttk.Label(root, text="Wähle Typ (acc/Angle):", font=("Arial", 12))
type_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")

type_dropdown = ttk.Combobox(root, textvariable=selected_type, values=["acc", "Angle"])
type_dropdown.grid(row=2, column=2, padx=10, pady=5, sticky="w")

axis_label = ttk.Label(root, text="Wähle Achse (x/y/z):", font=("Arial", 12))
axis_label.grid(row=3, column=2, padx=10, pady=5, sticky="w")

axis_dropdown = ttk.Combobox(root, textvariable=selected_axis, values=["x", "y", "z"])
axis_dropdown.grid(row=4, column=2, padx=10, pady=5, sticky="w")

read_btn = ttk.Button(root, text="Lesen", command=display_value)
read_btn.grid(row=5, column=2, padx=10, pady=10)

value_label = ttk.Label(root, text="Wert: ", font=("Arial", 12))
value_label.grid(row=6, column=2, padx=10, pady=5)

# Funktion zum Schließen: Verbindung sauber beenden
def on_closing():
    client.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Start der UI
root.mainloop()
