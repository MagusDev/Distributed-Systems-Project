# Distributed SCADA System for Smart Factory

## Description

This project aims to implement a Distributed Supervisory Control and Data Acquisition (SCADA) system tailored for a smart factory. The system is divided into multiple modules, each addressing a specific functionality:

1. **gRPC-based server and client for calculations** (current module)
2. **Database integration** with MongoDB using PyMongo and FastAPI (planned module)
3. **Asynchronous messaging** using Kafka for real-time communication (upcoming module)

The repository currently includes:

- The server code to handle gRPC requests.
- The client code to make gRPC calls to the server.
- A `.proto` file defining the gRPC service and messages.
- A FastAPI server with CRUD endpoints (database integration not yet implemented).

## Requirements

- Python 3.x
- [gRPC Tools](https://grpc.io/docs/languages/python/quickstart/)
- Recommended: Conda for managing the environment

## Installation

1. Clone this repository to your local machine:

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. (Optional but recommended) Create a Conda environment and activate it:

   ```bash
   conda create -n grpc_env python=3.x -y
   conda activate grpc_env
   ```

3. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Generating gRPC Server Files

If you make changes to the `grpc_server.proto` file, you must regenerate the gRPC Python files. Run the following command from the root directory:

```bash
python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. grpc_server.proto
```

This command generates two files:

- `grpc_server_pb2.py`: Contains the protocol buffer message classes.
- `grpc_server_pb2_grpc.py`: Contains the gRPC service classes.

## Usage

### Running the gRPC Server and Client

1. Start the gRPC server:

   ```bash
   python server.py
   ```

2. Use the gRPC client to make requests:

   ```bash
   python client.py
   ```

### Running the FastAPI Server

The FastAPI server provides CRUD endpoints, but database integration is not yet implemented. Update the `db_service.py` file to provide the correct database URL before starting the server. Once updated, start the server using Uvicorn:

```bash
uvicorn db_service:app --reload
```

Visit the FastAPI interactive API documentation at `http://127.0.0.1:8000/docs` to test the endpoints.

## Future Modules

1. **Database Integration**

   - Implement MongoDB for storing and querying factory data.
   - Integrate the database with the existing FastAPI CRUD endpoints.

2. **Asynchronous Messaging**

   - Incorporate Kafka for real-time asynchronous communication between components.
   - Enable reliable message queuing and distributed data handling.

## Development Notes

- Ensure that any changes to `grpc_server.proto` are reflected by regenerating the Python files as mentioned above.
- Follow best practices for gRPC service design, such as defining clear message structures and service methods in the `.proto` file.
- Future modules will expand the capabilities of this system to cover database integration, real-time messaging, and enhanced system performance.

## License

Include your preferred license here (e.g., MIT, Apache 2.0, etc.).

