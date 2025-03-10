import os
import json
import logging
import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaException, KafkaError
from sklearn.cluster import KMeans
from monitoring import ServiceMonitor
from prometheus_client import start_http_server
import joblib
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

class AnomalyDetectionService:
    def __init__(self, kafka_config, kafka_topic="plc_data", metrics_port=8006, model_folder="/app/models", model_filename="kmeans_model.pkl"):
        self.kafka_config = kafka_config
        self.kafka_topic = kafka_topic

        # Initialize the Kafka consumer
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe([self.kafka_topic])

        # Initialize monitoring
        self.monitor = ServiceMonitor('anomaly_detector', metrics_port)
        
        # Initialize counters with labels
        self.monitor.messages_total.labels(type='normal').inc(0)  # Initialize normal messages
        self.monitor.messages_total.labels(type='anomaly').inc(0)  # Initialize anomaly messages
        self.monitor.request_latency.labels(operation='detect')  # Initialize detection latency

        # Define the full path to the model
        self.model_path = os.path.join(model_folder, model_filename)

        # Load the trained model
        self.model = self.load_model()

    def load_model(self):
        """Load the trained KMeans model, waiting if necessary"""
        retries = 10
        wait_time = 5  # Wait 5 seconds before retrying

        while retries > 0:
            if os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                return joblib.load(self.model_path)
            
            logger.warning(f"Model not found at {self.model_path}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retries -= 1

        logger.error(f"Model file not found after multiple attempts: {self.model_path}")
        raise FileNotFoundError(f"Model file not found at {self.model_path}")

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

    def preprocess_data(self, variables):
        """Process and return the data in a format that the model expects."""
        # Expected features based on the model training, ordered correctly
        expected_features = ['motor_speed', 'oil_temperature', 'power_output', 'system_pressure']

        # Initialize a dictionary to store the values of the expected features
        processed_data = {feature: None for feature in expected_features}

        # Map the variable data into the dictionary, if available
        for feature in expected_features:
            if feature in variables:
                processed_data[feature] = variables[feature]['value']
            else:
                processed_data[feature] = np.nan  # Assign NaN if the feature is missing

        # Convert the processed data dictionary into a DataFrame (with 1 row for the current PLC data)
        df = pd.DataFrame([processed_data])

        # Reorder the columns to match the training order explicitly
        df = df[expected_features]

        # Fill missing values (NaN) with 0 or any other value that makes sense for your model
        df = df.fillna(0)

        logger.debug(f"Preprocessed data: {df}")
        return df

    def detect_anomalies(self, data):
        """Detect anomalies using the trained KMeans model"""
        with self.monitor.request_latency.labels(operation='detect').time():
            try:
                # Preprocess data to match the expected feature set
                df = self.preprocess_data(data)

                # Predict cluster labels
                cluster_labels = self.model.predict(df)

                # Identify anomalies (e.g., points that are far from cluster centers)
                anomalies = []
                for i, label in enumerate(cluster_labels):
                    # Use the cluster labels to determine if the point is an anomaly.
                    # We assume -1 or a specific label could indicate an anomaly, depending on your setup.
                    if label == -1:  # Assuming -1 indicates an anomaly
                        anomalies.append(df.iloc[i].to_dict())

                # Track number of anomalies
                if anomalies:
                    self.monitor.messages_total.labels(type='anomaly').inc(len(anomalies))
                else:
                    self.monitor.messages_total.labels(type='normal').inc()

                logger.debug(f"Detected anomalies: {anomalies}")
                return anomalies
            except Exception as e:
                self.monitor.messages_failed.inc()
                logger.error(f"Error in anomaly detection: {e}")
                return []

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

                # Track message size
                self.monitor.request_size.observe(len(msg_value))

                # Detect anomalies
                anomalies = self.detect_anomalies(variables)
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

if __name__ == "__main__":
    # Kafka configuration for the consumer
    kafka_config = {
        'bootstrap.servers': 'kafka:9092',  # Updated to use docker service name
        'group.id': 'anomaly-detection-group',
        'auto.offset.reset': 'earliest',  # Start reading from the beginning of the topic
    }

    # Initialize and run the Anomaly Detection service
    anomaly_service = AnomalyDetectionService(kafka_config=kafka_config, model_folder="/app/models")
    anomaly_service.run()