from confluent_kafka import Consumer
import json
from pymongo import MongoClient
from datetime import datetime

class DataStorage:
    def __init__(self, kafka_broker='localhost:9092', mongo_uri='mongodb://localhost:27017/'):
        self.consumer = Consumer({
            'bootstrap.servers': kafka_broker,
            'group.id': 'storage_group',
            'auto.offset.reset': 'earliest'
        })
        self.consumer.subscribe(['plc_data'])
        self.db_client = MongoClient(mongo_uri)
        self.db = self.db_client.scada_db
        
    def store_plc_data(self, plc_data):
        # Add storage timestamp
        plc_data['stored_at'] = datetime.now()
        collection = self.db.plc_data
        collection.insert_one(plc_data)
        print(f"Stored PLC data: {plc_data}")
        
    def run(self):
        print("Starting data storage service...")
        while True:
            try:
                msg = self.consumer.poll(1.0)
                if msg is None:
                    continue
                    
                if msg.error():
                    print(f"Consumer error: {msg.error()}")
                    continue
                    
                plc_data = json.loads(msg.value())
                self.store_plc_data(plc_data)
                
            except Exception as e:
                print(f"Error in storage service: {e}")

if __name__ == "__main__":
    storage = DataStorage()
    storage.run() 