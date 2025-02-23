import json
import logging
import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaException, KafkaError
from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.clustering import KMeans
from monitoring import ServiceMonitor
from prometheus_client import start_http_server

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

class AnomalyDetectionService:
    def __init__(self, kafka_config, kafka_topic="plc_data", metrics_port=8006):
        self.kafka_config = kafka_config
        self.kafka_topic = kafka_topic

        # Initialize the Kafka consumer
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe([self.kafka_topic])

        # Initialize Spark session
        self.spark = SparkSession.builder.appName("AnomalyDetection").getOrCreate()

        # Initialize monitoring
        self.monitor = ServiceMonitor('anomaly_detector', metrics_port)
        
        # Initialize counters with labels
        self.monitor.messages_total.labels(type='normal').inc(0)  # Initialize normal messages
        self.monitor.messages_total.labels(type='anomaly').inc(0)  # Initialize anomaly messages
        self.monitor.request_latency.labels(operation='detect')  # Initialize detection latency

    def consume_message(self):
        """Consume and process messages from Kafka"""
        try:
            msg = self.consumer.poll(timeout=1.0)
            if msg is None:
                return None
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"End of partition reached {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")
                else:
                    raise KafkaException(msg.error())
            return msg
        except KafkaException as e:
            logger.error(f"Error consuming message: {e}")
            return None

    def detect_anomalies(self, data):
        """Detect anomalies using Spark MLlib"""
        with self.monitor.request_latency.labels(operation='detect').time():
            try:
                # Create a Spark DataFrame from the data
                df = self.spark.createDataFrame(data)

                # Assemble features into a vector
                assembler = VectorAssembler(inputCols=df.columns, outputCol="features")
                df = assembler.transform(df)

                # Use KMeans for clustering and anomaly detection
                kmeans = KMeans().setK(2).setSeed(1)
                model = kmeans.fit(df)
                predictions = model.transform(df)

                # Identify anomalies based on cluster distance
                anomalies = predictions.filter(predictions.prediction == 1).collect()

                # Track number of anomalies
                if anomalies:
                    self.monitor.messages_total.labels(type='anomaly').inc(len(anomalies))
                else:
                    self.monitor.messages_total.labels(type='normal').inc()
                
                return anomalies
            except Exception as e:
                self.monitor.messages_failed.inc()
                raise e

    def process_data(self, msg_value):
        """Process the incoming PLC data"""
        with self.monitor.track_request(operation='process_plc_data'):  # Specify the operation
            try:
                self.monitor.messages_total.labels(type='normal').inc()
                self.monitor.requests_in_progress.inc()
                
                data = json.loads(msg_value)
                plc_id = data.get("plc_id")
                timestamp = data.get("timestamp")
                variables = data.get("variables", {})

                # Convert the variable values into a list of dictionaries for processing
                variable_data = [
                    {'name': var_name, 'value': var_info['value']}
                    for var_name, var_info in variables.items()
                ]

                # Track message size
                self.monitor.request_size.observe(len(msg_value))

                # Detect anomalies
                anomalies = self.detect_anomalies(variable_data)
                if anomalies:
                    logger.warning(f"Anomalies detected for PLC {plc_id} at {timestamp}: {anomalies}")
                else:
                    logger.info(f"No anomalies detected for PLC {plc_id} at {timestamp}")

            except Exception as e:
                self.monitor.messages_failed.inc()
                logger.error(f"Error processing data: {e}")
            finally:
                self.monitor.requests_in_progress.dec()

    def run(self):
        """Run the consumer and detect anomalies continuously"""
        logger.info("Anomaly detection service started with metrics on port 8006")
        while True:
            msg = self.consume_message()
            if msg:
                self.process_data(msg.value().decode('utf-8'))

            # Add sleep or backoff if needed to control the message consumption rate

if __name__ == "__main__":
    # Kafka configuration for the consumer
    kafka_config = {
        'bootstrap.servers': 'kafka:9092',  # Updated to use docker service name
        'group.id': 'anomaly-detection-group',
        'auto.offset.reset': 'earliest',  # Start reading from the beginning of the topic
    }

    # Initialize and run the Anomaly Detection service
    anomaly_service = AnomalyDetectionService(kafka_config=kafka_config)
    anomaly_service.run()