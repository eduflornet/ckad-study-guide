# Lab 4: Helm Basics

**Objective**: Learn Helm fundamentals for Kubernetes package management
**Time**: 35 minutes
**Difficulty**: Beginner

## Learning Goals

- Install and configure Helm
- Understand Helm charts and repositories
- Deploy applications using Helm charts
- Manage Helm releases
- Configure chart values
- Upgrade and rollback releases

## Prerequisites

Ensure Helm is installed. If not, install it:

```bash
# For Windows (using chocolatey)
choco install kubernetes-helm

# For macOS (using homebrew)
brew install helm

# For Linux
curl https://get.helm.sh/helm-v3.12.0-linux-amd64.tar.gz | tar -xzO linux-amd64/helm > /usr/local/bin/helm
chmod +x /usr/local/bin/helm

# Verify installation
helm version
```

## [Exercise 1: Helm Setup and Repository Management (10 minutes)](/02-application-deployment/labs/lab04-solution/exercise-01/)

### Task 1.1: Initialize Helm

```bash
# Check Helm version
helm version

# Add the official Helm stable charts repository
helm repo add stable https://charts.helm.sh/stable

# Add Bitnami repository (more up-to-date charts)
helm repo add bitnami https://charts.bitnami.com/bitnami

# Add ingress-nginx repository
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx

# List added repositories
helm repo list

# Update repositories
helm repo update
```

### Task 1.2: Search for Charts

```bash
# Search for nginx charts
helm search repo nginx

# Search for specific chart
helm search repo bitnami/nginx

# Search for all charts in bitnami repo
helm search repo bitnami/

# Get detailed information about a chart
helm show chart bitnami/nginx
helm show readme bitnami/nginx
helm show values bitnami/nginx
```

### Task 1.3: Chart Information

```bash
# Show all information about a chart
helm show all bitnami/apache

# Show only values
helm show values bitnami/apache > apache-values.yaml

# View the values file
cat apache-values.yaml
```

## [Exercise 2: Deploying Applications with Helm (15 minutes)](/02-application-deployment/labs/lab04-solution/exercise-02/)

### Task 2.1: Deploy NGINX with Default Values

```bash
# Create a namespace for our Helm deployments
kubectl create namespace helm-demo

# Deploy nginx with default values
helm install my-nginx bitnami/nginx --namespace helm-demo

# Check the release
helm list --namespace helm-demo

# Check Kubernetes resources created
kubectl get all -n helm-demo
```

### Task 2.2: Deploy with Custom Values

```bash
# Create custom values file
cat << EOF > nginx-custom-values.yaml
replicaCount: 3

image:
  registry: docker.io
  repository: bitnami/nginx
  tag: "1.21"

service:
  type: LoadBalancer
  port: 80

resources:
  limits:
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 50m
    memory: 64Mi

metrics:
  enabled: true

ingress:
  enabled: false

autoscaling:
  enabled: false
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80
EOF

# Deploy with custom values
helm install my-custom-nginx bitnami/nginx \
  --namespace helm-demo \
  --values nginx-custom-values.yaml

# Check the deployment
kubectl get deployments -n helm-demo
kubectl get pods -n helm-demo
```

### Task 2.3: Deploy with Inline Values

```bash
# Deploy with inline value overrides
helm install my-inline-nginx bitnami/nginx \
  --namespace helm-demo \
  --set replicaCount=2 \
  --set service.type=ClusterIP \
  --set image.tag=1.20

# Verify deployment
kubectl get deployments -n helm-demo
helm list --namespace helm-demo
```

### Task 2.4: Deploy Apache with Complex Configuration

