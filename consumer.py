from confluent_kafka import Consumer, KafkaException
import json

# Kafka configuration
config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'python-consumer-group',
    'auto.offset.reset': 'earliest'  # Start from the beginning
}
consumer = Consumer(config)

def consume_data():
    topic = "mytopic"
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)  # Wait for a message (1 second timeout)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaException._PARTITION_EOF:
                    continue
                else:
                    print(f"Consumer error: {msg.error()}")
                    break

            record_key = msg.key().decode("utf-8") if msg.key() else None          
            ##record_value = json.loads(msg.value().decode("utf-8"))
            record_value = msg.value().decode("utf-8")
            print(f"Consumed record with key {record_key} and value {record_value}")

    except KeyboardInterrupt:
        pass
    finally:
        consumer.close()

if __name__ == "__main__":
    consume_data()

