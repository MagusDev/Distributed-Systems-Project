from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pymongo import MongoClient
from bson import ObjectId
from typing import Optional

# Initialize FastAPI app
app = FastAPI()

# MongoDB connection
client = MongoClient("mongodb://localhost:27017/")
db = client["my_database"]
collection = db["my_collection"]

# Define Pydantic models for request and response validation
class Item(BaseModel):
    key: str
    value: str

class UpdateItem(BaseModel):
    value: str

# Helper function to serialize MongoDB documents
def serialize_document(doc):
    doc["id"] = str(doc["_id"])
    del doc["_id"]
    return doc

# CRUD Endpoints
@app.post("/create", response_model=dict)
async def create_item(item: Item):
    try:
        # Insert into MongoDB
        result = collection.insert_one(item.dict())
        return {"id": str(result.inserted_id), "message": "Item created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating item: {e}")

@app.get("/read/{key}", response_model=dict)
async def read_item(key: str):
    try:
        # Fetch from MongoDB
        item = collection.find_one({"key": key})
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")
        return serialize_document(item)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading item: {e}")

@app.put("/update/{key}", response_model=dict)
async def update_item(key: str, item: UpdateItem):
    try:
        # Update in MongoDB
        result = collection.update_one({"key": key}, {"$set": {"value": item.value}})
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Item not found or not modified")
        return {"message": "Item updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating item: {e}")

@app.delete("/delete/{key}", response_model=dict)
async def delete_item(key: str):
    try:
        # Delete from MongoDB
        result = collection.delete_one({"key": key})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found")
        return {"message": "Item deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting item: {e}")

# Run FastAPI with Uvicorn
# Command: uvicorn API_gateway:app --reload