```bash
# Create Apache values
cat << EOF > apache-values.yaml
replicaCount: 2

image:
  tag: "2.4"

service:
  type: ClusterIP
  port: 8080

httpd:
  enableXFF: true
  
resources:
  limits:
    cpu: 200m
    memory: 256Mi
  requests:
    cpu: 100m
    memory: 128Mi

persistence:
  enabled: false

metrics:
  enabled: true
EOF

# Deploy Apache
helm install my-apache bitnami/apache \
  --namespace helm-demo \
  --values apache-values.yaml

# Verify deployment
kubectl get all -n helm-demo -l app.kubernetes.io/name=apache
```

## [Exercise 3: Managing Helm Releases (10 minutes)](/02-application-deployment/labs/lab04-solution/exercise-03/)

### Task 3.1: List and Inspect Releases

```bash
# List all releases
helm list --all-namespaces

# List releases in specific namespace
helm list --namespace helm-demo

# Get release history
helm history my-nginx --namespace helm-demo

# Get release status
helm status my-nginx --namespace helm-demo

# Get release values
helm get values my-nginx --namespace helm-demo
helm get values my-custom-nginx --namespace helm-demo
```

### Task 3.2: Upgrade Releases

```bash
# Upgrade with new values
helm upgrade my-nginx bitnami/nginx \
  --namespace helm-demo \
  --set replicaCount=4 \
  --set image.tag=1.22

# Check upgrade
helm history my-nginx --namespace helm-demo
kubectl get pods -n helm-demo -l app.kubernetes.io/name=nginx

# Upgrade using values file
cat << EOF > nginx-upgrade-values.yaml
replicaCount: 5

image:
  tag: "1.23"

service:
  type: LoadBalancer

resources:
  limits:
    cpu: 150m
    memory: 256Mi
  requests:
    cpu: 75m
    memory: 128Mi
EOF

helm upgrade my-custom-nginx bitnami/nginx \
  --namespace helm-demo \
  --values nginx-upgrade-values.yaml

# Verify upgrade
helm get values my-custom-nginx --namespace helm-demo
```

### Task 3.3: Rollback Releases

```bash
# Check history before rollback
helm history my-nginx --namespace helm-demo

# Rollback to previous version
helm rollback my-nginx --namespace helm-demo

# Rollback to specific revision
helm rollback my-nginx 1 --namespace helm-demo

# Verify rollback
helm history my-nginx --namespace helm-demo
kubectl get pods -n helm-demo -l app.kubernetes.io/name=nginx
```

### Task 3.4: Uninstall Releases

```bash
# Uninstall a release
helm uninstall my-inline-nginx --namespace helm-demo

# Verify uninstallation
helm list --namespace helm-demo
kubectl get all -n helm-demo

# Uninstall with keeping history
helm uninstall my-apache --namespace helm-demo --keep-history

# Check that history is kept
helm history my-apache --namespace helm-demo
```

## [Exercise 4: Working with Chart Values (Bonus)](/02-application-deployment/labs/lab04-solution/exercise-04/)

### Task 4.1: Understanding Chart Structure

```bash
# Download a chart to examine its structure
helm pull bitnami/nginx --untar

# Examine the chart structure
ls -la nginx/
cat nginx/Chart.yaml
cat nginx/values.yaml
ls nginx/templates/
```

### Task 4.2: Template Debugging

```bash
# Render templates without installing
helm template my-test bitnami/nginx \
  --values nginx-custom-values.yaml \
  --namespace helm-demo

# Debug specific values
helm template my-test bitnami/nginx \
  --set replicaCount=3 \
  --set service.type=NodePort \
  --namespace helm-demo

# Lint the chart
helm lint nginx/
```

### Task 4.3: Dry Run Installations

```bash
# Perform dry run to see what would be installed
helm install my-dry-run bitnami/nginx \
  --namespace helm-demo \
  --dry-run \
  --debug

# Dry run with custom values
helm install my-dry-run bitnami/nginx \
  --namespace helm-demo \
  --values nginx-custom-values.yaml \
  --dry-run
```

## [Exercise 5: Advanced Helm Operations (Bonus)](/02-application-deployment/labs/lab04-solution/exercise-05/)

### Task 5.1: Chart Dependencies

