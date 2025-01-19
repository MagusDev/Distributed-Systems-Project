from fastapi import FastAPI, HTTPException, Depends
from pymongo import MongoClient
from typing import Optional, Dict, List
from datetime import datetime, timedelta
from pydantic import BaseModel
import time

app = FastAPI(title="SCADA API Gateway")

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
    def __init__(self, mongo_uri='mongodb://localhost:27017/'):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.scada_db

db = Database()

# Dependency to get database
async def get_db():
    return db.db

# User CRUD operations
@app.post("/users/", response_model=User)
async def create_user(user: UserCreate, db = Depends(get_db)):
    """
    Create a new user (will require admin privileges)
    """
    # TODO: Hash password before storing
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
    user = db.users.find_one({"id": user_id}, {'_id': 0})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=User)
async def update_user(user_id: str, user: UserBase, db = Depends(get_db)):
    """
    Update user details (will require authentication)
    """
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
    client = db.clients.find_one({"id": client_id}, {'_id': 0})
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@app.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client: ClientBase, db = Depends(get_db)):
    """
    Update client details (will require authentication)
    """
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
    result = db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Existing PLC data endpoints
@app.get("/plc/data")
async def get_plc_data(
    plc_id: Optional[str] = None,
    hours: Optional[int] = 1,
    variable: Optional[str] = None,
    db = Depends(get_db)
) -> List[Dict]:
    """
    Get PLC data with optional filtering
    """
    query = {}
    if plc_id:
        query['plc_id'] = plc_id
    if hours:
        query['timestamp'] = {
            '$gte': time.time() - (hours * 3600)
        }

    projection = {'_id': 0}
    
    data = list(db.plc_data.find(
        query,
        projection
    ).sort('timestamp', -1))
    
    if variable and data:
        for entry in data:
            if variable in entry['variables']:
                entry['variables'] = {
                    variable: entry['variables'][variable]
                }
    
    return data

@app.get("/plc/variables")
async def get_plc_variables(db = Depends(get_db)) -> List[str]:
    """
    Get list of available PLC variables
    """
    latest = db.plc_data.find_one(
        sort=[('timestamp', -1)]
    )
    if latest and 'variables' in latest:
        return list(latest['variables'].keys())
    return []

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 