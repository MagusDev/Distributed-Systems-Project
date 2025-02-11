# Step 1: Delete existing Minikube cluster and start a new one
minikube delete
minikube start --cpus=4 --memory=8192 --disk-size=20g
minikube addons enable metrics-server

# Step 2: Set up Minikube's Docker environment
minikube docker-env | Invoke-Expression

# Step 3: Define the list of services and their build contexts
$services = @(
    @{ name = "api-gateway"; context = "./api_gateway" },
    @{ name = "preprocessor"; context = "./mqtt_data_preprocessor" },
    @{ name = "db-interface"; context = "./db_interface" },
    @{ name = "anomaly-detector"; context = "./anomaly_detector" },
    @{ name = "plc-simulator"; context = "./plc_simulator" }
)

# Step 4: Loop through each service and build the Docker image in Minikube's Docker environment
foreach ($service in $services) {
    Write-Host "Building Docker image for service: $($service.name)"
    docker build -t $($service.name) $($service.context)
    Write-Host "Docker image for service $($service.name) built successfully."
}

# Step 5: Verify that the images are available in Minikube
Write-Host "Listing Docker images in Minikube..."
docker images

# Step 6: Create the output directory for Kubernetes manifests
$outputDir = "k8s-manifests"
if (-Not (Test-Path $outputDir)) {
    Remove-Item -Path $outputDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $outputDir
}

# Step 7: Convert Docker Compose to Kubernetes manifests using local kompose
$komposePath = Join-Path (Get-Location) "tools\kompose.exe"
if (-Not (Test-Path $komposePath)) {
    Write-Error "Kompose not found. Please run setup-tools.ps1 first."
    exit 1
}
& $komposePath convert -o $outputDir

Write-Host "Kompose conversion completed."

# Step 8: Modify Kubernetes manifests to use local images and set `imagePullPolicy: Never`
Get-ChildItem -Path $outputDir -Filter *.yaml | ForEach-Object {
    $manifestPath = $_.FullName
    $content = Get-Content -Path $manifestPath -Raw

    # Use regex to add `imagePullPolicy: Never` after the `image` field
    $content = $content -replace '(image:\s.*)', "`$1`n          imagePullPolicy: Never"

    # Save the modified manifest
    Set-Content -Path $manifestPath -Value $content
}

Write-Host "Kubernetes manifests updated to use local images."

# Step 9: Deploy to Kubernetes
kubectl apply -f $outputDir/
Write-Host "Deployment to Kubernetes completed."

# Step 10: Verify deployment
Write-Host "Checking pods..."
kubectl get pods

Write-Host "Checking services..."
kubectl get services

# Step 11: View Kubernetes dashboard using Minikube
Write-Host "Starting Kubernetes dashboard using Minikube..."
minikube dashboard
Write-Host "Kubernetes dashboard is available through Minikube."