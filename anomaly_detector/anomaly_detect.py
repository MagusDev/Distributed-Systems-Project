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
        self.model = None
        self.model_available = False

    def load_model(self):
        """Load the trained KMeans model, waiting if necessary"""
        wait_time = 10  # Wait 10 seconds before retrying

        while not self.model_available:
            if os.path.exists(self.model_path):
                logger.info(f"Loading model from {self.model_path}")
                self.model = joblib.load(self.model_path)
                self.model_available = True
                logger.info("Switched to using ML model for anomaly detection.")
                return
            
            logger.warning(f"Model not found at {self.model_path}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

        logger.error(f"Model file not found: {self.model_path}")

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

                # Predict cluster distances
                distances = self.model.transform(df)
                min_distances = distances.min(axis=1)
                max_distance = distances.max()
                probabilities = min_distances / max_distance

                anomaly_likelihoods = []
                for i, probability in enumerate(probabilities):
                    anomaly_likelihoods.append({df.index[i]: probability})

                # Track number of processed messages
                self.monitor.messages_total.labels(type='normal').inc()

                logger.debug(f"Anomaly likelihoods: {anomaly_likelihoods}")
                return anomaly_likelihoods
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
                anomaly_likelihoods = self.detect_anomalies(variables)
                for likelihood in anomaly_likelihoods:
                    if likelihood[list(likelihood.keys())[0]] >= 0.5:
                        logger.warning(f"\033[91mAnomaly Detected for PLC {plc_id} at {timestamp}: {likelihood}\033[0m")
                    else:
                        logger.info(f"Anomaly likelihood for PLC {plc_id} at {timestamp}: {likelihood}")

            except Exception as e:
                self.monitor.messages_failed.inc()
                logger.error(f"Error processing data: {e}")
            finally:
                self.monitor.requests_in_progress.dec()

    def run(self):
        """Run the consumer and detect anomalies continuously"""
        logger.info("Anomaly detection service started with metrics on port 8006")

        while not self.model_available:
            self.load_model()

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