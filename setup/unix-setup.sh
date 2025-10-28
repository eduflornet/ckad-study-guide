#!/bin/bash

# Unix/Linux/macOS Setup Script for CKAD Practice
echo "=== CKAD Practice Environment Setup ==="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        elif command_exists pacman; then
            echo "arch"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

OS=$(detect_os)
echo -e "${CYAN}Detected OS: $OS${NC}"
echo ""

# Install package manager for macOS if needed
if [[ "$OS" == "macos" ]] && ! command_exists brew; then
    echo -e "${YELLOW}Installing Homebrew package manager...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Install kubectl
if ! command_exists kubectl; then
    echo -e "${YELLOW}Installing kubectl...${NC}"
    case $OS in
        "ubuntu")
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
            rm kubectl
            ;;
        "centos")
            cat <<EOF | sudo tee /etc/yum.repos.d/kubernetes.repo
[kubernetes]
name=Kubernetes
baseurl=https://packages.cloud.google.com/yum/repos/kubernetes-el7-\$basearch
enabled=1
gpgcheck=1
gpgkey=https://packages.cloud.google.com/yum/doc/rpm-package-key.gpg
EOF
            sudo yum install -y kubectl
            ;;
        "macos")
            brew install kubectl
            ;;
        *)
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            chmod +x kubectl
            sudo mv kubectl /usr/local/bin/
            ;;
    esac
    echo -e "${GREEN}kubectl installed successfully ✓${NC}"
else
    echo -e "${GREEN}kubectl already installed ✓${NC}"
fi

# Install Docker
if ! command_exists docker; then
    echo -e "${YELLOW}Installing Docker...${NC}"
    case $OS in
        "ubuntu")
            sudo apt-get update
            sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            sudo usermod -aG docker $USER
            ;;
        "centos")
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            sudo yum install -y docker-ce docker-ce-cli containerd.io
            sudo systemctl start docker
            sudo systemctl enable docker
            sudo usermod -aG docker $USER
            ;;
        "macos")
            echo -e "${YELLOW}Please install Docker Desktop from https://www.docker.com/products/docker-desktop${NC}"
            echo -e "${YELLOW}Or use: brew install --cask docker${NC}"
            ;;
        *)
            echo -e "${RED}Please install Docker manually for your system${NC}"
            ;;
    esac
    echo -e "${GREEN}Docker installation completed ✓${NC}"
else
    echo -e "${GREEN}Docker already installed ✓${NC}"
fi

# Install kind (Kubernetes in Docker)
if ! command_exists kind; then
    echo -e "${YELLOW}Installing kind...${NC}"
    case $OS in
        "macos")
            brew install kind
            ;;
        *)
            curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
            chmod +x ./kind
            sudo mv ./kind /usr/local/bin/kind
            ;;
    esac
    echo -e "${GREEN}kind installed successfully ✓${NC}"
else
    echo -e "${GREEN}kind already installed ✓${NC}"
fi

# Install Git
if ! command_exists git; then
    echo -e "${YELLOW}Installing Git...${NC}"
    case $OS in
        "ubuntu")
            sudo apt-get install -y git
            ;;
        "centos")
            sudo yum install -y git
            ;;
        "macos")
            # Git is usually pre-installed on macOS, but install via Homebrew if needed
            brew install git
            ;;
        *)
            echo -e "${RED}Please install Git manually for your system${NC}"
            ;;
    esac
    echo -e "${GREEN}Git installed successfully ✓${NC}"
else
    echo -e "${GREEN}Git already installed ✓${NC}"
fi

# Setup kubectl aliases and completion
echo -e "${YELLOW}Setting up kubectl configuration...${NC}"

# Determine shell configuration file
if [[ "$SHELL" == */zsh ]]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [[ "$SHELL" == */bash ]]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    SHELL_CONFIG="$HOME/.profile"
fi

# Add kubectl aliases and completion
cat << 'EOF' >> "$SHELL_CONFIG"

# CKAD kubectl aliases and configuration
alias k=kubectl
alias kgp='kubectl get pods'
alias kgs='kubectl get svc'
alias kgd='kubectl get deployment'
alias kdp='kubectl describe pod'
alias kds='kubectl describe service'
alias kdd='kubectl describe deployment'

# Quick environment variables for CKAD
export do="--dry-run=client -o yaml"
export now="--force --grace-period=0"

# kubectl completion
if command -v kubectl > /dev/null; then
    source <(kubectl completion bash)
    complete -F __start_kubectl k
fi

echo "CKAD environment loaded! Use 'k' instead of 'kubectl'"
EOF

echo -e "${GREEN}Shell configuration updated with CKAD aliases ✓${NC}"

# Create practice directory structure
PRACTICE_DIR="$HOME/ckad-practice"
if [ ! -d "$PRACTICE_DIR" ]; then
    echo -e "${YELLOW}Creating practice directory at $PRACTICE_DIR...${NC}"
    mkdir -p "$PRACTICE_DIR"/{manifests,solutions,labs,mock-exams}
    echo -e "${GREEN}Practice directory structure created ✓${NC}"
fi

# Create useful scripts
cat << 'EOF' > "$PRACTICE_DIR/reset-cluster.sh"
#!/bin/bash
# Reset cluster for fresh practice session
echo "Resetting cluster for practice..."
kubectl delete namespace ckad-practice --ignore-not-found=true
kubectl create namespace ckad-practice
kubectl config set-context --current --namespace=ckad-practice
echo "Cluster reset complete. Working in namespace: ckad-practice"
EOF

cat << 'EOF' > "$PRACTICE_DIR/verify-setup.sh"
#!/bin/bash
# Verify CKAD practice environment
echo "=== CKAD Environment Verification ==="
echo ""

echo "Checking kubectl..."
kubectl version --client --short

echo "Checking cluster connection..."
kubectl cluster-info

echo "Checking nodes..."
kubectl get nodes

echo "Checking current namespace..."
kubectl config view --minify --output 'jsonpath={..namespace}'
echo ""

echo "Environment verification complete!"
EOF

chmod +x "$PRACTICE_DIR"/*.sh

# Verify installations
echo ""
echo -e "${CYAN}=== Verifying Installation ===${NC}"

# Check each tool
for tool in kubectl docker git kind; do
    if command_exists "$tool"; then
        version=$($tool --version 2>/dev/null | head -n1)
        echo -e "${tool}: ${GREEN}✓${NC} ($version)"
    else
        echo -e "${tool}: ${RED}✗${NC}"
    fi
done

# Check Docker daemon
if docker ps >/dev/null 2>&1; then
    echo -e "Docker daemon: ${GREEN}✓${NC}"
else
    echo -e "Docker daemon: ${YELLOW}✗ (Docker needs to be started)${NC}"
fi

echo ""
echo -e "${CYAN}=== Next Steps ===${NC}"
echo "1. Restart your terminal or run: source $SHELL_CONFIG"
echo "2. Start Docker daemon if not running"
echo "3. Create a kind cluster: kind create cluster --name ckad-practice"
echo "4. Or use Docker Desktop's built-in Kubernetes"
echo "5. Run: kubectl cluster-info to verify connection"
echo "6. Navigate to your CKAD study guide and start practicing!"
echo ""
echo "Practice scripts created in: $PRACTICE_DIR"
echo "- reset-cluster.sh: Clean environment for practice"
echo "- verify-setup.sh: Check environment status"
echo ""
echo -e "${GREEN}Happy practicing! 🚀${NC}"