# Distributed SCADA System for Smart Factory

## Description

This project implements a Distributed Supervisory Control and Data Acquisition (SCADA) system for a smart factory environment. The system is designed with a microservices architecture using various technologies for efficient data processing and monitoring.

Key components include:

1. **API Gateway**: Central entry point handling HTTP requests and routing
2. **MQTT Data Preprocessor**: Processes raw data from industrial devices
3. **Database Interface**: Manages interactions with MongoDB
4. **Anomaly Detector**: Monitors data streams for anomalous patterns
5. **PLC Simulator**: Simulates Programmable Logic Controller data for testing
6. **Supporting Infrastructure**: Kafka, MongoDB, MQTT broker, and Zookeeper

## Architecture

The system follows a message-driven microservices architecture:

- **Data Flow**: PLC Simulator → MQTT → Preprocessor → Kafka → Consumers (DB Interface, Anomaly Detector)
- **API Access**: External systems interact through the API Gateway
- **Persistence**: MongoDB stores processed data and system configurations
- **Messaging**: Kafka provides reliable message delivery between services

## Requirements

- Docker and Docker Compose
- Kubernetes cluster (for deployment)
- kubectl CLI tool
- kompose (for converting Docker Compose to Kubernetes manifests)

## Local Development with Docker Compose

### Setup and Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. Start the services using Docker Compose:

   ```bash
   docker-compose up -d
   ```

3. Monitor the logs:
   ```bash
   docker-compose logs -f
   ```

### Service Endpoints

- API Gateway: http://localhost:8000
- MQTT Broker: localhost:1883 (MQTT), http://localhost:9001 (WebSocket)
- MongoDB: localhost:27017

## Containerization

Each service has its own Dockerfile for containerization. Example structure:

```
service/
├── Dockerfile
├── requirements.txt
└── src/
    └── main.py
```

Example Dockerfile:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "src/main.py"]
```

## Kubernetes Deployment

### Converting from Docker Compose

1. Use kompose to convert Docker Compose to Kubernetes manifests(lots of modifications needed after conversion for a healthy deployment, see "Common Issues and Solutions"):

   ```bash
   kompose convert -f docker-compose.yml -o k8s-manifests
   ```

2. Apply the generated manifests:
   ```bash
   kubectl apply -f k8s-manifests/
   ```

### Managing Kubernetes Resources

- **Apply all resources**: `kubectl apply -f k8s-manifests/`
- **Delete all resources**: `kubectl delete -f k8s-manifests/`
- **Delete specific resource types**: `kubectl delete pods,deployments,services,pvc --all`
- **View logs**: `kubectl logs -f deployment/api-gateway`
- **Pod description**: `kubectl describe pod <pod-name>`

### Configuration

The system uses ConfigMaps for configuration. For example, the MQTT configuration:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mqtt-config
data:
  mosquitto.conf: |
    listener 1883
    allow_anonymous true
    persistence false
    log_dest stdout
```

### Common Issues and Solutions

1. **Kafka Cluster ID Mismatch**:

   - Solution: Delete the PVC for Kafka (`kubectl delete pvc kafka-data`) before redeploying

2. **Missing ConfigMaps**:

   - Solution: Create necessary ConfigMaps before deploying services (ex. for MQTT mosquitto)

3. **Liveness Probe Failures**:
   - Solution: Adjust probe parameters or ensure required utilities exist in containers (ex. kafka, zookeeeper, mqtt)

## Module Details

### API Gateway

REST API interface providing access to system functionality and data.

### MQTT Data Preprocessor

Subscribes to MQTT topics, processes incoming data, and forwards to Kafka.

### Database Interface

Consumes processed data from Kafka and stores in MongoDB.

### Anomaly Detector

Analyzes data streams for anomalous patterns and triggers alerts.

### PLC Simulator

Generates simulated industrial data and publishes to MQTT.

## Future Development

- Enhanced anomaly detection with machine learning
- Real-time dashboarding and visualization
- Historical data analysis capabilities
- Multi-cluster deployment support

## Contributing

Please follow standard Git workflow:

1. Fork the repository
2. Create feature branch
3. Submit pull request

## License

MIT