```bash
# Create a chart with dependencies
helm create my-webapp

# Edit Chart.yaml to add dependencies
cat << EOF >> my-webapp/Chart.yaml

dependencies:
  - name: nginx
    version: "13.x.x"
    repository: "https://charts.bitnami.com/bitnami"
  - name: redis
    version: "17.x.x" 
    repository: "https://charts.bitnami.com/bitnami"
    condition: redis.enabled
EOF

# Update dependencies
cd my-webapp
helm dependency update
cd ..

# Check dependencies
ls my-webapp/charts/
```

### Task 5.2: Release Testing

```bash
# Install with test hooks
helm install test-release bitnami/nginx \
  --namespace helm-demo \
  --set replicaCount=1

# Run tests
helm test test-release --namespace helm-demo

# Check test pods
kubectl get pods -n helm-demo -l app.kubernetes.io/name=nginx
```

## Lab Validation

### Validation Commands

```bash
# Check all Helm releases
helm list --all-namespaces

# Verify deployments are running
kubectl get deployments -n helm-demo

# Check services
kubectl get services -n helm-demo

# Test application accessibility
kubectl port-forward -n helm-demo svc/my-nginx 8080:80 &
curl http://localhost:8080

# Kill port-forward
pkill -f "kubectl port-forward"
```

### Health Checks

```bash
# Check pod health
kubectl get pods -n helm-demo
kubectl describe pods -n helm-demo

# Check Helm release status
helm status my-nginx --namespace helm-demo
helm status my-custom-nginx --namespace helm-demo
```

## Troubleshooting Common Issues

### Issue 1: Repository Not Found

```bash
# Update repositories
helm repo update

# List repositories
helm repo list

# Re-add repository if needed
helm repo add bitnami https://charts.bitnami.com/bitnami
```

### Issue 2: Release Installation Failed

```bash
# Check release status
helm status <release-name> --namespace <namespace>

# Get release history
helm history <release-name> --namespace <namespace>

# Check Kubernetes events
kubectl get events -n <namespace> --sort-by=.metadata.creationTimestamp
```

### Issue 3: Values Not Applied

```bash
# Check actual values used
helm get values <release-name> --namespace <namespace>

# Compare with chart defaults
helm show values <chart-name>

# Use --debug flag for troubleshooting
helm install <release-name> <chart> --debug --dry-run
```

## Cleanup

```bash
# Uninstall all releases
helm uninstall my-nginx --namespace helm-demo
helm uninstall my-custom-nginx --namespace helm-demo
helm uninstall test-release --namespace helm-demo

# Delete namespace
kubectl delete namespace helm-demo

# Clean up downloaded files
rm -f nginx-custom-values.yaml nginx-upgrade-values.yaml apache-values.yaml
rm -rf nginx/ my-webapp/
```

## Key Takeaways

1. **Helm** simplifies Kubernetes application deployment and management
2. **Charts** are packages of Kubernetes resources
3. **Values** allow customization without modifying charts
4. **Releases** are instances of charts deployed to clusters
5. **Repositories** provide collections of charts
6. **Upgrades and rollbacks** are seamless with Helm

## Best Practices

1. Always use specific chart versions in production
2. Use values files instead of inline --set parameters
3. Test deployments with --dry-run first
4. Keep track of release history
5. Use namespaces to organize releases
6. Backup values files and configurations

## Common CKAD Tasks

```bash
# 1. Install chart with custom values
helm install myapp bitnami/nginx --set replicaCount=3

# 2. Upgrade release
helm upgrade myapp bitnami/nginx --set image.tag=1.21

# 3. Check release status
helm status myapp

# 4. Rollback release
helm rollback myapp

# 5. List releases
helm list

# 6. Uninstall release
helm uninstall myapp
```

## Next Steps

- Learn to create custom Helm charts (Lab 5)
- Practice advanced release management (Lab 6)
- Explore Helm hooks and tests
- Study chart security best practices