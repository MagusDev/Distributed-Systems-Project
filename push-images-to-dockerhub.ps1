# DockerHub username
$username = "magusdev"

# Define the list of services and their build contexts
$services = @(
    @{ name = "api-gateway"; context = "./api_gateway" },
    @{ name = "preprocessor"; context = "./mqtt_data_preprocessor" },
    @{ name = "db-interface"; context = "./db_interface" },
    @{ name = "anomaly-detector"; context = "./anomaly_detector" },
    @{ name = "plc-simulator"; context = "./plc_simulator" }
)

# Loop through each service, build the Docker image, and push to DockerHub
foreach ($service in $services) {
    $imageName = "$username/$($service.name)"
    Write-Host "Building Docker image for service: $($service.name)"
    docker build -t $imageName $($service.context)
    Write-Host "Docker image for service $($service.name) built successfully."

    Write-Host "Pushing Docker image to DockerHub: $imageName"
    docker push $imageName
    Write-Host "Docker image for service $($service.name) pushed to DockerHub successfully."
}

# Verify that the images are available on DockerHub
Write-Host "Listing Docker images..."
docker images
