# Step 1: Define the directory containing the Kubernetes manifests
$manifestDir = "C:\Users\Walid\Distributed-Systems-Project\k8s-manifests"  # Replace with the actual path to your manifest files

# Step 2: Check if Minikube is running
Write-Host "Checking Minikube status..."
minikube status
if ($LASTEXITCODE -ne 0) {
    Write-Host "Minikube is not running. Starting Minikube..."
    minikube start
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to start Minikube. Please check your Minikube installation."
        exit 1
    }
}

# Step 3: Deploy the Kubernetes manifests
Write-Host "Deploying Kubernetes manifests..."
Get-ChildItem -Path $manifestDir -Filter *.yaml | ForEach-Object {
    Write-Host "Applying $($_.FullName)..."
    kubectl apply -f $_.FullName
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to apply $($_.FullName)."
        exit 1
    }
}

# Step 4: Verify the deployment
Write-Host "Checking pods..."
kubectl get pods

Write-Host "Checking services..."
kubectl get services

# Step 5: Open Minikube dashboard
Write-Host "Opening Minikube dashboard..."
minikube dashboard
