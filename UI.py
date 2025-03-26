import tkinter as tk
from tkinter import ttk
import json

# Funktion zum Senden der Werte
def send_values():
    # Erstellen eines Dictionarys mit den Werten
    data = {
        "gpio": selected_gpio.get(),
        "value": value.get()
    }
    
    # Umwandeln in JSON und Ausgeben
    json_data = json.dumps(data)
    print(json_data)

# Funktion zum Setzen des Werts über den Toggle (0 oder 1)
def toggle_value(event=None):
    if value.get() == 0:
        value.set(1)
        canvas.coords(toggle_slider, 50, 5, 95, 45)  # Set slider position to ON
    else:
        value.set(0)
        canvas.coords(toggle_slider, 5, 5, 50, 45)  # Set slider position to OFF

# Funktion zum Anzeigen des Werts im Label
import json
import random  # Simulating sensor data (use actual sensor reading in production)

# Function to simulate reading the sensor value
def read_sensor_data(value_type):
    # Simulate reading sensor data for acceleration or angle (this should be replaced with actual sensor reading logic)
    if value_type.endswith("acc"):
        # Simulating 3D accelerometer data
        return random.uniform(-10, 10)  # Random acceleration value between -10 and 10 m/s^2
    elif value_type.endswith("angle"):
        # Simulating 3D angle data (e.g., degrees)
        return random.uniform(-180, 180)  # Random angle value between -180 and 180 degrees
    return 0  # Default if no valid type is provided

# Function to create payload and fetch sensor data
def display_value():
    # Get the selected type (acceleration or angle) and axis (x, y, z)
    value_type = f"{selected_axis.get()}_{selected_type.get().lower()}"
    
    # Construct the payload
    payload = {
        "mode": "read",
        "data": {
            "value": value_type
        }
    }

    # Read sensor data based on the selected value (e.g., z_acc, x_angle)
    sensor_value = read_sensor_data(value_type)
    
    # Add the sensor value to the payload
    payload["data"]["sensor_value"] = sensor_value

    # Convert the payload to JSON and print it (this would be sent to a client or logged in a real application)
    json_data = json.dumps(payload, indent=4)
    print(json_data)

    # Update the value_label with the result (sensor value)
    value_label.config(text=f"Sensor Value: {sensor_value:.2f}")




# Hauptfenster
root = tk.Tk()
root.title("GPIO Steuerung")
root.geometry("500x600")  # Fenstergröße
root.resizable(False, False)  # Fenstergröße fixieren


# Stil hinzufügen
style = ttk.Style()
style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=("Arial", 12))
style.configure("TCheckbutton", font=("Arial", 12))
style.configure("TLabel", font=("Arial", 12))
style.configure("TRadiobutton", font=("Arial", 12))

# Variable für den GPIO-Wert
selected_gpio = tk.IntVar(value=-1)  # Standardwert -1, bevor ein GPIO ausgewählt wurde
value = tk.IntVar(value=0)  # Startwert für den Toggle (0 oder 1)

# Header Label
header_label = ttk.Label(root, text="GPIO Steuerung", font=("Arial", 16))
header_label.grid(row=0, column=0, columnspan=2, pady=20)

# Erstellen der GPIO-Auswahl-Buttons (Buttons für die linke Seite)
gpio_buttons_left = [
    4, 17, 27, 22, 5, 6, 13, 19, 26
]
for i, gpio in enumerate(gpio_buttons_left):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="w")

# Erstellen der GPIO-Auswahl-Buttons (Buttons für die rechte Seite)
gpio_buttons_right = [
    18, 23, 24, 25, 12, 16, 20, 21
]
for i, gpio in enumerate(gpio_buttons_right):
    btn = ttk.Radiobutton(root, text=str(gpio), variable=selected_gpio, value=gpio)
    btn.grid(row=i + 1, column=1, padx=10, pady=5, sticky="w")

# Erstellen des Toggle Switches (Canvas für den Switch)
toggle_label = ttk.Label(root, text="Toggle Value (0/1)", font=("Arial", 12))
toggle_label.grid(row=19, column=0, columnspan=2, pady=10)

# Canvas für den Toggle Switch
canvas = tk.Canvas(root, width=100, height=50, bg="#ccc", bd=0, highlightthickness=0)
canvas.grid(row=20, column=0, columnspan=2)

# Initialer Schalter (Slider auf der linken Seite = 0)
toggle_slider = canvas.create_rectangle(5, 5, 50, 45, fill="white", outline="white")

# Funktion zum Umschalten des Werts
canvas.bind("<Button-1>", toggle_value)  # Toggle on click

# Button zum Senden
send_btn = ttk.Button(root, text="Senden", command=send_values)
send_btn.grid(row=21, column=0, columnspan=2, pady=20)

label = tk.Label(root, text="By Kaserer, Gredna, Kofler")
label.grid(row=22, column=0) 

# Variable für den Typ (Acceleration oder Angle)
selected_type = tk.StringVar(value="Acceleration")  # Standardwert auf "Acceleration" gesetzt

# Variable für die Achse (x, y, z)
selected_axis = tk.StringVar(value="x")  # Standardwert auf "x" gesetzt


# Neue Spalte für die Dropdowns und den Lesen-Button
# Dropdown für den Typ (Acceleration oder Angle)
type_label = ttk.Label(root, text="Wähle Typ (Acceleration/Angle):", font=("Arial", 12))
type_label.grid(row=1, column=2, padx=10, pady=5, sticky="w")

type_dropdown = ttk.Combobox(root, textvariable=selected_type, values=["Acceleration", "Angle"])
type_dropdown.grid(row=2, column=2, padx=10, pady=5, sticky="w")

# Dropdown für die Achse (x, y, z)
axis_label = ttk.Label(root, text="Wähle Achse (x/y/z):", font=("Arial", 12))
axis_label.grid(row=3, column=2, padx=10, pady=5, sticky="w")

axis_dropdown = ttk.Combobox(root, textvariable=selected_axis, values=["x", "y", "z"])
axis_dropdown.grid(row=4, column=2, padx=10, pady=5, sticky="w")

# Button zum Lesen der Werte
read_btn = ttk.Button(root, text="Lesen", command=display_value)
read_btn.grid(row=5, column=2, padx=10, pady=10)

# Label zum Anzeigen des Werts
value_label = ttk.Label(root, text="Wert: ", font=("Arial", 12))
value_label.grid(row=6, column=2, padx=10, pady=5)


# Starten der GUI
root.mainloop()
