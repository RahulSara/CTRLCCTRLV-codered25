import tkinter as tk
from tkinter import messagebox
import subprocess

# Function to handle power button toggle
def toggle_power():
    if power_button.config('text')[-1] == 'Power ON':
        power_button.config(text='Power OFF', bg='red')
        set_controls_state('disabled')
    else:
        power_button.config(text='Power ON', bg='green')
        set_controls_state('normal')

# Function to enable/disable controls
def set_controls_state(state):
    slider.config(state=state)
    additional_button.config(state=state)

# Function to handle slider value change
def slider_changed(event):
    if slider.get() == 0:
        label.config(text="Indoor")
        run_hazard_script()
    else:
        label.config(text="Outdoor")
        run_outdoor_nav_script()
        
def run_hazard_script():
    try:
        subprocess.run(["python", "Hazard.py"], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to run Hazard.py: {str(e)}")

# Function to run OutdoorNav1.py script
def run_outdoor_nav_script():
    try:
        subprocess.run(["python", "OutdoorNav1.py"], check=True)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Failed to run OutdoorNav1.py: {str(e)}")

# Function for the additional button
def additional_function():
    messagebox.showinfo("Info", "Additional function executed")

# Create the main window
root = tk.Tk()
root.title("Tkinter App Example")
root.geometry("300x200")

# Power button
power_button = tk.Button(root, text="Power ON", bg='green', command=toggle_power)
power_button.pack(pady=10)

# Slider bar with two options
slider = tk.Scale(root, from_=0, to=1, orient='horizontal', command=slider_changed)
slider.pack(pady=10)

# Label to display slider value
label = tk.Label(root, text="State")
label.pack(pady=5)

# Additional function button
additional_button = tk.Button(root, text="Voice Activation", command=additional_function)
additional_button.pack(pady=10)

# Initially set controls to enabled
set_controls_state('normal')

# Run the application
root.mainloop()
