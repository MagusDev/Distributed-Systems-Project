import json
import logging
import numpy as np
import pandas as pd
from confluent_kafka import Consumer, KafkaException, KafkaError
from scipy.stats import zscore

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger()

class AnomalyDetectionService:
    def __init__(self, kafka_config, kafka_topic="plc_data"):
        self.kafka_config = kafka_config
        self.kafka_topic = kafka_topic

        # Initialize the Kafka consumer
        self.consumer = Consumer(self.kafka_config)
        self.consumer.subscribe([self.kafka_topic])

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
        """Detect anomalies based on Z-score or IQR method"""
        # Create a dataframe from the data for easy processing
        df = pd.DataFrame(data)

        anomalies = []
        
        # Check if the data contains numeric columns to apply outlier detection
        for column in df.columns:
            if df[column].dtype in ['float64', 'int64']:  # Only numeric columns
                # Z-score method for anomaly detection
                z_scores = zscore(df[column])
                outliers = np.where(np.abs(z_scores) > 3)  # Z-score > 3 means anomaly
                for index in outliers[0]:
                    anomalies.append({
                        'column': column,
                        'value': df[column].iloc[index],
                        'z_score': z_scores[index]
                    })
        return anomalies

    def process_data(self, msg_value):
        """Process the incoming PLC data"""
        try:
            data = json.loads(msg_value)
            plc_id = data.get("plc_id")
            timestamp = data.get("timestamp")
            variables = data.get("variables", {})

            # Convert the variable values into a list of dictionaries for processing
            variable_data = [
                {'name': var_name, 'value': var_info['value']}
                for var_name, var_info in variables.items()
            ]

            # Detect anomalies
            anomalies = self.detect_anomalies(variable_data)
            if anomalies:
                logger.warning(f"Anomalies detected for PLC {plc_id} at {timestamp}: {anomalies}")
            else:
                logger.info(f"No anomalies detected for PLC {plc_id} at {timestamp}")
        except Exception as e:
            logger.error(f"Error processing data: {e}")

    def run(self):
        """Run the consumer and detect anomalies continuously"""
        logger.info("Anomaly detection service started.")
        while True:
            msg = self.consume_message()
            if msg:
                self.process_data(msg.value().decode('utf-8'))

            # Add sleep or backoff if needed to control the message consumption rate

if __name__ == "__main__":
    # Kafka configuration for the consumer
    kafka_config = {
        'bootstrap.servers': 'localhost:9092',  # Adjust the Kafka broker address
        'group.id': 'anomaly-detection-group',
        'auto.offset.reset': 'earliest',  # Start reading from the beginning of the topic
    }

    # Initialize and run the Anomaly Detection service
    anomaly_service = AnomalyDetectionService(kafka_config=kafka_config)
    anomaly_service.run()
