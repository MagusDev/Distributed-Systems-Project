import json
import numpy as np
import pandas as pd
from pymongo import MongoClient, errors
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib
import os
import time
import logging

# Setting up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

class MLModelTrainer:
    def __init__(self, mongo_uri=None, mongo_db="plc_data_db", collection_name="processed_data", batch_size=100, wait_time=10, n_clusters=5):
        self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
        self.mongo_db = mongo_db
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.wait_time = wait_time
        self.n_clusters = n_clusters
        self.model_path = "/app/models/kmeans_model.pkl"
        self.feature_names_path = "/app/models/feature_names.pkl"
        self.current_model = self.load_model()
        self.feature_names = self.load_feature_names()
        self.mongo_client = self.connect_to_mongo()
        self.db = self.mongo_client[self.mongo_db]
        self.collection = self.db[self.collection_name]

    def connect_to_mongo(self):
        retries = 5
        while retries > 0:
            try:
                logging.debug("Connecting to MongoDB.")
                client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
                client.server_info()
                logging.debug("MongoDB connected successfully.")
                return client
            except errors.ServerSelectionTimeoutError as e:
                retries -= 1
                logging.error(f"MongoDB connection failed. Retries left: {retries}. Error: {str(e)}")
                if retries == 0:
                    raise Exception("Unable to connect to MongoDB after multiple retries.")
                time.sleep(5)
        raise Exception("Unable to establish MongoDB connection.")

    def load_model(self):
        if os.path.exists(self.model_path):
            logging.debug("Loading existing model.")
            return joblib.load(self.model_path)
        logging.debug("No existing model found.")
        return None

    def load_feature_names(self):
        if os.path.exists(self.feature_names_path):
            logging.debug("Loading existing feature names.")
            return joblib.load(self.feature_names_path)
        logging.debug("No existing feature names found.")
        return None

    def extract_data(self):
        logging.debug("Extracting data from MongoDB.")
        cursor = self.collection.find({}).limit(self.batch_size)
        data = list(cursor)
        if data:
            logging.debug(f"Extracted {len(data)} documents.")
        else:
            logging.debug("No data found.")
        return data

    def preprocess_data(self, data):
        """Preprocess the incoming data and ensure it's in the correct order."""
        df = pd.DataFrame(data)

        # Ensure 'variables' column exists and contains the right data
        if 'variables' not in df.columns:
            raise ValueError("The input data does not contain a 'variables' field.")
        
        # Extract the 'value' from the 'variables' field
        variables = df['variables'].apply(pd.Series)
        
        # Expected features that the model was trained on, in the correct order
        expected_features = ['motor_speed', 'oil_temperature', 'power_output', 'system_pressure']

        # Initialize a dictionary to store the values of the expected features
        processed_data = {feature: None for feature in expected_features}
        
        # Map the variable values to the corresponding features
        for feature in expected_features:
            if feature in variables.columns:
                processed_data[feature] = variables[feature].apply(lambda x: x.get('value') if isinstance(x, dict) else np.nan)
            else:
                processed_data[feature] = np.nan  # Set to NaN if the feature is missing
        
        # Convert to DataFrame for further processing
        df = pd.DataFrame(processed_data)

        # Ensure the columns are in the correct order
        df = df[expected_features]

        # Fill missing values with 0 (or another suitable value)
        df = df.fillna(0)

        return df

    def train_model(self, data):
        logging.debug("Training KMeans model.")
        kmeans = KMeans(n_clusters=self.n_clusters, random_state=42)
        kmeans.fit(data)
        self.feature_names = data.columns.tolist()  # Store feature names
        return kmeans

    def evaluate_model(self, model, data):
        logging.debug("Evaluating model.")
        if self.feature_names is None:
            raise ValueError("Feature names are not set. Ensure the model was trained with feature names.")
        
        # Ensure the feature names match
        if self.feature_names != list(data.columns):
            raise ValueError("The feature names should match those that were passed during fit.")
        
        labels = model.predict(data)
        unique_labels = np.unique(labels)
        
        if len(unique_labels) < 2:
            logging.warning("Only one cluster found or too few samples. Silhouette score cannot be calculated.")
            return -1

        try:
            score = silhouette_score(data, labels)
            logging.debug(f"Model evaluation score: {score}")
            return score
        except ValueError as e:
            logging.error(f"Silhouette score calculation failed: {e}")
            return -1

    def save_model(self, model):
        logging.debug("Saving model.")
        joblib.dump(model, self.model_path)
        joblib.dump(self.feature_names, self.feature_names_path)

    def run(self):
        while True:
            data = self.extract_data()
            
            if not data:
                logging.debug(f"No data available. Waiting for {self.wait_time} seconds before checking again.")
                time.sleep(self.wait_time)
                continue

            logging.debug("Data found. Starting model training.")
            preprocessed_data = self.preprocess_data(data)

            while preprocessed_data.shape[0] < self.n_clusters + 1:
                logging.debug(f"Not enough data points to train model. Waiting for more data. Current: {preprocessed_data.shape[0]}, Required: {self.n_clusters + 1}.")
                time.sleep(self.wait_time)
                data = self.extract_data()
                if data:
                    logging.debug(f"Extracted {len(data)} more documents.")
                    new_data = self.preprocess_data(data)
                    preprocessed_data = pd.concat([preprocessed_data, new_data], ignore_index=True)
                else:
                    logging.debug("No new data found. Continuing to wait.")

            n_clusters = min(self.n_clusters, preprocessed_data.shape[0] - 1)
            if n_clusters < 2:
                logging.warning("Not enough data points for clustering. Skipping model training.")
                continue

            self.n_clusters = n_clusters
            new_model = self.train_model(preprocessed_data)
            new_model_score = self.evaluate_model(new_model, preprocessed_data)

            if self.current_model:
                current_model_score = self.evaluate_model(self.current_model, preprocessed_data)
                if new_model_score > current_model_score:
                    logging.debug("New model is better, saving it.")
                    self.save_model(new_model)
                    self.current_model = new_model
            else:
                logging.debug("No current model, saving the new model.")
                self.save_model(new_model)
                self.current_model = new_model

if __name__ == "__main__":
    trainer = MLModelTrainer()
    trainer.run()
