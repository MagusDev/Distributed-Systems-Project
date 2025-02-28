# Kubernetes Deployment Guide

This guide explains how to deploy and test the system using Kubernetes, with specific instructions for local development using Minikube.

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
