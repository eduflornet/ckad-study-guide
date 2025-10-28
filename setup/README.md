# Practice Environment Setup

This directory contains scripts and instructions for setting up Kubernetes practice environments for CKAD exam preparation.

## 🎯 Available Options

1. **[Local Development](local-setup/README.md)** - minikube, kind, Docker Desktop
2. **[Cloud Platforms](cloud-setup/README.md)** - GKE, EKS, AKS free tiers
3. **[Remote Labs](remote-labs/README.md)** - Online Kubernetes playgrounds
4. **[Exam Simulation](exam-simulation/README.md)** - Replicate exam environment

## 🚀 Quick Start Recommendations

### For Beginners
Start with **Docker Desktop** or **minikube** for local development:
- Easy to install and manage
- Good for learning basics
- Matches exam single-cluster environment

### For Practice
Use **kind** (Kubernetes in Docker) for advanced practice:
- Multiple node clusters
- Fast cluster creation/deletion
- Good for networking and advanced scenarios

### For Exam Preparation
Use **killercoda** or **Play with Kubernetes** for exam-like experience:
- Browser-based terminals
- No local installation required
- Similar to actual exam environment

## 📋 Prerequisites

### System Requirements
- **OS**: Windows 10/11, macOS 10.14+, or Linux
- **RAM**: Minimum 4GB, Recommended 8GB+
- **CPU**: 2+ cores
- **Disk**: 20GB+ free space for local setups

### Required Tools
```bash
# Install these tools on your system
kubectl      # Kubernetes CLI
docker       # Container runtime
git          # Version control
curl/wget    # For downloading resources
```

## ⚡ One-Command Setup

### Windows (PowerShell)
```powershell
# Run setup script
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup\windows-setup.ps1
```

### macOS/Linux (Bash)
```bash
# Run setup script
chmod +x setup/unix-setup.sh
./setup/unix-setup.sh
```

## 🔧 Manual Installation Guides

Choose your preferred environment:

| Environment | Setup Time | Complexity | Best For |
|-------------|------------|------------|----------|
| [Docker Desktop](local-setup/docker-desktop.md) | 10 min | Easy | Beginners |
| [minikube](local-setup/minikube.md) | 15 min | Easy | Learning |
| [kind](local-setup/kind.md) | 10 min | Medium | Practice |
| [Google Cloud Shell](cloud-setup/gcp.md) | 5 min | Easy | No installation |
| [AWS Cloud9](cloud-setup/aws.md) | 15 min | Medium | AWS users |
| [Azure Cloud Shell](cloud-setup/azure.md) | 5 min | Easy | Azure users |
| [Killercoda](remote-labs/killercoda.md) | 2 min | Easy | Quick practice |

## 🎓 Practice Scenarios by Environment

### Local Development (minikube/kind/Docker Desktop)
- ✅ Pod and deployment creation
- ✅ Services and networking basics
- ✅ ConfigMaps and Secrets
- ✅ Jobs and CronJobs
- ✅ Basic troubleshooting
- ❌ LoadBalancer services (limited)
- ❌ Multiple node scenarios

### Cloud Platforms (GKE/EKS/AKS)
- ✅ All CKAD scenarios
- ✅ LoadBalancer services
- ✅ Persistent volumes
- ✅ Multiple node clusters
- ✅ Real cloud networking
- ❌ Costs money (after free tier)

### Remote Labs
- ✅ Browser-based (no installation)
- ✅ Exam-like environment
- ✅ Pre-configured clusters
- ✅ All CKAD scenarios
- ❌ Session time limits
- ❌ No persistent storage

## 🔄 Environment Management

### Quick Commands
```bash
# Check cluster status
kubectl cluster-info
kubectl get nodes
kubectl get namespaces

# Create practice namespace
kubectl create namespace ckad-practice
kubectl config set-context --current --namespace=ckad-practice

# Reset environment
kubectl delete namespace ckad-practice
kubectl create namespace ckad-practice
```

### Cluster Reset Scripts
- [reset-cluster.sh](scripts/reset-cluster.sh) - Clean up all resources
- [setup-practice.sh](scripts/setup-practice.sh) - Prepare for practice session
- [verify-setup.sh](scripts/verify-setup.sh) - Validate environment

## 📚 Environment-Specific Guides

### Networking Configuration
Different environments handle networking differently:
- **Docker Desktop**: Single node, automatic LoadBalancer
- **minikube**: Requires `minikube tunnel` for LoadBalancer
- **kind**: Requires port mapping for NodePort access
- **Cloud**: Full LoadBalancer support

### Storage Configuration
Storage classes vary by environment:
- **Local**: hostPath or local-path provisioner
- **GKE**: pd-standard, pd-ssd
- **EKS**: gp2, gp3
- **AKS**: managed-premium

### Resource Limits
Be aware of environment limitations:
- **Local**: Limited by system resources
- **Free tiers**: CPU/memory quotas
- **Remote labs**: Session time limits

## 🎯 Exam Environment Simulation

To closely match the CKAD exam environment:

1. **Use Ubuntu terminal** with bash shell
2. **Single cluster** configuration
3. **Pre-installed tools**: kubectl, vim, nano
4. **Time pressure** practice (2-hour sessions)
5. **Browser-based** terminal simulation

See [exam-simulation/README.md](exam-simulation/README.md) for detailed setup.

## 🛠️ Troubleshooting

### Common Issues

#### kubectl not working
```bash
# Check kubectl installation
kubectl version --client

# Check cluster connection
kubectl cluster-info

# Reset kubeconfig
kubectl config view
kubectl config get-contexts
```

#### Docker issues
```bash
# Check Docker status
docker --version
docker ps

# Restart Docker (Windows/Mac)
# Use Docker Desktop interface

# Restart Docker (Linux)
sudo systemctl restart docker
```

#### Port conflicts
```bash
# Check what's using port 8080
netstat -tulpn | grep 8080  # Linux/Mac
netstat -an | findstr 8080  # Windows

# Kill process using port
sudo kill -9 $(lsof -t -i:8080)  # Linux/Mac
taskkill /PID <PID> /F           # Windows
```

### Getting Help
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Reference](https://kubernetes.io/docs/reference/kubectl/)
- [Docker Documentation](https://docs.docker.com/)

## 📈 Practice Recommendations

### Daily Practice (30-60 minutes)
1. **Start environment** (2 minutes)
2. **Warm-up commands** (5 minutes) - basic kubectl
3. **Domain practice** (20-40 minutes) - focused on one domain
4. **Quick challenges** (10 minutes) - speed exercises
5. **Clean up** (3 minutes)

### Weekly Schedule
- **Monday**: Application Design and Build
- **Tuesday**: Application Deployment
- **Wednesday**: Environment, Configuration and Security
- **Thursday**: Services and Networking
- **Friday**: Application Observability and Maintenance
- **Saturday**: Mock exam practice
- **Sunday**: Review and weak area focus

---

*Choose your environment and start practicing! Consistency is key to CKAD success.*