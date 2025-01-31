import json
import paho.mqtt.client as mqtt
from confluent_kafka import Producer
from pymongo import MongoClient
from bson.objectid import ObjectId

class DataPreprocessingMicroservice:
    def __init__(self, mqtt_broker="localhost", mqtt_port=1883, mqtt_topic="plc/data",
                 kafka_broker="localhost:9092", kafka_topic="plc_data",
                 mongo_uri="mongodb://localhost:27017/", mongo_db="plc_data_db"):
        # MQTT Configuration
        self.mqtt_broker = mqtt_broker
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic

        # Kafka Configuration
        self.kafka_broker = kafka_broker
        self.kafka_topic = kafka_topic

        # MongoDB Configuration
        self.mongo_uri = mongo_uri
        self.mongo_db = mongo_db

        # Set up MQTT Client
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

        # Set up Kafka Producer
        self.kafka_producer = Producer({
            'bootstrap.servers': self.kafka_broker
        })

        # Set up MongoDB Client
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client[self.mongo_db]
        self.collection = self.db["processed_data"]

    def on_connect(self, client, userdata, flags, rc):
        print("Connected to MQTT broker with result code", rc)
        client.subscribe(self.mqtt_topic)

    def on_message(self, client, userdata, msg):
        try:
            # Decode and process the incoming MQTT message
            data = json.loads(msg.payload.decode("utf-8"))
            processed_data = self.process_data(data)

            # Send processed data to Kafka
            self.send_to_kafka(processed_data)

            # Optionally, store the processed data in MongoDB
            self.store_in_mongodb(processed_data)

            # Print processed data (ensure no ObjectId is present)
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

        # Create processed data without the MongoDB _id field
        processed_data = {
            "plc_id": plc_id,
            "timestamp": timestamp,
            "variables": variables
        }

        return processed_data

    def normalize_value(self, var_name, value):
        ranges = {
            "motor_speed": (0.0, 3000.0),
            "power_output": (0.0, 500.0),
            "system_pressure": (0.0, 10.0),
            "oil_temperature": (20.0, 95.0)
        }
        min_val, max_val = ranges.get(var_name, (0.0, 1.0))
        return (value - min_val) / (max_val - min_val) if max_val > min_val else 0

    def send_to_kafka(self, data):
        try:
            # Ensure no ObjectId is present in the data
            if "_id" in data:
                del data["_id"]  # Remove the _id field

            # Serialize data to JSON and send to Kafka
            self.kafka_producer.produce(
                self.kafka_topic,
                json.dumps(data).encode("utf-8"),
                callback=self.on_delivery
            )
            self.kafka_producer.flush()  # Ensure the message is sent
            print(f"Data sent to Kafka topic: {self.kafka_topic}")
        except Exception as e:
            print(f"Error sending data to Kafka: {e}")

    def on_delivery(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def store_in_mongodb(self, data):
        try:
            inserted_data = self.collection.insert_one(data)
            print("Data stored in MongoDB")

            # Convert ObjectId to string before using the data elsewhere
            data["_id"] = str(inserted_data.inserted_id)
            
        except Exception as e:
            print(f"Error storing data in MongoDB: {e}")

    def run(self):
        print(f"Starting Data Preprocessing Microservice, listening on {self.mqtt_topic}...")
        self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
        self.mqtt_client.loop_forever()

if __name__ == "__main__":
    service = DataPreprocessingMicroservice()
    service.run()
    