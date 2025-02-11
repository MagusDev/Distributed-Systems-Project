# Set up Minikube's Docker environment
minikube docker-env | Invoke-Expression

# Define the list of services and their build contexts
$services = @(
    @{ name = "api-gateway"; context = "./api_gateway" },
    @{ name = "preprocessor"; context = "./mqtt_data_preprocessor" },
    @{ name = "db-interface"; context = "./db_interface" },
    @{ name = "anomaly-detector"; context = "./anomaly_detector" },
    @{ name = "plc-simulator"; context = "./plc_simulator" }
)

# Loop through each service and build the Docker image
foreach ($service in $services) {
    Write-Host "Building Docker image for service: $($service.name)"
    docker build -t $($service.name) $($service.context)
    Write-Host "Docker image for service $($service.name) built successfully."
}

# Verify that the images are available in Minikube
Write-Host "Listing Docker images in Minikube..."
docker images
