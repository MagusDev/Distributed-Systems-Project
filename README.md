# Distributed SCADA System for Smart Factory

## Description

This project aims to implement a Distributed Supervisory Control and Data Acquisition (SCADA) system tailored for a smart factory. The system is divided into multiple modules, each addressing a specific functionality:

1. **gRPC-based server and client for calculations** (current module)
2. **Database integration** with MongoDB using PyMongo and FastAPI (upcoming module)
3. **Asynchronous messaging** using Kafka for real-time communication (upcoming module)

The repository currently includes:

- The server code to handle gRPC requests.
- The client code to make gRPC calls to the server.
- A `.proto` file defining the gRPC service and messages.

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

1. Start the gRPC server:

   ```bash
   python server.py
   ```

2. Use the gRPC client to make requests:

   ```bash
   python client.py
   ```

## Future Modules

1. **Database Integration**

   - Implement a MongoDB database for storing and querying factory data.
   - Use FastAPI to create RESTful APIs for interacting with the database.

2. **Asynchronous Messaging**

   - Incorporate Kafka for real-time asynchronous communication between components.
   - Enable reliable message queuing and distributed data handling.

## Development Notes

- Ensure that any changes to `grpc_server.proto` are reflected by regenerating the Python files as mentioned above.
- Follow best practices for gRPC service design, such as defining clear message structures and service methods in the `.proto` file.
- Upcoming modules will expand the capabilities of this system to cover database operations and real-time messaging.

## License

Include your preferred license here (e.g., MIT, Apache 2.0, etc.).

