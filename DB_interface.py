import json
from sqlite3 import DataError
from confluent_kafka import Consumer
from pymongo import MongoClient
from datetime import datetime
from monitoring import ServiceMonitor

class DataStorage:
    def __init__(self, kafka_broker='localhost:9092', mongo_uri='mongodb://localhost:27017/', metrics_port=8003):
        self.monitor = ServiceMonitor('db_interface', metrics_port)
        self.kafka_broker = kafka_broker
        self.mongo_uri = mongo_uri

        # Set up Kafka Consumer
        self.consumer = Consumer({
            'bootstrap.servers': self.kafka_broker,
            'group.id': 'db_storage_group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(['plc_data'])

        # Set up MongoDB Client
        self.mongo_client = MongoClient(self.mongo_uri)
        self.db = self.mongo_client['plc_data_db']
        self.collection = self.db['plc_data']

    def store_plc_data(self, plc_data):
        with self.monitor.track_db_query():
            try:
                self.monitor.db_connections.inc()
                self.collection.insert_one(plc_data)
                self.monitor.messages_total.labels(type='stored').inc()
            except Exception as e:
                self.monitor.messages_failed.inc()
                print(f"Error storing data in MongoDB: {e}")
            finally:
                self.monitor.db_connections.dec()

    def run(self):
        print("Starting Data Storage Service...")
        while True:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == DataError._PARTITION_EOF:
                    print(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                else:
                    print(f"Error: {msg.error()}")
                    continue

            plc_data = json.loads(msg.value().decode('utf-8'))
            self.store_plc_data(plc_data)

if __name__ == "__main__":
    storage = DataStorage()
    storage.run()