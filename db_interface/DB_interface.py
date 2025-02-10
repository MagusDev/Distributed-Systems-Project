import json
from sqlite3 import DataError
from confluent_kafka import Consumer, KafkaError
from pymongo import MongoClient
from datetime import datetime
from monitoring import ServiceMonitor
import os
import time

class DataStorage:
    def __init__(self, kafka_broker=None, mongo_uri=None, metrics_port=8003):
        self.monitor = ServiceMonitor('db_interface', metrics_port)
        self.kafka_broker = kafka_broker or os.getenv('KAFKA_BROKER', 'kafka:9092')
        self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')

        # Set up Kafka Consumer with additional configuration
        self.consumer = Consumer({
            'bootstrap.servers': self.kafka_broker,
            'group.id': 'db_storage_group',
            'auto.offset.reset': 'earliest',
            'socket.timeout.ms': 10000,  # 10 seconds
            'session.timeout.ms': 60000,  # 60 seconds
            'heartbeat.interval.ms': 20000,  # 20 seconds
            'max.poll.interval.ms': 300000  # 5 minutes
        })

        # Set up MongoDB Client with timeout
        self.mongo_client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=10000)
        self.db = self.mongo_client['plc_data_db']
        self.collection = self.db['plc_data']

    def test_connections(self):
        # Test MongoDB connection
        try:
            self.mongo_client.server_info()
            print("Successfully connected to MongoDB")
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")

        # Test Kafka connection
        try:
            metadata = self.consumer.list_topics(timeout=10)
            print(f"Successfully connected to Kafka. Available topics: {metadata.topics}")
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}")

    def store_plc_data(self, plc_data):
        with self.monitor.track_db_query():
            try:
                self.monitor.db_connections.inc()
                
                # Log the data being stored
                print("\n=== Storing PLC Data in MongoDB ===")
                print(f"PLC ID: {plc_data.get('plc_id', 'unknown')}")
                print(f"Timestamp: {plc_data.get('timestamp', 0)}")
                print("Variables:")
                for var_name, var_data in plc_data.get('variables', {}).items():
                    print(f"  {var_name}:")
                    print(f"    Value: {var_data.get('value')} {var_data.get('unit', '')}")
                    print(f"    Normalized: {var_data.get('normalized')}")
                print("================================\n")
                
                result = self.collection.insert_one(plc_data)
                print(f"Successfully stored document with ID: {result.inserted_id}")
                self.monitor.messages_total.labels(type='stored').inc()
                
            except Exception as e:
                self.monitor.messages_failed.inc()
                print(f"Error storing data in MongoDB: {e}")
            finally:
                self.monitor.db_connections.dec()

    def run(self):
        print(f"Starting Data Storage Service...")
        print(f"Kafka Broker: {self.kafka_broker}")
        print(f"MongoDB URI: {self.mongo_uri}")
        
        # Test connections before starting
        self.test_connections()

        print("Subscribing to topic: plc_data")
        self.consumer.subscribe(['plc_data'])

        while True:
            try:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        print(f"Reached end of partition: {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                    else:
                        print(f"Error while consuming message: {msg.error()}")
                        if "Connection refused" in str(msg.error()):
                            print("Attempting to reconnect to Kafka...")
                            time.sleep(5)  # Wait before retrying
                    continue

                # Process the message
                try:
                    plc_data = json.loads(msg.value().decode('utf-8'))
                    print("\n=== Received Kafka Message ===")
                    print(f"Topic: {msg.topic()}")
                    print(f"Partition: {msg.partition()}")
                    print(f"Offset: {msg.offset()}")
                    print(f"Message timestamp: {datetime.fromtimestamp(msg.timestamp()[1]/1000)}")
                    print("============================\n")
                    
                    self.store_plc_data(plc_data)
                except Exception as e:
                    print(f"Error processing message: {e}")

            except Exception as e:
                print(f"Unexpected error: {e}")
                time.sleep(1)  # Prevent tight loop in case of persistent errors

if __name__ == "__main__":
    storage = DataStorage()
    storage.run()