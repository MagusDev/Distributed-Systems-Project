import json
import paho.mqtt.client as mqtt
from confluent_kafka import Producer
from pymongo import MongoClient
from bson.objectid import ObjectId
from monitoring import ServiceMonitor
import time
import socket
import os

class DataPreprocessingMicroservice:
    def __init__(self, mqtt_broker=None, mqtt_port=1883, mqtt_topic="plc/data",
                 kafka_broker=None, kafka_topic="plc_data",
                 mongo_uri=None, mongo_db="plc_data_db",
                 metrics_port=8002):
        # Initialize monitoring
        self.monitor = ServiceMonitor('preprocessor', metrics_port)
        
        # Get connection details from environment variables
        self.mqtt_broker = mqtt_broker or os.getenv('MQTT_BROKER', 'mqtt')  # Use Docker service name
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic

        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'kafka:9092')  # Use Docker service name
        self.kafka_topic = kafka_topic

        self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')  # Use Docker service name
        self.mongo_db = mongo_db

        # Set up MQTT Client with protocol version 5
        self.mqtt_client = mqtt.Client(protocol=mqtt.MQTTv5)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.on_disconnect = self.on_disconnect  # Add disconnect handler

        # Set up Kafka Producer with error handling
        self.kafka_producer = Producer({
            'bootstrap.servers': self.kafka_broker,
            'socket.timeout.ms': 10000,  # 10 seconds timeout
            'message.timeout.ms': 10000
        })

        # Set up MongoDB Client with timeout
        self.mongo_client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client[self.mongo_db]
        self.collection = self.db["processed_data"]

    def on_connect(self, client, userdata, flags, rc, properties=None):
        """Handle connection with MQTTv5"""
        print("Connected to MQTT broker with result code", rc)
        client.subscribe(self.mqtt_topic)

    def on_disconnect(self, client, userdata, rc):
        """Handle MQTT disconnect events"""
        print(f"Disconnected from MQTT broker with result code {rc}")
        if rc != 0:
            print("Unexpected disconnection. Will attempt to reconnect...")

    def on_message(self, client, userdata, msg):
        with self.monitor.request_latency.labels(operation='process_message').time():
            try:
                self.monitor.messages_total.labels(type='processed').inc()
                self.monitor.requests_in_progress.inc()
                
                # Decode and process the incoming MQTT message
                data = json.loads(msg.payload.decode("utf-8"))
                print("\n=== Received MQTT Message ===")
                print(f"Topic: {msg.topic}")
                print(f"PLC ID: {data.get('plc_id', 'unknown')}")
                print(f"Timestamp: {data.get('timestamp', 0)}")
                print("Input Variables:")
                for var_name, var_data in data.get('variables', {}).items():
                    print(f"  {var_name}: {var_data.get('value')} {var_data.get('unit', '')}")
                
                processed_data = self.process_data(data)

                print("\n=== Processed Data ===")
                print(f"PLC ID: {processed_data['plc_id']}")
                print("Processed Variables:")
                for var_name, var_data in processed_data['variables'].items():
                    print(f"  {var_name}:")
                    print(f"    Value: {var_data.get('value')} {var_data.get('unit', '')}")
                    print(f"    Normalized: {var_data.get('normalized')}")
                print("==================\n")

                # Track message size
                self.monitor.request_size.observe(len(msg.payload))

                # Send processed data to Kafka
                self.send_to_kafka(processed_data)

                # Store in MongoDB
                with self.monitor.db_query_latency.time():
                    self.store_in_mongodb(processed_data)

            except Exception as e:
                self.monitor.messages_failed.inc()
                print("Error processing message:", e)
            finally:
                self.monitor.requests_in_progress.dec()

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
        with self.monitor.request_latency.labels(operation='send_to_kafka').time():
            try:
                if "_id" in data:
                    del data["_id"]

                self.kafka_producer.produce(
                    self.kafka_topic,
                    json.dumps(data).encode("utf-8"),
                    callback=self.on_delivery
                )
                self.kafka_producer.flush()
            except Exception as e:
                self.monitor.messages_failed.inc()
                print(f"Error sending data to Kafka: {e}")

    def on_delivery(self, err, msg):
        if err is not None:
            print(f"Message delivery failed: {err}")
        else:
            print(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def store_in_mongodb(self, data):
        with self.monitor.db_query_latency.time():
            try:
                self.monitor.db_connections.inc()
                inserted_data = self.collection.insert_one(data)
                data["_id"] = str(inserted_data.inserted_id)
            except Exception as e:
                self.monitor.messages_failed.inc()
                print(f"Error storing data in MongoDB: {e}")
            finally:
                self.monitor.db_connections.dec()

    def run(self):
        print(f"Starting Data Preprocessing Microservice...")
        print(f"MQTT Broker: {self.mqtt_broker}:{self.mqtt_port}")
        print(f"Kafka Broker: {self.kafka_broker}")
        print(f"MongoDB URI: {self.mongo_uri}")
        
        max_retries = 5
        retry_delay = 1

        # Test MongoDB connection
        try:
            self.mongo_client.server_info()
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

        # Test Kafka connection
        try:
            self.kafka_producer.list_topics(timeout=10)
            print("Successfully connected to Kafka")
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")

        for attempt in range(max_retries):
            try:
                print(f"Attempting to connect to MQTT broker (Attempt {attempt + 1}/{max_retries})")
                self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
                print("Successfully connected to MQTT broker")
                self.mqtt_client.loop_forever()
                break
            except (socket.error, ConnectionRefusedError) as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print("Max retries reached. Exiting.")
                    break

if __name__ == "__main__":
    service = DataPreprocessingMicroservice()
    service.run()