import time
from fastapi import FastAPI, HTTPException, Depends, Request
from pymongo import MongoClient
from typing import Optional, Dict, List
from datetime import datetime
from pydantic import BaseModel
from monitoring import ServiceMonitor
import os
import asyncio

app = FastAPI(title="SCADA API Gateway")

# Initialize monitoring
monitor = ServiceMonitor('api_gateway', 8004)

# Data Models
class UserBase(BaseModel):
    username: str
    email: str
    role: str  # 'admin', 'operator', 'viewer'

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    name: str
    description: Optional[str] = None
    api_key: Optional[str] = None
    permissions: List[str] = []  # List of allowed operations

class ClientCreate(ClientBase):
    pass

class Client(ClientBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Database connection
class Database:
    def __init__(self):
        # Get MongoDB URI from environment variable with fallback
        self.mongo_uri = os.getenv('MONGO_URI', 'mongodb://mongodb:27017/')
        print(f"Connecting to MongoDB at: {self.mongo_uri}")
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test the connection
            self.client.server_info()
            print("Successfully connected to MongoDB")
            self.db = self.client.plc_data_db
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

# Update database initialization
db = None

# Dependency to get database with connection retry
async def get_db():
    global db
    if db is None:
        max_retries = 5
        retry_delay = 1
        for attempt in range(max_retries):
            try:
                db = Database().db
                return db
            except Exception as e:
                if attempt == max_retries - 1:
                    raise HTTPException(
                        status_code=503,
                        detail=f"Database connection failed after {max_retries} attempts"
                    )
                print(f"Database connection attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
    return db

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    with monitor.request_latency.labels(
        method=request.method,
        endpoint=request.url.path
    ).time():
        with monitor.requests_in_progress.track_inprogress():
            response = await call_next(request)
            monitor.request_size.observe(len(await request.body()))
            return response

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# User CRUD operations
@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db = Depends(get_db)):
    """
    Create a new user (will require admin privileges)
    """
    with monitor.track_db_query():
        user_dict = user.dict()
        user_dict['created_at'] = datetime.now()
        user_dict['id'] = str(time.time())  # Temporary ID generation
        
        result = db.users.insert_one(user_dict)
        return user_dict

@app.get("/users/{user_id}", response_model=User)
async def read_user(user_id: str, db = Depends(get_db)):
    """
    Get user details (will require authentication)
    """
    with monitor.track_db_query():
        user = db.users.find_one({"id": user_id}, {'_id': 0})
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")
        return user

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserBase, db = Depends(get_db)):
    """
    Update user details (will require authentication)
    """
    with monitor.track_db_query():
        user_data = user.dict(exclude_unset=True)
        result = db.users.update_one(
            {"id": user_id},
            {"$set": user_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
            
        return {**user_data, "id": user_id}

@app.delete("/users/{user_id}")
async def delete_user(user_id: str, db = Depends(get_db)):
    """
    Delete a user (will require admin privileges)
    """
    with monitor.track_db_query():
        result = db.users.delete_one({"id": user_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User deleted successfully"}

# Client CRUD operations
@app.post("/clients/", response_model=Client)
async def create_client(client: ClientCreate, db = Depends(get_db)):
    """
    Create a new client (will require admin privileges)
    """
    with monitor.track_db_query():
        client_dict = client.dict()
        client_dict['created_at'] = datetime.now()
        client_dict['id'] = str(time.time())  # Temporary ID generation
        
        result = db.clients.insert_one(client_dict)
        return client_dict

@app.get("/clients/{client_id}", response_model=Client)
async def read_client(client_id: str, db = Depends(get_db)):
    """
    Get client details (will require authentication)
    """
    with monitor.track_db_query():
        client = db.clients.find_one({"id": client_id}, {'_id': 0})
        if client is None:
            raise HTTPException(status_code=404, detail="Client not found")
        return client

@app.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client: ClientBase, db = Depends(get_db)):
    """
    Update client details (will require authentication)
    """
    with monitor.track_db_query():
        client_data = client.dict(exclude_unset=True)
        result = db.clients.update_one(
            {"id": client_id},
            {"$set": client_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
            
        return {**client_data, "id": client_id}

@app.delete("/clients/{client_id}")
async def delete_client(client_id: str, db = Depends(get_db)):
    """
    Delete a client (will require admin privileges)
    """
    with monitor.track_db_query():
        result = db.clients.delete_one({"id": client_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
        return {"message": "Client deleted successfully"}

# Existing PLC data endpoints
@app.get("/plc/data")
async def get_plc_data(
    plc_id: Optional[str] = None,
    variable: Optional[str] = None,
    db = Depends(get_db)
) -> List[Dict]:
    """
    Get the latest PLC data for each PLC with optional filtering
    """
    with monitor.track_db_query():
        pipeline = [
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$plc_id",
                "latest_data": {"$first": "$$ROOT"}
            }},
            {"$replaceRoot": {"newRoot": "$latest_data"}}
        ]
        
        if plc_id:
            pipeline.insert(0, {"$match": {"plc_id": plc_id}})
        
        data = list(db.plc_data.aggregate(pipeline))
        
        if variable and data:
            for entry in data:
                if variable in entry['variables']:
                    entry['variables'] = {
                        variable: entry['variables'][variable]
                    }
        
        # Convert ObjectId to string
        for entry in data:
            entry['_id'] = str(entry['_id'])
        
        return data

@app.get("/plc/variables")
async def get_plc_variables(db = Depends(get_db)) -> List[str]:
    """
    Get list of available PLC variables
    """
    with monitor.track_db_query():
        latest = db.plc_data.find_one(
            sort=[('timestamp', -1)]
        )
        if latest and 'variables' in latest:
            return list(latest['variables'].keys())
        return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)