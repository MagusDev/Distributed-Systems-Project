# Kubernetes Deployment Guide

This guide explains how to deploy and test the system using Kubernetes, with specific instructions for local development using Minikube and deployment on CSC cPouta.

## Running in Kubernetes with Minikube

### Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- Docker

### Setup and Deployment

1. **Start Minikube**

   ```bash
   # Start Minikube with sufficient resources
   minikube start --cpus=4 --memory=8192 --disk-size=20g

   # Enable the Minikube dashboard (optional but recommended)
   minikube dashboard
   ```

2. **Apply Kubernetes Manifests**

   ```bash
   # Apply all manifests from the k8s-manifests directory
   kubectl apply -f k8s-manifests/

   # Check deployment status
   kubectl get pods
   ```

3. **Verify Services**

   ```bash
   # Check that all services are running
   kubectl get services
   ```

4. **Port Forward for Testing**

   Set up port forwarding to access the API Gateway from your local machine:

   ```bash
   # Port forward the API Gateway service
   kubectl port-forward service/api-gateway 8000:8000
   ```

5. **Enabling HPA**

   First add metrics-server to kubernetes:

   ```bash
   kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
   ```

   Then add limits for cpu and memory in deployments under "containers":

   ```yaml
   resources:
     requests:
       cpu: "100m"
       memory: "128Mi"
     limits:
       cpu: "500m"
       memory: "256Mi"
   ```

   Then add HPA manifest for the service with kind HorizontalPodAutoscaler

   Verify with:
   ```bash
   kubectl get hpa
   ```

### Running the Client GUI

To run the client GUI with the Kubernetes-deployed services:

1. **Ensure API Gateway Port Forwarding is Active**

   ```bash
   # Verify API Gateway is accessible
   curl http://localhost:8000/health
   ```

2. **Run the Client GUI**

   ```bash
   # Install required Python packages
   pip install aiohttp tkinter

   # Run the client GUI
   python client_gui.py
   ```

   The client GUI will connect to the API Gateway through the port-forwarding.

### Cleaning Up

When you're done testing, you can clean up resources:

1. **Delete All Deployed Resources**

   ```bash
   # Delete all resources created from the manifest files
   kubectl delete -f k8s-manifests/
   ```

2. **Stop Minikube**

   ```bash
   # Stop the Minikube cluster
   minikube stop

   # To completely delete the Minikube cluster
   minikube delete
   ```

## Deploying on CSC cPouta

### Prerequisites
- ssh into the master node
- Verify containerd and kubectl: `systemctl status containerd && kubectl version`
- Check nodes: `kubectl get nodes`
- Clone repository: `git clone https://github.com/MagusDev/Distributed-Systems-Project.git`

### Storage Configuration

#### PersistentVolume for Kafka
Create `kafka-data-persistentvolume.yaml`:
```yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: kafka-pv
  labels:
    type: local
    app: kafka
spec:
  storageClassName: my-default-sc
  capacity:
    storage: 100Mi
  accessModes: [ReadWriteOnce]
  hostPath:
    path: "/mnt/data/kafka"
```

#### Update PersistentVolumeClaim
Modify kafka-data-persistentvolumeclaim.yaml:
```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  creationTimestamp: null
  labels:
    io.kompose.service: kafka-data
  name: kafka-data
spec:
  # Add this line
  storageClassName: my-default-sc
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Mi
  # Add this line
  volumeName: kafka-pv
status: {}
```
> The changes connect the PVC to our specific PV using the storageClassName and volumeName.

### Prepare Node Storage
```bash
# On each worker node
sudo mkdir -p /mnt/data/kafka
sudo chmod 777 /mnt/data/kafka
```

### Kafka Configuration
Update security context in Kafka deployment to run as root:
```yaml
# Key changes in kafka-deployment.yaml
containers:
  - name: kafka
    # Add security context to run as root
    securityContext:
      runAsUser: 0
      runAsGroup: 0
    # rest of container config...
```
> Running Kafka as root (user 0) solves the permissions issues with volume mounts.

### Metrics Server Configuration
Edit metrics server with command:
```bash
kubectl edit deployment -n kube-system metrics-server
```

Enable insecure TLS in the metrics-server deployment:
```yaml
# Add to metrics-server deployment args
args:
- --kubelet-insecure-tls
```

### Deployment Order
```bash
# 1. Apply PV first
kubectl apply -f kafka-data-persistentvolume.yaml

# 2. Apply PVC
kubectl apply -f kafka-data-persistentvolumeclaim.yaml

# 3. Apply remaining manifests
kubectl apply -f k8s-manifests/
```

### Verification
```bash
kubectl get pods
kubectl get pv,pvc
```

## Managing Kubernetes Resources

- **Apply all resources**: `kubectl apply -f k8s-manifests/`
- **Delete all resources**: `kubectl delete -f k8s-manifests/`
- **Delete specific resource types**: `kubectl delete pods,deployments,services,pvc --all`
- **View logs**: `kubectl logs -f deployment/api-gateway`
- **Pod description**: `kubectl describe pod <pod-name>`

## Troubleshooting

- **Pod not starting**: Check logs with `kubectl logs <pod-name>`
- **Service not accessible**: Verify service is running with `kubectl get svc` and pod is ready with `kubectl get pods`
- **Connection refused**: Ensure port forwarding is active and service is running correctly
- **Kafka Cluster ID Mismatch**: Delete the PVC for Kafka (`kubectl delete pvc kafka-data`) before redeploying
- **Missing ConfigMaps**: Create necessary ConfigMaps before deploying services
- **Liveness Probe Failures**: Adjust probe parameters or ensure required utilities exist in containers
- **Kafka volume permission issues**: Verify PV directory has correct permissions or use the root security context
