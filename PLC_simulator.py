import time
import random
import json
from typing import Dict, Any
import uuid
from pymodbus.server import StartTcpServer as ModbusTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusContext
from pymodbus.datastore.store import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.transaction import ModbusRtuFramer, ModbusTcpFramer

class PLCSimulator:
    def __init__(self, modbus_port=5020):
        self.plc_id = str(uuid.uuid4())
        self.modbus_port = modbus_port
        
        # Initialize PLC variables
        self.variables = {
            'motor_speed': 0.0,      # RPM
            'power_output': 0.0,     # kW
            'system_pressure': 0.0,  # Bar
            'oil_temperature': 0.0   # °C
        }
        
        # Set operating ranges
        self.ranges = {
            'motor_speed': (0.0, 3000.0),
            'power_output': (0.0, 500.0),
            'system_pressure': (0.0, 10.0),
            'oil_temperature': (20.0, 95.0)
        }

        # Set up Modbus server
        self.store = self._create_modbus_store()
        self.server = ModbusTcpServer(self.store, port=self.modbus_port)

    def _create_modbus_store(self):
        # Create a Modbus data store with holding registers for each PLC variable
        block = ModbusSequentialDataBlock(0, [0] * 4)  # For 4 registers (one for each PLC variable)
        context = ModbusSlaveContext(
            hr=block,  # Holding Registers for the PLC variables
        )
        return context

    def simulate_process(self):
        # Simulate changes in PLC variables
        for var_name in self.variables:
            current = self.variables[var_name]
            min_val, max_val = self.ranges[var_name]
            # Simulate gradual changes
            change = random.uniform(-0.1, 0.1) * (max_val - min_val)
            new_value = max(min(current + change, max_val), min_val)
            self.variables[var_name] = round(new_value, 2)

        # Update Modbus holding registers with the latest PLC data
        self.store.getSlave(1).setValues(3, 0, [
            self.variables['motor_speed'],
            self.variables['power_output'],
            self.variables['system_pressure'],
            self.variables['oil_temperature']
        ])

        # Create PLC data reading (for logging or additional usage)
        reading = {
            'plc_id': self.plc_id,
            'timestamp': time.time(),
            'variables': {
                name: {
                    'value': value,
                    'unit': self._get_unit(name)
                }
                for name, value in self.variables.items()
            }
        }
        return reading

    def _get_unit(self, variable_name: str) -> str:
        units = {
            'motor_speed': 'RPM',
            'power_output': 'kW',
            'system_pressure': 'Bar',
            'oil_temperature': '°C'
        }
        return units.get(variable_name, '')

    def run(self):
        print(f"Starting Modbus PLC simulation on port {self.modbus_port}...")
        while True:
            try:
                # Simulate process and update the Modbus registers
                plc_data = self.simulate_process()

                # Log the PLC data (for monitoring)
                print(f"Simulated PLC data: {json.dumps(plc_data, indent=2)}")
                
                # Wait before the next update (can be adjusted based on simulation speed)
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in PLC simulation: {e}")
                time.sleep(1)

if __name__ == "__main__":
    plc = PLCSimulator()
    plc.run()
