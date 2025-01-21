from confluent_kafka import Producer
import json

# Kafka configuration
config = {
    'bootstrap.servers': 'localhost:9092',
    'client.id': 'python-producer'
}
producer = Producer(config)

def delivery_report(err, msg):
    """Callback for delivery reports."""
    if err is not None:
        print(f"Delivery failed for record {msg.key()}: {err}")
    else:
        print(f"Record {msg.key()} successfully produced to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def produce_data():
    topic = "mytopic"
    for i in range(10):
        record_key = f"key-{i}"
        record_value = json.dumps({"count": i})
        producer.produce(
            topic=topic,
            key=record_key,
            value=record_value,
            callback=delivery_report
        )
        producer.poll(0)

    producer.flush()  # Ensure all messages are sent

def send_data():
	producer.produce(
	topic="mytopic",
	key="mykey",
	value="Hello from python client for kafka",
	callback=delivery_report
	)
	producer.poll(0)
	producer.flush()

if __name__ == "__main__":
    ##produce_data()
    send_data()

