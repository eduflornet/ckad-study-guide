# Windows PowerShell Setup Script for CKAD Practice

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "This script requires Administrator privileges. Please run PowerShell as Administrator." -ForegroundColor Red
    exit 1
}

Write-Host "=== CKAD Practice Environment Setup for Windows ===" -ForegroundColor Green
Write-Host ""

# Function to check if command exists
function Test-Command($command) {
    try {
        Get-Command $command -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Install Chocolatey if not present
if (-not (Test-Command "choco")) {
    Write-Host "Installing Chocolatey package manager..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Install required tools
$tools = @("kubernetes-cli", "docker-desktop", "git")

foreach ($tool in $tools) {
    if ($tool -eq "kubernetes-cli" -and (Test-Command "kubectl")) {
        Write-Host "kubectl already installed ✓" -ForegroundColor Green
        continue
    } elseif ($tool -eq "docker-desktop" -and (Test-Command "docker")) {
        Write-Host "Docker already installed ✓" -ForegroundColor Green
        continue
    } elseif ($tool -eq "git" -and (Test-Command "git")) {
        Write-Host "Git already installed ✓" -ForegroundColor Green
        continue
    }
    
    Write-Host "Installing $tool..." -ForegroundColor Yellow
    try {
        choco install $tool -y
        Write-Host "$tool installed successfully ✓" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install $tool ✗" -ForegroundColor Red
    }
}

# Install kind (Kubernetes in Docker)
if (-not (Test-Command "kind")) {
    Write-Host "Installing kind (Kubernetes in Docker)..." -ForegroundColor Yellow
    try {
        curl -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.20.0/kind-windows-amd64
        mkdir -p "$env:ProgramFiles\kind" -ErrorAction SilentlyContinue
        Move-Item kind-windows-amd64.exe "$env:ProgramFiles\kind\kind.exe"
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("PATH", "Machine")
        if ($currentPath -notlike "*$env:ProgramFiles\kind*") {
            [Environment]::SetEnvironmentVariable("PATH", "$currentPath;$env:ProgramFiles\kind", "Machine")
        }
        
        Write-Host "kind installed successfully ✓" -ForegroundColor Green
    } catch {
        Write-Host "Failed to install kind ✗" -ForegroundColor Red
    }
}

# Refresh environment variables
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Setup kubectl aliases and bash completion
Write-Host "Setting up kubectl configuration..." -ForegroundColor Yellow

# Create PowerShell profile if it doesn't exist
if (!(Test-Path $PROFILE)) {
    New-Item -Type File -Path $PROFILE -Force
}

# Add aliases to PowerShell profile
$aliases = @"

# CKAD kubectl aliases
Set-Alias -Name k -Value kubectl
function kgp { kubectl get pods @args }
function kgs { kubectl get svc @args }
function kgd { kubectl get deployment @args }
function kdp { kubectl describe pod @args }
function kds { kubectl describe service @args }
function kdd { kubectl describe deployment @args }

# Quick environment variables for CKAD
`$env:do = "--dry-run=client -o yaml"
`$env:now = "--force --grace-period=0"

Write-Host "CKAD environment loaded! Use 'k' instead of 'kubectl'" -ForegroundColor Green
"@

Add-Content -Path $PROFILE -Value $aliases

Write-Host "PowerShell profile updated with CKAD aliases ✓" -ForegroundColor Green

# Create practice directory structure
$practiceDir = "$env:USERPROFILE\ckad-practice"
if (!(Test-Path $practiceDir)) {
    Write-Host "Creating practice directory at $practiceDir..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $practiceDir -Force
    
    # Create subdirectories
    $subdirs = @("manifests", "solutions", "labs", "mock-exams")
    foreach ($subdir in $subdirs) {
        New-Item -ItemType Directory -Path "$practiceDir\$subdir" -Force
    }
    
    Write-Host "Practice directory structure created ✓" -ForegroundColor Green
}

# Verify installations
Write-Host ""
Write-Host "=== Verifying Installation ===" -ForegroundColor Cyan

$verifications = @(
    @{Name="kubectl"; Command="kubectl version --client"},
    @{Name="docker"; Command="docker --version"},
    @{Name="git"; Command="git --version"}
)

foreach ($verification in $verifications) {
    try {
        $output = Invoke-Expression $verification.Command 2>$null
        Write-Host "$($verification.Name): ✓" -ForegroundColor Green
    } catch {
        Write-Host "$($verification.Name): ✗" -ForegroundColor Red
    }
}

# Check if Docker Desktop is running
try {
    docker ps 2>$null
    Write-Host "Docker daemon: ✓" -ForegroundColor Green
} catch {
    Write-Host "Docker daemon: ✗ (Docker Desktop needs to be started)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Start Docker Desktop application"
Write-Host "2. Enable Kubernetes in Docker Desktop settings"
Write-Host "3. Restart PowerShell to load new aliases"
Write-Host "4. Run 'kubectl cluster-info' to verify Kubernetes connection"
Write-Host "5. Navigate to your CKAD study guide and start practicing!"
Write-Host ""
Write-Host "Alternative: Create a kind cluster with:"
Write-Host "kind create cluster --name ckad-practice"
Write-Host ""
Write-Host "Happy practicing! 🚀" -ForegroundColor Green