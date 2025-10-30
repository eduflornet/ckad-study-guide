# Lab 1: Deployment Basics

**Objective**: Master the fundamentals of Kubernetes Deployments
**Time**: 30 minutes
**Difficulty**: Beginner

## Learning Goals

- Create and manage Kubernetes Deployments
- Scale applications up and down
- Understand Deployment specifications
- Monitor Deployment status
- Work with ReplicaSets
- Configure resource requirements

## Exercise 1: Create Your First Deployment (10 minutes)

### Task 1.1: Create a Basic Deployment

Create a simple nginx Deployment:

```bash
# Create a deployment using kubectl
kubectl create deployment nginx-app --image=nginx:1.21

# Alternatively, create using YAML
cat << EOF > nginx-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-app
  labels:
    app: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "128Mi"
            cpu: "100m"
EOF

# Apply the deployment
kubectl apply -f nginx-deployment.yaml
```

### Task 1.2: Examine the Deployment

```bash
# Get deployment information
kubectl get deployments
kubectl get deployment nginx-app -o wide

# Describe the deployment
kubectl describe deployment nginx-app

# Check the ReplicaSet created by the deployment
kubectl get replicasets
kubectl get rs -l app=nginx

# View the pods
kubectl get pods -l app=nginx
kubectl get pods -l app=nginx -o wide
```

**Questions:**
1. How many ReplicaSets were created?
2. What is the relationship between Deployment, ReplicaSet, and Pods?
3. What happens if you delete one of the pods?

### Task 1.3: Test Pod Self-Healing

```bash
# Delete a pod and watch it get recreated
kubectl delete pod <pod-name>

# Watch pods in real-time
kubectl get pods -l app=nginx -w

# Check deployment status
kubectl rollout status deployment/nginx-app
```

## Exercise 2: Scaling Deployments (10 minutes)

### Task 2.1: Manual Scaling

```bash
# Scale up to 5 replicas
kubectl scale deployment nginx-app --replicas=5

# Verify scaling
kubectl get deployments
kubectl get pods -l app=nginx

# Scale down to 2 replicas
kubectl scale deployment nginx-app --replicas=2

# Watch the scaling process
kubectl get pods -l app=nginx -w
```

### Task 2.2: Declarative Scaling

```bash
# Edit the deployment YAML
kubectl edit deployment nginx-app

# Or patch the deployment
kubectl patch deployment nginx-app -p '{"spec":{"replicas":4}}'

# Verify changes
kubectl get deployment nginx-app
```

### Task 2.3: Resource Management

Create a deployment with specific resource requirements:

```yaml
cat << EOF > resource-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: resource-app
  labels:
    app: resource-test
spec:
  replicas: 2
  selector:
    matchLabels:
      app: resource-test
  template:
    metadata:
      labels:
        app: resource-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
EOF

kubectl apply -f resource-deployment.yaml
```

## Exercise 3: Deployment Management (10 minutes)

### Task 3.1: Labeling and Selectors

```bash
# Add labels to deployment
kubectl label deployment nginx-app version=v1 environment=test

# View labels
kubectl get deployment nginx-app --show-labels

# Select deployments by label
kubectl get deployments -l environment=test
kubectl get deployments -l version=v1

# Update pod template labels
kubectl patch deployment nginx-app -p '{"spec":{"template":{"metadata":{"labels":{"version":"v1","tier":"frontend"}}}}}'
```

### Task 3.2: Deployment Annotations

```bash
# Add annotations to deployment
kubectl annotate deployment nginx-app deployment.kubernetes.io/revision="1"
kubectl annotate deployment nginx-app contact="admin@company.com"

# View annotations
kubectl get deployment nginx-app -o yaml | grep -A 10 annotations
```

### Task 3.3: Working with ReplicaSets

```bash
# List all ReplicaSets
kubectl get replicasets

# Get ReplicaSet details
kubectl describe rs <replicaset-name>

# Manually scale a ReplicaSet (not recommended)
kubectl scale rs <replicaset-name> --replicas=1

# Observe what happens
kubectl get deployment nginx-app
kubectl get rs -l app=nginx
```

## Exercise 4: Advanced Deployment Features (Bonus)

### Task 4.1: Deployment with Multiple Containers

```yaml
cat << EOF > multi-container-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: multi-container-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: multi-container
  template:
    metadata:
      labels:
        app: multi-container
    spec:
      containers:
      - name: web
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: shared-volume
          mountPath: /usr/share/nginx/html
      - name: content-generator
        image: busybox:1.35
        command:
        - /bin/sh
        - -c
        - |
          while true; do
            echo "<h1>Current time: $(date)</h1>" > /shared/index.html
            sleep 30
          done
        volumeMounts:
        - name: shared-volume
          mountPath: /shared
      volumes:
      - name: shared-volume
        emptyDir: {}
EOF

kubectl apply -f multi-container-deployment.yaml
```

### Task 4.2: Deployment with ConfigMap

```bash
# Create a ConfigMap
kubectl create configmap nginx-config --from-literal=server_name=example.com

# Create deployment using ConfigMap
cat << EOF > configmap-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: configmap-app
spec:
  replicas: 2
  selector:
    matchLabels:
      app: configmap-test
  template:
    metadata:
      labels:
        app: configmap-test
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        env:
        - name: SERVER_NAME
          valueFrom:
            configMapKeyRef:
              name: nginx-config
              key: server_name
        ports:
        - containerPort: 80
EOF

kubectl apply -f configmap-deployment.yaml
```

## Troubleshooting Common Issues

### Issue 1: Deployment Not Starting

```bash
# Check deployment status
kubectl get deployment <deployment-name>

# Check events
kubectl describe deployment <deployment-name>

# Check pod status
kubectl get pods -l app=<app-label>
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Issue 2: Insufficient Resources

```bash
# Check node resources
kubectl top nodes

# Check pod resource usage
kubectl top pods

# Describe nodes to see allocated resources
kubectl describe nodes
```

### Issue 3: Image Pull Issues

```bash
# Check pod events
kubectl describe pod <pod-name>

# Common solutions:
# - Verify image name and tag
# - Check image pull secrets
# - Ensure image registry is accessible
```

## Lab Validation

Verify your lab completion:

```bash
# Check all deployments
kubectl get deployments

# Verify scaling works
kubectl scale deployment nginx-app --replicas=6
kubectl get pods -l app=nginx

# Clean up resources
kubectl delete deployment nginx-app resource-app multi-container-app configmap-app
kubectl delete configmap nginx-config
```

## Key Takeaways

1. **Deployments** manage ReplicaSets, which manage Pods
2. **Scaling** can be done manually or declaratively
3. **Resource limits** prevent containers from consuming too many resources
4. **Labels and selectors** are crucial for Deployment management
5. **Self-healing** ensures desired state is maintained
6. **ReplicaSets** are typically managed by Deployments, not directly

## Next Steps

- Practice with different deployment strategies
- Learn about rolling updates and rollbacks (Lab 2)
- Explore deployment patterns (Lab 3)
- Try horizontal pod autoscaling

## Common CKAD Tasks

Practice these common exam scenarios:

```bash
# 1. Create deployment with 3 replicas
kubectl create deployment web --image=nginx:1.21 --replicas=3

# 2. Scale deployment to 5 replicas
kubectl scale deployment web --replicas=5

# 3. Set resource limits
kubectl set resources deployment web --limits=cpu=200m,memory=256Mi

# 4. Add environment variable
kubectl set env deployment web ENV=production

# 5. Check deployment status
kubectl rollout status deployment web
```