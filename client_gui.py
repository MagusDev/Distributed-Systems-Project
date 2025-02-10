import asyncio
import aiohttp
import tkinter as tk
from tkinter import ttk, messagebox
import time
from datetime import datetime

async def get_plc_data(base_url, plc_id=None, hours=1, variable=None):
    """
    Fetch PLC data with optional filters.

    :param base_url: Base URL of the API.
    :param plc_id: PLC ID to filter by (optional).
    :param hours: Number of hours to retrieve data for (default: 1).
    :param variable: Specific variable to retrieve (optional).
    :return: List of PLC data entries.
    """
    try:
        params = {}
        if plc_id:
            params["plc_id"] = plc_id
        if variable:
            params["variable"] = variable

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/plc/data", params=params) as response:
                response.raise_for_status()
                data = await response.json()
                print(f"Raw API Response: {data}")  # Debug print
                return data
    except aiohttp.ClientError as e:
        messagebox.showerror("Error", f"Failed to fetch PLC data: {e}")
        return []

async def get_plc_variables(base_url):
    """
    Retrieve the list of available PLC variables.

    :param base_url: Base URL of the API.
    :return: List of variable names.
    """
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/plc/variables") as response:
                response.raise_for_status()
                return await response.json()
    except aiohttp.ClientError as e:
        messagebox.showerror("Error", f"Failed to fetch PLC variables: {e}")
        return []

def format_plc_data(data):
    try:
        if not data:
            return "No data available"

        formatted_data = ""
        for entry in data:
            # Record ID and PLC ID
            if '_id' in entry:
                formatted_data += f"Record ID: {entry['_id']}\n"
            formatted_data += f"PLC ID: {entry.get('plc_id', 'Unknown')}\n"
            
            # Timestamp
            try:
                timestamp = datetime.fromtimestamp(entry.get('timestamp', 0))
                formatted_data += f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
            except Exception as e:
                formatted_data += f"Timestamp: Invalid\n"
                print(f"Error formatting timestamp: {e}")

            # Variables
            formatted_data += "Variables:\n"
            variables = entry.get('variables', {})
            for var_name, var_data in variables.items():
                formatted_data += f"  {var_name}:\n"
                if isinstance(var_data, dict):
                    # Value and unit
                    if 'value' in var_data:
                        formatted_data += f"    Value: {var_data['value']}"
                        if 'unit' in var_data:
                            formatted_data += f" {var_data['unit']}"
                        formatted_data += "\n"
                    # Normalized value
                    if 'normalized' in var_data:
                        formatted_data += f"    Normalized: {var_data['normalized']:.4f}\n"
                else:
                    # Handle case where var_data is not a dictionary
                    formatted_data += f"    Value: {var_data}\n"

            formatted_data += "-" * 40 + "\n"
        
        return formatted_data

    except Exception as e:
        error_msg = f"Error formatting data: {str(e)}\nRaw data: {data}"
        print(error_msg)  # Debug print
        return error_msg

async def fetch_data():
    try:
        base_url = base_url_entry.get()
        plc_id = plc_id_entry.get() or None
        variable = variable_entry.get() or None

        data = await get_plc_data(base_url, plc_id, None, variable)
        formatted_data = format_plc_data(data)
        
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, formatted_data)
    except Exception as e:
        error_msg = f"Error fetching data: {str(e)}"
        print(error_msg)  # Debug print
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, error_msg)

async def fetch_variables():
    base_url = base_url_entry.get()
    start_time = time.time()
    variables = await get_plc_variables(base_url)
    end_time = time.time()
    elapsed_time = end_time - start_time

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, variables)
    result_text.insert(tk.END, f"\nTime taken: {elapsed_time:.2f} seconds")

async def live_feed_update():
    if live_feed_running.get():
        try:
            data = await get_plc_data(
                base_url_entry.get(),
                plc_id_entry.get() or None,
                None,
                variable_entry.get() or None
            )
            formatted_data = format_plc_data(data)
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, formatted_data)
        except Exception as e:
            print(f"Live feed error: {e}")
        finally:
            if live_feed_running.get():
                root.after(5000, lambda: asyncio.run(live_feed_update()))

def start_live_feed():
    live_feed_running.set(True)
    asyncio.run(live_feed_update())

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
base_url_entry.insert(0, "http://localhost:8000")  # Prepopulate with localhost and FastAPI port
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
fetch_data_button = ttk.Button(main_frame, text="Fetch Data", command=lambda: asyncio.run(fetch_data()))
fetch_data_button.grid(row=4, column=0, sticky=(tk.W, tk.E))

fetch_variables_button = ttk.Button(main_frame, text="Fetch Variables", command=lambda: asyncio.run(fetch_variables()))
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