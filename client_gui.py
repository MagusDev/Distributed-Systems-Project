import requests
import tkinter as tk
from tkinter import ttk, messagebox
from threading import Thread
import time

def get_plc_data(base_url, plc_id=None, hours=1, variable=None):
    """
    Fetch PLC data with optional filters.

    :param base_url: Base URL of the API.
    :param plc_id: PLC ID to filter by (optional).
    :param hours: Number of hours to retrieve data for (default: 1).
    :param variable: Specific variable to retrieve (optional).
    :return: List of PLC data entries.
    """
    params = {
        "plc_id": plc_id,
        "hours": hours,
        "variable": variable,
    }
    response = requests.get(f"{base_url}/plc/data", params={k: v for k, v in params.items() if v is not None})
    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", f"Failed to fetch PLC data: {response.status_code}, {response.text}")
        return []

def get_plc_variables(base_url):
    """
    Retrieve the list of available PLC variables.

    :param base_url: Base URL of the API.
    :return: List of variable names.
    """
    response = requests.get(f"{base_url}/plc/variables")
    if response.status_code == 200:
        return response.json()
    else:
        messagebox.showerror("Error", f"Failed to fetch PLC variables: {response.status_code}, {response.text}")
        return []

def fetch_data():
    base_url = base_url_entry.get()
    plc_id = plc_id_entry.get()
    hours = hours_entry.get()
    variable = variable_entry.get()

    try:
        hours = int(hours) if hours else 1
    except ValueError:
        messagebox.showerror("Input Error", "Hours must be a number.")
        return

    data = get_plc_data(base_url, plc_id, hours, variable)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, data)

def fetch_variables():
    base_url = base_url_entry.get()
    variables = get_plc_variables(base_url)
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, variables)

def start_live_feed():
    base_url = base_url_entry.get()
    plc_id = plc_id_entry.get()
    variable = variable_entry.get()

    def live_feed():
        while live_feed_running.get():
            data = get_plc_data(base_url, plc_id, hours=1, variable=variable)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, data)
            time.sleep(5)  # Update every 5 seconds

    live_thread = Thread(target=live_feed, daemon=True)
    live_thread.start()

def stop_live_feed():
    live_feed_running.set(False)

# GUI Setup
root = tk.Tk()
root.title("PLC Data Viewer")

main_frame = ttk.Frame(root, padding="10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Base URL Entry
base_url_label = ttk.Label(main_frame, text="Base URL:")
base_url_label.grid(row=0, column=0, sticky=tk.W)
base_url_entry = ttk.Entry(main_frame, width=50)
base_url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E))

# PLC ID Entry
plc_id_label = ttk.Label(main_frame, text="PLC ID (optional):")
plc_id_label.grid(row=1, column=0, sticky=tk.W)
plc_id_entry = ttk.Entry(main_frame, width=50)
plc_id_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))

# Hours Entry
hours_label = ttk.Label(main_frame, text="Hours (default 1):")
hours_label.grid(row=2, column=0, sticky=tk.W)
hours_entry = ttk.Entry(main_frame, width=50)
hours_entry.grid(row=2, column=1, sticky=(tk.W, tk.E))

# Variable Entry
variable_label = ttk.Label(main_frame, text="Variable (optional):")
variable_label.grid(row=3, column=0, sticky=tk.W)
variable_entry = ttk.Entry(main_frame, width=50)
variable_entry.grid(row=3, column=1, sticky=(tk.W, tk.E))

# Buttons
fetch_data_button = ttk.Button(main_frame, text="Fetch Data", command=fetch_data)
fetch_data_button.grid(row=4, column=0, sticky=(tk.W, tk.E))

fetch_variables_button = ttk.Button(main_frame, text="Fetch Variables", command=fetch_variables)
fetch_variables_button.grid(row=4, column=1, sticky=(tk.W, tk.E))

live_feed_running = tk.BooleanVar(value=False)
start_live_button = ttk.Button(main_frame, text="Start Live Feed", command=lambda: [live_feed_running.set(True), start_live_feed()])
start_live_button.grid(row=5, column=0, sticky=(tk.W, tk.E))

stop_live_button = ttk.Button(main_frame, text="Stop Live Feed", command=stop_live_feed)
stop_live_button.grid(row=5, column=1, sticky=(tk.W, tk.E))

# Result Text
result_label = ttk.Label(main_frame, text="Results:")
result_label.grid(row=6, column=0, sticky=tk.W)
result_text = tk.Text(main_frame, height=15, width=80)
result_text.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E))

root.mainloop()
