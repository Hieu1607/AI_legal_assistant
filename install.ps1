# AI Legal Assistant Quick Installer
# Run this script on any Windows machine to setup the project

Write-Host "AI Legal Assistant - Quick Setup"
Write-Host "================================="

# Check prerequisites
Write-Host "Checking prerequisites..."

# Check Git
try {
    git --version | Out-Null
    Write-Host "Git: OK"
} catch {
    Write-Host "❌ Error: Git is not installed. Please install Git first."
    Read-Host -Prompt "Press Enter to exit..."
    return
}

# Check Docker
try {
    docker --version | Out-Null
    Write-Host "Docker: OK"
} catch {
    Write-Host "❌ Error: Docker is not installed. Please install Docker Desktop first."
    Read-Host -Prompt "Press Enter to exit..."
    return
}

# Check if Docker is running
Write-Host "Checking if Docker is running..."
$dockerRunning = $false
$dockerOutput = ""

try {
    $dockerOutput = docker info 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "Docker daemon: Running"
    } else {
        Write-Host "Docker command exit code: $LASTEXITCODE"
        Write-Host "Docker output: $dockerOutput"
    }
} catch {
    Write-Host "Exception caught: $_"
}

if (-not $dockerRunning) {
    Write-Host ""
    Write-Host "❌ Docker Desktop is not running!"
    Write-Host ""
    Write-Host "Please start Docker Desktop first:"
    Write-Host "1. Click on Docker Desktop icon in the system tray"
    Write-Host "2. Or run Docker Desktop from Start menu"
    Write-Host "3. Wait for Docker to start completely (whale icon should be stable)"
    Write-Host ""
    Write-Host "After starting Docker Desktop, please run this script again."
    Write-Host ""
    Read-Host -Prompt "Press Enter to exit..."
    return
}

Write-Host ""
Write-Host "✅ All prerequisites met!"
Write-Host ""

# Move to parent directory to avoid conflicts with project cloning
$originalLocation = Get-Location

# Download and run setup script
Write-Host "Downloading setup script..."
try {
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Hieu1607/AI_legal_assistant_production/main/setup.ps1" -OutFile "ai_legal_setup.ps1"
    Write-Host "Running setup..."
    .\ai_legal_setup.ps1
    Set-Location $originalLocation
    Remove-Item "ai_legal_setup.ps1"
} catch {
    Write-Host "❌ Error downloading or running setup script: $_"
    Read-Host -Prompt "Press Enter to exit..."
    return
}

# Return to original location
Set-Location $originalLocation

Read-Host -Prompt "✅ Press Enter to finish"
