# Enable strict mode and error handling
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

# Check if Docker Desktop is running
$dockerProcess = Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
if (-not $dockerProcess) {
    Write-Host "Docker Desktop is not running. Starting Docker Desktop..." -ForegroundColor Yellow
    Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    Write-Host "Waiting for Docker Desktop to start (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}

try {
    # Verify Docker is responsive
    docker info
    if ($LASTEXITCODE -ne 0) { 
        throw "Docker is not responding. Please ensure Docker Desktop is running properly."
    }

    # Step 1: Delete existing Minikube cluster and start a new one
    Write-Host "Deleting existing Minikube cluster..."
    minikube delete
    if ($LASTEXITCODE -ne 0) { Write-Host "Note: No existing cluster found. Continuing..." -ForegroundColor Yellow }

    Write-Host "Starting new Minikube cluster..."
    minikube start --driver=docker --cpus=4 --memory=8192 --disk-size=20g
    if ($LASTEXITCODE -ne 0) { throw "Failed to start Minikube cluster" }

    Write-Host "Enabling metrics-server..."
    minikube addons enable metrics-server
    if ($LASTEXITCODE -ne 0) { throw "Failed to enable metrics-server" }

    # Step 2: Set up Minikube's Docker environment
    Write-Host "Setting up Docker environment..."
    minikube docker-env | Invoke-Expression
    if ($LASTEXITCODE -ne 0) { throw "Failed to set up Docker environment" }

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
    if (Test-Path $outputDir) {
        Remove-Item -Path $outputDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $outputDir | Out-Null

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

    # Step 8: Deploy to Kubernetes with validation disabled
    Write-Host "Deploying to Kubernetes..."
    kubectl apply -f $outputDir/ --validate=false
    kubectl apply -f k8s-manifests/spark-cluster.yaml --validate=false
    kubectl apply -f k8s-manifests/kafka.yaml --validate=false
    kubectl apply -f k8s-manifests/anomaly-detector.yaml --validate=false
    if ($LASTEXITCODE -ne 0) { throw "Failed to apply Kubernetes manifests" }

    # Add delay to allow services to start
    Write-Host "Waiting for services to initialize (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # Step 9: Verify deployment
    Write-Host "Verifying deployment..."
    kubectl wait --for=condition=ready pod --all --timeout=300s
    if ($LASTEXITCODE -ne 0) { throw "Not all pods are ready" }

    kubectl get pods
    kubectl get services

    # Step 10: Launch dashboard
    Write-Host "Launching Kubernetes dashboard..."
    Start-Process powershell -ArgumentList "minikube dashboard"

    Write-Host "Deployment completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}