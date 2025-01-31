from concurrent import futures
import grpc
import time
from pymongo import MongoClient
from datetime import datetime
from google.protobuf.empty_pb2 import Empty
import scada_pb2
import scada_pb2_grpc

# Database connection
class Database:
    def __init__(self, mongo_uri='mongodb://localhost:27017/'):
        self.client = MongoClient(mongo_uri)
        self.db = self.client.scada_db

db = Database()

# gRPC Service Implementation
class SCADAService(scada_pb2_grpc.SCADAServiceServicer):
    def CreateUser(self, request, context):
        user_dict = {
            "username": request.username,
            "email": request.email,
            "role": request.role,
            "created_at": datetime.now().isoformat(),
            "id": str(time.time()),
        }
        db.db.users.insert_one(user_dict)
        return scada_pb2.UserResponse(user=scada_pb2.User(**user_dict))

    def GetUser(self, request, context):
        user = db.db.users.find_one({"id": request.id}, {'_id': 0})
        if user is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return scada_pb2.UserResponse()
        return scada_pb2.UserResponse(user=scada_pb2.User(**user))

    def UpdateUser(self, request, context):
        user_data = {
            "username": request.username,
            "email": request.email,
            "role": request.role,
        }
        result = db.db.users.update_one(
            {"id": request.id},
            {"$set": user_data}
        )
        if result.modified_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
            return scada_pb2.UserResponse()
        return scada_pb2.UserResponse(user=scada_pb2.User(**{**user_data, "id": request.id}))

    def DeleteUser(self, request, context):
        result = db.db.users.delete_one({"id": request.id})
        if result.deleted_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("User not found")
        return Empty()

    def CreateClient(self, request, context):
        client_dict = {
            "name": request.name,
            "description": request.description,
            "permissions": request.permissions,
            "created_at": datetime.now().isoformat(),
            "id": str(time.time()),
        }
        db.db.clients.insert_one(client_dict)
        return scada_pb2.ClientResponse(client=scada_pb2.Client(**client_dict))

    def GetClient(self, request, context):
        client = db.db.clients.find_one({"id": request.id}, {'_id': 0})
        if client is None:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Client not found")
            return scada_pb2.ClientResponse()
        return scada_pb2.ClientResponse(client=scada_pb2.Client(**client))

    def UpdateClient(self, request, context):
        client_data = {
            "name": request.name,
            "description": request.description,
            "permissions": request.permissions,
        }
        result = db.db.clients.update_one(
            {"id": request.id},
            {"$set": client_data}
        )
        if result.modified_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Client not found")
            return scada_pb2.ClientResponse()
        return scada_pb2.ClientResponse(client=scada_pb2.Client(**{**client_data, "id": request.id}))

    def DeleteClient(self, request, context):
        result = db.db.clients.delete_one({"id": request.id})
        if result.deleted_count == 0:
            context.set_code(grpc.StatusCode.NOT_FOUND)
            context.set_details("Client not found")
        return Empty()

    def GetPLCData(self, request, context):
        query = {}
        if request.plc_id:
            query['plc_id'] = request.plc_id
        if request.hours:
            query['timestamp'] = {
                '$gte': time.time() - (request.hours * 3600)
            }

        data = list(db.db.plc_data.find(query, {'_id': 0}).sort('timestamp', -1))
        if request.variable and data:
            for entry in data:
                if request.variable in entry['variables']:
                    entry['variables'] = {
                        request.variable: entry['variables'][request.variable]
                    }

        return scada_pb2.PLCDataResponse(data=[str(entry) for entry in data])

    def GetPLCVariables(self, request, context):
        latest = db.db.plc_data.find_one(sort=[('timestamp', -1)])
        if latest and 'variables' in latest:
            return scada_pb2.PLCVariablesResponse(variables=list(latest['variables'].keys()))
        return scada_pb2.PLCVariablesResponse(variables=[])

# Run the gRPC server
def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    scada_pb2_grpc.add_SCADAServiceServicer_to_server(SCADAService(), server)
    server.add_insecure_port('[::]:50051')
    print("gRPC server running on port 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
    