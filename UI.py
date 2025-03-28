import tkinter as tk
from tkinter import ttk, messagebox
import json
import threading
import pygame  # Alternative zu playsound

from tls_client import TLSClient

# Pygame-Mixer initialisieren
pygame.mixer.init()

server_address = "192.168.10.168"  # Ersetze durch die Server-IP
server_port = 12347                # Ersetze durch den Server-Port

# TLSClient-Instanz erstellen und verbinden
client = TLSClient(server_address, server_port)
if not client.connect():
    messagebox.showerror("Verbindungsfehler", f"Verbindung zu {server_address}:{server_port} fehlgeschlagen!")
    exit()

# ------------------ Normale GPIO-Steuerung ------------------
def send_values():
    data = {
        "gpio": selected_gpio.get(),
        "value": value.get()
    }
    client.send_write_request(data["gpio"], data["value"])

def toggle_value(event=None):
    if value.get() == 0:
        value.set(1)
        canvas.coords(toggle_slider, 50, 5, 95, 45)  # ON
    else:
        value.set(0)
        canvas.coords(toggle_slider, 5, 5, 50, 45)   # OFF

def display_value():
    value_type = f"{selected_axis.get()}_{selected_type.get().lower()}"
    sensor_value = client.send_read_request(value_type)
    if sensor_value is None:
        value_label.config(text="Sensor Value: Fehler")
        return

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
        value_label.config(text=f"Sensor Value: {float(sensor_value):.2f}")
    except (ValueError, TypeError):
        value_label.config(text=f"Sensor Value: {sensor_value}")

# ------------------ Ampelsteuerung ------------------
# Zustandsdefinitionen
RED = 0
YELLOW = 1
GREEN = 2

traffic_state = RED  # Anfangszustand

def play_green_sound():
    sound_path = r"C:\Users\flori\Downloads\tls_connection-main\tls_connection-main\Car starting sound effect.mp3"
    try:
        pygame.mixer.music.load(sound_path)
        pygame.mixer.music.play()
    except Exception as e:
        print("Fehler beim Abspielen des Sounds:", e)

def update_traffic_lights(state):
    # GPIO5: Rot, GPIO6: Gelb, GPIO13: Grün
    client.send_write_request(5, 1 if state == RED else 0)
    client.send_write_request(6, 1 if state == YELLOW else 0)
    client.send_write_request(13, 1 if state == GREEN else 0)

def set_traffic_state(state):
    global traffic_state
    traffic_state = state
    update_traffic_lights(traffic_state)
    if state == GREEN:
        # Sound asynchron abspielen, wenn der Zustand grün erreicht wird
        threading.Thread(target=play_green_sound).start()

# Manuelle Steuerung:
# • Von Rot → Grün: direkt
# • Von Grün → Rot: zuerst Gelb, dann automatisch Rot (kein separater Gelb-Knopf)
def manual_toggle_traffic():
    global traffic_state
    if traffic_state == RED:
        set_traffic_state(GREEN)
    elif traffic_state == GREEN:
        update_traffic_lights(YELLOW)
        # Nach 1 Sekunde automatisch zu Rot wechseln
        root.after(1000, lambda: set_traffic_state(RED))
    # Falls sich die Ampel im Gelb-Zustand befindet, passiert nichts.

# Automatische Steuerung:
# • Rot → Grün: direkt (kein Gelb)
# • Grün → Rot: über Gelb
def automatic_cycle():
    global traffic_state
    if traffic_mode.get() != "Automatisch":
        return
    if traffic_state == RED:
        set_traffic_state(GREEN)
        root.after(6000, automatic_cycle)
    elif traffic_state == GREEN:
        set_traffic_state(YELLOW)
        root.after(1000, automatic_cycle)
    elif traffic_state == YELLOW:
        set_traffic_state(RED)
        root.after(6000, automatic_cycle)

def traffic_mode_changed():
    if traffic_mode.get() == "Automatisch":
        toggle_traffic_btn.config(state="disabled")
        automatic_cycle()
    else:
        toggle_traffic_btn.config(state="normal")

# ------------------ UI-Aufbau ------------------
root = tk.Tk()
root.title("GPIO Steuerung")
root.geometry("800x800")
root.resizable(False, False)

style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=("Arial", 12))
style.configure("TCheckbutton", font=("Arial", 12))
style.configure("TLabel", font=("Arial", 12))
style.configure("TRadiobutton", font=("Arial", 12))

# Variablen für normale GPIO-Steuerung
selected_gpio = tk.IntVar(value=-1)
value = tk.IntVar(value=0)

header_label = ttk.Label(root, text="GPIO Steuerung", font=("Arial", 16))
header_label.grid(row=0, column=0, columnspan=2, pady=20)

gpio_buttons_left = [4, 17, 27, 22, 5, 6, 13, 19, 26]
for i, gpio in enumerate(gpio_buttons_left):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i+1, column=0, padx=10, pady=5, sticky="w")

gpio_buttons_right = [18, 23, 24, 25, 12, 16, 20, 21]
for i, gpio in enumerate(gpio_buttons_right):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i+1, column=1, padx=10, pady=5, sticky="w")

toggle_label = ttk.Label(root, text="Toggle Value (0/1)", font=("Arial", 12))
toggle_label.grid(row=19, column=0, columnspan=2, pady=10)

canvas = tk.Canvas(root, width=100, height=50, bg="#ccc", bd=0, highlightthickness=0)
canvas.grid(row=20, column=0, columnspan=2)
toggle_slider = canvas.create_rectangle(5, 5, 50, 45, fill="white", outline="white")
canvas.bind("<Button-1>", toggle_value)

send_btn = ttk.Button(root, text="Senden", command=send_values)
send_btn.grid(row=21, column=0, columnspan=2, pady=20)

footer_label = tk.Label(root, text="By Kaserer, Gredna, Kouflor, Imraaain")
footer_label.grid(row=22, column=0)

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

# ------------------ Ampelsteuerung UI ------------------
traffic_frame = ttk.LabelFrame(root, text="Ampel Steuerung")
traffic_frame.grid(row=23, column=0, columnspan=3, pady=20, padx=10, sticky="ew")

traffic_mode = tk.StringVar(value="Manuell")
rb_manual = ttk.Radiobutton(traffic_frame, text="Manuell", variable=traffic_mode,
                            value="Manuell", command=traffic_mode_changed)
rb_manual.grid(row=0, column=0, padx=10, pady=5, sticky="w")
rb_auto = ttk.Radiobutton(traffic_frame, text="Automatisch", variable=traffic_mode,
                          value="Automatisch", command=traffic_mode_changed)
rb_auto.grid(row=0, column=1, padx=10, pady=5, sticky="w")

toggle_traffic_btn = ttk.Button(traffic_frame, text="Toggle Ampel", command=manual_toggle_traffic)
toggle_traffic_btn.grid(row=1, column=0, columnspan=2, pady=10)

horizon_btn = ttk.Button(root, text="Horizont öffnen")
horizon_btn.grid(row=23, column=3, padx=10, pady=20, sticky="n")

# ------------------ Sauberes Beenden ------------------
def on_closing():
    client.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
