# Start Minikube with required resources
Write-Host "Starting Minikube..."
minikube start --cpus=4 --memory=8192 --disk-size=20g

# Configure Docker environment
Write-Host "Configuring Docker environment..."
& minikube -p minikube docker-env | Invoke-Expression

# Enable required addons
Write-Host "Enabling addons..."
minikube addons enable metrics-server
minikube addons enable dashboard
minikube addons enable ingress

# Start dashboard
Write-Host "Starting Kubernetes dashboard..."
Start-Process powershell -ArgumentList "minikube dashboard"

Write-Host "Minikube is ready! Dashboard should open in your browser."
