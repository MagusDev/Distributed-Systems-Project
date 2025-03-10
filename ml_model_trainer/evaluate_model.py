import joblib
import pandas as pd
from sklearn.metrics import silhouette_score
from pymongo import MongoClient
import os

def load_model(model_path):
    return joblib.load(model_path)

def extract_data(mongo_uri, mongo_db, collection_name, batch_size=100):
    mongo_client = MongoClient(mongo_uri)
    db = mongo_client[mongo_db]
    collection = db[collection_name]
    cursor = collection.find({}).limit(batch_size)
    data = list(cursor)
    return data

def preprocess_data(data):
    df = pd.DataFrame(data)
    variables = df['variables'].apply(pd.Series)
    variables = variables.applymap(lambda x: x.get('value') if isinstance(x, dict) else np.nan)
    return variables.dropna(axis=1, how='all').fillna(0)

def evaluate_model(model, data):
    labels = model.predict(data)
    score = silhouette_score(data, labels)
    return score

if __name__ == "__main__":
    model_path = "ml_model_trainer/models/kmeans_model.pkl"
    mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
    mongo_db = "plc_data_db"
    collection_name = "plc_data"
    
    model = load_model(model_path)
    data = extract_data(mongo_uri, mongo_db, collection_name)
    preprocessed_data = preprocess_data(data)
    score = evaluate_model(model, preprocessed_data)
    
    print(f"Silhouette Score: {score}")
