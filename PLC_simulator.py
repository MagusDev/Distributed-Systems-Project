import time
import random
from confluent_kafka import Producer
import json
from typing import Dict, Any
import uuid

class PLCSimulator:
    def __init__(self, kafka_broker='localhost:9092'):
        self.producer = Producer({'bootstrap.servers': kafka_broker})
        self.plc_id = str(uuid.uuid4())
        
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

    def simulate_process(self) -> Dict[str, Any]:
        # Simulate changes in PLC variables
        for var_name in self.variables:
            current = self.variables[var_name]
            min_val, max_val = self.ranges[var_name]
            # Simulate gradual changes
            change = random.uniform(-0.1, 0.1) * (max_val - min_val)
            new_value = max(min(current + change, max_val), min_val)
            self.variables[var_name] = round(new_value, 2)

        # Create PLC data reading
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
        print("Starting PLC simulation...")
        while True:
            try:
                # Generate PLC data
                plc_data = self.simulate_process()
                
                # Send to storage service
                self.producer.produce(
                    'plc_data',
                    key=self.plc_id,
                    value=json.dumps(plc_data)
                )
                print(f"Sent PLC data: {plc_data}")
                self.producer.flush()
                
                # Wait before next reading
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in PLC simulation: {e}")
                time.sleep(1)

if __name__ == "__main__":
    plc = PLCSimulator()
    plc.run() 