# Define the list of pods to troubleshoot
$pods = @(
    "anomaly-detector-846f6bbb6c-nxjkn",
    "api-gateway-6f6f495f5f-qqpfw",
    "db-interface-5dc7dc97fc-bf669",
    "kafka-5c58b8cd77-jvxp7",
    "mqtt-6d86bc998b-fzsm8",
    "plc-simulator-798776c85f-jnjls",
    "preprocessor-598b9b4cfc-57wml",
    "zookeeper-75b9d8c657-4vglb"
)

# Loop through each pod and get logs and description
foreach ($pod in $pods) {
    Write-Host "Fetching logs for pod: $pod"
    try {
        kubectl logs $pod
    } catch {
        Write-Host "Error fetching logs for pod: $pod. The pod might be in a waiting state."
    }

    Write-Host "Describing pod: $pod"
    kubectl describe pod $pod

    Write-Host "Checking for common issues..."
    $description = kubectl describe pod $pod
    if ($description -match "ImagePullBackOff") {
        Write-Host "Pod $pod is experiencing ImagePullBackOff. Ensure the image name is correct and accessible."
    } elseif ($description -match "CrashLoopBackOff") {
        Write-Host "Pod $pod is experiencing CrashLoopBackOff. Check the container logs for more details."
    }
}
