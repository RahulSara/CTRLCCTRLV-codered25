import tkinter as tk
from tkinter import messagebox
import subprocess

# Global variables for subprocesses
hazard_process = None
navigation_process = None

# Function to handle power button toggle
def toggle_power():
    if power_button.config('text')[-1] == 'Power ON':
        power_button.config(text='Power OFF', bg='red')
        set_controls_state('disabled')
        stop_all_processes()
    else:
        power_button.config(text='Power ON', bg='green')
        set_controls_state('normal')

# Function to enable/disable controls
def set_controls_state(state):
    scale.config(state=state)
    additional_button.config(state=state)

# Function to stop all running processes
def stop_all_processes():
    global hazard_process, navigation_process
    if hazard_process:
        hazard_process.terminate()
        hazard_process = None
    if navigation_process:
        navigation_process.terminate()
        navigation_process = None

# Function to run OutdoorNav1.py and Hazard.py scripts concurrently
def run_outdoor_and_hazard_scripts():
    global hazard_process, navigation_process
    stop_all_processes()  # Ensure no scripts are already running
    try:
        navigation_process = subprocess.Popen(["python", "OutdoorNav1.py"])
        hazard_process = subprocess.Popen(["python", "Hazard.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run outdoor or hazard script: {str(e)}")

# Function to run IndoorYolov8.py script
def run_indoor_nav_script():
    global navigation_process
    stop_all_processes()  # Ensure no scripts are already running
    try:
        navigation_process = subprocess.Popen(["python", "IndoorIntegrated.py"])
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run IndoorYolov8.py: {str(e)}")

# Function for slider change
def on_slider_change(value):
    if value == '1':
        label.config(text="Indoor")
        run_indoor_nav_script()
    elif value == '2':
        label.config(text="Outdoor")
        run_outdoor_and_hazard_scripts()

# Function for the Voice activation button
def additional_function():
    messagebox.showinfo("Info", "Additional function executed")

# Gracefully stop all processes when closing the application
def on_closing():
    stop_all_processes()
    root.destroy()

# Create the main window
root = tk.Tk()
root.title("visualEYEze")
root.geometry("300x300")

# Power button
power_button = tk.Button(root, text="Power ON", bg='green', command=toggle_power)
power_button.pack(pady=10)

# Slider to select mode
scale = tk.Scale(root, from_=1, to=2, orient="horizontal", tickinterval=1, command=on_slider_change, label="Select Mode")
scale.pack(pady=10)

# Label to display current state
label = tk.Label(root, text="State")
label.pack(pady=5)

# Additional function button
additional_button = tk.Button(root, text="Voice activation button", command=additional_function)
additional_button.pack(pady=10)

# Initially set controls to enabled
set_controls_state('normal')

# Bind the close event to stop processes
root.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
root.mainloop()
