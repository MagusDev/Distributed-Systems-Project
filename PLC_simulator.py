import time
import random
import json
import uuid
import paho.mqtt.client as mqtt

class PLCSimulator:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, mqtt_topic="plc/data"):
        self.plc_id = str(uuid.uuid4())
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        
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
        
        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)

    def simulate_process(self):
        # Simulate changes in PLC variables
        for var_name in self.variables:
            current = self.variables[var_name]
            min_val, max_val = self.ranges[var_name]
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
        print(f"Starting MQTT PLC simulation, publishing to {self.mqtt_topic}...")
        while True:
            try:
                plc_data = self.simulate_process()
                json_data = json.dumps(plc_data)
                
                # Publish data to MQTT broker
                self.mqtt_client.publish(self.mqtt_topic, json_data)
                
                print(f"Published PLC data: {json_data}")
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in PLC simulation: {e}")
                time.sleep(1)

if __name__ == "__main__":
    plc = PLCSimulator()
    plc.run()
