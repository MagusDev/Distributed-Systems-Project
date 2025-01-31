import grpc
import scada_pb2
import scada_pb2_grpc
import tkinter as tk
from tkinter import ttk, messagebox
from google.protobuf.empty_pb2 import Empty

# gRPC Client Setup
def get_plc_data(hours=1, plc_id=None, variable=None):
    """Fetch PLC data from the gRPC server."""
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = scada_pb2_grpc.SCADAServiceStub(channel)
        response = stub.GetPLCData(scada_pb2.PLCDataRequest(
            plc_id=plc_id,
            hours=hours,
            variable=variable
        ))
        return response.data

# GUI Application
class PLCDataApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA PLC Data Viewer")
        self.root.geometry("800x600")

        # Create a notebook (tabbed interface)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Latest Data Tab
        self.latest_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.latest_tab, text="Latest Data")

        # Previous Data Tab
        self.previous_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.previous_tab, text="Previous Data")

        # Initialize Latest Data Tab
        self.init_latest_tab()
        self.init_previous_tab()

    def init_latest_tab(self):
        """Initialize the Latest Data tab."""
        # Create a listbox to display data points
        self.latest_listbox = tk.Listbox(self.latest_tab, width=100, height=20)
        self.latest_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add a scrollbar
        scrollbar = tk.Scrollbar(self.latest_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.latest_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.latest_listbox.yview)

        # Bind click event to show details
        self.latest_listbox.bind('<<ListboxSelect>>', self.show_details)

        # Load latest data
        self.load_latest_data()

    def init_previous_tab(self):
        """Initialize the Previous Data tab."""
        # Create a listbox to display data points
        self.previous_listbox = tk.Listbox(self.previous_tab, width=100, height=20)
        self.previous_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add a scrollbar
        scrollbar = tk.Scrollbar(self.previous_listbox)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.previous_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.previous_listbox.yview)

        # Bind click event to show details
        self.previous_listbox.bind('<<ListboxSelect>>', self.show_details)

        # Load previous data
        self.load_previous_data()

    def load_latest_data(self):
        """Load the latest 100 PLC data points."""
        data = get_plc_data(hours=1)  # Fetch data from the last hour
        self.latest_listbox.delete(0, tk.END)
        for entry in data[:100]:  # Show only the latest 100 entries
            self.latest_listbox.insert(tk.END, entry)

    def load_previous_data(self):
        """Load previous PLC data points."""
        data = get_plc_data(hours=24)  # Fetch data from the last 24 hours
        self.previous_listbox.delete(0, tk.END)
        for entry in data:
            self.previous_listbox.insert(tk.END, entry)

    def show_details(self, event):
        """Show details of the selected data point."""
        # Get the selected tab
        current_tab = self.notebook.tab(self.notebook.select(), "text")

        # Get the selected item
        if current_tab == "Latest Data":
            selected_index = self.latest_listbox.curselection()
            if not selected_index:
                return
            selected_item = self.latest_listbox.get(selected_index)
        else:
            selected_index = self.previous_listbox.curselection()
            if not selected_index:
                return
            selected_item = self.previous_listbox.get(selected_index)

        # Show details in a messagebox
        messagebox.showinfo("PLC Data Details", selected_item)

# Run the GUI Application
if __name__ == "__main__":
    root = tk.Tk()
    app = PLCDataApp(root)
    root.mainloop()
    