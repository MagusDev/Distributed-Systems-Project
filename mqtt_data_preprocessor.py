import json
import paho.mqtt.client as mqtt

class DataPreprocessingMicroservice:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, mqtt_topic="plc/data"):
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        
        # Set up MQTT client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code", rc)
        client.subscribe(self.mqtt_topic)

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            processed_data = self.process_data(data)
            print("Processed Data:", json.dumps(processed_data, indent=2))
        except Exception as e:
            print("Error processing message:", e)
    
    def process_data(self, data):
        # Extract relevant information
        plc_id = data.get("plc_id", "unknown")
        timestamp = data.get("timestamp", 0)
        variables = data.get("variables", {})

        # Apply basic preprocessing
        for var_name, var_data in variables.items():
            value = var_data.get("value", 0)
            # Example: Normalize values (assuming known ranges)
            normalized_value = self.normalize_value(var_name, value)
            var_data["normalized"] = normalized_value
        
        return {
            "plc_id": plc_id,
            "timestamp": timestamp,
            "variables": variables
        }
    
    def normalize_value(self, var_name, value):
        ranges = {
            "motor_speed": (0.0, 3000.0),
            "power_output": (0.0, 500.0),
            "system_pressure": (0.0, 10.0),
            "oil_temperature": (20.0, 95.0)
        }
        min_val, max_val = ranges.get(var_name, (0.0, 1.0))
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0

    def run(self):
        print(f"Starting Data Preprocessing Microservice, listening on {self.mqtt_topic}...")
        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    service = DataPreprocessingMicroservice()
    service.run()
