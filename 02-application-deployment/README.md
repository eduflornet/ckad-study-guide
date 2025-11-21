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
🔹 Pods

# Create a simple Pod
kubectl run mypod --image=nginx

# Create Pod with exposed port
kubectl run mypod --image=nginx --port=80

# Create a Pod with environment variables:
kubectl run mypod --image=nginx --env="ENV=prod"


🔹 Deployments
#Create Deployment:
kubectl create deployment myapp --image=nginx

# Create Deployment with réplicas
kubectl create deployment myapp --image=nginx --replicas=3


#Scale Deployment:
kubectl scale deployment myapp --replicas=5

# Update image in Deployment
kubectl set image deployment/myapp nginx=nginx:1.19

# View rollout status
kubectl rollout status deployment myapp

# Deployment history
kubectl rollout history deployment myapp

# Revert to a previous version
kubectl rollout undo deployment myapp

🔹 ReplicaSets
#They are usually created through Deployments, but you can list them
kubectl get rs

🔹 Jobs y CronJobs

# Create Job
kubectl create job myjob --image=busybox -- echo "Hello CKAD"

# Create CronJob
kubectl create cronjob mycron --image=busybox --schedule="*/1 * * * *" -- echo "Hello CKAD"

🔹 Useful maintenance requirements

# Delete Pod/Deployment:
kubectl delete pod mypod
kubectl delete deployment myapp

# Describe resources
kubectl describe pod mypod
kubectl describe deployment myapp
```

Exam Strategy
Memorize the fastest commands: kubectl run, kubectl create deployment, kubectl scale, kubectl set image, kubectl rollout.

Practice Jobs and CronJobs, as they often appear in practical scenarios.

Use kubectl explain <resource> if you need to remember YAML fields.

Think speed: imperatives are your shortcut to avoid wasting time writing long manifests.

✅ In summary: The most important imperatives are kubectl run, kubectl create deployment, kubectl scale, kubectl set image, kubectl rollout, along with kubectl create job and kubectl create cronjob.

## 🎯 Mock Scenarios

- [Mock 1: Blue-Green deployment](mocks/mock01-blue-green-deployment.md)
- [Mock 2: Canary release strategy](mocks/mock02-canary-release.md)
-[Mock 2.1 Canary release strategy with imperative kubectl commands](/02-application-deployment/mocks/mock02.1-canary-strategy-imperative-commands.md)
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