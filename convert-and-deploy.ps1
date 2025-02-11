# Step 1: Create the output directory if it doesn't exist
$outputDir = "k8s-manifests"
if (-Not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir
}

# Step 2: Convert Docker Compose to Kubernetes manifests
kompose convert -o $outputDir

# Step 3: Fix unsupported restart policies in the generated manifests
Get-ChildItem -Path $outputDir -Filter *.yaml | ForEach-Object {
    (Get-Content $_.FullName) -replace 'restartPolicy: Always', 'restartPolicy: OnFailure' | Set-Content $_.FullName
}

# Step 4: Deploy to Kubernetes
kubectl apply -f $outputDir/

# Step 5: Verify deployment
Write-Host "Checking pods..."
kubectl get pods

Write-Host "Checking services..."
kubectl get services
