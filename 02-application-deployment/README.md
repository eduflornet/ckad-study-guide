# Application Deployment (20%)

## 📚 Topics Covered

### Deployments
- Rolling updates and rollbacks
- Deployment strategies
- Scaling applications
- Resource management

### ReplicaSets
- Desired state management
- Pod template specifications
- Selector matching

### Helm Basics
- Chart structure
- Template usage
- Release management
- Value overrides

## 🛠️ Practice Labs

### Labs: Deployments
- [01. Create and scale deployments](labs/lab01-deployment-basics.md)
- [02. Rolling updates and rollbacks](labs/lab02-rolling-updates.md)
- [03. Deployment strategies](labs/lab03-deployment-strategies.md)

### Labs: Helm
- [04. Install and use Helm charts](labs/lab04-helm-basics.md)
- [05. Create custom Helm charts](labs/lab05-custom-charts.md)
- [06. Manage releases](labs/lab06-helm-releases.md)

## ⚡ Quick Drills

```bash
# Create deployment
kubectl create deployment nginx --image=nginx:1.20

# Scale deployment
kubectl scale deployment nginx --replicas=5

# Update image
kubectl set image deployment/nginx nginx=nginx:1.21

# Check rollout status
kubectl rollout status deployment/nginx

# Rollback deployment
kubectl rollout undo deployment/nginx

# View rollout history
kubectl rollout history deployment/nginx
```

## 🎯 Mock Scenarios

- [Mock 1: Blue-Green deployment](mocks/mock01-blue-green-deployment.md)
- [Mock 2: Canary release strategy](mocks/mock02-canary-release.md)
- [Mock 3: Helm chart deployment](mocks/mock03-helm-deployment.md)

## 🔑 Key Concepts to Master

- [ ] Deployment update strategies (RollingUpdate, Recreate)
- [ ] Resource requests and limits
- [ ] Pod disruption budgets
- [ ] Horizontal Pod Autoscaler
- [ ] Helm chart templating
- [ ] Release management with Helm

## 📝 Common Exam Tasks

1. "Deploy an application with 3 replicas"
2. "Perform a rolling update to a new image version"
3. "Rollback a failed deployment"
4. "Scale an application based on CPU usage"
5. "Deploy an application using Helm"