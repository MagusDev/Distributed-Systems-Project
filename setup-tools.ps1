# Create tools directory
$toolsDir = ".\tools"
if (-Not (Test-Path $toolsDir)) {
    New-Item -ItemType Directory -Path $toolsDir
}

# Download kompose
$komposeUrl = "https://github.com/kubernetes/kompose/releases/download/v1.31.2/kompose-windows-amd64.exe"
$komposePath = Join-Path $toolsDir "kompose.exe"
Invoke-WebRequest -Uri $komposeUrl -OutFile $komposePath

Write-Host "Kompose downloaded to: $komposePath"
