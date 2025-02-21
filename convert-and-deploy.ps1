# Step 1: Delete existing Minikube cluster and start a new one
minikube delete
minikube start --cpus=4 --memory=8192 --disk-size=20g
minikube addons enable metrics-server

# Step 2: Set up Minikube's Docker environment
minikube docker-env | Invoke-Expression

# Step 3: Define the list of services and their DockerHub images
$services = @(
    @{ name = "api-gateway"; image = "magusdev/api-gateway" },
    @{ name = "preprocessor"; image = "magusdev/preprocessor" },
    @{ name = "db-interface"; image = "magusdev/db-interface" },
    @{ name = "anomaly-detector"; image = "magusdev/anomaly-detector" },
    @{ name = "plc-simulator"; image = "magusdev/plc-simulator" }
)

# Step 4: Create the output directory for Kubernetes manifests
$outputDir = "k8s-manifests"
if (-Not (Test-Path $outputDir)) {
    Remove-Item -Path $outputDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Path $outputDir
}

# Step 5: Convert Docker Compose to Kubernetes manifests using local kompose
$komposePath = Join-Path (Get-Location) "tools\kompose.exe"
if (-Not (Test-Path $komposePath)) {
    Write-Error "Kompose not found. Please run setup-tools.ps1 first."
    exit 1
}
& $komposePath convert -o $outputDir

Write-Host "Kompose conversion completed."

# Step 6: Modify Kubernetes manifests to use DockerHub images
Get-ChildItem -Path $outputDir -Filter *.yaml | ForEach-Object {
    $manifestPath = $_.FullName
    $content = Get-Content -Path $manifestPath -Raw

    foreach ($service in $services) {
        $content = $content -replace "(image:\s)$($service.name)", "`$1$($service.image)"
    }

    # Save the modified manifest
    Set-Content -Path $manifestPath -Value $content
}

Write-Host "Kubernetes manifests updated to use DockerHub images."

# Step 7: Deploy to Kubernetes
kubectl apply -f $outputDir/
Write-Host "Deployment to Kubernetes completed."

# Step 8: Verify deployment
Write-Host "Checking pods..."
kubectl get pods

Write-Host "Checking services..."
kubectl get services

# Step 9: View Kubernetes dashboard using Minikube
Write-Host "Starting Kubernetes dashboard using Minikube..."
minikube dashboard
Write-Host "Kubernetes dashboard is available through Minikube."